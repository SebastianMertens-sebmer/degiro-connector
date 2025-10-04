#!/usr/bin/env python3
"""Debug pricing batch for TSLA, CRWD, PYPL"""

import sys
import os
from pathlib import Path

# Set up paths
sys.path.insert(0, '/Users/sebastianmertens/Documents/GitHub/degiro-connector')
sys.path.insert(0, '/Users/sebastianmertens/Documents/GitHub/degiro-connector/custom-trading')

# Load environment from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / 'config' / '.env'
load_dotenv(env_path)

from api.main import get_real_prices_batch

# Test with 3 stock IDs
test_ids = {
    "TSLA": "1153605",
    "CRWD": "16082944",
    "PYPL": "7201951"
}

print("Testing get_real_prices_batch()...\n")

for symbol, stock_id in test_ids.items():
    print(f"Testing {symbol} (ID: {stock_id})...")
    result = get_real_prices_batch([stock_id])

    if stock_id in result:
        print(f"  ✅ Got pricing: {result[stock_id]}")
    else:
        print(f"  ❌ No pricing returned")
        print(f"  Result: {result}")
    print()
