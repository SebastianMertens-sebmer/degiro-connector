#!/usr/bin/env python3
"""
Google Stock Search and Order - Final Implementation
Following README sections 7.9 and 4 using installed package
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

def search_nasdaq_stocks(trading_api):
    """Search NASDAQ stocks using ProductSearch.RequestStocks as per README 7.9"""
    print("🔍 Searching NASDAQ stocks for Google/Alphabet...")
    
    # Use RequestStocks from protobuf models (README section 7.9)
    request_stock = ProductSearch.RequestStocks()
    request_stock.index_id = 122001    # NASDAQ 100
    request_stock.is_in_us_green_list = True
    request_stock.stock_country_id = 846  # US
    request_stock.search_text = ''  # Empty to get all
    request_stock.offset = 0
    request_stock.limit = 100
    request_stock.require_total = True
    request_stock.sort_columns = 'name'
    request_stock.sort_types = 'asc'
    
    try:
        # Try with raw=True to avoid the MessageToDict issue
        print("📡 Calling product_search with raw=True...")
        product_search = trading_api.product_search(request=request_stock, raw=True)
        
        print(f"📊 Raw response type: {type(product_search)}")
        
        # Handle raw response
        if isinstance(product_search, dict):
            products = product_search.get('products', [])
            print(f"📊 Retrieved {len(products)} NASDAQ stocks")
            
            # Filter for Google/Alphabet stocks
            google_stocks = []
            for product in products:
                name = product.get('name', '').upper()
                symbol = product.get('symbol', '').upper()
                
                # Look for Google/Alphabet stocks
                if any(keyword in name for keyword in ['GOOGLE', 'ALPHABET']) or \
                   any(keyword in symbol for keyword in ['GOOGL', 'GOOG']):
                    google_stocks.append({
                        'name': product.get('name', 'N/A'),
                        'id': product.get('id', 'N/A'),
                        'symbol': product.get('symbol', 'N/A'),
                        'isin': product.get('isin', 'N/A'),
                        'currency': product.get('currency', 'N/A'),
                        'exchange': product.get('exchangeId', 'N/A')
                    })
            
            if google_stocks:
                print(f"🎯 Found {len(google_stocks)} Google/Alphabet stocks:")
                for i, stock in enumerate(google_stocks):
                    print(f"   {i+1}. {stock['name']} ({stock['symbol']})")
                    print(f"      ID: {stock['id']}, ISIN: {stock['isin']}")
                    print(f"      Currency: {stock['currency']}, Exchange: {stock['exchange']}")
                    print()
            
            return google_stocks
        else:
            print(f"❌ Unexpected response format: {product_search}")
            return []
        
    except Exception as e:
        print(f"❌ Stock search failed: {e}")
        
        # Fallback: try a simple lookup request for specific Google symbols
        print("🔄 Trying fallback: direct symbol lookup...")
        try:
            lookup_request = ProductSearch.RequestLookup()
            lookup_request.search_text = 'GOOGL'
            lookup_request.limit = 10
            lookup_request.offset = 0
            lookup_request.product_type_id = 1  # Stocks
            
            print("📡 Calling product_search with GOOGL lookup...")
            lookup_result = trading_api.product_search(request=lookup_request, raw=True)
            
            if isinstance(lookup_result, dict) and 'products' in lookup_result:
                products = lookup_result['products']
                print(f"📊 Lookup found {len(products)} results for GOOGL")
                
                google_stocks = []
                for product in products:
                    google_stocks.append({
                        'name': product.get('name', 'N/A'),
                        'id': product.get('id', 'N/A'),
                        'symbol': product.get('symbol', 'N/A'),
                        'isin': product.get('isin', 'N/A'),
                        'currency': product.get('currency', 'N/A'),
                        'exchange': product.get('exchangeId', 'N/A')
                    })
                
                return google_stocks
            else:
                print(f"❌ Lookup also failed: {lookup_result}")
                return []
                
        except Exception as lookup_error:
            print(f"❌ Fallback lookup also failed: {lookup_error}")
            return []

def place_order(trading_api, product_id, product_name, product_symbol):
    """Place a buy order following README section 4"""
    print(f"📝 Placing order for {product_name} ({product_symbol})")
    print(f"    Product ID: {product_id}")
    
    # Create order using protobuf Order (README section 4)
    order = Order()
    order.action = Order.Action.BUY
    order.order_type = Order.OrderType.LIMIT
    order.price = 150.0  # Limit price - adjust as needed
    order.product_id = product_id
    order.size = 1  # Buy 1 share
    order.time_type = Order.TimeType.GOOD_TILL_DAY
    
    try:
        print("🔍 Step 1: Checking order (README section 4.1.1)...")
        # Step 1: Check order
        checking_response = trading_api.check_order(order=order)
        
        if checking_response:
            print("✅ Order check successful!")
            
            # Handle both dict and object responses
            if hasattr(checking_response, 'confirmation_id'):
                confirmation_id = checking_response.confirmation_id
                transaction_fees = getattr(checking_response, 'transaction_fees', 'N/A')
                free_space_new = getattr(checking_response, 'free_space_new', 'N/A')
            else:
                confirmation_id = checking_response.get('confirmation_id')
                transaction_fees = checking_response.get('transaction_fees', 'N/A')
                free_space_new = checking_response.get('free_space_new', 'N/A')
            
            print(f"   • Confirmation ID: {confirmation_id}")
            print(f"   • Transaction fees: {transaction_fees}")
            print(f"   • Free space new: {free_space_new}")
            
            if confirmation_id:
                print(f"\n💰 Order Summary:")
                print(f"   • Action: BUY")
                print(f"   • Product: {product_name} ({product_symbol})")
                print(f"   • Quantity: 1 share")
                print(f"   • Limit Price: €{order.price}")
                print(f"   • Estimated Fees: {transaction_fees}")
                
                print("\n❓ Do you want to confirm this order? (y/N): ", end="")
                confirm = input().strip().lower()
                
                if confirm == 'y' or confirm == 'yes':
                    print("✅ Step 2: Confirming order (README section 4.1.2)...")
                    # Step 2: Confirm order
                    confirmation_response = trading_api.confirm_order(
                        confirmation_id=confirmation_id,
                        order=order
                    )
                    
                    if confirmation_response:
                        # Handle both dict and object responses
                        if hasattr(confirmation_response, 'order_id'):
                            order_id = confirmation_response.order_id
                        else:
                            order_id = confirmation_response.get('order_id')
                            
                        print(f"🎉 Order placed successfully!")
                        print(f"   • Order ID: {order_id}")
                        print(f"   • Status: PENDING")
                        print(f"   • Product: {product_name} ({product_symbol})")
                        print(f"   • Action: BUY 1 share @ €{order.price}")
                        return order_id
                    else:
                        print("❌ Order confirmation failed")
                        return None
                else:
                    print("❌ Order cancelled by user")
                    return None
            else:
                print("❌ No confirmation ID received")
                return None
        else:
            print("❌ Order check failed")
            return None
            
    except Exception as e:
        print(f"❌ Order placement failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("🚀 Google Stock Search and Order (Final Implementation)")
    print("=" * 60)
    print("📖 Following README sections 7.9 (StocksRequest) and 4 (Orders)")
    print()
    
    try:
        # Connect to DEGIRO
        trading_api = connect_to_degiro()
        
        # Search for Google stocks
        google_stocks = search_nasdaq_stocks(trading_api)
        
        if not google_stocks:
            print("❌ No Google/Alphabet stocks found")
            print("💡 This might be due to market restrictions or regional availability")
            return
        
        # Let user choose which Google stock to buy
        print("📋 Select which Google/Alphabet stock to order:")
        for i, stock in enumerate(google_stocks):
            print(f"   {i+1}. {stock['name']} ({stock['symbol']})")
        
        print(f"\nEnter choice (1-{len(google_stocks)}): ", end="")
        choice = input().strip()
        
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(google_stocks):
                selected_stock = google_stocks[choice_idx]
                product_id = selected_stock['id']
                product_name = selected_stock['name']
                product_symbol = selected_stock['symbol']
                
                print(f"\n✅ Selected: {product_name} ({product_symbol})")
                
                # Place the order following README section 4
                order_id = place_order(trading_api, product_id, product_name, product_symbol)
                
                if order_id:
                    print(f"\n🎉 SUCCESS! Order placed with ID: {order_id}")
                    print("📱 You can monitor this order in your DEGIRO app or web interface")
                else:
                    print("\n❌ Failed to place order")
                    
            else:
                print("❌ Invalid choice")
                
        except ValueError:
            print("❌ Invalid input - please enter a number")
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()