#!/usr/bin/env python3
"""
Search for Google/Alphabet stock and place an order
"""

import json
from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.trading_pb2 import Credentials

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

def search_google_stock(trading_api):
    """Search for Google/Alphabet stock"""
    print("🔍 Searching for Google/Alphabet stock...")
    
    # Use product lookup as shown in README section 7.2
    from degiro_connector.trading.models.trading_pb2 import ProductSearch
    
    # Search for Google/Alphabet
    product_request = ProductSearch.RequestLookup()
    product_request.search_text = 'GOOGL'
    product_request.limit = 10
    product_request.offset = 0
    product_request.product_type_id = 1  # Stocks
    
    try:
        search_results = trading_api.product_search(request=product_request, raw=True)
        
        print(f"📊 Found {len(search_results['products'])} results for GOOGL:")
        
        google_stocks = []
        for i, product in enumerate(search_results['products'][:5]):  # Show top 5
            print(f"   {i+1}. {product['name']} ({product['symbol']})")
            print(f"      ID: {product['id']}, Exchange: {product.get('exchangeId', 'N/A')}")
            print(f"      ISIN: {product.get('isin', 'N/A')}")
            google_stocks.append(product)
            print()
        
        return google_stocks
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return []

def place_order(trading_api, product_id, product_name):
    """Place a buy order for the selected stock"""
    print(f"📝 Placing order for {product_name} (ID: {product_id})...")
    
    from degiro_connector.trading.models.trading_pb2 import Order
    
    # Create order as shown in README section 4
    order = Order()
    order.action = Order.Action.BUY
    order.order_type = Order.OrderType.LIMIT
    order.price = 150.0  # Limit price (adjust as needed)
    order.product_id = product_id
    order.size = 1  # Buy 1 share
    order.time_type = Order.TimeType.GOOD_TILL_DAY
    
    try:
        print("🔍 Checking order...")
        # Step 1: Check order (as per README section 4.1.1)
        checking_response = trading_api.check_order(order=order)
        
        if checking_response:
            print("✅ Order check successful!")
            print(f"   • Confirmation ID: {checking_response.get('confirmation_id', 'N/A')}")
            print(f"   • Transaction fees: {checking_response.get('transaction_fees', 'N/A')}")
            print(f"   • Free space new: {checking_response.get('free_space_new', 'N/A')}")
            
            confirmation_id = checking_response.get('confirmation_id')
            
            if confirmation_id:
                print("\n❓ Do you want to confirm this order? (y/N): ", end="")
                confirm = input().strip().lower()
                
                if confirm == 'y' or confirm == 'yes':
                    print("✅ Confirming order...")
                    # Step 2: Confirm order (as per README section 4.1.2)
                    confirmation_response = trading_api.confirm_order(
                        confirmation_id=confirmation_id,
                        order=order
                    )
                    
                    if confirmation_response:
                        order_id = confirmation_response.get('order_id')
                        print(f"🎉 Order placed successfully!")
                        print(f"   • Order ID: {order_id}")
                        print(f"   • Action: BUY")
                        print(f"   • Quantity: 1 share")
                        print(f"   • Limit Price: €{order.price}")
                        print(f"   • Product: {product_name}")
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
    print("🚀 Google Stock Search and Order")
    print("=" * 40)
    
    try:
        # Connect to DEGIRO
        trading_api = connect_to_degiro()
        
        # Search for Google stock
        google_stocks = search_google_stock(trading_api)
        
        if not google_stocks:
            print("❌ No Google stocks found")
            return
        
        # Let user choose which Google stock to buy
        print("📋 Select which Google stock to order:")
        for i, stock in enumerate(google_stocks):
            print(f"   {i+1}. {stock['name']} ({stock['symbol']})")
        
        print("\nEnter choice (1-{}): ".format(len(google_stocks)), end="")
        choice = input().strip()
        
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(google_stocks):
                selected_stock = google_stocks[choice_idx]
                product_id = selected_stock['id']
                product_name = selected_stock['name']
                
                print(f"\n✅ Selected: {product_name}")
                
                # Place the order
                order_id = place_order(trading_api, product_id, product_name)
                
                if order_id:
                    print(f"\n🎉 Success! Order placed with ID: {order_id}")
                else:
                    print("\n❌ Failed to place order")
                    
            else:
                print("❌ Invalid choice")
                
        except ValueError:
            print("❌ Invalid input")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()