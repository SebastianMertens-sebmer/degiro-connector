#!/usr/bin/env python3
"""
Test the FastAPI trading endpoint
"""

import requests
import json

# API configuration
API_URL = "http://localhost:8000"
API_KEY = "your-secure-api-key-here"  # Match the default in trading_api.py

def test_api_search(query, action="LONG", min_leverage=2.0, max_leverage=10.0, limit=5):
    """Test the universal search API"""
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "q": query,
        "action": action,
        "min_leverage": min_leverage,
        "max_leverage": max_leverage,
        "limit": limit
    }
    
    print(f"\n🔍 Testing search for: '{query}'")
    print(f"   Action: {action}, Leverage: {min_leverage}-{max_leverage}x")
    
    try:
        response = requests.post(f"{API_URL}/api/products/search", 
                               headers=headers, 
                               json=payload,
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"   ✅ SUCCESS!")
            
            # Direct stock
            if data.get("direct_stock"):
                stock = data["direct_stock"]
                print(f"   📈 Direct Stock: {stock['name']} ({stock['isin']})")
                print(f"      Price: {stock['current_price']['last']} {stock['currency']}")
            else:
                print(f"   ❌ No direct stock found")
            
            # Leveraged products
            leveraged = data.get("leveraged_products", [])
            print(f"   🎯 Found {len(leveraged)} leveraged products:")
            
            for i, product in enumerate(leveraged[:3], 1):  # Show top 3
                print(f"      {i}. {product['name'][:50]}...")
                print(f"         Leverage: {product['leverage']}x | Direction: {product['direction']}")
                print(f"         Price: {product['current_price']['last']} {product['currency']}")
                print(f"         ISIN: {product['isin']}")
            
            return data
            
        else:
            print(f"   ❌ API Error: {response.status_code}")
            print(f"      {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return None

def test_health():
    """Test API health"""
    try:
        response = requests.get(f"{API_URL}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"🔋 API Health: {data['status']}")
            print(f"   DEGIRO: {data['degiro_connection']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing DEGIRO Trading API")
    print(f"   API URL: {API_URL}")
    print(f"   API Key: {API_KEY}")
    
    # Test health first
    if not test_health():
        print("❌ API not healthy, stopping tests")
        exit(1)
    
    # Test different search types
    test_cases = [
        # ISIN searches
        {"query": "DE000CBK1001", "description": "Commerzbank ISIN"},
        {"query": "DE0005200000", "description": "Beiersdorf ISIN"},
        {"query": "NL0000235190", "description": "Airbus ISIN"},
        
        # Company name searches
        {"query": "Commerzbank", "description": "Company name"},
        {"query": "CISCO", "description": "Company name (US)"},
        
        # Ticker/Symbol searches
        {"query": "CBK", "description": "German ticker"},
        {"query": "AAPL", "description": "US ticker"},
        
        # Partial matches
        {"query": "Microsoft", "description": "Partial company name"},
    ]
    
    print(f"\n{'='*60}")
    print("🧪 Running test cases...")
    
    for test in test_cases:
        print(f"\n📋 Test: {test['description']}")
        result = test_api_search(test["query"], limit=3)
        
        if result:
            total = result.get("total_found", {})
            print(f"   📊 Summary: {total.get('direct_stock', 0)} stock, {total.get('leveraged_products', 0)} leveraged")
    
    print(f"\n{'='*60}")
    print("✅ API testing complete!")
    print(f"📖 API Documentation: {API_URL}/docs")