#!/usr/bin/env python3
"""
Test batch pricing limits using direct quotecast approach
"""

import os
import sys
import json
sys.path.append('/Users/sebastianmertens/Documents/GitHub/degiro-connector')

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials
from degiro_connector.quotecast.models.ticker import TickerRequest
from degiro_connector.quotecast.tools.ticker_fetcher import TickerFetcher
from degiro_connector.quotecast.tools.ticker_to_df import TickerToDF

def test_batch_limits():
    """Test how many products we can fetch in one quotecast request"""
    print("🔍 Testing Quotecast Batch Limits")
    print("=" * 50)
    
    # Test products we know have vwdIds
    test_products = {
        "28208959": "DE000PC1GF88.BNP,W",  # P&G leverage 10.2x
        "28208960": "DE000PC1GF96.BNP,W",  # P&G leverage 8.5x
        # Add more as we discover them
    }
    
    try:
        # Get credentials
        credentials = Credentials(
            username="bastiheye",
            password="!c3c6kdG5j6NFB7R",
            totp_secret_key="5ADDODASZT7CHKD273VFMJMJZNAUHVBH",
            int_account=31043411
        )
        
        api = TradingAPI(credentials=credentials)
        api.connect()
        
        # Get user token from config
        with open("/Users/sebastianmertens/Documents/GitHub/degiro-connector/config/config.json") as f:
            config = json.load(f)
            user_token = config.get("user_token")
        
        print(f"✅ Connected and got user token: {user_token}")
        
        # Test batch sizes
        batch_sizes = [1, 2, 5, 10, 20, 50]
        
        for batch_size in batch_sizes:
            print(f"\n🧪 Testing batch size: {batch_size}")
            
            # Create request map with multiple products
            request_map = {}
            vwd_ids = list(test_products.values())
            
            # Repeat vwd_ids to reach desired batch size
            for i in range(batch_size):
                vwd_id = vwd_ids[i % len(vwd_ids)]
                # Add unique suffix to avoid conflicts
                unique_vwd_id = f"{vwd_id}_{i}" if i >= len(vwd_ids) else vwd_id
                request_map[unique_vwd_id] = ["LastPrice", "BidPrice", "AskPrice"]
            
            print(f"   Request map size: {len(request_map)}")
            
            try:
                # Build session
                session = TickerFetcher.build_session()
                session_id = TickerFetcher.get_session_id(user_token=user_token)
                
                if not session_id:
                    print(f"   ❌ Failed to get session ID")
                    continue
                
                # Create ticker request
                ticker_request = TickerRequest(
                    request_type="subscription",
                    request_map=request_map
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
                    print(f"   ✅ Batch size {batch_size}: SUCCESS")
                    
                    # Try to parse
                    try:
                        ticker_to_df = TickerToDF()
                        df = ticker_to_df.parse(ticker=ticker)
                        if df is not None:
                            print(f"   📊 DataFrame rows: {len(df)}")
                        else:
                            print(f"   ⚠️  DataFrame is None")
                    except Exception as parse_error:
                        print(f"   ⚠️  Parse error: {parse_error}")
                else:
                    print(f"   ❌ Batch size {batch_size}: No ticker data")
                    break
                    
            except Exception as batch_error:
                print(f"   ❌ Batch size {batch_size}: {batch_error}")
                break
        
        print(f"\n🎯 Testing with real products only (no repeats)")
        real_request_map = {}
        for product_id, vwd_id in test_products.items():
            real_request_map[vwd_id] = ["LastPrice", "BidPrice", "AskPrice"]
        
        session = TickerFetcher.build_session()
        session_id = TickerFetcher.get_session_id(user_token=user_token)
        
        ticker_request = TickerRequest(
            request_type="subscription",
            request_map=real_request_map
        )
        
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
            print(f"✅ Real products batch successful")
            ticker_to_df = TickerToDF()
            df = ticker_to_df.parse(ticker=ticker)
            if df is not None:
                print(f"📊 Results: {len(df)} products with data")
                pandas_df = df.to_pandas()
                for index, row in pandas_df.iterrows():
                    last_price = row.get('LastPrice', 'N/A')
                    print(f"   💰 Row {index}: Last price €{last_price}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_batch_limits()