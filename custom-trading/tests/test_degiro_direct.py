#!/usr/bin/env python3
"""
Test DEGIRO connection directly to diagnose stock search issues
"""

import os
import sys
sys.path.append('/Users/sebastianmertens/Documents/GitHub/degiro-connector')

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials
from degiro_connector.trading.models.product_search import StocksRequest

def test_degiro_connection():
    """Test direct DEGIRO connection and search"""
    print("🔍 Testing Direct DEGIRO Connection")
    print("=" * 50)
    
    # Load credentials
    username = os.getenv("DEGIRO_USERNAME")
    password = os.getenv("DEGIRO_PASSWORD") 
    totp_secret = os.getenv("DEGIRO_TOTP_SECRET")
    int_account = os.getenv("DEGIRO_INT_ACCOUNT")
    
    if not all([username, password, totp_secret, int_account]):
        print("❌ Missing DEGIRO credentials")
        return False
    
    print(f"📋 Username: {username}")
    print(f"📋 Account: {int_account}")
    
    try:
        # Create credentials
        credentials = Credentials(
            username=username,
            password=password,
            totp_secret_key=totp_secret,
            int_account=int(int_account)
        )
        
        print("✅ Credentials created")
        
        # Create API instance
        api = TradingAPI(credentials=credentials)
        print("✅ API instance created")
        
        # Try to connect
        connection_result = api.connect()
        print(f"🔗 Connection result: {connection_result}")
        
        # Test simple search
        print("\n🔍 Testing stock search...")
        
        stock_request = StocksRequest(
            search_text="BMW",
            offset=0,
            limit=10,
            require_total=True,
            sort_columns="name",
            sort_types="asc"
        )
        
        print(f"📋 Search request: {stock_request}")
        
        # Perform search
        search_results = api.product_search(stock_request, raw=True)
        print(f"📊 Raw search results type: {type(search_results)}")
        print(f"📊 Raw search results: {search_results}")
        
        if isinstance(search_results, dict):
            print(f"📊 Result keys: {search_results.keys()}")
            if 'products' in search_results:
                products = search_results['products']
                print(f"📊 Products found: {len(products) if products else 0}")
                if products:
                    print(f"📊 First product: {products[0]}")
                else:
                    print("❌ Products list is empty")
            else:
                print("❌ No 'products' key in results")
        
        # Try alternative search methods
        print("\n🔍 Testing alternative search methods...")
        
        # Try with different parameters
        simple_request = StocksRequest(
            search_text="A",  # Very simple search
            offset=0,
            limit=5
        )
        
        simple_results = api.product_search(simple_request, raw=True)
        print(f"📊 Simple search results: {simple_results}")
        
        return True
        
    except Exception as e:
        print(f"❌ DEGIRO connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test execution"""
    # Load environment
    import subprocess
    try:
        result = subprocess.run(['source', '../config/.env'], shell=True, capture_output=True, text=True)
    except:
        pass
    
    # Set environment variables manually
    os.environ["DEGIRO_USERNAME"] = "bastiheye"
    os.environ["DEGIRO_PASSWORD"] = "!c3c6kdG5j6NFB7R"
    os.environ["DEGIRO_TOTP_SECRET"] = "5ADDODASZT7CHKD273VFMJMJZNAUHVBH"
    os.environ["DEGIRO_INT_ACCOUNT"] = "31043411"
    
    success = test_degiro_connection()
    
    if success:
        print("\n✅ DEGIRO connection test completed")
    else:
        print("\n❌ DEGIRO connection test failed")

if __name__ == "__main__":
    main()