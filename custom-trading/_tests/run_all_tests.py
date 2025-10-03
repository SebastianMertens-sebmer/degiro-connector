#!/usr/bin/env python3
"""
Master test runner - Execute all 10 API endpoint tests
"""

import os
import sys
import subprocess
import time

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_test_script(script_name, description):
    """Run a single test script and return success status"""
    print(f"\n{'='*60}")
    print(f"🧪 Running: {description}")
    print(f"{'='*60}")
    
    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, script_name)
    
    try:
        result = subprocess.run([
            sys.executable, script_path
        ], capture_output=True, text=True, timeout=200)
        
        print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"❌ Test {script_name} timed out after 200 seconds")
        return False
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        return False

def main():
    print("🚀 DEGIRO Trading API - Complete Test Suite")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("TRADING_API_KEY")
    if not api_key:
        print("❌ TRADING_API_KEY not found in environment")
        print("💡 Run: source config/.env")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Test suite - all 10 endpoints
    tests = [
        ("test_01_root.py", "Root Endpoint - API Overview"),
        ("test_02_health.py", "Health Check - API & DEGIRO Status"),
        ("test_03_stocks_search.py", "Stocks Search - Individual Stock Lookup"),
        ("test_04_leveraged_search.py", "Leveraged Search - Leveraged Products"),
        ("test_05_products_search.py", "Universal Search - Combined Search"),
        ("test_06_volume_opening.py", "Volume Opening - Real-time Volume Data"),
        ("test_07_volume_nasdaq.py", "Volume NASDAQ - Batch Volume Data"),
        ("test_08_price_current.py", "Price Current - Real-time Price Data"),
        ("test_09_orders_check.py", "Orders Check - Order Validation"),
        ("test_10_orders_place.py", "Orders Place - Order Execution")
    ]
    
    results = []
    start_time = time.time()
    
    for script, description in tests:
        success = run_test_script(script, description)
        results.append((script, description, success))
        
        # Small delay between tests
        time.sleep(1)
    
    # Summary
    total_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"📊 TEST SUITE SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    failed = 0
    
    for script, description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {description}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 Results: {passed} passed, {failed} failed")
    print(f"⏱️  Total time: {total_time:.1f} seconds")
    
    if failed == 0:
        print("\n🎉 All tests passed! API is working correctly.")
    else:
        print(f"\n⚠️  {failed} tests failed. Check individual results above.")

if __name__ == "__main__":
    main()