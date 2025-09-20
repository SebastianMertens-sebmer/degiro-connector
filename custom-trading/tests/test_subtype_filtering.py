#!/usr/bin/env python3
"""
Test product subtype filtering functionality
"""

import os
# Note: Run this test from the custom-trading directory

def test_subtype_filtering():
    """Test the filter_by_product_subtype function"""
    print("🔍 Testing Product Subtype Filtering")
    print("=" * 50)
    
    # Mock product data based on our analysis
    mock_products = [
        {"name": "BNP APPLE Call STR 145 R 0.100 18/06/2026 LV 2.26", "id": 1},
        {"name": "BNP APPLE Put STR 22 R 0.100 19/12/2025 LV 6.21", "id": 2},
        {"name": "BNP APPLE Mini Long SL 10.5051 STR 9.7722 R 0.100 LV 1.89", "id": 3},
        {"name": "BNP APPLE Mini Short SL 11.0427 STR 10.5169 R 0.100 LV 2.02", "id": 4},
        {"name": "BNP APPLE Unlimited Long SL 10.6400 STR 10.6400 R 0.100 LV 2.02", "id": 5},
        {"name": "BNP APPLE Unlimited Short SL 11.4371 STR 11.4371 R 0.100 LV 2.19", "id": 6},
        {"name": "SG Apple Standard-Optionsschein Call STR 150 LV 0.01", "id": 7},
    ]
    
    try:
        from api.main import filter_by_product_subtype
        
        # Test ALL filter (should return all products)
        all_products = filter_by_product_subtype(mock_products, "ALL")
        print(f"✅ ALL filter: {len(all_products)}/7 products returned")
        
        # Test CALL_PUT filter (should return calls and puts)
        call_put_products = filter_by_product_subtype(mock_products, "CALL_PUT")
        print(f"✅ CALL_PUT filter: {len(call_put_products)} products returned")
        for product in call_put_products:
            print(f"   - {product['name']}")
        
        # Test MINI filter (should return knockouts)
        mini_products = filter_by_product_subtype(mock_products, "MINI")
        print(f"✅ MINI filter: {len(mini_products)} products returned")
        for product in mini_products:
            print(f"   - {product['name']}")
        
        # Test UNLIMITED filter (should return faktor certificates)
        unlimited_products = filter_by_product_subtype(mock_products, "UNLIMITED")
        print(f"✅ UNLIMITED filter: {len(unlimited_products)} products returned")
        for product in unlimited_products:
            print(f"   - {product['name']}")
        
        print(f"\n🎯 FILTERING SUMMARY:")
        print(f"   📊 Total products: {len(mock_products)}")
        print(f"   📞 CALL_PUT (Optionsscheine): {len(call_put_products)}")
        print(f"   🔨 MINI (Knockouts): {len(mini_products)}")
        print(f"   ♾️  UNLIMITED (Faktor): {len(unlimited_products)}")
        
        # Verify expected results
        expected_call_put = 3  # Two BNP call/put + one SG optionsschein
        expected_mini = 2      # Two mini long/short
        expected_unlimited = 2 # Two unlimited long/short
        
        if len(call_put_products) == expected_call_put:
            print("   ✅ CALL_PUT filtering correct")
        else:
            print(f"   ❌ CALL_PUT filtering incorrect: expected {expected_call_put}, got {len(call_put_products)}")
        
        if len(mini_products) == expected_mini:
            print("   ✅ MINI filtering correct")
        else:
            print(f"   ❌ MINI filtering incorrect: expected {expected_mini}, got {len(mini_products)}")
        
        if len(unlimited_products) == expected_unlimited:
            print("   ✅ UNLIMITED filtering correct")
        else:
            print(f"   ❌ UNLIMITED filtering incorrect: expected {expected_unlimited}, got {len(unlimited_products)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_subtype_filtering()