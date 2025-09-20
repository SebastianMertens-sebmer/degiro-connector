#!/usr/bin/env python3
"""
Test script for /api/orders/place endpoint
Tests order placement functionality

⚠️  WARNING: This script can place REAL orders with REAL money!
⚠️  Use with extreme caution and only with test accounts!
⚠️  Set DRY_RUN=True to prevent actual order placement
"""

import os
import sys
import requests
import json
from datetime import datetime

# Add project root to path

# SAFETY FLAG - Set to False to actually place orders
DRY_RUN = True

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

def test_order_place(config, product_id, action="BUY", order_type="LIMIT", quantity=1, price=None, **kwargs):
    """Test order placement endpoint"""
    print(f"\n🚨 Testing order placement:")
    print(f"   Product ID: {product_id}")
    print(f"   Action: {action}")
    print(f"   Order Type: {order_type}")
    print(f"   Quantity: {quantity}")
    if price:
        print(f"   Price: {price}")
    
    if DRY_RUN:
        print(f"   🔒 DRY RUN MODE - No real order will be placed!")
    else:
        print(f"   ⚠️  LIVE MODE - This will place a REAL order!")
        confirmation = input("   Type 'CONFIRM' to proceed with real order: ")
        if confirmation != "CONFIRM":
            print("   ❌ Order cancelled by user")
            return None
    
    payload = {
        "product_id": product_id,
        "action": action,
        "order_type": order_type,
        "quantity": quantity
    }
    
    if price:
        payload["price"] = price
    
    # Add any extra parameters
    payload.update(kwargs)
    
    if DRY_RUN:
        print(f"   🔍 DRY RUN: Would send this payload:")
        print(f"   {json.dumps(payload, indent=2)}")
        print(f"   ✅ DRY RUN completed - no real order placed")
        return {"dry_run": True, "payload": payload}
    
    try:
        response = requests.post(
            f"{config['base_url']}/api/orders/place",
            headers=config['headers'],
            json=payload,
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            success = data.get("success", False)
            print(f"   {'✅ ORDER PLACED SUCCESSFULLY!' if success else '❌ ORDER FAILED'}")
            
            # Show order details
            if data.get("order_id"):
                print(f"   🎫 Order ID: {data['order_id']}")
            
            if data.get("confirmation_id"):
                print(f"   🎫 Confirmation ID: {data['confirmation_id']}")
            
            print(f"   📝 Message: {data.get('message', 'No message')}")
            
            # Show order summary
            print(f"   📊 Order Summary:")
            print(f"      Product: {data.get('product_id')}")
            print(f"      Action: {data.get('action')}")
            print(f"      Type: {data.get('order_type')}")
            print(f"      Quantity: {data.get('quantity')}")
            if data.get("price"):
                print(f"      Price: {data.get('price')}")
            if data.get("estimated_fee"):
                print(f"      Fee: {data.get('estimated_fee')}")
            if data.get("total_cost"):
                print(f"      Total Cost: {data.get('total_cost')}")
            print(f"      Created: {data.get('created_at')}")
            
            return data
        else:
            print(f"   ❌ ERROR: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None

def test_order_workflow(config, product_id, product_name, price, action="BUY", quantity=1):
    """Test complete order workflow: check -> place"""
    print(f"\n🔄 Testing complete order workflow for: {product_name}")
    
    # Step 1: Check order first
    print(f"   📋 Step 1: Validating order...")
    
    check_payload = {
        "product_id": product_id,
        "action": action,
        "order_type": "LIMIT",
        "quantity": quantity,
        "price": price,
        "time_type": "DAY"
    }
    
    try:
        check_response = requests.post(
            f"{config['base_url']}/api/orders/check",
            headers=config['headers'],
            json=check_payload,
            timeout=10
        )
        
        if check_response.status_code != 200:
            print(f"   ❌ Order validation failed: {check_response.status_code}")
            return None
        
        check_data = check_response.json()
        if not check_data.get("valid", False):
            print(f"   ❌ Order is invalid: {check_data.get('message')}")
            return None
        
        print(f"   ✅ Order validation passed")
        if check_data.get("estimated_fee"):
            print(f"      Estimated fee: {check_data['estimated_fee']}")
        if check_data.get("total_cost"):
            print(f"      Total cost: {check_data['total_cost']}")
        
    except Exception as e:
        print(f"   ❌ Order validation error: {e}")
        return None
    
    # Step 2: Place order
    print(f"   📋 Step 2: Placing order...")
    
    place_result = test_order_place(
        config,
        product_id=product_id,
        action=action,
        order_type="LIMIT",
        quantity=quantity,
        price=price,
        time_type="DAY"
    )
    
    return place_result

def get_test_products(config):
    """Get some safe products for testing"""
    print("🔍 Finding safe products for order testing...")
    
    test_products = []
    
    # Try to get a cheap stock for testing
    try:
        payload = {"q": "AAPL", "limit": 1}
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
                test_products.append({
                    "id": stock["product_id"],
                    "name": stock["name"],
                    "type": "stock",
                    "price": stock["current_price"]["last"],
                    "currency": stock["currency"]
                })
                print(f"   ✅ Stock: {stock['name']} (Price: {stock['current_price']['last']} {stock['currency']})")
    except Exception as e:
        print(f"   ❌ Error getting stocks: {e}")
    
    return test_products

def main():
    """Main test execution"""
    print("🧪 Order Placement API Test")
    print("=" * 50)
    
    if DRY_RUN:
        print("🔒 DRY RUN MODE - No real orders will be placed!")
    else:
        print("⚠️  LIVE MODE - This can place REAL orders with REAL money!")
        print("⚠️  Make sure you're using a test account!")
        confirmation = input("Type 'I UNDERSTAND THE RISKS' to continue: ")
        if confirmation != "I UNDERSTAND THE RISKS":
            print("❌ Test cancelled for safety")
            return
    
    print("=" * 50)
    
    config = load_config()
    if not config:
        return
    
    # Get test products
    test_products = get_test_products(config)
    
    if not test_products:
        print("❌ No products found for testing. Check search endpoints first.")
        return
    
    print(f"\n{'='*50}")
    print("🚨 Testing Order Placement")
    
    successful_tests = 0
    failed_tests = 0
    placed_orders = 0
    
    # Test with very small quantities to minimize risk
    for product in test_products[:1]:  # Only test with first product
        print(f"\n📋 Testing orders for: {product['name']} ({product['type']})")
        
        # Calculate safe test parameters
        base_price = product["price"]
        currency = product["currency"]
        
        # Test cases with minimal quantities
        test_cases = [
            {
                "description": "Minimal BUY order (1 unit, slightly above market)",
                "action": "BUY",
                "quantity": 1,
                "price": base_price * 1.05  # 5% above current price (less likely to execute immediately)
            }
        ]
        
        if not DRY_RUN:
            print(f"\n   ⚠️  WARNING: Testing with REAL money!")
            print(f"   Product: {product['name']}")
            print(f"   Current price: {base_price} {currency}")
            confirmation = input(f"   Type 'PROCEED' to test with this product: ")
            if confirmation != "PROCEED":
                print("   ❌ Skipped by user")
                continue
        
        for test_case in test_cases:
            print(f"\n   🔧 {test_case['description']}")
            
            result = test_order_workflow(
                config,
                product_id=product["id"],
                product_name=product["name"],
                price=test_case["price"],
                action=test_case["action"],
                quantity=test_case["quantity"]
            )
            
            if result is not None:
                successful_tests += 1
                if not DRY_RUN and result.get("success", False):
                    placed_orders += 1
                    print(f"      ✅ Real order placed!")
                elif DRY_RUN:
                    print(f"      ✅ Dry run completed")
            else:
                failed_tests += 1
                print(f"      ❌ Test failed")
    
    print(f"\n{'='*50}")
    print(f"📊 Test Summary:")
    print(f"   ✅ Successful tests: {successful_tests}")
    print(f"   ❌ Failed tests: {failed_tests}")
    
    if DRY_RUN:
        print(f"   🔒 DRY RUN - No real orders placed")
    else:
        print(f"   🚨 REAL orders placed: {placed_orders}")
        if placed_orders > 0:
            print(f"   ⚠️  Check your DEGIRO account for order status!")
    
    if successful_tests > 0:
        print(f"\n💡 Order placement API is working!")
        if DRY_RUN:
            print(f"🔒 Set DRY_RUN=False to place real orders (use with caution!)")
    else:
        print(f"\n❌ Order placement is not working. Check API and DEGIRO connection.")

if __name__ == "__main__":
    main()