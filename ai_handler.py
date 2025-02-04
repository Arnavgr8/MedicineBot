from typing import List, Dict

class AIHandler:
    def __init__(self):
        pass
    
    def generate_response(self, products: list, query: str) -> str:
        """Generate a response without using AI"""
        if not products:
            return "I couldn't find any products matching your query. Could you please try with different keywords?"
        
        response = f"I found {len(products)} products matching '{query}':\n\n"
        
        # Show only first 5 products to avoid too long messages
        for product in products[:5]:
            response += f"• {product['name']}\n"
            response += f"  Price: ${product['price']:.2f}\n"
            response += f"  {product['description']}\n\n"
            
        if len(products) > 5:
            response += f"\n...and {len(products) - 5} more products."
        
        return response 