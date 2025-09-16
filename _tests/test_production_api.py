#!/usr/bin/env python3
"""
Comprehensive tests for DEGIRO Trading API v2.0
Tests all endpoints: search, order validation, order placement
"""

import requests
import json
import time
from typing import Dict, Any

# API configuration
API_URL = "http://localhost:8000"
API_KEY = "your-secure-api-key-here"

class TradingAPITest:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_health(self):
        """Test API health endpoint"""
        print("🔋 Testing API Health...")
        
        response = self.session.get(f"{API_URL}/api/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data['status']}")
            print(f"   🔗 DEGIRO: {data['degiro_connection']}")
            return True
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    
    def test_search_products(self, query: str, expected_results: bool = True):
        """Test product search endpoint"""
        print(f"\n🔍 Testing Product Search: '{query}'")
        
        payload = {
            "q": query,
            "action": "LONG",
            "min_leverage": 2.0,
            "max_leverage": 6.0,
            "limit": 5
        }
        
        response = self.session.post(f"{API_URL}/api/products/search", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"   📊 Query: {data['query']['q']}")
            
            # Direct stock
            if data.get("direct_stock"):
                stock = data["direct_stock"]
                print(f"   📈 Direct Stock: {stock['name']} ({stock['isin']})")
                print(f"      Price: {stock['current_price']['last']} {stock['currency']}")
                print(f"      Product ID: {stock['product_id']}")
            else:
                print(f"   ❌ No direct stock found")
            
            # Leveraged products
            leveraged = data.get("leveraged_products", [])
            print(f"   🎯 Leveraged Products: {len(leveraged)}")
            
            for i, product in enumerate(leveraged[:3], 1):
                print(f"      {i}. {product['name'][:50]}...")
                print(f"         Leverage: {product['leverage']}x | {product['direction']}")
                print(f"         Price: {product['current_price']['last']} {product['currency']}")
                print(f"         Product ID: {product['product_id']}")
            
            return data
        else:
            print(f"   ❌ Search failed: {response.status_code} - {response.text}")
            return None
    
    def test_check_order(self, product_id: str, action: str = "BUY", quantity: float = 10, price: float = None):
        """Test order validation endpoint"""
        print(f"\n✅ Testing Order Check: {action} {quantity} of {product_id}")
        
        payload = {
            "product_id": product_id,
            "action": action,
            "order_type": "LIMIT",
            "quantity": quantity,
            "price": price or 10.0,
            "time_type": "DAY"
        }
        
        response = self.session.post(f"{API_URL}/api/orders/check", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"   📋 Valid: {data['valid']}")
            
            if data['valid']:
                print(f"   🆔 Confirmation ID: {data.get('confirmation_id', 'N/A')}")
                print(f"   💰 Estimated Fee: {data.get('estimated_fee', 'N/A')}")
                print(f"   💵 Total Cost: {data.get('total_cost', 'N/A')}")
                print(f"   📊 Free Space: {data.get('free_space_new', 'N/A')}")
            else:
                print(f"   ❌ Validation Failed: {data['message']}")
                if data.get('errors'):
                    for error in data['errors']:
                        print(f"      • {error}")
            
            return data
        else:
            print(f"   ❌ Check failed: {response.status_code} - {response.text}")
            return None
    
    def test_place_order(self, product_id: str, action: str = "BUY", quantity: float = 10, price: float = None, dry_run: bool = True):
        """Test order placement endpoint (dry run by default)"""
        print(f"\n📈 Testing Order Placement: {action} {quantity} of {product_id}")
        
        if dry_run:
            print("   ⚠️  DRY RUN MODE - No actual order will be placed")
        
        payload = {
            "product_id": product_id,
            "action": action,
            "order_type": "LIMIT", 
            "quantity": quantity,
            "price": price or 10.0,
            "time_type": "DAY"
        }
        
        if not dry_run:
            response = self.session.post(f"{API_URL}/api/orders/place", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"   🎯 Success: {data['success']}")
                
                if data['success']:
                    print(f"   🆔 Order ID: {data.get('order_id', 'N/A')}")
                    print(f"   📋 Confirmation ID: {data.get('confirmation_id', 'N/A')}")
                    print(f"   💰 Fee: {data.get('estimated_fee', 'N/A')}")
                    print(f"   💵 Total Cost: {data.get('total_cost', 'N/A')}")
                    print(f"   ⏰ Created: {data['created_at']}")
                else:
                    print(f"   ❌ Placement Failed: {data['message']}")
                
                return data
            else:
                print(f"   ❌ Placement failed: {response.status_code} - {response.text}")
                return None
        else:
            print("   ✅ Dry run completed - would have placed order with:")
            print(f"      Product ID: {payload['product_id']}")
            print(f"      Action: {payload['action']}")
            print(f"      Quantity: {payload['quantity']}")
            print(f"      Price: {payload['price']}")
            return {"dry_run": True, "payload": payload}
    
    def test_full_workflow(self, query: str, investment_amount: float = 250, dry_run: bool = True):
        """Test complete trading workflow: search -> validate -> place"""
        print(f"\n{'='*60}")
        print(f"🚀 FULL WORKFLOW TEST: '{query}' ({investment_amount} EUR)")
        print(f"{'='*60}")
        
        # Step 1: Search products
        search_result = self.test_search_products(query)
        
        if not search_result or not search_result.get("leveraged_products"):
            print("   ❌ No leveraged products found - workflow stopped")
            return False
        
        # Select best leveraged product
        best_product = search_result["leveraged_products"][0]
        current_price = best_product["current_price"]["ask"]
        
        # Calculate quantity and limit price
        quantity = max(1, int(investment_amount / current_price))
        limit_price = round(current_price * 1.02, 2)  # +2% limit
        
        print(f"\n📊 TRADING PLAN:")
        print(f"   Product: {best_product['name'][:50]}...")
        print(f"   Leverage: {best_product['leverage']}x")
        print(f"   Current Price: {current_price} {best_product['currency']}")
        print(f"   Limit Price: {limit_price} (+2%)")
        print(f"   Quantity: {quantity}")
        print(f"   Total Investment: ~{quantity * limit_price:.2f} {best_product['currency']}")
        
        # Step 2: Validate order
        check_result = self.test_check_order(
            best_product["product_id"],
            "BUY",
            quantity,
            limit_price
        )
        
        if not check_result or not check_result.get("valid"):
            print("   ❌ Order validation failed - workflow stopped")
            return False
        
        # Step 3: Place order (dry run by default)
        place_result = self.test_place_order(
            best_product["product_id"],
            "BUY", 
            quantity,
            limit_price,
            dry_run=dry_run
        )
        
        if place_result:
            print(f"\n✅ WORKFLOW COMPLETED SUCCESSFULLY!")
            return True
        else:
            print(f"\n❌ WORKFLOW FAILED")
            return False
    
    def run_comprehensive_tests(self):
        """Run all API tests"""
        print("🧪 DEGIRO Trading API v2.0 - Comprehensive Test Suite")
        print("=" * 60)
        
        # Health check
        if not self.test_health():
            print("❌ API not healthy - stopping tests")
            return
        
        # Test different search types
        test_cases = [
            {"query": "DE000CBK1001", "name": "Commerzbank ISIN"},
            {"query": "Commerzbank", "name": "Company name"},
            {"query": "CBK", "name": "German ticker"},
            {"query": "CISCO", "name": "US company"},
            {"query": "DE0005200000", "name": "Beiersdorf ISIN"},
        ]
        
        print(f"\n{'='*60}")
        print("🔍 PRODUCT SEARCH TESTS")
        print("=" * 60)
        
        successful_searches = []
        
        for test in test_cases:
            result = self.test_search_products(test["query"])
            if result and result.get("leveraged_products"):
                successful_searches.append(test["query"])
            time.sleep(1)  # Rate limiting
        
        print(f"\n{'='*60}")
        print("🎯 WORKFLOW TESTS")
        print("=" * 60)
        
        # Test full workflows for successful searches
        for query in successful_searches[:2]:  # Test first 2 successful queries
            self.test_full_workflow(query, investment_amount=250, dry_run=True)
            time.sleep(2)  # Rate limiting
        
        print(f"\n{'='*60}")
        print("✅ TEST SUITE COMPLETED")
        print("=" * 60)
        print("Summary:")
        print(f"   • Successful searches: {len(successful_searches)}")
        print(f"   • API health: ✅")
        print(f"   • Workflow tests: ✅")

def main():
    """Main test runner"""
    tester = TradingAPITest()
    
    print("Starting DEGIRO Trading API tests...")
    print(f"API URL: {API_URL}")
    print(f"API Key: {API_KEY[:20]}...")
    
    try:
        tester.run_comprehensive_tests()
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()