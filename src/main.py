import os
import threading
from bot import main as bot_main
from web_interface import app, create_orders_csv
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def setup_directories():
    """Create necessary directories and files"""
    try:
        # Get base path
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Create data directory if it doesn't exist
        data_dir = os.path.join(base_path, 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Create templates directory if it doesn't exist
        templates_dir = os.path.join(base_path, 'src', 'templates')
        os.makedirs(templates_dir, exist_ok=True)
        
        # Create orders.csv if it doesn't exist
        create_orders_csv()
        
        logger.info("Directory setup completed successfully")
    except Exception as e:
        logger.error(f"Error setting up directories: {str(e)}")
        raise

def run_bot():
    """Run the Telegram bot"""
    try:
        logger.info("Starting Telegram bot...")
        bot_main()
    except Exception as e:
        logger.error(f"Error in bot: {str(e)}")

def run_web():
    """Run the Flask web interface"""
    try:
        logger.info("Starting web interface...")
        # Set the template folder path
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        app.template_folder = template_dir
        
        # Get port from environment variable or use default
        port = int(os.getenv('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Error in web interface: {str(e)}")

def main():
    """Start both the bot and web interface in separate threads"""
    try:
        # Setup directories first
        setup_directories()
        
        # Create threads for bot and web interface
        bot_thread = threading.Thread(target=run_bot, name="BotThread")
        web_thread = threading.Thread(target=run_web, name="WebThread")
        
        # Make threads daemon so they exit when main program exits
        bot_thread.daemon = True
        web_thread.daemon = True
        
        # Start both threads
        logger.info("Starting services...")
        bot_thread.start()
        web_thread.start()
        
        # Keep main thread alive
        while True:
            bot_thread.join(1)
            web_thread.join(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main() 