import pandas as pd
import random
import argparse

def update_quantities(file_path: str, min_qty: int = 0, max_qty: int = 25):
    """Update quantities in the CSV file with random values"""
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Generate random quantities
        df['quantity'] = [random.randint(min_qty, max_qty) for _ in range(len(df))]
        
        # Save back to CSV
        df.to_csv(file_path, index=False)
        print(f"Successfully updated quantities for {len(df)} products")
        
    except Exception as e:
        print(f"Error updating quantities: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update product quantities with random values')
    parser.add_argument('file_path', help='Path to the CSV file')
    parser.add_argument('--min', type=int, default=0, help='Minimum quantity (default: 0)')
    parser.add_argument('--max', type=int, default=25, help='Maximum quantity (default: 25)')
    
    args = parser.parse_args()
    update_quantities(args.file_path, args.min, args.max) 