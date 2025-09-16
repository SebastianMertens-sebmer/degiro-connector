#!/usr/bin/env python3
"""
Test Google Stock Search and Order with Fixed Environment
"""

import json
from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.trading_pb2 import Credentials, ProductSearch, Order

def connect_to_degiro():
    """Connect to DEGIRO using saved credentials"""
    print("🔄 Connecting to DEGIRO...")
    
    # Load credentials from config
    with open('config/config.json', 'r') as f:
        config = json.load(f)
    
    credentials = Credentials()
    credentials.username = config['username']
    credentials.password = config['password']
    credentials.totp_secret_key = config['totp_secret_key']
    credentials.int_account = config['int_account']
    
    trading_api = TradingAPI(credentials=credentials)
    trading_api.connect()
    
    print(f"✅ Connected! Session ID: {trading_api.connection_storage.session_id}")
    return trading_api

def search_google_stocks(trading_api):
    """Search for Google stocks using proper product search"""
    print("🔍 Searching for Google/Alphabet stocks...")
    
    # Try lookup first
    lookup_request = ProductSearch.RequestLookup()
    lookup_request.search_text = 'GOOGL'
    lookup_request.limit = 10
    lookup_request.offset = 0
    lookup_request.product_type_id = 1  # Stocks
    
    try:
        print("📡 Searching for GOOGL...")
        search_results = trading_api.product_search(request=lookup_request, raw=True)
        
        print(f"📊 Raw search results: {type(search_results)}")
        
        google_stocks = []
        if isinstance(search_results, dict) and 'products' in search_results:
            for product in search_results['products']:
                google_stocks.append({
                    'id': product.get('id'),
                    'name': product.get('name', 'N/A'),
                    'symbol': product.get('symbol', 'N/A'),
                    'isin': product.get('isin', 'N/A'),
                    'currency': product.get('currency', 'N/A'),
                    'exchange': product.get('exchangeId', 'N/A'),
                })
                print(f"   ✅ Found: {product.get('name', 'N/A')} ({product.get('symbol', 'N/A')})")
        
        return google_stocks
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return []

def get_product_info(trading_api, product_ids):
    """Get product info using get_products_info"""
    print("🔍 Getting product information...")
    
    try:
        product_info = trading_api.get_products_info(product_ids, raw=False)
        print(f"✅ Product info retrieved successfully")
        print(f"Type: {type(product_info)}")
        return product_info
    except Exception as e:
        print(f"❌ Failed to get product info: {e}")
        return None

def place_order(trading_api, product_id, product_name):
    """Place a buy order"""
    print(f"📝 Placing order for {product_name} (ID: {product_id})")
    
    # Create order
    order = Order()
    order.action = Order.Action.BUY
    order.order_type = Order.OrderType.LIMIT
    order.price = 150.0
    order.product_id = product_id
    order.size = 1
    order.time_type = Order.TimeType.GOOD_TILL_DAY
    
    try:
        print("🔍 Checking order...")
        checking_response = trading_api.check_order(order=order)
        
        if checking_response:
            print("✅ Order check successful!")
            confirmation_id = checking_response.confirmation_id
            print(f"   • Confirmation ID: {confirmation_id}")
            
            print("\n❓ Do you want to confirm this order? (y/N): ", end="")
            confirm = input().strip().lower()
            
            if confirm == 'y':
                print("✅ Confirming order...")
                confirmation_response = trading_api.confirm_order(
                    confirmation_id=confirmation_id,
                    order=order
                )
                
                if confirmation_response:
                    order_id = confirmation_response.order_id
                    print(f"🎉 Order placed! ID: {order_id}")
                    return order_id
                else:
                    print("❌ Order confirmation failed")
            else:
                print("❌ Order cancelled")
        else:
            print("❌ Order check failed")
        
        return None
        
    except Exception as e:
        print(f"❌ Order failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("🚀 Google Stock Search and Order (Fixed Environment)")
    print("=" * 55)
    
    try:
        # Connect
        trading_api = connect_to_degiro()
        
        # Search for Google
        google_stocks = search_google_stocks(trading_api)
        
        if google_stocks:
            print(f"\n📋 Found {len(google_stocks)} Google stocks:")
            for i, stock in enumerate(google_stocks):
                print(f"   {i+1}. {stock['name']} ({stock['symbol']})")
            
            # Let user choose
            choice = input(f"\nSelect stock (1-{len(google_stocks)}): ").strip()
            
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(google_stocks):
                    selected = google_stocks[choice_idx]
                    
                    # Get detailed info
                    product_info = get_product_info(trading_api, [selected['id']])
                    
                    # Place order
                    order_id = place_order(trading_api, selected['id'], selected['name'])
                    
                    if order_id:
                        print(f"\n🎉 SUCCESS! Order ID: {order_id}")
                else:
                    print("❌ Invalid choice")
            except ValueError:
                print("❌ Invalid input")
        else:
            print("❌ No Google stocks found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()