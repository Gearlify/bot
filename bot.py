from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
from flask import Flask
import google.generativeai as genai
import os
import threading
import time
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")  # e.g. https://telegram-bot-bohe.onrender.com
PORT = int(os.environ.get("PORT", 10000))

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Flask app (for health check and webhook hosting)
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "<h3>✅ Telegram Gemini Bot is running on webhook!</h3>"

@flask_app.route('/health')
def health():
    return {"status": "ok", "message": "Bot active!"}

# Telegram Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! I'm your Gemini AI bot. Ask me anything ✨")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    response = model.generate_content(user_text)
    await update.message.reply_text(response.text)

@flask_app.route('/webhook', methods=['POST'])
def telegram_webhook():
    return "OK", 200

def run_http():
    print(f"🌐 Starting HTTP server on port {PORT}")
    flask_app.run(host="0.0.0.0", port=PORT)

def main():
    if not BOT_TOKEN or not GEMINI_API_KEY:
        print("❌ BOT_TOKEN or GEMINI_API_KEY is missing!")
        return

    print("🚀 Launching Gemini Telegram Bot")

    # Start Flask app in a background thread
    threading.Thread(target=run_http).start()
    time.sleep(2)

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Set webhook URL (important)
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    print(f"🔗 Setting webhook to {webhook_url}")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_path="/webhook",
        webhook_url=webhook_url
    )

if __name__ == '__main__':
    main()
