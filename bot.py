import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai
import logging
from dotenv import load_dotenv
import json

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
model = genai.GenerativeModel("gemini-1.5-pro")

# Create Flask app
app = Flask(__name__)

# Telegram API base URL
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id, text):
    """Send message to Telegram chat"""
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text
        }
        response = requests.post(url, json=data)
        return response.json()
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return None

def set_webhook():
    """Set the webhook URL"""
    try:
        webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
        url = f"{TELEGRAM_API_URL}/setWebhook"
        data = {
            "url": webhook_url,
            "drop_pending_updates": True
        }
        response = requests.post(url, json=data)
        result = response.json()
        logger.info(f"Webhook set result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return None

@app.route('/')
def index():
    return "<h3>✅ Telegram Gemini Bot is running on webhook!</h3>"

@app.route('/health')
def health():
    return jsonify({"status": "ok", "message": "Bot active!"})

@app.route('/set_webhook')
def setup_webhook():
    """Manually set webhook (for debugging)"""
    result = set_webhook()
    return jsonify(result)

@app.route('/webhook_info')
def webhook_info():
    """Get webhook info"""
    try:
        url = f"{TELEGRAM_API_URL}/getWebhookInfo"
        response = requests.get(url)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook updates"""
    try:
        # Get JSON data from request
        json_data = request.get_json()
        
        if not json_data:
            logger.error("No JSON data received")
            return "Bad Request", 400
        
        logger.info("Received webhook update")
        
        # Check if it's a message
        if 'message' in json_data:
            message = json_data['message']
            chat_id = message['chat']['id']
            
            # Handle /start command
            if 'text' in message and message['text'] == 'Hi':
                send_message(chat_id, "Hi! I'm your Gemini AI bot. Ask me anything ✨")
                logger.info(f"Start command handled for chat {chat_id}")
                
            # Handle regular messages
            elif 'text' in message:
                user_text = message['text']
                logger.info(f"Processing message from chat {chat_id}: {user_text[:50]}...")
                
                try:
                    # Generate response with Gemini
                    response = model.generate_content(user_text)
                    send_message(chat_id, response.text)
                    logger.info("Message processed successfully")
                    
                except Exception as e:
                    logger.error(f"Error generating response: {e}")
                    send_message(chat_id, "Sorry, I encountered an error. Please try again.")
        
        return "OK", 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 500

def setup_webhook_on_startup():
    """Set webhook on startup"""
    logger.info("Setting up webhook...")
    set_webhook()

def main():
    """Main function"""
    if not BOT_TOKEN or not GEMINI_API_KEY or not RENDER_EXTERNAL_URL:
        logger.error("Missing required environment variables!")
        logger.error(f"BOT_TOKEN: {'✓' if BOT_TOKEN else '✗'}")
        logger.error(f"GEMINI_API_KEY: {'✓' if GEMINI_API_KEY else '✗'}")
        logger.error(f"RENDER_EXTERNAL_URL: {'✓' if RENDER_EXTERNAL_URL else '✗'}")
        return
    
    logger.info("Starting Telegram Bot...")
    
    # Set webhook immediately
    setup_webhook_on_startup()
    
    # Start Flask app
    logger.info(f"Starting Flask server on port {PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)

if __name__ == '__main__':
    main()
