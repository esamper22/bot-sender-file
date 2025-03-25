import asyncio
import re
from telethon import TelegramClient, events
from telethon.errors import ChatWriteForbiddenError
from config.config import API_ID, API_HASH, PHONE, TELEGRAM_SESSION, ALLOWED_CHAT
from handlers.file_handler import process_file_request

client = TelegramClient(TELEGRAM_SESSION, API_ID, API_HASH)
ALLOWED_CHAT_ID = int(ALLOWED_CHAT)

# Diccionarios para gestionar solicitudes
pending_requests = {}  # chat_id -> URL pendiente
active_requests = {}   # chat_id -> bool (solicitud en proceso)

@client.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    if event.chat_id != ALLOWED_CHAT_ID:
        return
    try:
        welcome_text = (
            "👋 ¡Hola! Bienvenido al bot de envío de archivos.\n\n"
            "📋 Comandos disponibles:\n"
            "➡️ /sendfile - Inicia el proceso para enviar un archivo desde una URL.\n"
            "➡️ /help - Muestra este menú de ayuda.\n"
        )
        await event.reply(welcome_text)
    except ChatWriteForbiddenError:
        print(f"No se puede escribir en el chat {event.chat_id}.")
    except Exception as e:
        print("Error en start_command:", e)

@client.on(events.NewMessage(pattern='/help'))
async def help_command(event):
    if event.chat_id != ALLOWED_CHAT_ID:
        return
    try:
        help_text = (
            "ℹ️ *Ayuda del Bot*\n\n"
            "Comandos disponibles:\n"
            "➡️ /sendfile - Inicia el proceso para enviar un archivo desde una URL.\n"
            "➡️ /help - Muestra este menú de ayuda.\n\n"
            "Para enviar un archivo, usa /sendfile y luego envía la URL.\n"
            "Responde con **descargar** para iniciar o **cancelar** para abortar."
        )
        await event.reply(help_text, parse_mode='markdown')
    except ChatWriteForbiddenError:
        print(f"No se puede escribir en el chat {event.chat_id}.")
    except Exception as e:
        print("Error en help_command:", e)

@client.on(events.NewMessage(pattern='/sendfile'))
async def sendfile_command_handler(event):
    if event.chat_id != ALLOWED_CHAT_ID:
        return
    try:
        if active_requests.get(event.chat_id, False):
            await event.reply("⚠️ Ya tienes una solicitud activa. Espera a que termine.")
            return
        pending_requests.pop(event.chat_id, None)
        await event.reply("📥 Por favor, envía la URL del archivo que deseas descargar y enviar.")
    except ChatWriteForbiddenError:
        print(f"No se puede escribir en el chat {event.chat_id}.")
    except Exception as e:
        print("Error en sendfile_command_handler:", e)

@client.on(events.NewMessage)
async def url_message_handler(event):
    if event.chat_id != ALLOWED_CHAT_ID:
        return
    try:
        # Evitamos procesar comandos o respuestas predeterminadas
        if event.raw_text.startswith('/') or event.raw_text.lower() in ("descargar", "cancelar"):
            return

        # Buscar URL en el mensaje
        url_pattern = r'(https?://\S+)'
        match = re.search(url_pattern, event.raw_text)
        if match:
            url = match.group(1)
            if event.chat_id in pending_requests:
                await event.reply("⚠️ Ya tienes una solicitud pendiente. Responde **descargar** o **cancelar**.")
                return
            pending_requests[event.chat_id] = url
            await event.reply(
                f"🔗 *URL detectada:*\n{url}\n\nResponde **descargar** para iniciar o **cancelar** para abortar.",
                parse_mode='markdown'
            )
        else:
            await event.reply("⚠️ No se detectó ninguna URL. Envía una URL válida.")
    except ChatWriteForbiddenError:
        print(f"No se puede escribir en el chat {event.chat_id}.")
    except Exception as e:
        print("Error en url_message_handler:", e)

@client.on(events.NewMessage(chats=ALLOWED_CHAT_ID))
async def user_response_handler(event):
    if event.chat_id not in pending_requests:
        return
    try:
        response = event.raw_text.strip().lower()
        if response == "descargar":
            if active_requests.get(event.chat_id, False):
                await event.reply("⚠️ Ya hay una solicitud activa. Espera a que termine.")
                return
            active_requests[event.chat_id] = True
            await event.reply("⏳ Procesando tu solicitud. Por favor, espera...")
            await process_file_request(pending_requests[event.chat_id], client, event.chat_id)
            await event.reply("✅ Archivo(s) enviado(s) correctamente.")
            pending_requests.pop(event.chat_id, None)
            active_requests.pop(event.chat_id, None)
        elif response == "cancelar":
            await event.reply("❌ Operación cancelada.")
            pending_requests.pop(event.chat_id, None)
    except Exception as e:
        print("Error en user_response_handler:", e)

async def main():
    try:
        await client.start(phone=PHONE)
        print("✅ Cliente iniciado como usuario. Esperando comandos...")
        await client.run_until_disconnected()
    except Exception as e:
        print("Error en main:", e)

if __name__ == '__main__':
    asyncio.run(main())
