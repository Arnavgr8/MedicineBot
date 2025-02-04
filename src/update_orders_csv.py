import pandas as pd
import os

def get_base_path():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def add_status_column():
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    orders_path = os.path.join(base_path, 'data', 'orders.csv')
    
    if os.path.exists(orders_path):
        df = pd.read_csv(orders_path)
        if 'status' not in df.columns:
            df['status'] = 'pending'  # Add status column with default value
            df.to_csv(orders_path, index=False)
            print("Added status column to orders.csv")
    else:
        print("orders.csv not found")

def add_address_columns():
    """Add address and phone columns if they don't exist"""
    orders_path = os.path.join(get_base_path(), 'data', 'orders.csv')
    if os.path.exists(orders_path):
        df = pd.read_csv(orders_path)
        changed = False
        
        if 'delivery_address' not in df.columns:
            df['delivery_address'] = ''
            changed = True
            
        if 'phone_number' not in df.columns:
            df['phone_number'] = ''
            changed = True
            
        if changed:
            df.to_csv(orders_path, index=False)

if __name__ == '__main__':
    add_status_column() 