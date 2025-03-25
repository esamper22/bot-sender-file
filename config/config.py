# Credenciales de Telegram (API_ID, API_HASH, PHONE)
import os
from dotenv import load_dotenv

# config/config.py
load_dotenv()
API_ID = os.getenv("API_ID")  # Carga el API_ID desde las variables de entorno
API_HASH = os.getenv("API_HASH")  # Carga el API_HASH desde las variables de entorno
# TELEGRAM_TOKEN_API = os.getenv("TELEGRAM_TOKEN_API")  # Carga el token de la API de Telegram desde las variables de entorno
PHONE = os.getenv("PHONE_NUMBER")  # Carga el número de teléfono desde las variables de entorno
TELEGRAM_SESSION = os.getenv("TELEGRAM_SESSION")  # Carga el nombre de la sesión desde las variables de entorno
ALLOWED_CHAT = os.getenv("ALLOWED_CHAT")  # Carga el ID del chat permitido desde las variables de entorno