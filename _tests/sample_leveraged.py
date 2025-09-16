#!/usr/bin/env python3
"""
Get sample of leveraged products to understand underlying ID mapping
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

def sample_leveraged():
    trading_api = connect_to_degiro()
    
    print("🔍 Getting sample of leveraged products...")
    
    leveraged_request = ProductSearch.RequestLeverageds()
    leveraged_request.popular_only = False
    leveraged_request.input_aggregate_types = ''
    leveraged_request.input_aggregate_values = ''
    leveraged_request.search_text = ''
    leveraged_request.offset = 0
    leveraged_request.limit = 500  # Just get 500 for now
    leveraged_request.require_total = True
    leveraged_request.sort_columns = 'name'
    leveraged_request.sort_types = 'asc'
    
    try:
        search_results = trading_api.product_search(request=leveraged_request, raw=True)
        
        if isinstance(search_results, dict) and 'products' in search_results:
            products = search_results['products']
            total_available = search_results.get('total', 0)
            
            print(f"   📊 Found {len(products)} leveraged products (total available: {total_available})")
            
            # Group by underlying ID
            underlying_groups = {}
            
            for product in products[:50]:  # Just look at first 50
                name = product.get('name', '')
                underlying_id = product.get('underlying_product_id')
                leverage = product.get('leverage')
                shortlong = product.get('shortlong')
                tradable = product.get('tradable')
                
                if underlying_id:
                    if underlying_id not in underlying_groups:
                        underlying_groups[underlying_id] = {
                            'underlying_id': underlying_id,
                            'products': [],
                            'inferred_company': ''
                        }
                    
                    underlying_groups[underlying_id]['products'].append({
                        'name': name,
                        'leverage': leverage,
                        'shortlong': shortlong,
                        'tradable': tradable
                    })
                    
                    # Try to infer company name from product name
                    if name and not underlying_groups[underlying_id]['inferred_company']:
                        parts = name.split()
                        if len(parts) > 2:
                            # Skip issuer (BNP, SG, etc.)
                            company = ' '.join(parts[1:3])
                            underlying_groups[underlying_id]['inferred_company'] = company
            
            print(f"\n📋 Underlying groups found:")
            for underlying_id, group in underlying_groups.items():
                print(f"\n   Underlying ID {underlying_id}: {group['inferred_company']}")
                print(f"      Products: {len(group['products'])}")
                for product in group['products'][:3]:  # Show first 3
                    print(f"         • {product['name'][:60]}... (Lev: {product['leverage']})")
            
            # Look for CISCO and Google specifically
            print(f"\n🎯 Looking for key companies:")
            search_companies = ['CISCO', 'ALPHABET', 'GOOGLE', 'ORACLE']
            
            for company in search_companies:
                found_ids = []
                for underlying_id, group in underlying_groups.items():
                    if company.upper() in group['inferred_company'].upper():
                        found_ids.append((underlying_id, group['inferred_company'], len(group['products'])))
                
                if found_ids:
                    print(f"   {company}:")
                    for underlying_id, company_name, count in found_ids:
                        print(f"      ID {underlying_id}: {company_name} ({count} products)")
                        
                        # This is the key - show the URL pattern
                        print(f"      🔗 URL: https://trader.degiro.nl/trader/#/products?productType=14&subProductType=14&shortLong=-1&issuer=-1&underlying={underlying_id}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    sample_leveraged()