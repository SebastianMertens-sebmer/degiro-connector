#!/usr/bin/env python3
"""
Debug underlying products for leveraged products
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

def debug_leveraged_underlyings():
    trading_api = connect_to_degiro()
    
    print("🔍 Getting leveraged products to find Google/Alphabet...")
    
    # Get all leveraged products
    leveraged_request = ProductSearch.RequestLeverageds()
    leveraged_request.popular_only = False
    leveraged_request.input_aggregate_types = ''
    leveraged_request.input_aggregate_values = ''
    leveraged_request.search_text = ''
    leveraged_request.offset = 0
    leveraged_request.limit = 100
    leveraged_request.require_total = True
    leveraged_request.sort_columns = 'name'
    leveraged_request.sort_types = 'asc'
    
    try:
        search_results = trading_api.product_search(request=leveraged_request, raw=True)
        
        if isinstance(search_results, dict) and 'products' in search_results:
            products = search_results['products']
            print(f"📊 Found {len(products)} leveraged products")
            
            # Collect unique underlying product IDs
            underlying_ids = set()
            google_products = []
            
            for product in products:
                name = product.get('name', '').upper()
                underlying_id = product.get('underlying_product_id')
                
                if underlying_id:
                    underlying_ids.add(underlying_id)
                
                # Look for Google/Alphabet related products
                if any(keyword in name for keyword in ['GOOGLE', 'ALPHABET', 'GOOGL', 'GOOG']):
                    google_products.append({
                        'name': product.get('name'),
                        'underlying_product_id': underlying_id,
                        'leverage': product.get('leverage'),
                        'isin': product.get('isin'),
                        'vwd_id': product.get('vwdId')
                    })
            
            print(f"\n📊 Found {len(google_products)} Google/Alphabet leveraged products:")
            for prod in google_products:
                print(f"   • {prod['name']}")
                print(f"     Underlying ID: {prod['underlying_product_id']}, Leverage: {prod['leverage']}x")
                print(f"     ISIN: {prod['isin']}, VWD ID: {prod['vwd_id']}")
                print()
            
            # Now get info about these underlying products
            if google_products:
                google_underlying_ids = list(set(p['underlying_product_id'] for p in google_products if p['underlying_product_id']))
                print(f"🔍 Getting info for Google underlying IDs: {google_underlying_ids}")
                
                try:
                    product_info = trading_api.get_products_info(google_underlying_ids, raw=True)
                    
                    if product_info and 'data' in product_info:
                        print("\n📊 Google underlying stock details:")
                        for uid, data in product_info['data'].items():
                            print(f"   ID {uid}: {data.get('name')} ({data.get('symbol')})")
                            print(f"     ISIN: {data.get('isin')}")
                            print(f"     VWD ID: {data.get('vwdId')}")
                            print()
                    
                except Exception as e:
                    print(f"❌ Failed to get underlying info: {e}")
            
            # Sample some other underlying IDs to see what stocks have leveraged products
            sample_underlying_ids = list(underlying_ids)[:10]
            print(f"\n🔍 Sample underlying product IDs: {sample_underlying_ids}")
            
            try:
                sample_info = trading_api.get_products_info(sample_underlying_ids, raw=True)
                
                if sample_info and 'data' in sample_info:
                    print("\n📊 Sample underlying stocks with leveraged products:")
                    for uid, data in sample_info['data'].items():
                        print(f"   ID {uid}: {data.get('name', 'N/A')} ({data.get('symbol', 'N/A')})")
                
            except Exception as e:
                print(f"❌ Failed to get sample info: {e}")
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_leveraged_underlyings()