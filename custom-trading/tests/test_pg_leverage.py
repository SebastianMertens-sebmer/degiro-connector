#!/usr/bin/env python3
"""
Test real prices for P&G leverage product ID 28208959
"""

import os
import sys
sys.path.append('/Users/sebastianmertens/Documents/GitHub/degiro-connector')

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials

def test_pg_leverage_price():
    """Get real price for P&G leverage product 28208959"""
    print("🔍 Testing P&G Leverage Product Price")
    print("=" * 50)
    
    # Load credentials
    username = "bastiheye"
    password = "!c3c6kdG5j6NFB7R"
    totp_secret = "5ADDODASZT7CHKD273VFMJMJZNAUHVBH"
    int_account = 31043411
    
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
        
        # Test P&G leverage product ID 28208959
        pg_product_id = 28208959
        
        print(f"\n🏭 Getting real price for P&G Leverage (Product ID: {pg_product_id})")
        
        # Get product info
        product_info = api.get_products_info(
            product_list=[pg_product_id],
            raw=True
        )
        
        print(f"📊 Raw product info: {product_info}")
        
        if isinstance(product_info, dict) and 'data' in product_info:
            pg_data = product_info['data'].get(str(pg_product_id))
            if pg_data:
                print(f"\n🏭 P&G Leverage Real Data:")
                print(f"   Name: {pg_data.get('name', 'N/A')}")
                print(f"   ISIN: {pg_data.get('isin', 'N/A')}")
                print(f"   Currency: {pg_data.get('currency', 'N/A')}")
                print(f"   Close Price: {pg_data.get('closePrice', 'N/A')}")
                print(f"   Close Price Date: {pg_data.get('closePriceDate', 'N/A')}")
                
                # Check ALL price-related fields
                print(f"\n📋 All price-related fields:")
                for key, value in pg_data.items():
                    if 'price' in key.lower() or 'Price' in key:
                        print(f"   {key}: {value}")
                
                # Check ALL fields to understand structure
                print(f"\n📋 ALL available fields:")
                for key, value in pg_data.items():
                    print(f"   {key}: {value}")
            else:
                print(f"❌ No data found for product {pg_product_id}")
        else:
            print("❌ Invalid response format")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_pg_leverage_price()