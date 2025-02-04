import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from product_db import ProductDB
from ai_handler import AIHandler
import logging
import sys
import csv
from datetime import datetime
import pandas as pd

# Set up logging - reduce verbosity
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',  # Simplified format
    level=logging.WARNING  # Change to WARNING level
)
logger = logging.getLogger(__name__)

load_dotenv()

def get_base_path():
    """Get the base path of the application"""
    if getattr(sys, 'frozen', False):
        # If running as exe
        return os.path.dirname(os.path.dirname(sys.executable))
    else:
        # If running as script
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Get paths
base_path = get_base_path()
csv_path = os.path.join(base_path, 'data', os.getenv('dataset_path'))
orders_path = os.path.join(base_path, 'data', 'orders.csv')

def create_orders_csv():
    """Create orders.csv if it doesn't exist"""
    if not os.path.exists(orders_path):
        os.makedirs(os.path.dirname(orders_path), exist_ok=True)
        with open(orders_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'order_id', 'user_id', 'user_name', 'medicine_name', 
                'quantity', 'price_per_unit', 'total_price', 'order_date', 
                'status', 'delivery_address'
            ])
        logger.info(f"Created orders.csv at {orders_path}")

# Create orders.csv if needed
create_orders_csv()

# Initialize our handlers
product_db = ProductDB(csv_path)
ai_handler = AIHandler()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        'Welcome to MediSearch! 🏥\n\n'
        'I can help you find and order medicines. You can:\n\n'
        '🔍 Search by:\n'
        '• Medicine name\n'
        '• Salt composition\n'
        '• Therapeutic class\n\n'
        '🛒 Shopping:\n'
        '• Add medicines to cart\n'
        '• View cart with /cart\n'
        '• Place orders\n\n'
        'Send me any search term to begin!\n'
        'Use /help for more details.'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        '📖 How to use MediSearch:\n\n'
        '🔍 Search Medicines:\n'
        '• Type medicine name (e.g., "Crocin")\n'
        '• Type salt name (e.g., "Paracetamol")\n'
        '• Type category (e.g., "Antibiotic")\n\n'
        '🛒 Shopping Commands:\n'
        '• Click "Add to Cart" on any medicine\n'
        '• Use /cart to view your cart\n'
        '• Clear cart or place order from cart view\n\n'
        '📋 Medicine Details Include:\n'
        '• Medicine name\n'
        '• Price\n'
        '• Available stock\n'
        '• Salt composition\n'
        '• Package size\n'
        '• Manufacturer\n'
        '• Type/Category\n\n'
        '🛍️ Order Process:\n'
        '1. Search for medicines\n'
        '2. Add items to cart\n'
        '3. Review cart with /cart\n'
        '4. Click "Place Order"\n\n'
        '❓ Need more help? Contact @support'
    )

