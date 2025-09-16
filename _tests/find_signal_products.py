#!/usr/bin/env python3
"""
Find leveraged products for the 3 trading signals - be creative with search
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

def search_by_isin(trading_api, isin):
    """Try to find underlying stock by ISIN first"""
    print(f"   🔍 Searching by ISIN: {isin}")
    
    stock_request = ProductSearch.RequestStocks()
    stock_request.search_text = isin
    stock_request.offset = 0
    stock_request.limit = 10
    
    try:
        search_results = trading_api.product_search(request=stock_request, raw=True)
        if isinstance(search_results, dict) and 'products' in search_results:
            products = search_results['products']
            print(f"      📊 Found {len(products)} stocks by ISIN")
            
            for product in products:
                if product.get('isin') == isin:
                    print(f"      ✅ Exact ISIN match: {product.get('name')} (ID: {product.get('id')})")
                    return product.get('id')
            
            # Show what we found
            for product in products[:3]:
                print(f"         • {product.get('name')} (ISIN: {product.get('isin')})")
    except Exception as e:
        print(f"      ❌ ISIN search failed: {e}")
    
    return None

def search_leveraged_creative(trading_api, search_terms, signal_info):
    """Search leveraged products with multiple strategies"""
    
    print(f"\n{'='*60}")
    print(f"🎯 {signal_info['company_name']} (Strength: {signal_info['signal_strength']})")
    print(f"   ISIN: {signal_info['symbol']}")
    
    # Calculate investment amount
    investment_amount = 250 if signal_info['signal_strength'] == 3 else (300 if signal_info['signal_strength'] == 4 else 400)
    print(f"   💰 Investment: {investment_amount} EUR")
    
    # Strategy 1: Search by ISIN first
    underlying_id = search_by_isin(trading_api, signal_info['symbol'])
    
    # Strategy 2: Try different search terms
    for term in search_terms:
        print(f"\n   🔍 Searching leveraged products for: '{term}'")
        
        leveraged_request = ProductSearch.RequestLeverageds()
        leveraged_request.popular_only = False
        leveraged_request.input_aggregate_types = ''
        leveraged_request.input_aggregate_values = ''
        leveraged_request.search_text = term
        leveraged_request.offset = 0
        leveraged_request.limit = 100  # Get more results
        leveraged_request.require_total = True
        leveraged_request.sort_columns = 'leverage'
        leveraged_request.sort_types = 'asc'
        
        try:
            search_results = trading_api.product_search(request=leveraged_request, raw=True)
            
            if isinstance(search_results, dict) and 'products' in search_results:
                products = search_results['products']
                total = search_results.get('total', 0)
                
                print(f"      📊 Found {len(products)} leveraged products (total: {total})")
                
                if not products:
                    continue
                
                # Analyze what's available
                leverages = set()
                shortlong_counts = {'long': 0, 'short': 0}
                tradable_count = 0
                
                suitable_products = []
                
                for product in products:
                    leverage = product.get('leverage', 0)
                    shortlong = product.get('shortlong')
                    tradable = product.get('tradable', False)
                    name = product.get('name', '')
                    
                    leverages.add(leverage)
                    
                    if shortlong == 1:
                        shortlong_counts['long'] += 1
                    elif shortlong == -1:
                        shortlong_counts['short'] += 1
                    
                    if tradable:
                        tradable_count += 1
                    
                    # Be more flexible with criteria
                    if (leverage >= 2 and  # Lower leverage requirement
                        shortlong == 1 and  # LONG only
                        tradable):
                        suitable_products.append(product)
                
                print(f"      📈 Available leverages: {sorted(leverages)}")
                print(f"      📊 Long: {shortlong_counts['long']}, Short: {shortlong_counts['short']}")
                print(f"      ✅ Tradable: {tradable_count}")
                print(f"      🎯 Suitable products (2x+ leverage, LONG, tradable): {len(suitable_products)}")
                
                if suitable_products:
                    print(f"\n      🏆 BEST OPTIONS:")
                    
                    # Sort by leverage (prefer higher leverage)
                    suitable_products.sort(key=lambda x: x.get('leverage', 0), reverse=True)
                    
                    for i, product in enumerate(suitable_products[:5]):
                        name = product.get('name', '')
                        leverage = product.get('leverage')
                        product_id = product.get('id')
                        isin = product.get('isin', '')
                        
                        print(f"         {i+1}. {name[:60]}...")
                        print(f"            Leverage: {leverage}x | ID: {product_id} | ISIN: {isin}")
                    
                    return suitable_products
                else:
                    # Show some examples of what we found
                    print(f"      📋 Sample products found:")
                    for i, product in enumerate(products[:3]):
                        name = product.get('name', '')
                        leverage = product.get('leverage')
                        shortlong = "LONG" if product.get('shortlong') == 1 else "SHORT"
                        tradable = "✅" if product.get('tradable') else "❌"
                        
                        print(f"         {i+1}. {name[:50]}... (Lev: {leverage}x, {shortlong}, Tradable: {tradable})")
                        
        except Exception as e:
            print(f"      ❌ Search failed for '{term}': {e}")
    
    return []

def find_signal_products():
    trading_api = connect_to_degiro()
    
    # The 3 signals
    signals = [
        {
            "symbol": "NL0000235190",
            "company_name": "Airbus Group (EADS)",
            "signal_strength": 5,
            "search_terms": ["AIRBUS", "EADS", "AIR"]
        },
        {
            "symbol": "DE0005200000", 
            "company_name": "Beiersdorf",
            "signal_strength": 3,
            "search_terms": ["BEIERSDORF", "BEI"]
        },
        {
            "symbol": "DE000CBK1001",
            "company_name": "Commerzbank", 
            "signal_strength": 4,
            "search_terms": ["COMMERZBANK", "CBK", "COMMERZ"]
        }
    ]
    
    print("🚀 Finding leveraged products for trading signals...")
    
    results = {}
    
    for signal in signals:
        leveraged_products = search_leveraged_creative(trading_api, signal['search_terms'], signal)
        
        results[signal['company_name']] = {
            'signal': signal,
            'leveraged_products': leveraged_products,
            'tradeable': len(leveraged_products) > 0
        }
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📋 SUMMARY:")
    
    for company, result in results.items():
        status = "✅ TRADEABLE" if result['tradeable'] else "❌ NO PRODUCTS"
        count = len(result['leveraged_products'])
        strength = result['signal']['signal_strength']
        
        print(f"   {company} (Strength {strength}): {status}")
        if count > 0:
            print(f"      Found {count} suitable leveraged products")
    
    return results

if __name__ == "__main__":
    find_signal_products()