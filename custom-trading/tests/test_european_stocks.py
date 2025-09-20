#!/usr/bin/env python3
"""
Test script specifically for European stocks that should be available on DEGIRO
Tests with German, Dutch, French, and other European market symbols
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
        "base_url": "http://152.53.200.195:7731",  # Using your VPS
        "headers": {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    }

def test_stock_search(config, query, market="", limit=5):
    """Test stock search endpoint"""
    print(f"\n🔍 Testing: '{query}' ({market})")
    
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
            
            if total > 0:
                print(f"   ✅ SUCCESS - Found {total} stocks!")
                
                for i, stock in enumerate(stocks[:3], 1):
                    print(f"   {i}. {stock['name']}")
                    print(f"      Symbol: {stock.get('symbol', 'N/A')}")
                    print(f"      ISIN: {stock['isin']}")
                    print(f"      ID: {stock['product_id']}")
                    print(f"      Price: {stock['current_price']['last']} {stock['currency']}")
                    print(f"      Exchange: {stock['exchange_id']}")
                
                return data
            else:
                print(f"   ❌ No results found")
                return None
        else:
            print(f"   ❌ ERROR: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None

def test_product_search(config, query, market=""):
    """Test universal product search"""
    print(f"\n🔍 Testing product search: '{query}' ({market})")
    
    payload = {"q": query}
    
    try:
        response = requests.post(
            f"{config['base_url']}/api/products/search",
            headers=config['headers'],
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check direct stock
            direct_stock = data.get("direct_stock")
            leveraged_products = data.get("leveraged_products", [])
            
            if direct_stock:
                print(f"   ✅ Found direct stock: {direct_stock['name']}")
                print(f"      ISIN: {direct_stock['isin']}")
                print(f"      Price: {direct_stock['current_price']['last']} {direct_stock['currency']}")
            
            if leveraged_products:
                print(f"   🎯 Found {len(leveraged_products)} leveraged products")
                for product in leveraged_products[:2]:
                    print(f"      - {product['name'][:50]}... ({product['leverage']:.1f}x)")
            
            if direct_stock or leveraged_products:
                return data
            else:
                print(f"   ❌ No products found")
                return None
        else:
            print(f"   ❌ ERROR: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None

def main():
    """Main test execution"""
    print("🇪🇺 European Stocks Test for DEGIRO")
    print("=" * 50)
    
    config = load_config()
    if not config:
        return
    
    # European stock test cases
    european_stocks = [
        # German stocks (DAX)
        {"query": "BMW", "market": "German - BMW"},
        {"query": "VW", "market": "German - Volkswagen"},
        {"query": "DAI", "market": "German - Daimler"},
        {"query": "SAP", "market": "German - SAP"},
        {"query": "SIE", "market": "German - Siemens"},
        {"query": "ALV", "market": "German - Allianz"},
        {"query": "BAS", "market": "German - BASF"},
        {"query": "DTE", "market": "German - Deutsche Telekom"},
        
        # Dutch stocks (AEX)
        {"query": "ASML", "market": "Dutch - ASML"},
        {"query": "RDSA", "market": "Dutch - Shell"},
        {"query": "PHIA", "market": "Dutch - Philips"},
        {"query": "UNA", "market": "Dutch - Unilever"},
        {"query": "INGA", "market": "Dutch - ING"},
        {"query": "KPN", "market": "Dutch - KPN"},
        
        # French stocks (CAC 40)
        {"query": "MC", "market": "French - LVMH"},
        {"query": "OR", "market": "French - L'Oréal"},
        {"query": "TTE", "market": "French - TotalEnergies"},
        {"query": "SAN", "market": "French - Sanofi"},
        {"query": "BNP", "market": "French - BNP Paribas"},
        
        # Swiss stocks
        {"query": "NESN", "market": "Swiss - Nestlé"},
        {"query": "ROG", "market": "Swiss - Roche"},
        {"query": "NOVN", "market": "Swiss - Novartis"},
        
        # UK stocks
        {"query": "LLOY", "market": "UK - Lloyds"},
        {"query": "BP", "market": "UK - BP"},
        {"query": "SHEL", "market": "UK - Shell"},
        
        # Company names (more likely to work)
        {"query": "BMW", "market": "Company name"},
        {"query": "Volkswagen", "market": "Company name"},
        {"query": "Siemens", "market": "Company name"},
        {"query": "Shell", "market": "Company name"},
        {"query": "Unilever", "market": "Company name"},
        
        # Common ISINs
        {"query": "DE0005190003", "market": "BMW ISIN"},
        {"query": "DE0007664039", "market": "Volkswagen ISIN"},
        {"query": "NL0010273215", "market": "ASML ISIN"},
        {"query": "NL0000009538", "market": "Shell ISIN"},
    ]
    
    successful_searches = []
    failed_searches = []
    
    print("\n🔍 Testing Stock Search Endpoint:")
    print("-" * 50)
    
    for stock in european_stocks:
        result = test_stock_search(config, stock["query"], stock["market"])
        if result:
            successful_searches.append(stock)
        else:
            failed_searches.append(stock)
    
    # Test product search with successful queries
    if successful_searches:
        print(f"\n🎯 Testing Product Search with successful queries:")
        print("-" * 50)
        
        for stock in successful_searches[:5]:  # Test first 5 successful
            test_product_search(config, stock["query"], stock["market"])
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 European Stocks Test Summary")
    print(f"{'='*50}")
    
    total_tests = len(european_stocks)
    successful_count = len(successful_searches)
    failed_count = len(failed_searches)
    
    print(f"✅ Successful searches: {successful_count}/{total_tests}")
    print(f"❌ Failed searches: {failed_count}/{total_tests}")
    
    if successful_count > 0:
        success_rate = (successful_count / total_tests) * 100
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        print(f"\n🎉 WORKING STOCK SYMBOLS:")
        for stock in successful_searches:
            print(f"   ✅ {stock['query']} - {stock['market']}")
        
        print(f"\n💡 Use these symbols in your Make.com modules!")
        
    else:
        print(f"❌ No European stocks found either!")
        print(f"🔍 This suggests a deeper issue with:")
        print(f"   - DEGIRO account market access")
        print(f"   - API search implementation")
        print(f"   - DEGIRO database connection")
        
    if failed_count > 0:
        print(f"\n❌ These searches failed:")
        for stock in failed_searches[:10]:  # Show first 10 failures
            print(f"   ❌ {stock['query']} - {stock['market']}")

if __name__ == "__main__":
    main()