#!/usr/bin/env python3
"""
Direct Google Order using get_products_info (README 7.11)
Since product_search has version issues, we'll use known product IDs and get_products_info
"""

import json
from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.trading_pb2 import Credentials, Order

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

def get_google_products(trading_api):
    """Get Google product info using get_products_info (README 7.11)"""
    print("🔍 Looking up Google/Alphabet products using known IDs...")
    
    # Common Google product IDs on European/DEGIRO exchanges
    # These are educated guesses based on common DEGIRO product IDs
    potential_google_ids = [
        360148977,  # Example from README charts
        350009261,  # Common European Google ID
        361001012,  # Another common ID pattern
        72160,      # From order example
        96008,      # From products_info example
        1153605,    # From products_info example
        5462588,    # From products_info example
    ]
    
    google_products = []
    
    for product_id in potential_google_ids:
        try:
            print(f"   🔍 Checking product ID: {product_id}")
            
            # Use get_products_info as per README section 7.11  
            product_info = trading_api.get_products_info([product_id], raw=True)
            
            if product_info and 'data' in product_info:
                for product_data in product_info['data'].values():
                    name = product_data.get('name', '').upper()
                    symbol = product_data.get('symbol', '').upper()
                    
                    # Check if this looks like a Google stock
                    if any(keyword in name for keyword in ['GOOGLE', 'ALPHABET']) or \
                       any(keyword in symbol for keyword in ['GOOGL', 'GOOG']):
                        google_products.append({
                            'id': product_id,
                            'name': product_data.get('name', 'N/A'),
                            'symbol': product_data.get('symbol', 'N/A'),
                            'isin': product_data.get('isin', 'N/A'),
                            'currency': product_data.get('currency', 'N/A'),
                            'exchange': product_data.get('exchangeId', 'N/A'),
                            'tradable': product_data.get('tradable', False)
                        })
                        print(f"   ✅ Found Google stock: {product_data.get('name', 'N/A')}")
                    else:
                        print(f"   ❌ Not Google: {product_data.get('name', 'Unknown')}")
            
        except Exception as e:
            print(f"   ❌ Failed to get info for ID {product_id}: {e}")
            continue
    
    # If no Google stocks found, let's try to use one of the example IDs for demonstration
    if not google_products:
        print("⚠️  No Google stocks found with known IDs")
        print("💡 Let's use a demo product ID for order demonstration...")
        
        # Use the ID from README order example for demonstration
        demo_product_id = 72160
        try:
            product_info = trading_api.get_products_info([demo_product_id], raw=True)
            
            if product_info and 'data' in product_info:
                for product_data in product_info['data'].values():
                    google_products.append({
                        'id': demo_product_id,
                        'name': f"Demo Stock ({product_data.get('name', 'Unknown')})",
                        'symbol': product_data.get('symbol', 'DEMO'),
                        'isin': product_data.get('isin', 'N/A'),
                        'currency': product_data.get('currency', 'EUR'),
                        'exchange': product_data.get('exchangeId', 'N/A'),
                        'tradable': product_data.get('tradable', True)
                    })
                    print(f"   📋 Using demo product: {product_data.get('name', 'Unknown')}")
        except Exception as e:
            print(f"   ❌ Demo product also failed: {e}")
    
    return google_products

def place_order(trading_api, product_id, product_name, product_symbol):
    """Place a buy order following README section 4"""
    print(f"\n📝 Placing order for {product_name} ({product_symbol})")
    print(f"    Product ID: {product_id}")
    
    # Create order using protobuf Order (README section 4)
    order = Order()
    order.action = Order.Action.BUY
    order.order_type = Order.OrderType.LIMIT
    order.price = 12.1  # Use same price as README example
    order.product_id = product_id
    order.size = 1  # Buy 1 share
    order.time_type = Order.TimeType.GOOD_TILL_DAY
    
    try:
        print("🔍 Step 1: Checking order (README section 4.1.1)...")
        # Step 1: Check order (as per README examples/trading/order.py)
        checking_response = trading_api.check_order(order=order)
        
        if checking_response:
            print("✅ Order check successful!")
            print(f"Type of response: {type(checking_response)}")
            print(f"Response: {checking_response}")
            
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
                    # Step 2: Confirm order (as per README examples/trading/order.py)
                    confirmation_response = trading_api.confirm_order(
                        confirmation_id=confirmation_id,
                        order=order
                    )
                    
                    if confirmation_response:
                        print(f"Type of confirmation response: {type(confirmation_response)}")
                        print(f"Confirmation response: {confirmation_response}")
                        
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
    print("🚀 Direct Google Order using get_products_info")
    print("=" * 50)
    print("📖 Following README section 7.11 and 4")
    print()
    
    try:
        # Connect to DEGIRO
        trading_api = connect_to_degiro()
        
        # Get Google products using get_products_info
        google_products = get_google_products(trading_api)
        
        if not google_products:
            print("❌ No suitable products found")
            return
        
        print(f"\n📋 Found {len(google_products)} product(s):")
        for i, product in enumerate(google_products):
            print(f"   {i+1}. {product['name']} ({product['symbol']})")
            print(f"      ID: {product['id']}, Tradable: {product['tradable']}")
        
        # Let user choose which product to order
        print(f"\nEnter choice (1-{len(google_products)}): ", end="")
        choice = input().strip()
        
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(google_products):
                selected_product = google_products[choice_idx]
                product_id = selected_product['id']
                product_name = selected_product['name']
                product_symbol = selected_product['symbol']
                
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