#!/usr/bin/env python3
"""
Export all underlying stock IDs and names to JSON
This will help us build a mapping for leveraged products
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

def export_underlying_stocks():
    trading_api = connect_to_degiro()
    
    print("🔍 Exporting all underlying stocks...")
    
    all_stocks = {}
    
    # Search for all stocks with pagination
    offset = 0
    limit = 1000
    total_stocks_processed = 0
    
    print("   📊 Searching for stocks with pagination...")
    
    while True:
        stock_request = ProductSearch.RequestStocks()
        stock_request.is_in_us_green_list = False
        stock_request.index_id = 0
        stock_request.exchange_id = 0
        stock_request.stock_country_id = 0
        stock_request.search_text = ''
        stock_request.offset = offset
        stock_request.limit = limit
        stock_request.require_total = True
        stock_request.sort_columns = 'name'
        stock_request.sort_types = 'asc'
        
        try:
            search_results = trading_api.product_search(request=stock_request, raw=True)
            
            if isinstance(search_results, dict) and 'products' in search_results:
                products = search_results['products']
                total_available = search_results.get('total', 0)
                
                print(f"   📄 Page {offset//limit + 1}: Found {len(products)} stocks (total available: {total_available})")
                
                if not products:  # No more products
                    break
                
                for product in products:
                    product_id = product.get('id')
                    name = product.get('name')
                    symbol = product.get('symbol')
                    isin = product.get('isin')
                    currency = product.get('currency')
                    exchange = product.get('exchangeId')
                    
                    if product_id and name:
                        all_stocks[str(product_id)] = {
                            'id': product_id,
                            'name': name,
                            'symbol': symbol,
                            'isin': isin,
                            'currency': currency,
                            'exchange_id': exchange,
                            'type': 'STOCK'
                        }
                
                total_stocks_processed += len(products)
                
                # Check if we've gotten all available stocks
                if len(products) < limit or total_stocks_processed >= total_available:
                    break
                    
                offset += limit
                
            else:
                print(f"   ⚠️ No products found at offset {offset}")
                break
                
        except Exception as e:
            print(f"   ❌ Failed at offset {offset}: {e}")
            break
    
    print(f"   ✅ Total stocks processed: {total_stocks_processed}")
    
    # Also get ETFs with pagination
    print("   📊 Searching for ETFs with pagination...")
    
    etf_offset = 0
    total_etfs_processed = 0
    
    while True:
        etf_request = ProductSearch.RequestETFs()
        etf_request.popular_only = False
        etf_request.input_aggregate_types = ''
        etf_request.input_aggregate_values = ''
        etf_request.search_text = ''
        etf_request.offset = etf_offset
        etf_request.limit = limit
        etf_request.require_total = True
        etf_request.sort_columns = 'name'
        etf_request.sort_types = 'asc'
        
        try:
                etf_results = trading_api.product_search(request=etf_request, raw=True)
                
                if isinstance(etf_results, dict) and 'products' in etf_results:
                    etf_products = etf_results['products']
                    etf_total_available = etf_results.get('total', 0)
                    
                    print(f"   📄 ETF Page {etf_offset//limit + 1}: Found {len(etf_products)} ETFs (total available: {etf_total_available})")
                    
                    if not etf_products:  # No more ETFs
                        break
                    
                    for product in etf_products:
                        product_id = product.get('id')
                        name = product.get('name')
                        symbol = product.get('symbol')
                        isin = product.get('isin')
                        currency = product.get('currency')
                        exchange = product.get('exchangeId')
                        
                        if product_id and name:
                            all_stocks[str(product_id)] = {
                                'id': product_id,
                                'name': name,
                                'symbol': symbol,
                                'isin': isin,
                                'currency': currency,
                                'exchange_id': exchange,
                                'type': 'ETF'
                            }
                    
                    total_etfs_processed += len(etf_products)
                    
                    # Check if we've gotten all available ETFs
                    if len(etf_products) < limit or total_etfs_processed >= etf_total_available:
                        break
                        
                    etf_offset += limit
                    
                else:
                    print(f"   ⚠️ No ETFs found at offset {etf_offset}")
                    break
                    
            except Exception as e:
                print(f"   ❌ ETF search failed at offset {etf_offset}: {e}")
                break
        
        print(f"   ✅ Total ETFs processed: {total_etfs_processed}")
        
        # Export to JSON
        output_file = 'underlying_stocks_mapping.json'
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': '2025-09-13',
                'total_products': len(all_stocks),
                'description': 'Complete mapping of underlying stock IDs to names, symbols, and ISINs',
                'products': all_stocks
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ SUCCESS!")
        print(f"   • Total products exported: {len(all_stocks)}")
        print(f"   • Output file: {output_file}")
        
        # Show some sample entries
        print(f"\n📋 Sample entries:")
        sample_count = 0
        for product_id, data in all_stocks.items():
            if sample_count < 10:
                print(f"   ID {product_id}: {data['name']} ({data['symbol']}) - {data['isin']}")
                sample_count += 1
        
        # Look for specific companies we're interested in
        print(f"\n🎯 Looking for key companies:")
        search_companies = ['cisco', 'alphabet', 'google', 'oracle', 'microsoft', 'apple']
        
        for company in search_companies:
            found = []
            for product_id, data in all_stocks.items():
                if company.lower() in data['name'].lower():
                    found.append(f"ID {product_id}: {data['name']} ({data['symbol']})")
            
            if found:
                print(f"   {company.upper()}:")
                for item in found[:3]:  # Show first 3 matches
                    print(f"      {item}")
        
        return all_stocks
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return {}

if __name__ == "__main__":
    export_underlying_stocks()