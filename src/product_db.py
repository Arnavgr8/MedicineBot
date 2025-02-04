import pandas as pd
from typing import List, Dict, Optional
import os

class ProductDB:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path  # Store path for later use
        
        # Create empty DataFrame if file doesn't exist
        if not os.path.exists(csv_path):
            self.df = pd.DataFrame(columns=[
                'name', 'price(₹)', 'manufacturer_name', 'type', 
                'pack_size_label', 'short_composition1', 'short_composition2',
                'quantity', 'Is_discontinued'
            ])
            return
            
        # Load initial data
        self._load_data()
    
    def _load_data(self):
        """Load and clean data from CSV"""
        # Read without dtypes to see what we have
        self.df = pd.read_csv(self.csv_path, low_memory=False)
        
        # Clean price column first - remove any currency symbols and convert to float
        self.df['price(₹)'] = (self.df['price(₹)']
                              .astype(str)
                              .str.replace('₹', '', regex=False)
                              .str.replace('Rs.', '', regex=False)
                              .str.strip())
        self.df['price(₹)'] = pd.to_numeric(self.df['price(₹)'], errors='coerce')
        
        # Convert medicine names to lowercase and store original names
        self.df['name_lower'] = self.df['name'].str.lower()  # Add lowercase column for searching
        
        # Clean text columns
        text_columns = ['manufacturer_name', 'type', 'pack_size_label', 'short_composition1', 'short_composition2']
        for col in text_columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).str.strip()
        
        # Convert boolean column
        if 'Is_discontinued' in self.df.columns:
            self.df['Is_discontinued'] = self.df['Is_discontinued'].astype(bool)
        
        # Add quantity column if it doesn't exist
        if 'quantity' not in self.df.columns:
            self.df['quantity'] = 100  # Default quantity for existing products
        else:
            self.df['quantity'] = pd.to_numeric(self.df['quantity'], errors='coerce').fillna(0).astype(int)
        
        # Clean up any NaN values
        self.df = self.df.fillna('')
    
    def search_products(self, query: str) -> List[Dict]:
        """Search products with a more flexible matching algorithm."""
        try:
            # Reload data to get latest changes
            self._load_data()
            
            # Convert query to lowercase and split into terms
            search_terms = query.lower().split()
            
            # First try exact match using lowercase name
            exact_matches = self.df[
                self.df['name_lower'] == query.lower()
            ].copy()
            
            if not exact_matches.empty:
                matches = exact_matches
            else:
                # Try matching products that start with the first search term
                starts_with_matches = self.df[
                    self.df['name_lower'].str.startswith(search_terms[0])
                ].copy()
                
                if not starts_with_matches.empty:
                    matches = starts_with_matches
                else:
                    # Try matching all terms in sequence
                    matches = self.df[
                        self.df['name_lower'].apply(
                            lambda x: all(
                                term in x[i:] 
                                for i, term in enumerate(search_terms)
                            )
                        )
                    ].copy()
                    
                    # If still no matches, fall back to the original flexible matching
                    if matches.empty:
                        matches = self.df[
                            self.df['name_lower'].apply(
                                lambda x: all(term in x for term in search_terms)
                            )
                        ].copy()
            
            # Convert matches to list of dictionaries
            results = []
            for _, row in matches.iterrows():
                composition = row['short_composition1']
                if pd.notna(row['short_composition2']):
                    composition += f", {row['short_composition2']}"
                
                results.append({
                    'name': row['name'],
                    'price': float(row['price(₹)']),
                    'quantity': int(row['quantity']),
                    'manufacturer': row['manufacturer_name'],
                    'category': row['type'],
                    'package_size': row['pack_size_label'],
                    'salt': composition
                })
            
            return results

        except Exception as e:
            print(f"Error in search_products: {str(e)}")
            return []

    def get_product_by_name(self, name: str) -> Optional[Dict]:
        """Get medicine details by name"""
        try:
            # Reload data to get latest changes
            self._load_data()
            
            matches = self.df[self.df['name_lower'] == name.lower()]
            if not matches.empty:
                row = matches.iloc[0]
                composition = row['short_composition1']
                if pd.notna(row['short_composition2']):
                    composition += f", {row['short_composition2']}"

                return {
                    'name': row['name'],
                    'price': float(row['price(₹)']),
                    'quantity': int(row['quantity']),
                    'manufacturer': row['manufacturer_name'],
                    'category': row['type'],
                    'package_size': row['pack_size_label'],
                    'salt': composition
                }
            return None
        except Exception as e:
            print(f"Error in get_product_by_name: {str(e)}")
            return None 