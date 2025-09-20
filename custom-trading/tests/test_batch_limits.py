#!/usr/bin/env python3
"""
Test batch pricing limits - how many products can we fetch at once?
"""

import os
import sys
sys.path.append('/Users/sebastianmertens/Documents/GitHub/degiro-connector')

def test_batch_limits():
    """Test how many products we can fetch in one batch"""
    print("🔍 Testing Batch Pricing Limits")
    print("=" * 50)
    
    # Test our batch function with different sizes
    sys.path.append('/Users/sebastianmertens/Documents/GitHub/degiro-connector/custom-trading')
    
    # Test known product IDs
    test_product_ids = [
        "28208959",  # P&G leverage 10.2x - €0.89
        "28208960",  # P&G leverage 8.5x - €0.39
        "331868",    # Apple - $245
        "3597",      # BMW
        "331874",    # P&G stock
    ]
    
    print(f"📋 Testing with {len(test_product_ids)} products:")
    for pid in test_product_ids:
        print(f"   - {pid}")
    
    try:
        # Set environment variable to avoid API key requirement
        os.environ["TRADING_API_KEY"] = "test_key"
        
        from api.main import get_real_prices_batch
        
        # Test batch pricing
        print(f"\n🚀 Fetching prices for {len(test_product_ids)} products...")
        
        real_prices = get_real_prices_batch(test_product_ids)
        
        print(f"✅ Batch pricing successful!")
        print(f"📊 Results: {len(real_prices)}/{len(test_product_ids)} products with pricing data")
        
        for product_id, price_info in real_prices.items():
            print(f"   💰 Product {product_id}: €{price_info.last} (bid: €{price_info.bid}, ask: €{price_info.ask})")
        
        # Test larger batch
        print(f"\n🔍 Testing larger batch (10 products)...")
        large_batch = test_product_ids * 2  # 10 products
        large_prices = get_real_prices_batch(large_batch)
        print(f"📊 Large batch: {len(large_prices)}/{len(large_batch)} products with pricing data")
        
        return True
        
    except Exception as e:
        print(f"❌ Batch test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_batch_limits()