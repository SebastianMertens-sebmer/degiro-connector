#!/usr/bin/env python3
"""
Test with companies we know have leveraged products
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

def search_leveraged_products(trading_api, underlying_id, company_name):
    """Search leveraged products using the method that worked before"""
    
    print(f"\n🎯 Testing {company_name} (ID: {underlying_id})")
    
    # Method 1: Direct underlying search (like we used for CISCO)
    leveraged_request = ProductSearch.RequestLeverageds()
    leveraged_request.popular_only = False
    leveraged_request.input_aggregate_types = ''
    leveraged_request.input_aggregate_values = ''
    leveraged_request.search_text = company_name
    leveraged_request.offset = 0
    leveraged_request.limit = 50
    leveraged_request.require_total = True
    leveraged_request.sort_columns = 'leverage'
    leveraged_request.sort_types = 'asc'
    
    try:
        search_results = trading_api.product_search(request=leveraged_request, raw=True)
        
        if isinstance(search_results, dict) and 'products' in search_results:
            products = search_results['products']
            total = search_results.get('total', 0)
            
            print(f"   📊 Found {len(products)} leveraged products (total: {total}) for text search")
            
            # Filter for suitable products
            suitable = []
            for product in products:
                leverage = product.get('leverage', 0)
                shortlong = product.get('shortlong')
                tradable = product.get('tradable', False)
                underlying_product_id = product.get('underlying_product_id')
                
                # Check if this matches our underlying ID
                if (underlying_product_id == underlying_id and 
                    4 <= leverage <= 5 and 
                    shortlong == 1 and 
                    tradable):
                    suitable.append(product)
            
            print(f"   ✅ Found {len(suitable)} suitable products (4-5x leverage, LONG, tradable)")
            
            # Show first few
            for i, product in enumerate(suitable[:3]):
                name = product.get('name', '')
                leverage = product.get('leverage')
                print(f"      {i+1}. {name[:60]}... (Lev: {leverage}x)")
            
            return suitable
            
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
        return []

def test_known_companies():
    trading_api = connect_to_degiro()
    
    # Test with companies we know have leveraged products
    known_companies = [
        {"id": 232, "name": "CISCO"},
        {"id": 488, "name": "GOOGLE"}, 
        {"id": 694, "name": "MICROSOFT"},
        {"id": 59, "name": "APPLE"},
        {"id": 796, "name": "ORACLE"},
        # Test the signal companies
        {"id": 33, "name": "AIRBUS"},
        {"id": 182, "name": "Beiersdorf"},
        {"id": 240, "name": "COMMERZBANK"}
    ]
    
    print("🔍 Testing known companies for leveraged products...")
    
    for company in known_companies:
        leveraged_products = search_leveraged_products(trading_api, company['id'], company['name'])
        
        if leveraged_products:
            print(f"   🎯 {company['name']}: TRADEABLE ✅")
        else:
            print(f"   ❌ {company['name']}: NO LEVERAGED PRODUCTS")

if __name__ == "__main__":
    test_known_companies()