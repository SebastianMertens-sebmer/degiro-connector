#!/usr/bin/env python3
"""
Test real prices for P&G leveraged products using DEGIRO quotecast API directly
"""

import os
import sys
sys.path.append('/Users/sebastianmertens/Documents/GitHub/degiro-connector')

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials

def test_quotecast_real_prices():
    """Test real prices using quotecast API for P&G leveraged products"""
    print("🔍 Testing Real P&G Leveraged Product Prices via Quotecast")
    print("=" * 65)
    
    # P&G leveraged products we found
    pg_products = [
        {"id": 28208959, "leverage": "10.2x", "fake_price": "€100.25"},
        {"id": 28208960, "leverage": "8.5x", "fake_price": "€85.40"}, 
        {"id": 28208961, "leverage": "5.0x", "fake_price": "€50.15"}
    ]
    
    try:
        # Create credentials and connect
        credentials = Credentials(
            username="bastiheye",
            password="!c3c6kdG5j6NFB7R", 
            totp_secret_key="5ADDODASZT7CHKD273VFMJMJZNAUHVBH",
            int_account=31043411
        )
        
        api = TradingAPI(credentials=credentials)
        print("✅ API instance created")
        
        connection_result = api.connect()
        print(f"✅ Connected: {connection_result}")
        
        # Test each P&G product
        for product in pg_products:
            product_id = product["id"]
            leverage = product["leverage"]
            fake_price = product["fake_price"]
            
            print(f"\n🏭 Testing Product ID: {product_id}")
            print(f"   Leverage: {leverage}")
            print(f"   Previous Fake Price: {fake_price}")
            
            try:
                # Get product metadata to get vwdId
                product_info = api.get_products_info(
                    product_list=[product_id],
                    raw=True
                )
                
                if isinstance(product_info, dict) and 'data' in product_info:
                    product_data = product_info['data'].get(str(product_id))
                    if product_data:
                        vwd_id = product_data.get('vwdId')
                        product_name = product_data.get('name', 'N/A')
                        currency = product_data.get('currency', 'N/A')
                        
                        print(f"   Product Name: {product_name}")
                        print(f"   Currency: {currency}")
                        print(f"   vwdId: {vwd_id}")
                        
                        if vwd_id:
                            # Try to get real-time price using quotecast
                            try:
                                from degiro_connector.quotecast.models.ticker import TickerRequest
                                from degiro_connector.quotecast.tools.ticker_fetcher import TickerFetcher
                                from degiro_connector.quotecast.tools.ticker_to_df import TickerToDF
                                
                                # Get user token from config file
                                import json
                                try:
                                    with open("/Users/sebastianmertens/Documents/GitHub/degiro-connector/config/config.json") as config_file:
                                        config_dict = json.load(config_file)
                                        user_token = config_dict.get("user_token")
                                except Exception as config_error:
                                    print(f"   ❌ Config error: {config_error}")
                                    user_token = None
                                if user_token:
                                    print(f"   ✅ User token available")
                                    
                                    # Build session and get session ID
                                    session = TickerFetcher.build_session()
                                    session_id = TickerFetcher.get_session_id(user_token=user_token)
                                    
                                    if session_id:
                                        print(f"   ✅ Quotecast session ID: {session_id}")
                                        
                                        # Create ticker request
                                        ticker_request = TickerRequest(
                                            request_type="subscription",
                                            request_map={
                                                vwd_id: [
                                                    "LastPrice",
                                                    "BidPrice",
                                                    "AskPrice"
                                                ]
                                            }
                                        )
                                        
                                        # Subscribe and fetch
                                        logger = TickerFetcher.build_logger()
                                        
                                        TickerFetcher.subscribe(
                                            ticker_request=ticker_request,
                                            session_id=session_id,
                                            session=session,
                                            logger=logger,
                                        )
                                        
                                        ticker = TickerFetcher.fetch_ticker(
                                            session_id=session_id,
                                            session=session,
                                            logger=logger,
                                        )
                                        
                                        if ticker:
                                            print(f"   ✅ Ticker data received")
                                            print(f"   Raw ticker type: {type(ticker)}")
                                            print(f"   Raw ticker data: {ticker}")
                                            
                                            # Try to parse ticker data
                                            try:
                                                ticker_to_df = TickerToDF()
                                                df = ticker_to_df.parse(ticker=ticker)
                                                print(f"   ✅ Ticker parsing successful")
                                            except Exception as parse_error:
                                                print(f"   ❌ Ticker parsing failed: {parse_error}")
                                                df = None
                                            
                                            if df is not None and len(df) > 0:
                                                print(f"   ✅ DataFrame created with {len(df)} rows")
                                                print(f"   DataFrame columns: {list(df.columns)}")
                                                
                                                # Get first row data (since we only requested one product)
                                                row_dict = df.to_pandas().iloc[0].to_dict()
                                                last_price = row_dict.get('LastPrice', None)
                                                bid_price = row_dict.get('BidPrice', None)
                                                ask_price = row_dict.get('AskPrice', None)
                                                
                                                print(f"   🎯 REAL PRICES FOUND:")
                                                print(f"      Last: {last_price}")
                                                print(f"      Bid: {bid_price}")
                                                print(f"      Ask: {ask_price}")
                                                
                                                if last_price is not None:
                                                    import pandas as pd
                                                    if not pd.isna(last_price):
                                                        print(f"   🚀 SUCCESS! Real price: €{float(last_price):.2f}")
                                                        print(f"   🎯 HUGE DIFFERENCE FROM FAKE PRICE!")
                                                        print(f"      Fake: {fake_price} vs Real: €{float(last_price):.2f}")
                                                    else:
                                                        print(f"   ⚠️  Last price is NaN")
                                                else:
                                                    print(f"   ❌ No last price available")
                                            else:
                                                print(f"   ❌ Empty or invalid DataFrame")
                                        else:
                                            print(f"   ❌ No ticker data received")
                                    else:
                                        print(f"   ❌ No quotecast session ID")
                                else:
                                    print(f"   ❌ No user token available")
                                    
                            except Exception as quotecast_error:
                                print(f"   ❌ Quotecast error: {quotecast_error}")
                                import traceback
                                traceback.print_exc()
                        else:
                            print(f"   ❌ No vwdId available for real-time pricing")
                    else:
                        print(f"   ❌ No product data found")
                else:
                    print(f"   ❌ Invalid product info response")
                    
            except Exception as e:
                print(f"   ❌ Product error: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quotecast_real_prices()