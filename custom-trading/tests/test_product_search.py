#!/usr/bin/env python3
"""
Test script for /api/products/search endpoint
Tests universal product search functionality (legacy endpoint)
"""

import os
import sys
import requests
import json
from datetime import datetime

# Add project root to path

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

def test_product_search(config, query, **kwargs):
    """Test universal product search endpoint"""
    print(f"\n🔍 Testing product search: '{query}'")
    
    payload = {"q": query}
    payload.update(kwargs)
    
    # Show search parameters
    for key, value in kwargs.items():
        print(f"   {key}: {value}")
    
    try:
        response = requests.post(
            f"{config['base_url']}/api/products/search",
            headers=config['headers'],
            json=payload,
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Direct stock
            direct_stock = data.get("direct_stock")
            if direct_stock:
                print(f"   📈 Direct Stock Found:")
                print(f"      Name: {direct_stock['name']}")
                print(f"      ISIN: {direct_stock['isin']}")
                print(f"      Price: {direct_stock['current_price']['last']} {direct_stock['currency']}")
                print(f"      Tradable: {direct_stock['tradable']}")
            else:
                print(f"   ❌ No direct stock found")
            
            # Leveraged products
            leveraged_products = data.get("leveraged_products", [])
            print(f"   🎯 Leveraged Products: {len(leveraged_products)} found")
            
            for i, product in enumerate(leveraged_products[:3], 1):
                print(f"   {i}. {product['name'][:50]}...")
                print(f"      Leverage: {product['leverage']:.2f}x {product['direction']}")
                print(f"      Price: {product['current_price']['last']} {product['currency']}")
                print(f"      ISIN: {product['isin']}")
                print(f"      Issuer: {product.get('issuer', 'N/A')}")
            
            # Summary
            total_found = data.get("total_found", {})
            print(f"   📊 Total Found:")
            print(f"      Direct Stocks: {total_found.get('direct_stock', 0)}")
            print(f"      Leveraged Products: {total_found.get('leveraged_products', 0)}")
            
            return data
        else:
            print(f"   ❌ ERROR: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None

def main():
    """Main test execution"""
    print("🧪 Universal Product Search API Test")
    print("=" * 50)
    
    config = load_config()
    if not config:
        return
    
    # Test cases with different parameters
    test_cases = [
        # Basic searches
        {
            "query": "AAPL",
            "description": "Basic Apple search",
            "params": {}
        },
        {
            "query": "TSLA", 
            "description": "Basic Tesla search",
            "params": {}
        },
        {
            "query": "META",
            "description": "Basic Meta search", 
            "params": {}
        },
        
        # With leverage filters
        {
            "query": "AAPL",
            "description": "Apple with conservative leverage",
            "params": {
                "action": "LONG",
                "min_leverage": 2.0,
                "max_leverage": 5.0,
                "limit": 5
            }
        },
        {
            "query": "TSLA",
            "description": "Tesla with aggressive leverage",
            "params": {
                "action": "LONG", 
                "min_leverage": 5.0,
                "max_leverage": 10.0,
                "limit": 3
            }
        },
        
        # SHORT positions
        {
            "query": "META",
            "description": "Meta SHORT positions",
            "params": {
                "action": "SHORT",
                "min_leverage": 2.0,
                "max_leverage": 8.0,
                "limit": 5
            }
        },
        
        # Company name searches
        {
            "query": "Apple",
            "description": "Apple by company name",
            "params": {
                "action": "LONG",
                "limit": 3
            }
        },
        {
            "query": "Microsoft",
            "description": "Microsoft by company name",
            "params": {
                "action": "LONG",
                "limit": 3
            }
        },
        
        # European stocks
        {
            "query": "ASML",
            "description": "ASML (Dutch semiconductor)",
            "params": {
                "action": "LONG",
                "min_leverage": 2.0,
                "max_leverage": 5.0
            }
        },
        {
            "query": "SAP",
            "description": "SAP (German software)",
            "params": {
                "action": "LONG",
                "limit": 5
            }
        },
    ]
    
    successful_tests = 0
    failed_tests = 0
    found_stocks = 0
    found_leveraged = 0
    
    for test in test_cases:
        print(f"\n📋 Test: {test['description']}")
        result = test_product_search(config, test["query"], **test["params"])
        
        if result:
            successful_tests += 1
            
            # Count results
            if result.get("direct_stock"):
                found_stocks += 1
            
            leveraged_count = len(result.get("leveraged_products", []))
            if leveraged_count > 0:
                found_leveraged += leveraged_count
                
        else:
            failed_tests += 1
    
    print(f"\n{'='*50}")
    print(f"📊 Test Summary:")
    print(f"   ✅ Successful API calls: {successful_tests}")
    print(f"   ❌ Failed API calls: {failed_tests}")
    print(f"   📈 Direct stocks found: {found_stocks}")
    print(f"   🎯 Leveraged products found: {found_leveraged}")
    
    if successful_tests + failed_tests > 0:
        success_rate = (successful_tests/(successful_tests+failed_tests)*100)
        print(f"   📊 Success Rate: {success_rate:.1f}%")
    
    if successful_tests > 0:
        print(f"\n💡 Universal product search is working!")
        if found_stocks == 0:
            print(f"⚠️  No direct stocks found - check DEGIRO stock database")
        if found_leveraged == 0:
            print(f"⚠️  No leveraged products found - check DEGIRO leveraged products")
    else:
        print(f"\n❌ Universal product search is not working. Check API and DEGIRO connection.")

if __name__ == "__main__":
    main()