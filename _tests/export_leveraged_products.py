#!/usr/bin/env python3
"""
Export ALL leveraged products (type 14) with their underlying IDs
This is much more efficient than searching stocks first
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

def export_leveraged_products():
    trading_api = connect_to_degiro()
    
    print("🔍 Exporting ALL leveraged products (type 14)...")
    
    all_leveraged = {}
    underlying_mapping = {}  # Map underlying_id -> underlying info
    
    # Search for ALL leveraged products with pagination
    offset = 0
    limit = 1000
    total_processed = 0
    
    print("   📊 Searching leveraged products with pagination...")
    
    while True:
        leveraged_request = ProductSearch.RequestLeverageds()
        leveraged_request.popular_only = False
        leveraged_request.input_aggregate_types = ''
        leveraged_request.input_aggregate_values = ''
        leveraged_request.search_text = ''  # Get ALL leveraged products
        leveraged_request.offset = offset
        leveraged_request.limit = limit
        leveraged_request.require_total = True
        leveraged_request.sort_columns = 'name'
        leveraged_request.sort_types = 'asc'
        
        try:
            search_results = trading_api.product_search(request=leveraged_request, raw=True)
            
            if isinstance(search_results, dict) and 'products' in search_results:
                products = search_results['products']
                total_available = search_results.get('total', 0)
                
                print(f"   📄 Page {offset//limit + 1}: Found {len(products)} leveraged products (total available: {total_available})")
                
                if not products:  # No more products
                    break
                
                for product in products:
                    product_id = product.get('id')
                    name = product.get('name')
                    isin = product.get('isin')
                    leverage = product.get('leverage')
                    underlying_id = product.get('underlying_product_id')
                    shortlong = product.get('shortlong')
                    tradable = product.get('tradable')
                    vwd_id = product.get('vwdId')
                    
                    if product_id and name:
                        all_leveraged[str(product_id)] = {
                            'id': product_id,
                            'name': name,
                            'isin': isin,
                            'leverage': leverage,
                            'underlying_product_id': underlying_id,
                            'shortlong': shortlong,
                            'tradable': tradable,
                            'vwd_id': vwd_id
                        }
                        
                        # Build underlying mapping
                        if underlying_id and underlying_id not in underlying_mapping:
                            # Extract underlying company from product name
                            # e.g., "BNP CISCO SYSTEMS Call..." -> "CISCO SYSTEMS"
                            if name:
                                parts = name.split()
                                if len(parts) > 2:
                                    # Skip issuer (BNP, SG, etc.) and try to extract company
                                    company_part = ' '.join(parts[1:3])  # Take next 2 words after issuer
                                    underlying_mapping[underlying_id] = {
                                        'id': underlying_id,
                                        'inferred_name': company_part,
                                        'leveraged_count': 0
                                    }
                        
                        # Count leveraged products per underlying
                        if underlying_id in underlying_mapping:
                            underlying_mapping[underlying_id]['leveraged_count'] += 1
                
                total_processed += len(products)
                
                # Check if we've gotten all available products
                if len(products) < limit or total_processed >= total_available:
                    break
                    
                offset += limit
                
            else:
                print(f"   ⚠️ No products found at offset {offset}")
                break
                
        except Exception as e:
            print(f"   ❌ Failed at offset {offset}: {e}")
            break
    
    print(f"   ✅ Total leveraged products processed: {total_processed}")
    
    # Export leveraged products
    leveraged_file = 'all_leveraged_products.json'
    with open(leveraged_file, 'w') as f:
        json.dump({
            'timestamp': '2025-09-13',
            'total_products': len(all_leveraged),
            'description': 'Complete mapping of ALL leveraged products (type 14)',
            'products': all_leveraged
        }, f, indent=2, ensure_ascii=False)
    
    # Export underlying mapping
    underlying_file = 'underlying_mapping_from_leveraged.json'
    with open(underlying_file, 'w') as f:
        json.dump({
            'timestamp': '2025-09-13',
            'total_underlyings': len(underlying_mapping),
            'description': 'Underlying IDs extracted from leveraged products with counts',
            'underlyings': underlying_mapping
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ SUCCESS!")
    print(f"   • Total leveraged products: {len(all_leveraged)}")
    print(f"   • Total underlying assets: {len(underlying_mapping)}")
    print(f"   • Leveraged products file: {leveraged_file}")
    print(f"   • Underlying mapping file: {underlying_file}")
    
    # Show top underlyings by leveraged product count
    print(f"\n🎯 Top underlying assets by leveraged product count:")
    sorted_underlyings = sorted(underlying_mapping.items(), 
                               key=lambda x: x[1]['leveraged_count'], 
                               reverse=True)
    
    for i, (underlying_id, data) in enumerate(sorted_underlyings[:20]):
        print(f"   {i+1:2d}. ID {underlying_id}: {data['inferred_name']} ({data['leveraged_count']} products)")
    
    # Look for specific companies
    print(f"\n🔍 Looking for key companies in underlying mapping:")
    search_terms = ['CISCO', 'ALPHABET', 'GOOGLE', 'ORACLE', 'MICROSOFT', 'APPLE']
    
    for term in search_terms:
        found = []
        for underlying_id, data in underlying_mapping.items():
            if term.upper() in data['inferred_name'].upper():
                found.append(f"ID {underlying_id}: {data['inferred_name']} ({data['leveraged_count']} products)")
        
        if found:
            print(f"   {term}:")
            for item in found:
                print(f"      {item}")
    
    return all_leveraged, underlying_mapping

if __name__ == "__main__":
    export_leveraged_products()