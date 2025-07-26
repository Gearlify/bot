from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
from flask import Flask, request
import google.generativeai as genai
import os
import threading
import time
import asyncio
import json
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")  # e.g. https://telegram-bot-xr0o.onrender.com
PORT = int(os.environ.get("PORT", 10000))

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Flask app (for health check and webhook hosting)
flask_app = Flask(__name__)

# Global variable to store the bot application
bot_app = None

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
    try:
        user_text = update.message.text
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        print(f"Error handling message: {e}")
        await update.message.reply_text("Sorry, I encountered an error. Please try again.")

@flask_app.route('/webhook', methods=['POST'])
def telegram_webhook():
    """Handle incoming webhook updates from Telegram"""
    global bot_app
    
    if bot_app is None:
        return "Bot not initialized", 500
    
    try:
        # Get the JSON data from Telegram
        json_data = request.get_json()
        
        if not json_data:
            return "No JSON data received", 400
        
        # Create Update object from JSON
        update = Update.de_json(json_data, bot_app.bot)
        
        # Process the update asynchronously
        asyncio.create_task(bot_app.process_update(update))
        
        return "OK", 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return "Error", 500

def run_flask():
    """Run Flask app"""
    print(f"🌐 Starting Flask server on port {PORT}")
    flask_app.run(host="0.0.0.0", port=PORT, debug=False)

async def setup_bot():
    """Setup the Telegram bot"""
    global bot_app
    
    if not BOT_TOKEN or not GEMINI_API_KEY:
        print("❌ BOT_TOKEN or GEMINI_API_KEY is missing!")
        return None

    print("🤖 Setting up Telegram bot...")
    
    # Create the Application
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Set webhook
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    print(f"🔗 Setting webhook to {webhook_url}")
    
    try:
        await app.bot.set_webhook(url=webhook_url)
        print("✅ Webhook set successfully!")
        
        # Verify webhook
        webhook_info = await app.bot.get_webhook_info()
        print(f"📡 Webhook info: {webhook_info.url}")
        
    except Exception as e:
        print(f"❌ Failed to set webhook: {e}")
        return None
    
    # Initialize the bot
    await app.initialize()
    
    return app

def main():
    """Main function"""
    global bot_app
    
    print("🚀 Launching Gemini Telegram Bot")
    
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Give Flask time to start
    time.sleep(3)
    
    # Setup bot with asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        bot_app = loop.run_until_complete(setup_bot())
        if bot_app:
            print("✅ Bot setup complete! Webhook is active.")
            # Keep the main thread alive
            while True:
                time.sleep(60)
        else:
            print("❌ Failed to setup bot")
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")
    finally:
        if bot_app:
            loop.run_until_complete(bot_app.shutdown())

if __name__ == '__main__':
    main()
