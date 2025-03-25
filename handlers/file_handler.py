import os
import aiohttp
import tempfile
from urllib.parse import urlparse, unquote
from utils.downloader import get_file_size, download_file_in_chunks, MAX_CHUNK_SIZE
from utils.compressor import compress_file_to_rar
import zipfile

def get_filename_from_url(url):
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    return unquote(filename) if filename else "archivo_descargado"

def compress_file_to_zip(input_path, output_dir):
    zip_path = os.path.join(output_dir, os.path.basename(input_path) + ".zip")
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(input_path, arcname=os.path.basename(input_path))
        return zip_path
    except Exception as e:
        print(f"[ERROR] ZIP: {e}")
        return None

async def download_file_with_progress(url, client, chat_id, temp_dir):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Código de estado: {response.status}")
                
                total_size = int(response.headers.get('Content-Length', 0))
                file_name = get_filename_from_url(url)
                temp_file_path = os.path.join(temp_dir, file_name)
                
                progress_message = await client.send_message(chat_id, "⏳ Descargando: 0%")
                downloaded = 0
                last_progress = 0

                with open(temp_file_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(1024 * 64):
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            if progress - last_progress >= 5:
                                last_progress = progress
                                try:
                                    await progress_message.edit(f"⏳ Descargando: {progress}%")
                                except:
                                    pass

                await progress_message.edit("✅ Descarga completada")
                return temp_file_path
                
    except Exception as e:
        error_msg = f"❌ Error en descarga: {str(e)[:150]}"
        await client.send_message(chat_id, error_msg)
        raise

async def process_file_request(url, client, chat_id):
    try:
        file_size = get_file_size(url)
        if not file_size:
            await client.send_message(chat_id, "❌ No se pudo obtener el tamaño")
            return False

        with tempfile.TemporaryDirectory() as temp_dir:
            await client.send_message(chat_id, f"📦 Tamaño del archivo: {file_size/1024/1024:.2f} MB")
            
            if file_size <= MAX_CHUNK_SIZE:
                # Descarga normal
                file_path = await download_file_with_progress(url, client, chat_id, temp_dir)
                await client.send_message(chat_id, "⚙️ Comprimiendo archivo...")
                
                # Intentar RAR primero
                try:
                    rar_path = compress_file_to_rar(file_path, temp_dir)
                except Exception as e:
                    await client.send_message(chat_id, "⚠️ Falló compresión RAR, usando ZIP")
                    rar_path = compress_file_to_zip(file_path, temp_dir)
                
                if rar_path and os.path.exists(rar_path):
                    await client.send_message(chat_id, "📤 Enviando archivo...")
                    await client.send_file(chat_id, rar_path, caption="✅ Archivo procesado")
                    return True
                else:
                    await client.send_message(chat_id, "❌ Falló la compresión")
                    return False
            else:
                # Lógica para archivos grandes
                await client.send_message(chat_id, "🔀 Procesando archivo grande en partes...")
                chunk_paths = download_file_in_chunks(url, temp_dir)
                for chunk in chunk_paths:
                    await client.send_file(chat_id, chunk, caption="📦 Parte de archivo")
                return True
                
    except Exception as e:
        await client.send_message(chat_id, f"❌ Error crítico: {str(e)[:150]}")
        return False
    finally:
        await client.send_message(chat_id, "🧹 Todos los archivos temporales han sido eliminados")
