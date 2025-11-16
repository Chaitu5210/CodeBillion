from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from memory import Memory

BOT_TOKEN = "8212881730:AAESYCH_R3xs1qE1d2kBgTvGPZNc5zchHhg"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Handling a new message....")
    if update.message is None:
        return
    
    text = update.message.text or "<non-text message>"
    Memory.put(text)

def retrive_telegram_messages():
    print("Starting Telegram message retrieval....")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    app.run_polling()