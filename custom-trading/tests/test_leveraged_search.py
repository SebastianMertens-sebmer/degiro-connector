#!/usr/bin/env python3
"""
Test script for /api/leveraged/search endpoint
Tests leveraged products search functionality
"""

import os
import sys
import requests
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_config():
    """Load API configuration"""
    api_key = os.getenv("TRADING_API_KEY")
    if not api_key:
        print("❌ TRADING_API_KEY environment variable not set")
        print("Run: source config/.env")
        return None
    
    return {
        "base_url": "http://localhost:7731",
        "headers": {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    }

def test_leveraged_search(config, underlying_id, action="LONG", min_leverage=2.0, max_leverage=10.0, limit=10):
    """Test leveraged products search endpoint"""
    print(f"\n🎯 Testing leveraged search:")
    print(f"   Underlying ID: {underlying_id}")
    print(f"   Action: {action}")
    print(f"   Leverage: {min_leverage}x - {max_leverage}x")
    print(f"   Limit: {limit}")
    
    payload = {
        "underlying_id": underlying_id,
        "action": action,
        "min_leverage": min_leverage,
        "max_leverage": max_leverage,
        "limit": limit
    }
    
    try:
        response = requests.post(
            f"{config['base_url']}/api/leveraged/search",
            headers=config['headers'],
            json=payload,
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Underlying stock info
            underlying = data.get("underlying_stock")
            if underlying:
                print(f"   📈 Underlying Stock: {underlying['name']}")
                print(f"      Symbol: {underlying.get('symbol', 'N/A')}")
                print(f"      Price: {underlying['current_price']['last']} {underlying['currency']}")
            
            # Leveraged products
            products = data.get("leveraged_products", [])
            total = data.get("total_found", 0)
            
            print(f"   ✅ SUCCESS - Found {total} leveraged products")
            
            for i, product in enumerate(products[:5], 1):
                print(f"   {i}. {product['name'][:60]}...")
                print(f"      ISIN: {product['isin']}")
                print(f"      Leverage: {product['leverage']:.2f}x")
                print(f"      Direction: {product['direction']}")
                print(f"      Price: {product['current_price']['last']} {product['currency']}")
                print(f"      Issuer: {product.get('issuer', 'N/A')}")
                print(f"      Expiration: {product.get('expiration_date', 'N/A')}")
                print(f"      Tradable: {product['tradable']}")
            
            return data
        else:
            print(f"   ❌ ERROR: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None

def get_sample_stock_ids(config):
    """Get some stock IDs to test leveraged search"""
    print("🔍 Finding stock IDs for testing...")
    
    sample_stocks = []
    queries = ["AAPL", "TSLA", "META", "MSFT", "NVDA"]
    
    for query in queries:
        try:
            payload = {"q": query, "limit": 1}
            response = requests.post(
                f"{config['base_url']}/api/stocks/search",
                headers=config['headers'],
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                stocks = data.get("stocks", [])
                if stocks:
                    stock = stocks[0]
                    sample_stocks.append({
                        "id": stock["product_id"],
                        "name": stock["name"],
                        "symbol": stock.get("symbol", query)
                    })
                    print(f"   ✅ {query}: {stock['name']} (ID: {stock['product_id']})")
                else:
                    print(f"   ❌ {query}: No results")
            else:
                print(f"   ❌ {query}: API error {response.status_code}")
        except Exception as e:
            print(f"   ❌ {query}: Exception {e}")
    
    return sample_stocks

def main():
    """Main test execution"""
    print("🧪 Leveraged Products Search API Test")
    print("=" * 50)
    
    config = load_config()
    if not config:
        return
    
    # First, get some stock IDs to test with
    sample_stocks = get_sample_stock_ids(config)
    
    if not sample_stocks:
        print("❌ No stock IDs found for testing. Check stock search endpoint first.")
        return
    
    print(f"\n{'='*50}")
    print("🎯 Testing Leveraged Products Search")
    
    successful_tests = 0
    failed_tests = 0
    
    # Test different configurations for each stock
    test_configs = [
        {"action": "LONG", "min_leverage": 2.0, "max_leverage": 5.0, "description": "Conservative LONG"},
        {"action": "LONG", "min_leverage": 5.0, "max_leverage": 10.0, "description": "Aggressive LONG"},
        {"action": "SHORT", "min_leverage": 2.0, "max_leverage": 5.0, "description": "Conservative SHORT"},
        {"action": "SHORT", "min_leverage": 5.0, "max_leverage": 10.0, "description": "Aggressive SHORT"},
    ]
    
    for stock in sample_stocks[:3]:  # Test first 3 stocks
        print(f"\n📋 Testing leveraged products for: {stock['name']} ({stock['symbol']})")
        
        for test_config in test_configs:
            print(f"\n   🔧 Config: {test_config['description']}")
            result = test_leveraged_search(
                config,
                underlying_id=stock["id"],
                action=test_config["action"],
                min_leverage=test_config["min_leverage"],
                max_leverage=test_config["max_leverage"],
                limit=5
            )
            
            if result and result.get("leveraged_products"):
                successful_tests += 1
                count = len(result["leveraged_products"])
                print(f"      ✅ Found {count} products")
            else:
                failed_tests += 1
                print(f"      ❌ No products found")
    
    print(f"\n{'='*50}")
    print(f"📊 Test Summary:")
    print(f"   ✅ Successful: {successful_tests}")
    print(f"   ❌ Failed: {failed_tests}")
    if successful_tests + failed_tests > 0:
        print(f"   📈 Success Rate: {(successful_tests/(successful_tests+failed_tests)*100):.1f}%")
    
    if successful_tests > 0:
        print(f"\n💡 Leveraged products search is working!")
    else:
        print(f"\n⚠️  No leveraged products found. Check DEGIRO connection or try different stocks.")

if __name__ == "__main__":
    main()