#!/usr/bin/env python3
"""
Test real prices for all P&G leveraged products using our new implementation
"""

import os
# Note: Run this test from the custom-trading directory

# Test the real pricing function directly
def test_pg_real_prices():
    """Test real prices for all P&G leveraged products"""
    print("🔍 Testing Real P&G Leveraged Product Prices")
    print("=" * 60)
    
    # P&G leveraged products we found
    pg_products = [
        {"id": 28208959, "leverage": "10.2x", "fake_price": "€100.25"},
        {"id": 28208960, "leverage": "8.5x", "fake_price": "€85.40"},
        {"id": 28208961, "leverage": "5.0x", "fake_price": "€50.15"}
    ]
    
    # Import our API's real price function
    sys.path.append('/Users/sebastianmertens/Documents/GitHub/degiro-connector/custom-trading')
    from api.main import get_real_price
    
    for product in pg_products:
        product_id = product["id"]
        leverage = product["leverage"]
        fake_price = product["fake_price"]
        
        print(f"\n🏭 Testing Product ID: {product_id}")
        print(f"   Leverage: {leverage}")
        print(f"   Previous Fake Price: {fake_price}")
        
        try:
            # Test our real price function
            real_price_info = get_real_price(str(product_id))
            
            print(f"   ✅ Real Prices Retrieved:")
            print(f"      Bid: €{real_price_info.bid}")
            print(f"      Ask: €{real_price_info.ask}")
            print(f"      Last: €{real_price_info.last}")
            
        except Exception as e:
            print(f"   ❌ Real Price Error: {e}")
            
            # Fallback: Test with direct DEGIRO API to get vwdId
            try:
                from degiro_connector.trading.api import API as TradingAPI
                from degiro_connector.trading.models.credentials import Credentials
                
                credentials = Credentials(
                    username=os.getenv("DEGIRO_USERNAME"),
                    password=os.getenv("DEGIRO_PASSWORD"),
                    totp_secret_key=os.getenv("DEGIRO_TOTP_SECRET"),
                    int_account=int(os.getenv("DEGIRO_INT_ACCOUNT", 0))
                )
                
                api = TradingAPI(credentials=credentials)
                api.connect()
                
                # Get product info to check vwdId
                product_info = api.get_products_info(
                    product_list=[product_id],
                    raw=True
                )
                
                if isinstance(product_info, dict) and 'data' in product_info:
                    product_data = product_info['data'].get(str(product_id))
                    if product_data:
                        vwd_id = product_data.get('vwdId')
                        print(f"      vwdId: {vwd_id}")
                        print(f"      Product Name: {product_data.get('name', 'N/A')}")
                        print(f"      Currency: {product_data.get('currency', 'N/A')}")
                
            except Exception as fallback_error:
                print(f"   ❌ Fallback Error: {fallback_error}")

if __name__ == "__main__":
    test_pg_real_prices()