# Funciones para descargar archivos en modo streaming y particionarlos
import requests
import os
import tempfile

# Tamaño máximo de cada trozo en bytes (2GB)
MAX_CHUNK_SIZE = 2 * 1024**3

def get_file_size(url):
    """
    Obtiene el tamaño del archivo desde la URL.
    """
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        response.raise_for_status()
        size = int(response.headers.get('Content-Length', 0))
        return size
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener el tamaño del archivo: {e}")
        return 0

def download_file_in_chunks(url):
    """
    Descarga el archivo desde la URL en trozos de 2GB.
    Devuelve una lista de rutas temporales a los archivos descargados.
    """
    try:
        file_size = get_file_size(url)
        chunk_paths = []

        # Si no se puede determinar o es menor a 2GB, se descarga de una vez
        if file_size == 0 or file_size <= MAX_CHUNK_SIZE:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.bin')
            try:
                with requests.get(url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(temp_file.name, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                chunk_paths.append(temp_file.name)
            except requests.exceptions.RequestException as e:
                print(f"Error al descargar el archivo: {e}")
                os.unlink(temp_file.name)  # Elimina el archivo temporal en caso de error
        else:
            # Descarga por partes: calcula el número de partes y descarga cada una
            headers = {}
            start = 0
            part = 1
            while start < file_size:
                end = min(start + MAX_CHUNK_SIZE - 1, file_size - 1)
                headers['Range'] = f'bytes={start}-{end}'
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'_part{part}.bin')
                try:
                    with requests.get(url, headers=headers, stream=True, timeout=30) as r:
                        r.raise_for_status()
                        with open(temp_file.name, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                    chunk_paths.append(temp_file.name)
                except requests.exceptions.RequestException as e:
                    print(f"Error al descargar la parte {part}: {e}")
                    os.unlink(temp_file.name)  # Elimina el archivo temporal en caso de error
                    break
                start += MAX_CHUNK_SIZE
                part += 1

        return chunk_paths
    except Exception as e:
        print(f"Error inesperado: {e}")
        return []
