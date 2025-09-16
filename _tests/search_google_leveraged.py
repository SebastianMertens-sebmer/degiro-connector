#!/usr/bin/env python3
"""
Search for Google leveraged products more thoroughly
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

def search_google_leveraged():
    trading_api = connect_to_degiro()
    
    print("🔍 Searching for Google leveraged products...")
    
    # Try leveraged search with Google keywords
    leveraged_request = ProductSearch.RequestLeverageds()
    leveraged_request.popular_only = False
    leveraged_request.input_aggregate_types = ''
    leveraged_request.input_aggregate_values = ''
    leveraged_request.search_text = 'Alphabet'  # Search for Alphabet specifically
    leveraged_request.offset = 0
    leveraged_request.limit = 100
    leveraged_request.require_total = True
    leveraged_request.sort_columns = 'name'
    leveraged_request.sort_types = 'asc'
    
    try:
        search_results = trading_api.product_search(request=leveraged_request, raw=True)
        
        if isinstance(search_results, dict) and 'products' in search_results:
            products = search_results['products']
            print(f"📊 Found {len(products)} products matching 'Alphabet'")
            
            for i, product in enumerate(products):
                print(f"\n--- Product {i+1} ---")
                print(f"Name: {product.get('name')}")
                print(f"ID: {product.get('id')}")
                print(f"ISIN: {product.get('isin')}")
                print(f"Leverage: {product.get('leverage')}")
                print(f"Underlying Product ID: {product.get('underlying_product_id')}")
                print(f"VWD ID: {product.get('vwdId')}")
                print(f"Short/Long: {product.get('shortlong')}")
                print(f"Tradable: {product.get('tradable')}")
        
        # Also try with 'Google'
        print("\n" + "="*50)
        print("🔍 Searching with 'Google'...")
        
        leveraged_request.search_text = 'Google'
        search_results2 = trading_api.product_search(request=leveraged_request, raw=True)
        
        if isinstance(search_results2, dict) and 'products' in search_results2:
            products2 = search_results2['products']
            print(f"📊 Found {len(products2)} products matching 'Google'")
            
            for i, product in enumerate(products2):
                print(f"\n--- Product {i+1} ---")
                print(f"Name: {product.get('name')}")
                print(f"ID: {product.get('id')}")
                print(f"ISIN: {product.get('isin')}")
                print(f"Leverage: {product.get('leverage')}")
                print(f"Underlying Product ID: {product.get('underlying_product_id')}")
                print(f"VWD ID: {product.get('vwdId')}")
                print(f"Short/Long: {product.get('shortlong')}")
                print(f"Tradable: {product.get('tradable')}")
        
        # Try with GOOGL symbol
        print("\n" + "="*50)
        print("🔍 Searching with 'GOOGL'...")
        
        leveraged_request.search_text = 'GOOGL'
        search_results3 = trading_api.product_search(request=leveraged_request, raw=True)
        
        if isinstance(search_results3, dict) and 'products' in search_results3:
            products3 = search_results3['products']
            print(f"📊 Found {len(products3)} products matching 'GOOGL'")
            
            for i, product in enumerate(products3):
                print(f"\n--- Product {i+1} ---")
                print(f"Name: {product.get('name')}")
                print(f"ID: {product.get('id')}")
                print(f"ISIN: {product.get('isin')}")
                print(f"Leverage: {product.get('leverage')}")
                print(f"Underlying Product ID: {product.get('underlying_product_id')}")
                print(f"VWD ID: {product.get('vwdId')}")
                print(f"Short/Long: {product.get('shortlong')}")
                print(f"Tradable: {product.get('tradable')}")
                
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    search_google_leveraged()