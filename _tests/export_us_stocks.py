#!/usr/bin/env python3
"""
Export US stocks specifically - they might be in a separate category
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

def export_us_stocks():
    trading_api = connect_to_degiro()
    
    print("🔍 Exporting US stocks specifically...")
    
    all_stocks = {}
    
    # Search for US stocks specifically
    stock_request = ProductSearch.RequestStocks()
    stock_request.is_in_us_green_list = True  # Focus on US stocks
    stock_request.index_id = 0
    stock_request.exchange_id = 0
    stock_request.stock_country_id = 0
    stock_request.search_text = ''
    stock_request.offset = 0
    stock_request.limit = 10000
    stock_request.require_total = True
    stock_request.sort_columns = 'name'
    stock_request.sort_types = 'asc'
    
    try:
        print("   📊 Searching for US stocks...")
        search_results = trading_api.product_search(request=stock_request, raw=True)
        
        if isinstance(search_results, dict) and 'products' in search_results:
            products = search_results['products']
            print(f"   ✅ Found {len(products)} US stocks")
            
            for product in products:
                product_id = product.get('id')
                name = product.get('name')
                symbol = product.get('symbol')
                isin = product.get('isin')
                currency = product.get('currency')
                
                if product_id and name:
                    all_stocks[str(product_id)] = {
                        'id': product_id,
                        'name': name,
                        'symbol': symbol,
                        'isin': isin,
                        'currency': currency
                    }
        
        # Also try individual searches for major companies
        major_companies = [
            'CISCO', 'cisco', 'Cisco Systems',
            'ALPHABET', 'alphabet', 'Alphabet Inc',
            'GOOGLE', 'google', 'Google',
            'ORACLE', 'oracle', 'Oracle Corp',
            'MICROSOFT', 'microsoft', 'Microsoft Corp',
            'APPLE', 'apple', 'Apple Inc'
        ]
        
        print("   🔍 Searching for major companies individually...")
        
        for company in major_companies:
            lookup_request = ProductSearch.RequestLookup()
            lookup_request.search_text = company
            lookup_request.limit = 20
            lookup_request.offset = 0
            lookup_request.product_type_id = 1  # Stocks
            
            try:
                company_results = trading_api.product_search(request=lookup_request, raw=True)
                
                if isinstance(company_results, dict) and 'products' in company_results:
                    company_products = company_results['products']
                    
                    for product in company_products:
                        product_id = product.get('id')
                        name = product.get('name')
                        symbol = product.get('symbol')
                        isin = product.get('isin')
                        currency = product.get('currency')
                        
                        if product_id and name and str(product_id) not in all_stocks:
                            all_stocks[str(product_id)] = {
                                'id': product_id,
                                'name': name,
                                'symbol': symbol,
                                'isin': isin,
                                'currency': currency
                            }
                            print(f"      Found: ID {product_id} - {name} ({symbol})")
            
            except Exception as e:
                print(f"      ⚠️ Search for {company} failed: {e}")
        
        # Export to JSON
        output_file = 'us_stocks_mapping.json'
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': '2025-09-13',
                'total_products': len(all_stocks),
                'description': 'US stocks mapping with focus on major companies',
                'products': all_stocks
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ SUCCESS!")
        print(f"   • Total US stocks exported: {len(all_stocks)}")
        print(f"   • Output file: {output_file}")
        
        # Show key companies found
        print(f"\n🎯 Key companies found:")
        search_terms = ['cisco', 'alphabet', 'google', 'oracle', 'microsoft', 'apple']
        
        for term in search_terms:
            found = []
            for product_id, data in all_stocks.items():
                if term.lower() in data['name'].lower():
                    found.append(f"ID {product_id}: {data['name']} ({data['symbol']})")
            
            if found:
                print(f"   {term.upper()}:")
                for item in found:
                    print(f"      {item}")
        
        return all_stocks
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return {}

if __name__ == "__main__":
    export_us_stocks()