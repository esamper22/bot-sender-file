import os
import aiohttp
import tempfile
from urllib.parse import urlparse, unquote
from utils.downloader import get_file_size, download_file_in_chunks, MAX_CHUNK_SIZE
from utils.compressor import compress_file_to_rar  # Función original que usa "rar"
import zipfile

def get_filename_from_url(url):
    """
    Extrae y sanitiza el nombre de archivo de la URL,
    ignorando parámetros y caracteres especiales.
    """
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    filename = unquote(filename)
    return filename if filename else "archivo_descargado"

def compress_file_to_zip(input_path, output_dir):
    """
    Comprime el archivo de entrada a formato ZIP y retorna la ruta del archivo ZIP.
    """
    zip_path = os.path.join(output_dir, os.path.basename(input_path) + ".zip")
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(input_path, arcname=os.path.basename(input_path))
        return zip_path
    except Exception as e:
        print(f"[DEBUG] Error comprimiendo a ZIP: {e}")
        return None

async def download_file_with_progress(url, client, chat_id, temp_dir):
    """
    Descarga el archivo mostrando el progreso, actualizando cada 5%.
    Utiliza el directorio temporal proporcionado para almacenar el archivo.
    Retorna la ruta del archivo descargado.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Error al descargar, código de estado: {response.status}")
                total_size = response.headers.get('Content-Length')
                if total_size is None:
                    raise Exception("No se encontró la cabecera 'Content-Length'.")
                total_size = int(total_size)
                file_name = get_filename_from_url(url)
                temp_file_path = os.path.join(temp_dir, file_name)
                print(f"[DEBUG] Archivo se guardará en: {temp_file_path}")
                downloaded = 0
                last_progress = 0

                progress_message = await client.send_message(chat_id, "Descargando: 0%")
                with open(temp_file_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(1024 * 64):
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Actualiza cada 5%
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            if progress - last_progress >= 5:
                                last_progress = progress
                                try:
                                    await progress_message.edit(f"Descargando: {progress}%")
                                except Exception as e:
                                    print("Error editando progreso:", e)
                print(f"[DEBUG] Descarga completada. Bytes descargados: {downloaded} / {total_size}")
                # Verificamos que el archivo se descargó correctamente
                if not os.path.exists(temp_file_path):
                    raise Exception(f"El archivo no se encontró en {temp_file_path}")
                actual_size = os.path.getsize(temp_file_path)
                print(f"[DEBUG] Tamaño del archivo en disco: {actual_size} bytes")
                if actual_size < total_size:
                    raise Exception(f"Archivo incompleto. Se esperaba {total_size} bytes, se descargaron {actual_size} bytes.")
                await progress_message.edit("Descarga completada.")
                return temp_file_path
    except Exception as e:
        error_msg = f"❌ Error durante la descarga: {e}"
        await client.send_message(chat_id, error_msg)
        print(error_msg)
        raise

async def process_file_request(url, client, chat_id):
    """
    Procesa la solicitud:
      - Si el archivo es menor o igual a 2GB, se descarga con barra de progreso,
        se comprime (usando RAR o, en caso de error, ZIP) y se envía a Telegram.
      - Si es mayor a 2GB, se descarga en partes, se comprime cada parte
        y se envía cada segmento.
    Se eliminan los archivos temporales al finalizar.
    """
    try:
        file_size = get_file_size(url)
        if file_size == 0:
            await client.send_message(chat_id, "❌ No se pudo obtener el tamaño del archivo.")
            return

        with tempfile.TemporaryDirectory() as temp_dir:
            if file_size <= MAX_CHUNK_SIZE:
                file_path = await download_file_with_progress(url, client, chat_id, temp_dir)
                if not os.path.exists(file_path):
                    raise Exception(f"El archivo descargado no se encontró en {file_path}")
                print(f"[DEBUG] Archivo descargado correctamente: {file_path}")
                # Intentamos comprimir usando RAR
                try:
                    rar_path = compress_file_to_rar(file_path, temp_dir)
                except Exception as e:
                    print(f"[DEBUG] Error en compresión RAR: {e}")
                    rar_path = None
                # Si falla la compresión RAR, usamos ZIP
                if not rar_path or not os.path.exists(rar_path):
                    print("[DEBUG] Se usará compresión a ZIP como alternativa.")
                    rar_path = compress_file_to_zip(file_path, temp_dir)
                    if not rar_path or not os.path.exists(rar_path):
                        raise Exception("No se pudo comprimir el archivo con RAR ni ZIP.")
                print(f"[DEBUG] Archivo comprimido generado: {rar_path}")
                await client.send_file(chat_id, rar_path, caption="Archivo comprimido")
            else:
                # Para archivos mayores a 2GB, descarga en partes (no se muestra compresión alternativa aquí, pero se podría extender la lógica)
                chunk_paths = download_file_in_chunks(url, temp_dir)
                rar_files = []
                for chunk_path in chunk_paths:
                    if not os.path.exists(chunk_path):
                        print(f"[DEBUG] El chunk {chunk_path} no existe.")
                        continue
                    try:
                        rar_path = compress_file_to_rar(chunk_path, temp_dir)
                    except Exception as e:
                        print(f"[DEBUG] Error en compresión RAR del chunk: {e}")
                        rar_path = compress_file_to_zip(chunk_path, temp_dir)
                    if rar_path and os.path.exists(rar_path):
                        rar_files.append(rar_path)
                for rar_file in rar_files:
                    await client.send_file(chat_id, rar_file, caption="Parte de archivo comprimido")
    except Exception as e:
        await client.send_message(chat_id, f"❌ Error en el procesamiento del archivo: {e}")
    print(f"[DEBUG] Error en process_file_request: {e}")
 
