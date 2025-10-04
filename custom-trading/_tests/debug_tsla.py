#!/usr/bin/env python3
"""Debug TSLA product info"""

import os
import sys
from pathlib import Path
sys.path.insert(0, os.path.abspath('..'))

from dotenv import load_dotenv
from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials

# Load environment from .env file
env_path = Path(__file__).parent.parent / 'config' / '.env'
load_dotenv(env_path)

# Load credentials
credentials = Credentials(
    username=os.getenv("DEGIRO_USERNAME"),
    password=os.getenv("DEGIRO_PASSWORD"),
    totp_secret_key=os.getenv("DEGIRO_TOTP_SECRET"),
    int_account=int(os.getenv("DEGIRO_INT_ACCOUNT", 0))
)

api = TradingAPI(credentials=credentials)
api.connect()

# Test getting product info for TSLA
print("Testing product_info for TSLA (1153605)...")
try:
    product_info = api.get_products_info(
        product_list=[1153605],
        raw=True
    )
    print(f"Success! product_info keys: {product_info.keys() if isinstance(product_info, dict) else type(product_info)}")

    if isinstance(product_info, dict):
        if 'data' in product_info:
            print(f"Has 'data' key: {bool(product_info['data'])}")
            if product_info['data']:
                tsla_data = product_info['data'].get('1153605')
                print(f"TSLA data: {tsla_data}")
        else:
            print(f"No 'data' key. Available keys: {list(product_info.keys())}")
            print(f"Full response: {product_info}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
