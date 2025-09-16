#!/usr/bin/env python3
"""
Proper Google Stock Search and Order following README methodology
Using StocksRequest for NASDAQ stocks as shown in examples/trading/product_search.py
"""

import sys
import os
sys.path.insert(0, '/Users/sebastianmertens/Documents/GitHub/degiro-connector/src')

import json
from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.trading_pb2 import Credentials
from degiro_connector.trading.models.product_search import StocksRequest
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

def search_nasdaq_stocks(trading_api):
    """Search NASDAQ stocks including Google using StocksRequest as per README 7.9"""
    print("🔍 Searching NASDAQ stocks for Google/Alphabet...")
    
    # Use StocksRequest from README section 7.9
    request_stock = StocksRequest(
        index_id=122001,    # NASDAQ 100 (as shown in example)
        is_in_us_green_list=True,
        stock_country_id=846,  # US
        search_text='',  # Empty to get all, then filter for Google
        offset=0,
        limit=100,
        require_total=True,
        sort_columns='name',
        sort_types='asc',
    )
    
    try:
        # FETCH DATA using product_search as shown in README
        product_search = trading_api.product_search(product_request=request_stock, raw=False)
        
        print(f"📊 Retrieved {len(product_search.products)} NASDAQ stocks")
        
        # Filter for Google/Alphabet stocks
        google_stocks = []
        for product in product_search.products:
            name = product.name.upper()
            symbol = getattr(product, 'symbol', '').upper()
            
            # Look for Google/Alphabet stocks
            if any(keyword in name for keyword in ['GOOGLE', 'ALPHABET']) or \
               any(keyword in symbol for keyword in ['GOOGL', 'GOOG']):
                google_stocks.append({
                    'name': product.name,
                    'id': product.id,
                    'symbol': getattr(product, 'symbol', 'N/A'),
                    'isin': getattr(product, 'isin', 'N/A'),
                    'currency': getattr(product, 'currency', 'N/A'),
                    'exchange': getattr(product, 'exchangeId', 'N/A')
                })
        
        if google_stocks:
            print(f"🎯 Found {len(google_stocks)} Google/Alphabet stocks:")
            for i, stock in enumerate(google_stocks):
                print(f"   {i+1}. {stock['name']} ({stock['symbol']})")
                print(f"      ID: {stock['id']}, ISIN: {stock['isin']}")
                print(f"      Currency: {stock['currency']}, Exchange: {stock['exchange']}")
                print()
        
        return google_stocks
        
    except Exception as e:
        print(f"❌ Stock search failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def place_order(trading_api, product_id, product_name, product_symbol):
    """Place a buy order following README section 4"""
    print(f"📝 Placing order for {product_name} ({product_symbol})")
    print(f"    Product ID: {product_id}")
    
    # Create order as shown in README section 4 and examples/trading/order.py
    order = Order(
        buy_sell=Action.BUY,
        order_type=OrderType.LIMIT,
        price=150.0,  # Limit price - adjust as needed
        product_id=product_id,
        size=1,  # Buy 1 share
        time_type=TimeType.GOOD_TILL_DAY,
    )
    
    try:
        print("🔍 Step 1: Checking order (README section 4.1.1)...")
        # Step 1: Check order
        checking_response = trading_api.check_order(order=order)
        
        if checking_response:
            print("✅ Order check successful!")
            print(f"   • Confirmation ID: {checking_response.confirmation_id}")
            print(f"   • Transaction fees: {getattr(checking_response, 'transaction_fees', 'N/A')}")
            print(f"   • Free space new: {getattr(checking_response, 'free_space_new', 'N/A')}")
            
            confirmation_id = checking_response.confirmation_id
            
            if confirmation_id:
                print(f"\n💰 Order Summary:")
                print(f"   • Action: BUY")
                print(f"   • Product: {product_name} ({product_symbol})")
                print(f"   • Quantity: 1 share")
                print(f"   • Limit Price: €{order.price}")
                print(f"   • Estimated Fees: {getattr(checking_response, 'transaction_fees', 'N/A')}")
                
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
                        order_id = confirmation_response.order_id
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
    print("🚀 Google Stock Search and Order (Following README)")
    print("=" * 55)
    print("📖 Using methodology from README sections 7.9 and 4")
    print()
    
    try:
        # Connect to DEGIRO
        trading_api = connect_to_degiro()
        
        # Search for Google stocks using StocksRequest (README 7.9)
        google_stocks = search_nasdaq_stocks(trading_api)
        
        if not google_stocks:
            print("❌ No Google/Alphabet stocks found in NASDAQ search")
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