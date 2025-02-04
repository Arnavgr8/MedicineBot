import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from product_db import ProductDB
from ai_handler import AIHandler
import logging
import sys

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

def get_application_path():
    if getattr(sys, 'frozen', False):
        # If running as exe
        base_path = os.path.dirname(os.path.dirname(sys.executable))
    else:
        # If running as script
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Construct path to the CSV file in the data directory
    data_path = os.path.join(base_path, 'data', os.getenv('dataset_path'))
    return data_path

# Initialize our handlers
csv_path = get_application_path()
product_db = ProductDB(csv_path)
ai_handler = AIHandler()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        'Welcome to MediSearch! 🏥\n\n'
        'I can help you find medicines and their details. You can search by:\n'
        '• Medicine name\n'
        '• Salt composition\n'
        '• Therapeutic class\n\n'
        'Send me any search term to begin!'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        'How to use MediSearch:\n\n'
        '1. Search by medicine name (e.g., "Crocin")\n'
        '2. Search by salt (e.g., "Paracetamol")\n'
        '3. Search by category (e.g., "Antibiotic")\n\n'
        'Click on any medicine to see detailed information including:\n'
        '• Full medicine name\n'
        '• Salt composition\n'
        '• Package size\n'
        '• Manufacturer\n'
        '• Price'
    )

async def search_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search medicines based on user message."""
    query = update.message.text.lower()
    logger.info(f"Received query: {query}")
    
    try:
        # Search for medicines
        products = product_db.search_products(query)
        logger.info(f"Found {len(products)} medicines")
        
        if not products:
            await update.message.reply_text(
                "I couldn't find any medicines matching your query.\n"
                "Try searching by:\n"
                "• Medicine name\n"
                "• Composition\n"
                "• Type"
            )
            return

        # Store search results in user_data
        if not context.user_data:
            context.user_data.clear()
        context.user_data['last_search'] = products[:10]

        # Create inline keyboard with medicine buttons
        keyboard = []
        for idx, product in enumerate(products[:10]):
            # Use shorter callback data
            callback_data = f"med_{idx}"  # Much shorter than JSON
            keyboard.append([InlineKeyboardButton(
                text=f"{product['name'][:30]} - ₹{product['price']:.2f}",
                callback_data=callback_data
            )])

        reply_markup = InlineKeyboardMarkup(keyboard)
        
        total_found = len(products)
        shown = min(10, total_found)
        
        message = (
            f"Found {total_found} medicines matching '{query}'.\n"
            f"Showing first {shown} results. Click for details:"
        )
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        await update.message.reply_text(
            "Sorry, I encountered an error processing your request.\n"
            "Please try again or contact support."
        )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks for medicine details."""
    query = update.callback_query
    try:
        # Parse simpler callback data
        if query.data.startswith("med_"):
            idx = int(query.data.split("_")[1])
            if 'last_search' in context.user_data:
                products = context.user_data['last_search']
                if 0 <= idx < len(products):
                    product = products[idx]
                    detail_text = (
                        f"💊 Medicine Details:\n\n"
                        f"Name: {product['name']}\n"
                        f"Price: ₹{product['price']:.2f}\n"
                        f"Composition: {product['salt']}\n"
                        f"Package Size: {product['package_size']}\n"
                        f"Manufacturer: {product['manufacturer']}\n"
                        f"Type: {product['category']}"
                    )
                    await query.message.reply_text(detail_text)
                else:
                    await query.message.reply_text("Sorry, I couldn't find the medicine details.")
            else:
                await query.message.reply_text("Please search again to see medicine details.")
        
        await query.answer()
    except Exception as e:
        logger.error(f"Error handling button click: {str(e)}")
        await query.message.reply_text("Sorry, there was an error getting the medicine details.")

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN found in environment variables!")
        return
        
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_products))
    application.add_handler(CallbackQueryHandler(button_click))

    logger.info("Bot started!")
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 