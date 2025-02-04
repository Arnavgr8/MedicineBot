import pandas as pd
from typing import List, Dict, Optional

class ProductDB:
    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path)
        # Add quantity column if it doesn't exist
        if 'quantity' not in self.df.columns:
            self.df['quantity'] = 100  # Default quantity for existing products
        print("Columns after adding quantity:", self.df.columns.tolist())  # Debug print
        print("Sample quantities:", self.df['quantity'].head())  # Show first few quantities
        # Print column names to debug
        print("Available columns:", self.df.columns.tolist())
        # Clean data in text columns
        for col in self.df.columns:
            if self.df[col].dtype == 'object':
                self.df[col] = self.df[col].str.strip()
    
    def search_products(self, query: str) -> List[Dict]:
        """Search medicines based on name or composition with multi-word support"""
        # Split query into words and clean them
        search_words = [word.strip().lower() for word in query.split() if word.strip()]
        
        try:
            # Initialize mask for all rows as True
            mask = pd.Series([True] * len(self.df))
            
            # Apply each search word to filter results
            for word in search_words:
                word_mask = (
                    self.df['name'].str.lower().str.contains(word, na=False) |
                    self.df['short_composition1'].str.lower().str.contains(word, na=False) |
                    self.df['short_composition2'].str.lower().str.contains(word, na=False) |
                    self.df['type'].str.lower().str.contains(word, na=False)
                )
                mask = mask & word_mask
            
            matches = self.df[mask]
            
            # Convert to list of dictionaries with renamed keys for consistency
            results = []
            for _, row in matches.iterrows():
                # Combine compositions if both exist
                composition = row['short_composition1']
                if pd.notna(row['short_composition2']):
                    composition += f", {row['short_composition2']}"

                results.append({
                    'name': row['name'],
                    'description': f"Composition: {composition}\nType: {row['type']}",
                    'price': float(str(row['price(₹)']).replace('₹', '').replace('Rs.', '').strip()),
                    'category': row['type'],
                    'manufacturer': row['manufacturer_name'],
                    'package_size': row['pack_size_label'],
                    'salt': composition,
                    'quantity': row['quantity']
                })
            
            # Sort results by relevance (exact matches first)
            results.sort(key=lambda x: sum(word.lower() in x['name'].lower() for word in search_words), reverse=True)
            
            return results
            
        except Exception as e:
            print(f"Error in search_products: {str(e)}")
            return []

    def get_product_by_name(self, name: str) -> Optional[Dict]:
        """Get medicine details by name"""
        try:
            matches = self.df[self.df['name'].str.lower().str.contains(name.lower(), na=False)]
            if not matches.empty:
                row = matches.iloc[0]
                # Combine compositions if both exist
                composition = row['short_composition1']
                if pd.notna(row['short_composition2']):
                    composition += f", {row['short_composition2']}"

                return {
                    'name': row['name'],
                    'description': (
                        f"Composition: {composition}\n"
                        f"Package Size: {row['pack_size_label']}\n"
                        f"Manufacturer: {row['manufacturer_name']}"
                    ),
                    'price': float(str(row['price(₹)']).replace('₹', '').replace('Rs.', '').strip()),
                    'category': row['type'],
                    'manufacturer': row['manufacturer_name'],
                    'package_size': row['pack_size_label'],
                    'salt': composition,
                    'quantity': row['quantity']
                }
            return None
        except Exception as e:
            print(f"Error in get_product_by_name: {str(e)}")
            return None 