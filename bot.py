import os
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
import logging
from dotenv import load_dotenv

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
PORT = int(os.environ.get("PORT", 10000))

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Create Flask app
app = Flask(__name__)

# Global bot application
bot_application = None

@app.route('/')
def index():
    return "<h3>✅ Telegram Gemini Bot is running on webhook!</h3>"

@app.route('/health')
def health():
    return {"status": "ok", "message": "Bot active!"}

# Telegram command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    try:
        await update.message.reply_text("Hi! I'm your Gemini AI bot. Ask me anything ✨")
        logger.info(f"Start command handled for user {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error in start command: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    try:
        user_text = update.message.text
        logger.info(f"Processing message: {user_text[:50]}...")
        
        # Generate response with Gemini
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
        
        logger.info("Message processed successfully")
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("Sorry, I encountered an error. Please try again.")

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook updates"""
    try:
        # Get JSON data from request
        json_data = request.get_json(force=True)
        logger.info("Received webhook update")
        
        if not json_data:
            logger.error("No JSON data in webhook request")
            return "Bad Request", 400
        
        # Create Update object
        update = Update.de_json(json_data, bot_application.bot)
        
        # Process update in event loop
        asyncio.run_coroutine_threadsafe(
            bot_application.process_update(update),
            bot_application._loop
        )
        
        return "OK", 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Internal Server Error", 500

async def setup_application():
    """Set up the telegram application"""
    global bot_application
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Initialize application
    await application.initialize()
    await application.start()
    
    # Set webhook
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    logger.info(f"Setting webhook to: {webhook_url}")
    
    await application.bot.set_webhook(
        url=webhook_url,
        drop_pending_updates=True
    )
    
    # Verify webhook
    webhook_info = await application.bot.get_webhook_info()
    logger.info(f"Webhook set successfully: {webhook_info.url}")
    
    bot_application = application
    return application

def main():
    """Main function"""
    if not BOT_TOKEN or not GEMINI_API_KEY or not RENDER_EXTERNAL_URL:
        logger.error("Missing required environment variables!")
        return
    
    logger.info("Starting Telegram Bot...")
    
    # Set up asyncio event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Setup bot application
    try:
        application = loop.run_until_complete(setup_application())
        application._loop = loop
        logger.info("Bot application setup complete!")
        
        # Start Flask app
        logger.info(f"Starting Flask server on port {PORT}")
        app.run(host="0.0.0.0", port=PORT, debug=False)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
    finally:
        if bot_application:
            loop.run_until_complete(bot_application.shutdown())

if __name__ == '__main__':
    main()
