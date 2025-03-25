import asyncio
import re
from telethon import TelegramClient, events
# Removed unused import
from config.config import API_ID, API_HASH, PHONE, TELEGRAM_SESSION, ALLOWED_CHAT
from handlers.file_handler import process_file_request

client = TelegramClient(TELEGRAM_SESSION, API_ID, API_HASH)
ALLOWED_CHAT_ID = int(ALLOWED_CHAT)

request_queue = {}  # chat_id: {'url': str, 'active': bool}

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.chat_id != ALLOWED_CHAT_ID:
        return
    await event.reply(
        "🤖 **Bot de Descargas**\n\n"
        "Envía /sendfile seguido de una URL para comenzar\n"
        "Usa /help para ver todos los comandos",
        parse_mode='md'
    )

@client.on(events.NewMessage(pattern='/sendfile'))
async def sendfile_handler(event):
    if event.chat_id != ALLOWED_CHAT_ID:
        return
    
    current = request_queue.get(event.chat_id)
    if current and current['active']:
        await event.reply("⏳ Ya tienes una descarga en progreso")
        return
    
    request_queue[event.chat_id] = {'url': None, 'active': False}
    await event.reply("📥 Por favor envía la URL del archivo")

@client.on(events.NewMessage)
async def message_handler(event):
    if event.chat_id != ALLOWED_CHAT_ID:
        return
    
    # Detectar URLs
    url_match = re.search(r'https?://\S+', event.raw_text)
    if url_match and not event.raw_text.startswith('/') and not event.raw_text.lower() in ['descargar', 'cancelar']:
        if event.chat_id not in request_queue:
            request_queue[event.chat_id] = {
                'url': url_match.group(),
                'active': False
            }
            await event.reply(
                f"🔗 URL detectada:\n{url_match.group()}\n\n"
                "Responde 'descargar' para continuar o 'cancelar' para abortar"
            )
        else:
            await event.reply(
               "Url ya está en cola, responde 'cancelar' para abortar"
            )
    
    # Manejar respuestas
    elif event.raw_text.lower() in ['descargar', 'cancelar']:
        current = request_queue.get(event.chat_id)
        if not current:
            return
            
        if event.raw_text.lower() == 'descargar':
            if current['active']:
                await event.reply("🔄 Ya se está procesando esta solicitud")
                return
                
            request_queue[event.chat_id]['active'] = True
            await event.reply("🚀 Iniciando descarga...")
            
            try:
                # Check if the request was canceled before starting the download
                if event.chat_id not in request_queue or not request_queue[event.chat_id]['active']:
                    await event.reply("❌ Operación cancelada antes de iniciar la descarga")
                    return
                
                success = await process_file_request(
                    current['url'],
                    client,
                    event.chat_id
                )
                
                if success:
                    await event.reply("🎉 Proceso completado exitosamente")
                else:
                    await event.reply("⚠️ Finalizado con errores")
                    
            except Exception as e:
                await event.reply(f"❌ Error fatal: {str(e)[:150]}")
                
            finally:
                del request_queue[event.chat_id]
                
        elif event.raw_text.lower() == 'cancelar':
            try:
                del request_queue[event.chat_id]
                await event.reply("❌ Operación cancelada")
            except:
                await event.reply("❌ No hay operaciones para cancelar")

async def main():
    await client.start(phone=PHONE)
    print("✅ Bot iniciado")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
