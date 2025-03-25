import os
from dotenv import set_key, load_dotenv

def read_session_file(file_path):
    """Lee el contenido del archivo .session"""
    try:
        with open(file_path, 'rb') as file:
            return file.read()
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {file_path}")
        return None
    except Exception as e:
        print(f"❌ Error al leer el archivo: {e}")
        return None

def save_session_to_env(session_data, env_file='.env', chunk_size=1000):
    """Guarda la sesión dividida en partes numeradas en el archivo .env"""
    if not session_data:
        print("❌ No hay datos de sesión para guardar.")
        return False

    parts = len(session_data) // chunk_size + (1 if len(session_data) % chunk_size != 0 else 0)
    
    try:
        # Guardar cada parte
        for i in range(parts):
            part_key = f'TELEGRAM_SESSION_PART_{i}'
            part_value = session_data[i * chunk_size : (i + 1) * chunk_size].hex()
            set_key(env_file, part_key, part_value)
        
        # Guardar el número total de partes al final
        set_key(env_file, 'TELEGRAM_SESSION_PARTS', str(parts))
        
        print(f"✅ Sesión dividida en {parts} partes y guardada en {env_file}")
        return True
    except Exception as e:
        print(f"❌ Error al guardar la sesión: {e}")
        return False
    
def reconstruct_session_from_env(env_file='.env'):
    """Reconstruye la sesión a partir de las partes guardadas en .env"""
    load_dotenv(env_file)
    parts = int(os.getenv('TELEGRAM_SESSION_PARTS', '0'))
    if parts == 0:
        print("❌ No se encontraron partes de la sesión.")
        return None
    
    session_data = b''
    for i in range(parts):
        part_key = f'TELEGRAM_SESSION_PART_{i}'
        part = os.getenv(part_key)
        if part is None:
            print(f"❌ Falta la parte {i} de la sesión.")
            return None
        session_data += bytes.fromhex(part)
    
    return session_data

if __name__ == '__main__':
    load_dotenv()
    TELEGRAM_SESSION = os.environ.get('TELEGRAM_SESSION', '') + '.session'
    print(f"ℹ️ Leyendo datos de sesión desde {TELEGRAM_SESSION}")
    session_data = read_session_file(TELEGRAM_SESSION)
    save_session_to_env(session_data)