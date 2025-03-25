# Función para comprimir un archivo (o trozo) en formato .rar con partición

import subprocess, os, tempfile

def compress_file_to_rar(input_path):
    """
    Comprime el archivo (o trozo) en formato .rar.
    Si el archivo es grande, se crea un .rar segmentado (volúmenes de 2GB).
    Devuelve la ruta del archivo .rar (o la primera parte si es segmentado).
    """
    # Genera un nombre de archivo temporal para el .rar resultante
    temp_dir = tempfile.gettempdir()
    base_name = os.path.basename(input_path)
    output_path = os.path.join(temp_dir, f"{base_name}.rar")
    
    # Comando para comprimir en volúmenes de 2GB:
    # El parámetro -v2g indica un volumen máximo de 2GB
    # El parámetro -m0 indica sin compresión (puedes ajustar el nivel)
    command = ["rar", "a", "-v2g", "-m0", output_path, input_path]
    try:
        subprocess.run(command, check=True)
        # En caso de archivos segmentados, rar genera output_path, output_path.part1.rar, output_path.part2.rar, etc.
        # Retornamos la ruta de la primera parte
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error al comprimir: {e}")
        return None
