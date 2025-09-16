#!/usr/bin/env python3
"""
Debug the leveraged product data to understand the structure
"""

import json
from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.trading_pb2 import Credentials, ProductSearch

def connect_to_degiro():
    with open('config/config.json', 'r') as f:
        config = json.load(f)
    
    credentials = Credentials()
    credentials.username = config['username']
    credentials.password = config['password']
    credentials.totp_secret_key = config['totp_secret_key']
    credentials.int_account = config['int_account']
    
    trading_api = TradingAPI(credentials=credentials)
    trading_api.connect()
    return trading_api

def debug_product_data():
    trading_api = connect_to_degiro()
    
    print("🔍 Debugging leveraged product data structure...")
    
    # Search for CBK (had some higher leverage products)
    leveraged_request = ProductSearch.RequestLeverageds()
    leveraged_request.popular_only = False
    leveraged_request.search_text = 'CBK'
    leveraged_request.offset = 0
    leveraged_request.limit = 50
    
    try:
        search_results = trading_api.product_search(request=leveraged_request, raw=True)
        
        if isinstance(search_results, dict) and 'products' in search_results:
            products = search_results['products']
            
            print(f"Found {len(products)} products for CBK")
            
            # Look for products with higher leverage
            high_leverage = []
            for product in products:
                leverage = product.get('leverage', 0)
                if leverage >= 2:
                    high_leverage.append(product)
            
            print(f"\nFound {len(high_leverage)} products with 2x+ leverage:")
            
            for i, product in enumerate(high_leverage[:10]):
                print(f"\n--- Product {i+1} ---")
                for key, value in product.items():
                    print(f"{key}: {value}")
                
                # Show full product structure
                print(f"JSON: {json.dumps(product, indent=2)}")
                print("-" * 50)
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    debug_product_data()