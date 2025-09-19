#!/usr/bin/env python3
"""
Test suite for DEGIRO Trading API endpoints
Tests the new 3-endpoint workflow: stocks search -> leveraged search -> orders
"""

import os
import sys
import json
import requests
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class APITester:
    def __init__(self, base_url: str = "http://localhost:7731", api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key or os.getenv("TRADING_API_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def test_health(self) -> Dict[str, Any]:
        """Test health endpoint (no auth required)"""
        print("🔍 Testing health endpoint...")
        response = requests.get(f"{self.base_url}/api/health")
        
        if response.status_code == 200:
            print("✅ Health check passed")
            return response.json()
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return {}
    
    def test_stock_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Test stock search endpoint"""
        print(f"🔍 Testing stock search for '{query}'...")
        
        payload = {
            "q": query,
            "limit": limit
        }
        
        response = requests.post(
            f"{self.base_url}/api/stocks/search",
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            stock_count = len(data.get("stocks", []))
            print(f"✅ Stock search passed - found {stock_count} stocks")
            return data
        else:
            print(f"❌ Stock search failed: {response.status_code} - {response.text}")
            return {}
    
    def test_leveraged_search(self, underlying_id: str, action: str = "LONG", 
                            min_leverage: float = 5.0, max_leverage: float = 10.0,
                            limit: int = 5) -> Dict[str, Any]:
        """Test leveraged products search endpoint"""
        print(f"🔍 Testing leveraged search for stock ID {underlying_id}...")
        
        payload = {
            "underlying_id": underlying_id,
            "action": action,
            "min_leverage": min_leverage,
            "max_leverage": max_leverage,
            "limit": limit
        }
        
        response = requests.post(
            f"{self.base_url}/api/leveraged/search",
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            product_count = len(data.get("leveraged_products", []))
            print(f"✅ Leveraged search passed - found {product_count} products")
            return data
        else:
            print(f"❌ Leveraged search failed: {response.status_code} - {response.text}")
            return {}
    
    def test_order_check(self, product_id: str, action: str = "BUY", 
                        quantity: float = 1, price: float = None) -> Dict[str, Any]:
        """Test order validation endpoint"""
        print(f"🔍 Testing order check for product {product_id}...")
        
        payload = {
            "product_id": product_id,
            "action": action,
            "order_type": "LIMIT",
            "quantity": quantity,
            "time_type": "DAY"
        }
        
        if price:
            payload["price"] = price
        
        response = requests.post(
            f"{self.base_url}/api/orders/check",
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            is_valid = data.get("valid", False)
            print(f"✅ Order check passed - valid: {is_valid}")
            return data
        else:
            print(f"❌ Order check failed: {response.status_code} - {response.text}")
            return {}
    
    def test_full_workflow(self, search_query: str = "Meta Platforms", 
                          target_leverage: float = 5.0) -> bool:
        """Test complete workflow: stock search -> leveraged search -> order check"""
        print(f"\n🚀 Testing FULL WORKFLOW for '{search_query}' with {target_leverage}x leverage")
        print("=" * 80)
        
        # Step 1: Search for stocks
        stock_results = self.test_stock_search(search_query)
        if not stock_results or not stock_results.get("stocks"):
            print("❌ Workflow failed at stock search")
            return False
        
        # Find the best matching stock (Meta Platforms Inc)
        target_stock = None
        for stock in stock_results.get("stocks", []):
            if "Meta Platforms" in stock.get("name", ""):
                target_stock = stock
                break
        
        if not target_stock:
            print("❌ Could not find Meta Platforms Inc in search results")
            return False
        
        print(f"📊 Selected stock: {target_stock['name']} (ID: {target_stock['product_id']})")
        
        # Step 2: Search for leveraged products
        leveraged_results = self.test_leveraged_search(
            underlying_id=target_stock["product_id"],
            action="LONG",
            min_leverage=target_leverage,
            max_leverage=target_leverage + 2.0,
            limit=5
        )
        
        if not leveraged_results or not leveraged_results.get("leveraged_products"):
            print("❌ Workflow failed at leveraged search")
            return False
        
        # Find best leveraged product
        target_product = leveraged_results["leveraged_products"][0]
        print(f"📈 Selected leveraged product: {target_product['name']}")
        print(f"   Leverage: {target_product['leverage']}x")
        print(f"   Current price: €{target_product['current_price']['last']}")
        
        # Step 3: Calculate order for €250
        target_amount = 250.0
        product_price = target_product['current_price']['last']
        quantity = target_amount / product_price
        
        print(f"💰 Order calculation: €{target_amount} / €{product_price} = {quantity:.2f} units")
        
        # Step 4: Check order (validation only)
        order_result = self.test_order_check(
            product_id=target_product["product_id"],
            action="BUY",
            quantity=quantity,
            price=product_price * 1.01  # Slightly above current price
        )
        
        if not order_result:
            print("❌ Workflow failed at order check")
            return False
        
        print("\n🎉 FULL WORKFLOW COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print(f"✅ Found stock: {target_stock['name']}")
        print(f"✅ Found leveraged product: {target_product['leverage']:.2f}x leverage")
        print(f"✅ Order validation: {order_result.get('message', 'Success')}")
        
        return True
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🧪 DEGIRO Trading API Test Suite")
        print("=" * 50)
        
        # Test 1: Health check
        health = self.test_health()
        if not health:
            print("❌ Cannot proceed - API not healthy")
            return
        
        print(f"📊 API Status: {health.get('degiro_connection', 'unknown')}")
        print()
        
        # Test 2: Multiple stock searches
        test_queries = ["Meta", "Meta Platforms", "GOOGL", "Apple"]
        
        for query in test_queries:
            print(f"\n--- Testing Stock Search: '{query}' ---")
            results = self.test_stock_search(query, limit=5)
            if results:
                print(f"   Found {results['total_found']} stocks")
                for stock in results.get("stocks", [])[:3]:
                    print(f"   - {stock['name']} ({stock['symbol']})")
        
        # Test 3: Full workflow test
        print("\n" + "=" * 50)
        success = self.test_full_workflow()
        
        print(f"\n{'🎉 ALL TESTS PASSED' if success else '❌ SOME TESTS FAILED'}")

def main():
    """Main test execution"""
    # Load API key from environment
    api_key = os.getenv("TRADING_API_KEY")
    if not api_key:
        print("❌ TRADING_API_KEY environment variable not set")
        print("Please set it or run: source config/.env")
        return
    
    # Create tester and run tests
    tester = APITester(api_key=api_key)
    tester.run_all_tests()

if __name__ == "__main__":
    main()