async def search_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search medicines based on user message."""
    query = update.message.text.lower()
    
    # Handle address input if we're waiting for it
    if context.user_data.get('awaiting_address'):
        address = update.message.text
        cart = context.user_data.get('cart', [])
        
        # Generate order ID
        order_id = f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{update.message.from_user.id}"
        
        # Save order with address
        orders_df = pd.read_csv(orders_path)
        
        new_orders = []
        for item in cart:
            new_orders.append({
                'order_id': order_id,
                'user_id': update.message.from_user.id,
                'user_name': update.message.from_user.full_name,
                'medicine_name': item['name'],
                'quantity': item['quantity'],
                'price_per_unit': item['price'],
                'total_price': item['quantity'] * item['price'],
                'order_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'pending',
                'delivery_address': address
            })
            
            # Update stock
            product_db.df.loc[product_db.df['name'] == item['name'], 'quantity'] -= item['quantity']
        
        # Update CSVs
        new_orders_df = pd.DataFrame(new_orders)
        updated_orders = pd.concat([orders_df, new_orders_df], ignore_index=True)
        updated_orders.to_csv(orders_path, index=False)
        product_db.df.to_csv(csv_path, index=False)
        
        # Clear cart and address flag
        context.user_data['cart'] = []
        context.user_data['awaiting_address'] = False
        
        # Send confirmation
        total = sum(item['quantity'] * item['price'] for item in cart)
        await update.message.reply_text(
            f"✅ Order placed successfully!\n\n"
            f"Order ID: {order_id}\n"
            f"Total Amount: ₹{total:.2f}\n"
            f"Delivery Address: {address}\n\n"
            "Your order will be delivered to the provided address.\n"
            "Search for another medicine to place a new order."
        )
        return
    
    # Continue with normal search if not waiting for address
    logger.info(f"Received query: {query}")
    
    try:
        # Search for medicines
        products = product_db.search_products(query)
        # Filter out products with zero quantity
        products = [p for p in products if p['quantity'] > 0]
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
                text=f"{product['name'][:30]} - ₹{product['price']:.2f} (Stock: {product['quantity']})",
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
    await query.answer()
    
    if query.data == "checkout":
        # Ask for delivery address when user clicks "Place Order"
        await query.edit_message_text(
            text="Please enter your delivery address:\n\n"
                 "(Include complete address with landmark and PIN code)"
        )
        context.user_data['awaiting_address'] = True
        return
    
    try:
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
                        f"Stock Available: {product['quantity']} units\n"
                        f"Composition: {product['salt']}\n"
                        f"Package Size: {product['package_size']}\n"
                        f"Manufacturer: {product['manufacturer']}\n"
                        f"Type: {product['category']}"
                    )
                    
                    # Add quantity selection buttons
                    keyboard = [
                        [
                            InlineKeyboardButton("1️⃣", callback_data=f"add_{idx}_1"),
                            InlineKeyboardButton("2️⃣", callback_data=f"add_{idx}_2"),
                            InlineKeyboardButton("3️⃣", callback_data=f"add_{idx}_3"),
                            InlineKeyboardButton("4️⃣", callback_data=f"add_{idx}_4"),
                            InlineKeyboardButton("5️⃣", callback_data=f"add_{idx}_5")
                        ],
                        [
                            InlineKeyboardButton("🛒 View Cart", callback_data="view_cart")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.message.reply_text(
                        detail_text + "\n\n📦 Select quantity to add to cart:",
                        reply_markup=reply_markup
                    )
                else:
                    await query.message.reply_text("Sorry, I couldn't find the medicine details.")
        
        elif query.data.startswith("add_"):
            # Handle adding to cart
            _, idx, qty = query.data.split("_")
            idx, qty = int(idx), int(qty)
            
            if 'last_search' not in context.user_data:
                await query.message.reply_text("Please search for the medicine again.")
                return
                
            product = context.user_data['last_search'][idx]
            
            # Check if quantity is available
            if qty > product['quantity']:
                await query.message.reply_text(
                    f"Sorry, only {product['quantity']} units available in stock."
                )
                return
            
            # Initialize cart if doesn't exist
            if 'cart' not in context.user_data:
                context.user_data['cart'] = []
            
            # Check if item already in cart
            existing_item = next(
                (item for item in context.user_data['cart'] if item['name'] == product['name']), 
                None
            )
            
            if existing_item:
                # Update quantity if already in cart
                new_qty = existing_item['quantity'] + qty
                if new_qty > product['quantity']:
                    await query.message.reply_text(
                        f"Cannot add {qty} more units. You already have {existing_item['quantity']} in cart "
                        f"and only {product['quantity']} available in stock."
                    )
                    return
                existing_item['quantity'] = new_qty
                msg = f"Updated quantity to {new_qty}x {product['name']} in cart!"
            else:
                # Add new item to cart
                cart_item = {
                    'name': product['name'],
                    'price': product['price'],
                    'quantity': qty
                }
                context.user_data['cart'].append(cart_item)
                msg = f"Added {qty}x {product['name']} to cart!"
            
            # Show confirmation with view cart option
            keyboard = [[InlineKeyboardButton("🛒 View Cart", callback_data="view_cart")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                f"{msg}\nUse /cart to view or checkout.",
                reply_markup=reply_markup
            )
        
        elif query.data == "view_cart":
            await show_cart(update, context)
            
        elif query.data == "clear_cart":
            context.user_data['cart'] = []
            await query.message.reply_text("Cart cleared! 🗑️")
            
        elif query.data == "place_order":
            await process_order(update, context)
        
    except Exception as e:
        logger.error(f"Error handling button click: {str(e)}")
        await query.message.reply_text("Sorry, there was an error processing your request.")

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show cart contents and checkout button."""
    if 'cart' not in context.user_data or not context.user_data['cart']:
        await update.effective_message.reply_text("Your cart is empty!")
        return
        
    cart = context.user_data['cart']
    total = sum(item['price'] * item['quantity'] for item in cart)
    
    cart_text = "🛒 Your Cart:\n\n"
    for item in cart:
        cart_text += f"• {item['quantity']}x {item['name']}\n"
        cart_text += f"  Subtotal: ₹{item['price'] * item['quantity']:.2f}\n"
    
    cart_text += f"\nTotal: ₹{total:.2f}"
    
    keyboard = [
        [
            InlineKeyboardButton("🗑️ Clear Cart", callback_data="clear_cart"),
            InlineKeyboardButton("✅ Place Order", callback_data="place_order")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_message.reply_text(
        cart_text,
        reply_markup=reply_markup
    )

async def process_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the order and ask for delivery address."""
    query = update.callback_query
    await query.answer()
    
    cart = context.user_data.get('cart', [])
    if not cart:
        await query.edit_message_text("Your cart is empty!")
        return
        
    # Ask for delivery address
    await query.edit_message_text(
        text="Please enter your delivery address:\n\n"
             "(Include complete address with landmark and PIN code)"
    )
    context.user_data['awaiting_address'] = True

async def cart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cart command"""
    await show_cart(update, context)

def main():
    """Start the bot."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN found!")  # Simplified error
        return
        
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_products))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(CommandHandler("cart", cart_command))

    logger.warning("Bot started!")  # Changed to warning level
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()