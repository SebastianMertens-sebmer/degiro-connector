#!/usr/bin/env python3
"""
Test script for /api/orders/check endpoint
Tests order validation functionality (does NOT place real orders)
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

def test_order_check(config, product_id, action="BUY", order_type="LIMIT", quantity=1, price=None, **kwargs):
    """Test order validation endpoint"""
    print(f"\n💰 Testing order check:")
    print(f"   Product ID: {product_id}")
    print(f"   Action: {action}")
    print(f"   Order Type: {order_type}")
    print(f"   Quantity: {quantity}")
    if price:
        print(f"   Price: {price}")
    
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
    
    try:
        response = requests.post(
            f"{config['base_url']}/api/orders/check",
            headers=config['headers'],
            json=payload,
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            is_valid = data.get("valid", False)
            print(f"   ✅ Order Check Result: {'VALID' if is_valid else 'INVALID'}")
            
            # Show validation details
            if data.get("confirmation_id"):
                print(f"   🎫 Confirmation ID: {data['confirmation_id']}")
            
            if data.get("estimated_fee") is not None:
                print(f"   💵 Estimated Fee: {data['estimated_fee']}")
            
            if data.get("total_cost") is not None:
                print(f"   💰 Total Cost: {data['total_cost']}")
            
            if data.get("free_space_new") is not None:
                print(f"   💳 Free Space After: {data['free_space_new']}")
            
            print(f"   📝 Message: {data.get('message', 'No message')}")
            
            # Show warnings and errors
            warnings = data.get("warnings", [])
            if warnings:
                print(f"   ⚠️  Warnings:")
                for warning in warnings:
                    print(f"      - {warning}")
            
            errors = data.get("errors", [])
            if errors:
                print(f"   ❌ Errors:")
                for error in errors:
                    print(f"      - {error}")
            
            return data
        else:
            print(f"   ❌ ERROR: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None

def get_test_products(config):
    """Get some products to test orders with"""
    print("🔍 Finding products for order testing...")
    
    test_products = []
    
    # Try to get some stocks first
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
    
    # Try to get some leveraged products
    if test_products:
        try:
            payload = {
                "underlying_id": test_products[0]["id"],
                "action": "LONG",
                "limit": 1
            }
            response = requests.post(
                f"{config['base_url']}/api/leveraged/search",
                headers=config['headers'],
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("leveraged_products", [])
                if products:
                    product = products[0]
                    test_products.append({
                        "id": product["product_id"],
                        "name": product["name"][:50] + "...",
                        "type": "leveraged",
                        "price": product["current_price"]["last"],
                        "currency": product["currency"],
                        "leverage": product["leverage"]
                    })
                    print(f"   ✅ Leveraged: {product['name'][:30]}... (Price: {product['current_price']['last']} {product['currency']})")
        except Exception as e:
            print(f"   ❌ Error getting leveraged products: {e}")
    
    return test_products

def main():
    """Main test execution"""
    print("🧪 Order Check API Test")
    print("=" * 50)
    print("⚠️  This test ONLY validates orders, it does NOT place real orders!")
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
    print("💰 Testing Order Validation")
    
    successful_tests = 0
    failed_tests = 0
    valid_orders = 0
    invalid_orders = 0
    
    # Test different order configurations
    for product in test_products:
        print(f"\n📋 Testing orders for: {product['name']} ({product['type']})")
        
        # Calculate test quantities and prices
        base_price = product["price"]
        currency = product["currency"]
        
        test_cases = [
            {
                "description": "Small BUY order at market",
                "action": "BUY",
                "order_type": "MARKET",
                "quantity": 1,
                "price": None
            },
            {
                "description": "Small BUY order with limit price",
                "action": "BUY", 
                "order_type": "LIMIT",
                "quantity": 1,
                "price": base_price * 1.01  # 1% above current price
            },
            {
                "description": "Small SELL order with limit price",
                "action": "SELL",
                "order_type": "LIMIT", 
                "quantity": 1,
                "price": base_price * 0.99  # 1% below current price
            },
            {
                "description": "Larger BUY order",
                "action": "BUY",
                "order_type": "LIMIT",
                "quantity": 5,
                "price": base_price * 1.02
            }
        ]
        
        for test_case in test_cases:
            print(f"\n   🔧 {test_case['description']}")
            result = test_order_check(
                config,
                product_id=product["id"],
                action=test_case["action"],
                order_type=test_case["order_type"],
                quantity=test_case["quantity"],
                price=test_case["price"],
                time_type="DAY"
            )
            
            if result is not None:
                successful_tests += 1
                if result.get("valid", False):
                    valid_orders += 1
                    print(f"      ✅ Order is valid")
                else:
                    invalid_orders += 1
                    print(f"      ❌ Order is invalid")
            else:
                failed_tests += 1
                print(f"      ❌ API call failed")
    
    print(f"\n{'='*50}")
    print(f"📊 Test Summary:")
    print(f"   ✅ Successful API calls: {successful_tests}")
    print(f"   ❌ Failed API calls: {failed_tests}")
    print(f"   ✅ Valid orders: {valid_orders}")
    print(f"   ❌ Invalid orders: {invalid_orders}")
    
    if successful_tests + failed_tests > 0:
        success_rate = (successful_tests/(successful_tests+failed_tests)*100)
        print(f"   📊 API Success Rate: {success_rate:.1f}%")
    
    if successful_tests > 0:
        print(f"\n💡 Order validation is working!")
        print(f"🔒 No real orders were placed - this was validation only.")
        if valid_orders > 0:
            print(f"✅ {valid_orders} orders would be valid if placed")
        if invalid_orders > 0:
            print(f"⚠️  {invalid_orders} orders were rejected (normal for testing)")
    else:
        print(f"\n❌ Order validation is not working. Check API and DEGIRO connection.")

if __name__ == "__main__":
    main()