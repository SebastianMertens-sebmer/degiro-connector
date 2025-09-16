#!/usr/bin/env python3
"""
Test leveraged products search to understand the data structure
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

def test_leveraged_search():
    trading_api = connect_to_degiro()
    
    print("🔍 Testing leveraged products search...")
    
    # Test general leveraged products search
    leveraged_request = ProductSearch.RequestLeverageds()
    leveraged_request.popular_only = False
    leveraged_request.input_aggregate_types = ''
    leveraged_request.input_aggregate_values = ''
    leveraged_request.search_text = ''  # Empty to get all
    leveraged_request.offset = 0
    leveraged_request.limit = 20
    leveraged_request.require_total = True
    leveraged_request.sort_columns = 'name'
    leveraged_request.sort_types = 'asc'
    
    try:
        search_results = trading_api.product_search(request=leveraged_request, raw=True)
        
        print(f"📊 Response type: {type(search_results)}")
        
        if isinstance(search_results, dict):
            print(f"📊 Keys: {search_results.keys()}")
            
            if 'products' in search_results:
                products = search_results['products']
                print(f"📊 Found {len(products)} leveraged products")
                
                # Show first few products to understand structure
                for i, product in enumerate(products[:5]):
                    print(f"\n--- Product {i+1} ---")
                    for key, value in product.items():
                        print(f"  {key}: {value}")
            else:
                print("📊 Raw response:")
                print(json.dumps(search_results, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_leveraged_search()