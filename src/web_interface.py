from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
import os
from datetime import datetime
import csv
from dotenv import load_dotenv
import sys
import logging

# Update the template directory setup
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle (PyInstaller)
    template_dir = os.path.join(sys._MEIPASS, 'templates')
else:
    # If the application is run from Python interpreter
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'your_secret_key_here'  # Required for flash messages

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_base_path():
    """Get the base path for the application, works both in dev and packaged mode"""
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, use the parent directory of the executable
        return os.path.dirname(os.path.dirname(sys.executable))
    else:
        # If the application is run from Python interpreter
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_data_path():
    """Get the data directory path"""
    base = get_base_path()
    data_path = os.path.join(base, 'data')
    
    # Create data directory if it doesn't exist
    os.makedirs(data_path, exist_ok=True)
    
    logger.debug(f"Data directory path: {data_path}")
    return data_path

# Update paths
base_path = get_base_path()
data_path = get_data_path()
orders_path = os.path.join(data_path, 'orders.csv')

logger.debug(f"Base path: {base_path}")
logger.debug(f"Orders path: {orders_path}")
logger.debug(f"Orders file exists: {os.path.exists(orders_path)}")

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

# Create orders.csv if it doesn't exist
create_orders_csv()

@app.route('/')
def index():
    return redirect(url_for('orders'))

@app.route('/get_customers')
def get_customers():
    """API endpoint to get customer names for autocomplete"""
    try:
        search = request.args.get('term', '').lower()
        orders_df = pd.read_csv(orders_path)
        customers = orders_df['user_name'].dropna().unique()
        
        # Filter customers based on search term
        filtered_customers = [
            name for name in customers 
            if search in name.lower()
        ]
        
        return jsonify(filtered_customers)
    except Exception as e:
        return jsonify([])

@app.route('/orders')
def orders():
    try:
        # Get filter parameters from URL
        filter_date = request.args.get('date')
        filter_name = request.args.get('name', '').lower()
        
        orders_df = pd.read_csv(orders_path)
        # Clean any NaN values and remove invalid rows
        orders_df = orders_df[orders_df['order_id'].notna()]
        orders_df['status'] = orders_df['status'].fillna('pending')
        
        # Convert order_date to datetime safely
        def safe_datetime(x):
            try:
                return pd.to_datetime(x)
            except:
                return pd.NaT  # Not a Time value for invalid dates
        
        orders_df['order_date'] = orders_df['order_date'].apply(safe_datetime)
        
        # Apply filters
        if filter_date and filter_date.strip():  # Check if date filter is not empty
            try:
                filter_date = pd.to_datetime(filter_date).date()
                orders_df = orders_df[orders_df['order_date'].dt.date == filter_date]
            except:
                flash('Invalid date format')
        
        if filter_name:
            orders_df = orders_df[orders_df['user_name'].str.lower().str.contains(filter_name)]
        
        # Calculate total profit from completed orders
        completed_orders = orders_df[orders_df['status'] == 'completed']
        total_profit = completed_orders['total_price'].sum()
        
        # Group by order_id to get order summaries
        order_groups = orders_df.groupby('order_id').agg({
            'user_name': 'first',
            'order_date': 'first',
            'total_price': 'sum',
            'status': 'first',
            'delivery_address': 'first'
        }).reset_index()
        
        # Remove rows with invalid dates
        order_groups = order_groups.dropna(subset=['order_date'])
        
        # Sort by date (newest first)
        order_groups = order_groups.sort_values('order_date', ascending=False)
        
        orders_by_status = {
            'pending': order_groups[order_groups['status'] == 'pending'].to_dict('records'),
            'completed': order_groups[order_groups['status'] == 'completed'].to_dict('records'),
            'cancelled': order_groups[order_groups['status'] == 'cancelled'].to_dict('records')
        }
        
        return render_template('orders.html', 
                             orders_by_status=orders_by_status,
                             total_profit=total_profit,
                             filter_date=filter_date,
                             filter_name=filter_name)
    except Exception as e:
        logger.error(f"Error in orders route: {str(e)}", exc_info=True)
        flash(f'Error loading orders: {str(e)}')
        return render_template('orders.html', 
                             orders_by_status={'pending': [], 'completed': [], 'cancelled': []},
                             total_profit=0,
                             filter_date=None,
                             filter_name='')

@app.route('/order/<order_id>')
def order_detail(order_id):
    try:
        orders_df = pd.read_csv(orders_path)
        order_items = orders_df[orders_df['order_id'] == order_id].to_dict('records')
        if not order_items:
            flash('Order not found')
            return redirect(url_for('orders'))
            
        return render_template('order_detail.html', 
                             items=order_items, 
                             order_id=order_id,
                             delivery_address=order_items[0].get('delivery_address', ''))
    except Exception as e:
        flash(f'Error loading order details: {str(e)}')
        return redirect(url_for('orders'))

@app.route('/update_status/<order_id>', methods=['POST'])
def update_status(order_id):
    new_status = request.form.get('status')
    orders_df = pd.read_csv(orders_path)
    orders_df.loc[orders_df['order_id'] == order_id, 'status'] = new_status
    orders_df.to_csv(orders_path, index=False)
    flash(f'Order {order_id} status updated to {new_status}')
    return redirect(url_for('orders'))

if __name__ == '__main__':
    app.run(debug=True) 