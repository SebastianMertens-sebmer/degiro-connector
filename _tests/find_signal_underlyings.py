#!/usr/bin/env python3
"""
Find underlying IDs for the companies in our trading signals
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

def find_signal_underlyings():
    trading_api = connect_to_degiro()
    
    # Companies from the trading signals JSON
    signal_companies = [
        {"symbol": "US17275R1023", "company_name": "Cisco Systems", "search_terms": ["CISCO", "Cisco Systems"]},
        {"symbol": "US5951121038", "company_name": "Micron Technology", "search_terms": ["MICRON", "Micron Technology"]},
        {"symbol": "US68389X1054", "company_name": "Oracle", "search_terms": ["ORACLE", "Oracle Corp"]},
        {"symbol": "US1491231015", "company_name": "Caterpillar", "search_terms": ["CATERPILLAR", "Caterpillar Inc"]},
        {"symbol": "US92840M1027", "company_name": "Vistra", "search_terms": ["VISTRA", "Vistra Corp"]},
        {"symbol": "US98419M1009", "company_name": "Xylem", "search_terms": ["XYLEM", "Xylem Inc"]},
        # Add major ones we know have leveraged products
        {"symbol": "US02079K3059", "company_name": "Alphabet Inc", "search_terms": ["ALPHABET", "GOOGLE", "Alphabet Inc"]},
        {"symbol": "US5949181045", "company_name": "Microsoft Corp", "search_terms": ["MICROSOFT", "Microsoft Corp"]},
        {"symbol": "US0378331005", "company_name": "Apple Inc", "search_terms": ["APPLE", "Apple Inc"]}
    ]
    
    underlying_mapping = {}
    
    print("🎯 Finding underlying IDs for trading signal companies...")
    
    for company in signal_companies:
        print(f"\n🔍 Searching for {company['company_name']}...")
        found = False
        
        for search_term in company['search_terms']:
            if found:
                break
                
            print(f"   Trying search term: '{search_term}'")
            
            # Search leveraged products for this company
            leveraged_request = ProductSearch.RequestLeverageds()
            leveraged_request.popular_only = False
            leveraged_request.input_aggregate_types = ''
            leveraged_request.input_aggregate_values = ''
            leveraged_request.search_text = search_term
            leveraged_request.offset = 0
            leveraged_request.limit = 50  # Just need a few to get the underlying ID
            leveraged_request.require_total = True
            leveraged_request.sort_columns = 'name'
            leveraged_request.sort_types = 'asc'
            
            try:
                search_results = trading_api.product_search(request=leveraged_request, raw=True)
                
                if isinstance(search_results, dict) and 'products' in search_results:
                    products = search_results['products']
                    
                    if products:
                        # Get the underlying ID from the first product
                        first_product = products[0]
                        underlying_id = first_product.get('underlying_product_id')
                        product_name = first_product.get('name', '')
                        
                        if underlying_id:
                            print(f"   ✅ Found underlying ID: {underlying_id}")
                            print(f"      Sample product: {product_name}")
                            print(f"      🔗 DEGIRO URL: https://trader.degiro.nl/trader/#/products?productType=14&subProductType=14&shortLong=-1&issuer=-1&underlying={underlying_id}")
                            
                            # Count total products for this underlying
                            leveraged_count = len(products) if len(products) < 50 else "50+"
                            
                            underlying_mapping[company['symbol']] = {
                                'isin': company['symbol'],
                                'company_name': company['company_name'],
                                'underlying_id': underlying_id,
                                'leveraged_products_count': leveraged_count,
                                'sample_product': product_name,
                                'search_term_used': search_term,
                                'degiro_url': f"https://trader.degiro.nl/trader/#/products?productType=14&subProductType=14&shortLong=-1&issuer=-1&underlying={underlying_id}"
                            }
                            
                            found = True
                        else:
                            print(f"   ⚠️ Found products but no underlying_product_id")
                    else:
                        print(f"   ❌ No leveraged products found for '{search_term}'")
                        
            except Exception as e:
                print(f"   ❌ Search failed for '{search_term}': {e}")
        
        if not found:
            print(f"   ❌ Could not find underlying ID for {company['company_name']}")
    
    # Export the mapping
    output_file = 'signal_companies_underlying_mapping.json'
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': '2025-09-13',
            'description': 'Underlying IDs for companies in trading signals',
            'total_companies': len(underlying_mapping),
            'companies': underlying_mapping
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ SUCCESS!")
    print(f"   • Found underlying IDs for {len(underlying_mapping)} companies")
    print(f"   • Output file: {output_file}")
    
    print(f"\n📋 Summary:")
    for isin, data in underlying_mapping.items():
        print(f"   {data['company_name']}: ID {data['underlying_id']} ({data['leveraged_products_count']} products)")
    
    return underlying_mapping

if __name__ == "__main__":
    find_signal_underlyings()