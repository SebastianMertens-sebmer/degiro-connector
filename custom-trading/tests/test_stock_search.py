#!/usr/bin/env python3
"""
Test script for /api/stocks/search endpoint
Tests stock search functionality with various queries
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

def test_stock_search(config, query, limit=10):
    """Test stock search endpoint"""
    print(f"\n🔍 Testing stock search: '{query}' (limit: {limit})")
    
    payload = {
        "q": query,
        "limit": limit
    }
    
    try:
        response = requests.post(
            f"{config['base_url']}/api/stocks/search",
            headers=config['headers'],
            json=payload,
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            stocks = data.get("stocks", [])
            total = data.get("total_found", 0)
            
            print(f"   ✅ SUCCESS - Found {total} stocks")
            
            for i, stock in enumerate(stocks[:5], 1):
                print(f"   {i}. {stock['name']}")
                print(f"      Symbol: {stock.get('symbol', 'N/A')}")
                print(f"      ISIN: {stock['isin']}")
                print(f"      ID: {stock['product_id']}")
                print(f"      Price: {stock['current_price']['last']} {stock['currency']}")
                print(f"      Exchange: {stock['exchange_id']}")
                print(f"      Tradable: {stock['tradable']}")
            
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
    print("🧪 Stock Search API Test")
    print("=" * 50)
    
    config = load_config()
    if not config:
        return
    
    # Test cases - various search patterns
    test_cases = [
        # Ticker symbols
        {"query": "AAPL", "description": "Apple ticker"},
        {"query": "TSLA", "description": "Tesla ticker"},
        {"query": "META", "description": "Meta ticker"},
        {"query": "NVDA", "description": "NVIDIA ticker"},
        {"query": "MSFT", "description": "Microsoft ticker"},
        
        # Company names
        {"query": "Apple", "description": "Apple company name"},
        {"query": "Tesla", "description": "Tesla company name"},
        {"query": "Microsoft", "description": "Microsoft company name"},
        {"query": "Alphabet", "description": "Alphabet company name"},
        
        # European stocks
        {"query": "ASML", "description": "ASML (Dutch)"},
        {"query": "SAP", "description": "SAP (German)"},
        {"query": "Volkswagen", "description": "Volkswagen"},
        
        # ISINs (if known)
        {"query": "US0378331005", "description": "Apple ISIN"},
        {"query": "US88160R1014", "description": "Tesla ISIN"},
        
        # Partial matches
        {"query": "Micro", "description": "Partial: Micro"},
        {"query": "Tech", "description": "Partial: Tech"},
    ]
    
    successful_tests = 0
    failed_tests = 0
    
    for test in test_cases:
        print(f"\n📋 Test: {test['description']}")
        result = test_stock_search(config, test["query"], limit=5)
        
        if result and result.get("stocks"):
            successful_tests += 1
            print(f"   📊 Found {len(result['stocks'])} stocks")
        else:
            failed_tests += 1
            print(f"   ❌ No results found")
    
    print(f"\n{'='*50}")
    print(f"📊 Test Summary:")
    print(f"   ✅ Successful: {successful_tests}")
    print(f"   ❌ Failed: {failed_tests}")
    print(f"   📈 Success Rate: {(successful_tests/(successful_tests+failed_tests)*100):.1f}%")
    
    if successful_tests > 0:
        print(f"\n💡 Working queries found! Use these for further testing.")
    else:
        print(f"\n⚠️  No queries returned results. Check DEGIRO connection.")

if __name__ == "__main__":
    main()