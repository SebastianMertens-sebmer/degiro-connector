#!/usr/bin/env python3
"""
Test searching for leveraged products using trading signals data
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

def find_underlying_id_by_company_name(trading_api, company_name):
    """Find underlying ID by matching company name in our extracted JSON"""
    
    # Load our extracted companies
    with open('underlying_companies_from_html.json', 'r') as f:
        companies = json.load(f)
    
    # Search for company name (fuzzy match)
    matches = []
    search_terms = company_name.lower().split()
    
    for company in companies:
        company_lower = company['name'].lower()
        
        # Check if any search term matches
        for term in search_terms:
            if term in company_lower:
                matches.append(company)
                break
    
    print(f"   🔍 Found {len(matches)} potential matches for '{company_name}':")
    for match in matches[:5]:  # Show first 5
        print(f"      ID {match['id']}: {match['name']}")
    
    return matches[0] if matches else None

def search_leveraged_for_underlying(trading_api, underlying_id, target_leverage_min=4, target_leverage_max=5):
    """Search leveraged products for specific underlying ID"""
    
    print(f"   🎯 Searching leveraged products for underlying ID {underlying_id}...")
    
    leveraged_request = ProductSearch.RequestLeverageds()
    leveraged_request.popular_only = False
    leveraged_request.input_aggregate_types = f'underlying:{underlying_id}'
    leveraged_request.input_aggregate_values = str(underlying_id)
    leveraged_request.search_text = ''
    leveraged_request.offset = 0
    leveraged_request.limit = 100
    leveraged_request.require_total = True
    leveraged_request.sort_columns = 'leverage'
    leveraged_request.sort_types = 'asc'
    
    try:
        search_results = trading_api.product_search(request=leveraged_request, raw=True)
        
        if isinstance(search_results, dict) and 'products' in search_results:
            products = search_results['products']
            total = search_results.get('total', 0)
            
            print(f"      📊 Found {len(products)} leveraged products (total: {total})")
            
            # Filter by target leverage
            suitable_products = []
            for product in products:
                leverage = product.get('leverage', 0)
                shortlong = product.get('shortlong')  # 1 = long, -1 = short
                tradable = product.get('tradable', False)
                
                if (target_leverage_min <= leverage <= target_leverage_max and 
                    shortlong == 1 and  # Only LONG products
                    tradable):
                    suitable_products.append(product)
            
            print(f"      ✅ Found {len(suitable_products)} suitable products (leverage {target_leverage_min}-{target_leverage_max}x, LONG, tradable)")
            
            # Show best options
            for i, product in enumerate(suitable_products[:5]):
                name = product.get('name', '')
                leverage = product.get('leverage')
                product_id = product.get('id')
                isin = product.get('isin', '')
                
                print(f"         {i+1}. {name[:50]}... (Lev: {leverage}x, ID: {product_id})")
                print(f"            ISIN: {isin}")
            
            return suitable_products
        
    except Exception as e:
        print(f"      ❌ Search failed: {e}")
        return []

def test_trading_signals():
    trading_api = connect_to_degiro()
    
    # Test signals from the JSON
    test_signals = [
        {
            "symbol": "NL0000235190",  # ISIN
            "company_name": "Airbus Group (EADS)",
            "action": "LONG",
            "signal_strength": 5,
            "entry_price": 196.9,
            "currency": "EUR"
        },
        {
            "symbol": "DE0005200000",  # ISIN
            "company_name": "Beiersdorf", 
            "action": "LONG",
            "signal_strength": 3,
            "entry_price": 95.06,
            "currency": "EUR"
        },
        {
            "symbol": "DE000CBK1001",  # ISIN
            "company_name": "Commerzbank",
            "action": "LONG", 
            "signal_strength": 4,
            "entry_price": 33.01,
            "currency": "EUR"
        }
    ]
    
    print("🎯 Testing trading signals search for leveraged products...")
    
    for i, signal in enumerate(test_signals, 1):
        print(f"\n{'='*60}")
        print(f"🔍 Signal {i}: {signal['company_name']} (Strength: {signal['signal_strength']})")
        print(f"   ISIN: {signal['symbol']}")
        print(f"   Entry Price: {signal['entry_price']} {signal['currency']}")
        
        # Calculate investment amount based on signal strength
        if signal['signal_strength'] >= 5:
            investment_amount = 400
        elif signal['signal_strength'] >= 4:
            investment_amount = 300
        else:
            investment_amount = 250
            
        print(f"   💰 Investment Amount: {investment_amount} EUR")
        
        # Try to find underlying ID by company name
        underlying_match = find_underlying_id_by_company_name(trading_api, signal['company_name'])
        
        if underlying_match:
            underlying_id = underlying_match['id']
            print(f"   ✅ Found underlying ID: {underlying_id} ({underlying_match['name']})")
            
            # Search for suitable leveraged products
            leveraged_products = search_leveraged_for_underlying(trading_api, underlying_id)
            
            if leveraged_products:
                print(f"   🎯 TRADEABLE: YES - Found {len(leveraged_products)} suitable leveraged products")
                
                # Show the best option
                best_product = leveraged_products[0]
                print(f"   🏆 BEST OPTION: {best_product.get('name', '')}")
                print(f"      Leverage: {best_product.get('leverage')}x")
                print(f"      Product ID: {best_product.get('id')}")
                print(f"      ISIN: {best_product.get('isin', '')}")
            else:
                print(f"   ❌ TRADEABLE: NO - No suitable leveraged products found")
        else:
            print(f"   ❌ Could not find underlying ID for '{signal['company_name']}'")
            
            # Try searching by text (fallback)
            print(f"   🔄 Trying text search as fallback...")
            
            leveraged_request = ProductSearch.RequestLeverageds()
            leveraged_request.popular_only = False
            leveraged_request.search_text = signal['company_name'].split()[0]  # Use first word
            leveraged_request.offset = 0
            leveraged_request.limit = 20
            
            try:
                search_results = trading_api.product_search(request=leveraged_request, raw=True)
                if isinstance(search_results, dict) and 'products' in search_results:
                    products = search_results['products']
                    print(f"      📊 Text search found {len(products)} products")
                    
                    for product in products[:3]:
                        print(f"         • {product.get('name', '')[:50]}...")
            except Exception as e:
                print(f"      ❌ Text search failed: {e}")

if __name__ == "__main__":
    test_trading_signals()