import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.request import HTTPXRequest
import requests

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

ENDPOINT = "https://api.adwadev.com/api/gate.php?url="
proxy_url = None

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Hi! Send me one or more URLs (space-separated) or a .txt file with URLs and I will fetch data for you.')

async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    urls = text.split()
    await process_urls(update, context, urls)

async def handle_document(update: Update, context: CallbackContext) -> None:
    document = update.message.document
    if document.file_name.endswith('.txt'):
        file = await document.get_file()
        file_path = await file.download_to_drive()
        with open(file_path, 'r') as f:
            urls = f.read().split()
        await process_urls(update, context, urls)
    else:
        await update.message.reply_text('Please send a valid .txt file.')

async def process_urls(update: Update, context: CallbackContext, urls: list) -> None:
    for url in urls:
        if url.startswith("http://") or url.startswith("https://"):
            try:
                response = requests.get(
                    f"{ENDPOINT}{url}", 
                    proxies={"http": proxy_url, "https": proxy_url} if proxy_url else None
                )
                if response.status_code == 200:
                    data = response.json()
                    formatted_message = (
                        f"*URL:* {data['Site']}\n"
                        f"*Status:* {data['Status']}\n"
                        f"*Gateway:* {data['Gateway']}\n"
                        f"*Captcha:* {data['Captcha']}\n"
                        f"*Cloudflare:* {data['Cloudflare']}\n"
                        f"*GraphQL:* {data['GraphQL']}\n"
                        f"*Platform:* {data['Platform']}\n"
                        f"*IP:* {data['IP Info']['IP']}\n"
                        f"*Country:* {data['IP Info']['Country']}\n"
                        f"*ISP:* {data['IP Info']['ISP']}\n\n"
                    )
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("Owner", url="https://t.me/rundilundlegamera")]
                    ])
                    await update.message.reply_text(formatted_message, parse_mode='Markdown', reply_markup=keyboard)
                else:
                    await update.message.reply_text(f'Failed to fetch data from the URL: {url}')
            except Exception as e:
                await update.message.reply_text(f'Error: {str(e)}')
        else:
            await update.message.reply_text(f'Invalid URL: {url}')

async def set_proxy(update: Update, context: CallbackContext) -> None:
    global proxy_url
    proxy_url = context.args[0] if context.args else None
    await update.message.reply_text(f'Proxy set to: {proxy_url}' if proxy_url else 'Proxy removed.')

def main() -> None:
    request = HTTPXRequest(
        timeout=5.0
    )

    application = Application.builder().token("7428102257:AAEtVfBFNysLcUIK4K0awRHjm96gaP_ogic").request(request).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_proxy))
    application.add_handler(CommandHandler("remove", set_proxy))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.FileExtension("txt") & ~filters.COMMAND, handle_document))

    application.run_polling()

if __name__ == '__main__':
    main()
                  
