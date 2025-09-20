#!/usr/bin/env python3
"""
Test real prices using DEGIRO's products_info API
Compare with our API's mock prices to find the issue
"""

import os

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials

def test_real_prices():
    """Get real prices for Apple using DEGIRO's products_info API"""
    print("🔍 Testing Real Prices from DEGIRO")
    print("=" * 50)
    
    # Load credentials
    username = os.getenv("DEGIRO_USERNAME")
    password = os.getenv("DEGIRO_PASSWORD")
    totp_secret = os.getenv("DEGIRO_TOTP_SECRET")
    int_account = int(os.getenv("DEGIRO_INT_ACCOUNT", 0))
    
    try:
        # Create credentials
        credentials = Credentials(
            username=username,
            password=password,
            totp_secret_key=totp_secret,
            int_account=int_account
        )
        
        # Create API instance
        api = TradingAPI(credentials=credentials)
        print("✅ API instance created")
        
        # Connect
        connection_result = api.connect()
        print(f"✅ Connected: {connection_result}")
        
        # Test Apple product ID 331868 (from our API search)
        apple_product_id = 331868
        
        print(f"\n🍎 Getting real price for Apple (Product ID: {apple_product_id})")
        
        # Get product info
        product_info = api.get_products_info(
            product_list=[apple_product_id],
            raw=True
        )
        
        print(f"📊 Raw product info: {product_info}")
        
        if isinstance(product_info, dict) and 'data' in product_info:
            apple_data = product_info['data'].get(str(apple_product_id))
            if apple_data:
                print(f"\n🍎 Apple Real Data:")
                print(f"   Name: {apple_data.get('name', 'N/A')}")
                print(f"   ISIN: {apple_data.get('isin', 'N/A')}")
                print(f"   Currency: {apple_data.get('currency', 'N/A')}")
                print(f"   Close Price: {apple_data.get('closePrice', 'N/A')}")
                print(f"   Close Price Date: {apple_data.get('closePriceDate', 'N/A')}")
                
                # Check if there are other price fields
                print(f"\n📋 All available fields:")
                for key, value in apple_data.items():
                    if 'price' in key.lower() or 'Price' in key:
                        print(f"   {key}: {value}")
        
        # Try with BMW too (Product ID: 3597)
        bmw_product_id = 3597
        print(f"\n🚗 Getting real price for BMW (Product ID: {bmw_product_id})")
        
        bmw_info = api.get_products_info(
            product_list=[bmw_product_id],
            raw=True
        )
        
        if isinstance(bmw_info, dict) and 'data' in bmw_info:
            bmw_data = bmw_info['data'].get(str(bmw_product_id))
            if bmw_data:
                print(f"🚗 BMW Real Data:")
                print(f"   Name: {bmw_data.get('name', 'N/A')}")
                print(f"   Close Price: {bmw_data.get('closePrice', 'N/A')}")
                print(f"   Currency: {bmw_data.get('currency', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_real_prices()