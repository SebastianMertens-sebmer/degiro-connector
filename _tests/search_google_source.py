#!/usr/bin/env python3
"""
Search for Google and place order using source code models
"""

import sys
import os
sys.path.insert(0, '/Users/sebastianmertens/Documents/GitHub/degiro-connector/src')

import json
from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.trading_pb2 import Credentials
from degiro_connector.trading.models.product_search import LookupRequest
from degiro_connector.trading.models.order import Order, Action, OrderType, TimeType

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
    """Search for Google/Alphabet stock using source models"""
    print("🔍 Searching for Google/Alphabet stock...")
    
    # Use LookupRequest from source models
    lookup_request = LookupRequest(
        search_text="GOOGL",
        limit=10,
        offset=0,
        product_type_id=1,  # Stocks
    )
    
    try:
        search_results = trading_api.product_search(product_request=lookup_request, raw=False)
        
        print(f"📊 Search results for GOOGL:")
        print(f"Type: {type(search_results)}")
        
        if hasattr(search_results, 'products'):
            products = search_results.products
        elif isinstance(search_results, dict) and 'products' in search_results:
            products = search_results['products']
        else:
            print(f"Raw results: {search_results}")
            return []
        
        google_stocks = []
        for i, product in enumerate(products[:5]):  # Show top 5
            if hasattr(product, 'name'):
                name = product.name
                product_id = product.id
                symbol = getattr(product, 'symbol', 'N/A')
                isin = getattr(product, 'isin', 'N/A')
            else:
                name = product.get('name', 'N/A')
                product_id = product.get('id', 'N/A')
                symbol = product.get('symbol', 'N/A')
                isin = product.get('isin', 'N/A')
            
            print(f"   {i+1}. {name} ({symbol})")
            print(f"      ID: {product_id}")
            print(f"      ISIN: {isin}")
            google_stocks.append({
                'name': name,
                'id': product_id,
                'symbol': symbol,
                'isin': isin
            })
            print()
        
        return google_stocks
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def place_order(trading_api, product_id, product_name):
    """Place a buy order for the selected stock"""
    print(f"📝 Placing order for {product_name} (ID: {product_id})...")
    
    # Create order using source models
    order = Order(
        buy_sell=Action.BUY,
        order_type=OrderType.LIMIT,
        price=150.0,  # Limit price
        product_id=product_id,
        size=1,  # Buy 1 share
        time_type=TimeType.GOOD_TILL_DAY,
    )
    
    try:
        print("🔍 Checking order...")
        # Step 1: Check order
        checking_response = trading_api.check_order(order=order)
        
        if checking_response:
            print("✅ Order check successful!")
            
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
                print("\n❓ Do you want to confirm this order? (y/N): ", end="")
                confirm = input().strip().lower()
                
                if confirm == 'y' or confirm == 'yes':
                    print("✅ Confirming order...")
                    # Step 2: Confirm order
                    confirmation_response = trading_api.confirm_order(
                        confirmation_id=confirmation_id,
                        order=order
                    )
                    
                    if confirmation_response:
                        if hasattr(confirmation_response, 'order_id'):
                            order_id = confirmation_response.order_id
                        else:
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
    print("🚀 Google Stock Search and Order (Source Version)")
    print("=" * 50)
    
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
        
        print(f"\nEnter choice (1-{len(google_stocks)}): ", end="")
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