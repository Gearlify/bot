from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am your bot. How can I help you today?")

# Handle text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    if "hello" in user_message.lower():
        await update.message.reply_text("Hi there!")
    elif "bye" in user_message.lower():
        await update.message.reply_text("Goodbye! Have a nice day!")
    elif "how are you" in user_message.lower():
        await update.message.reply_text("I'm just a bot, but I'm doing great!")
    elif "What are the servies you offer" in user_message.lower():
        await update.message.reply_text("Yh,, I can help you with various tasks like answering questions, providing information, and more. Just ask!")
    else:
        await update.message.reply_text(f"You said: {user_message}")

# Main function
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is running...")
    app.run_polling()
