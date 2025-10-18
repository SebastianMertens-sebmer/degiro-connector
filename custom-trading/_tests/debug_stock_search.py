#!/usr/bin/env python3
"""
Debug script to investigate why stock search is filtering out results
"""

import os
import sys
sys.path.insert(0, '/Users/sebastianmertens/Documents/GitHub/degiro-connector/custom-trading')

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv('config/.env')

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials
from degiro_connector.trading.models.product_search import StocksRequest

# Load credentials from environment
username = os.getenv("DEGIRO_USERNAME")
password = os.getenv("DEGIRO_PASSWORD")
totp_secret = os.getenv("DEGIRO_TOTP_SECRET")
int_account = int(os.getenv("DEGIRO_INT_ACCOUNT", 0))

print(f"Debug: username={username is not None}, password={password is not None}")

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
print("🔍 DEBUGGING STOCK SEARCH FILTERING")
print("=" * 80)

# Test stocks that are failing
test_queries = ["PYPL", "PayPal", "MSFT", "Microsoft", "META", "WBD"]

for query in test_queries:
    print(f"\n📊 Testing: {query}")
    print("-" * 80)

    try:
        # Perform raw DEGIRO search
        stock_request = StocksRequest(
            search_text=query,
            offset=0,
            limit=20,
            require_total=True,
            sort_columns="name",
            sort_types="asc"
        )

        search_results = api.product_search(stock_request, raw=True)

        if isinstance(search_results, dict) and 'products' in search_results:
            products = search_results['products']

            print(f"✅ DEGIRO Found: {len(products)} products")

            if products:
                for i, product in enumerate(products[:3], 1):
                    product_id = product.get('id')
                    name = product.get('name', 'N/A')
                    symbol = product.get('symbol', 'N/A')
                    isin = product.get('isin', 'N/A')
                    tradable = product.get('tradable', False)

                    print(f"\n  {i}. {symbol} - {name}")
                    print(f"     Product ID: {product_id}")
                    print(f"     ISIN: {isin}")
                    print(f"     Tradable: {tradable}")

                    # Try to get product metadata (including vwdId for pricing)
                    try:
                        product_info = api.get_products_info(
                            product_list=[int(product_id)],
                            raw=True
                        )

                        if isinstance(product_info, dict) and 'data' in product_info:
                            product_data = product_info['data'].get(str(product_id))
                            if product_data:
                                vwd_id = product_data.get('vwdId')
                                print(f"     VWD ID: {vwd_id or 'MISSING - NO REAL-TIME PRICING'}")

                                if not vwd_id:
                                    print(f"     ⚠️  REASON FOR FILTERING: No vwdId means no real-time price data")
                            else:
                                print(f"     ⚠️  REASON FOR FILTERING: Product metadata not available")
                        else:
                            print(f"     ⚠️  REASON FOR FILTERING: Product info fetch failed")

                    except Exception as e:
                        print(f"     ❌ Product info error: {e}")
                        print(f"     ⚠️  REASON FOR FILTERING: Cannot fetch product metadata")
            else:
                print("  ⚠️  DEGIRO returned 0 products")
        else:
            print(f"  ❌ Unexpected response format: {type(search_results)}")

    except Exception as e:
        print(f"  ❌ Search error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("🎯 CONCLUSION:")
print("=" * 80)
print("If products show 'No vwdId', they are being filtered out because")
print("the API requires real-time pricing data to include them in results.")
print()
print("SOLUTION: Remove pricing requirement or make pricing optional.")
print("=" * 80)
