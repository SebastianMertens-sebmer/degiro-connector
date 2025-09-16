#!/usr/bin/env python3
"""
Test different search terms for CISCO leveraged products
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

def test_cisco_search():
    trading_api = connect_to_degiro()
    
    search_terms = ["CISCO", "Cisco", "CSCO", "cisco systems", "CISCO SYSTEMS"]
    
    for search_term in search_terms:
        print(f"\n🔍 Testing search term: '{search_term}'")
        print("-" * 50)
        
        leveraged_request = ProductSearch.RequestLeverageds()
        leveraged_request.popular_only = False
        leveraged_request.input_aggregate_types = ''
        leveraged_request.input_aggregate_values = ''
        leveraged_request.search_text = search_term
        leveraged_request.offset = 0
        leveraged_request.limit = 20
        leveraged_request.require_total = True
        leveraged_request.sort_columns = 'name'
        leveraged_request.sort_types = 'asc'
        
        try:
            search_results = trading_api.product_search(request=leveraged_request, raw=True)
            
            if isinstance(search_results, dict) and 'products' in search_results:
                products = search_results['products']
                print(f"   📊 Found {len(products)} leveraged products")
                
                for i, product in enumerate(products[:5]):  # Show first 5
                    name = product.get('name', 'N/A')
                    leverage = product.get('leverage', 'N/A')
                    isin = product.get('isin', 'N/A')
                    tradable = product.get('tradable', False)
                    shortlong = product.get('shortlong', 'N/A')
                    
                    print(f"      {i+1}. {name}")
                    print(f"         ISIN: {isin}, Leverage: {leverage}, Tradable: {tradable}, S/L: {shortlong}")
            else:
                print("   ❌ No products found")
                
        except Exception as e:
            print(f"   ❌ Search failed: {e}")

if __name__ == "__main__":
    test_cisco_search()