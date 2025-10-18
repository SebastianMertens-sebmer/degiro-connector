#!/usr/bin/env python3
"""
Debug script to investigate why get_real_prices_batch() is failing
"""

import os
import sys
import json
sys.path.insert(0, '/Users/sebastianmertens/Documents/GitHub/degiro-connector/custom-trading')

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv('config/.env')

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials
from degiro_connector.quotecast.models.ticker import TickerRequest
from degiro_connector.quotecast.tools.ticker_fetcher import TickerFetcher
import pandas as pd

# Load credentials
username = os.getenv("DEGIRO_USERNAME")
password = os.getenv("DEGIRO_PASSWORD")
totp_secret = os.getenv("DEGIRO_TOTP_SECRET")
int_account = int(os.getenv("DEGIRO_INT_ACCOUNT", 0))

credentials = Credentials(
    username=username,
    password=password,
    totp_secret_key=totp_secret,
    int_account=int_account
)

# Create API instance
api = TradingAPI(credentials=credentials)
api.connect()

print("=" * 80)
print("🔍 DEBUGGING PRICE FETCHING")
print("=" * 80)

# Test products that have vwdIds but aren't showing up
test_products = {
    "PYPL": "7201951",
    "MSFT": "332111",
    "WBD": "22187048"
}

for symbol, product_id in test_products.items():
    print(f"\n📊 Testing: {symbol} (Product ID: {product_id})")
    print("-" * 80)

    try:
        # Step 1: Get product metadata
        print("Step 1: Fetching product metadata...")
        product_info = api.get_products_info(
            product_list=[int(product_id)],
            raw=True
        )

        if not isinstance(product_info, dict) or 'data' not in product_info:
            print(f"  ❌ No data in product_info response")
            continue

        product_data = product_info['data'].get(str(product_id))
        if not product_data:
            print(f"  ❌ No product data for {product_id}")
            continue

        vwd_id = product_data.get('vwdId')
        print(f"  ✅ vwdId: {vwd_id}")

        if not vwd_id:
            print(f"  ❌ No vwdId found")
            continue

        # Step 2: Get user token
        print("\nStep 2: Loading user token...")
        try:
            with open('config/config.json', 'r') as f:
                config_dict = json.load(f)
            user_token = config_dict.get("user_token")
            print(f"  ✅ User token loaded: {user_token} (type: {type(user_token).__name__})")
        except Exception as e:
            print(f"  ❌ Config load error: {e}")
            import traceback
            traceback.print_exc()
            continue

        if not user_token:
            print(f"  ❌ No user token in config")
            continue

        # Step 3: Get quotecast session
        print("\nStep 3: Establishing quotecast session...")
        try:
            session = TickerFetcher.build_session()
            session_id = TickerFetcher.get_session_id(user_token=user_token)
            print(f"  ✅ Session ID: {session_id}")
        except Exception as e:
            print(f"  ❌ Session error: {e}")
            continue

        if not session_id:
            print(f"  ❌ No session ID")
            continue

        # Step 4: Subscribe to ticker
        print("\nStep 4: Subscribing to ticker data...")
        request_map = {vwd_id: ["LastPrice", "BidPrice", "AskPrice"]}

        ticker_request = TickerRequest(
            request_type="subscription",
            request_map=request_map
        )

        logger = TickerFetcher.build_logger()

        try:
            TickerFetcher.subscribe(
                ticker_request=ticker_request,
                session_id=session_id,
                session=session,
                logger=logger,
            )
            print(f"  ✅ Subscribed successfully")
        except Exception as e:
            print(f"  ❌ Subscribe error: {e}")
            continue

        # Step 5: Fetch ticker data
        print("\nStep 5: Fetching ticker data...")
        try:
            ticker = TickerFetcher.fetch_ticker(
                session_id=session_id,
                session=session,
                logger=logger,
            )
            print(f"  ✅ Ticker data: {ticker is not None}")

            if ticker:
                print(f"  Ticker content preview: {str(ticker)[:200]}")
            else:
                print(f"  ❌ Ticker is None")

        except Exception as e:
            print(f"  ❌ Fetch error: {e}")
            import traceback
            traceback.print_exc()
            continue

    except Exception as e:
        print(f"  ❌ Overall error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("🎯 CONCLUSION:")
print("=" * 80)
print("Check which step is failing to identify the root cause")
print("=" * 80)
