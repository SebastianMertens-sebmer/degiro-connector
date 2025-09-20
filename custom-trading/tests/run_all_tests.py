#!/usr/bin/env python3
"""
Master test runner for all DEGIRO Trading API endpoints
Runs all 5 endpoint tests in sequence
"""

import os
import sys
import subprocess
from datetime import datetime

def run_test(test_name, script_path):
    """Run a single test script"""
    print(f"\n{'='*60}")
    print(f"🧪 Running {test_name}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, 
                              text=True, 
                              timeout=60)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"❌ {test_name} timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"❌ {test_name} failed with exception: {e}")
        return False

def main():
    """Run all API tests"""
    print("🚀 DEGIRO Trading API - Complete Test Suite")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check environment
    api_key = os.getenv("TRADING_API_KEY")
    if not api_key:
        print("❌ TRADING_API_KEY environment variable not set")
        print("Run: source config/.env")
        return
    
    # Test scripts in order
    tests = [
        ("Stock Search", "test_stock_search.py"),
        ("Leveraged Search", "test_leveraged_search.py"), 
        ("Product Search", "test_product_search.py"),
        ("Order Check", "test_order_check.py"),
        ("Order Place", "test_order_place.py")
    ]
    
    results = []
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    for test_name, script_name in tests:
        script_path = os.path.join(test_dir, script_name)
        
        if not os.path.exists(script_path):
            print(f"❌ Test script not found: {script_path}")
            results.append((test_name, False))
            continue
        
        success = run_test(test_name, script_path)
        results.append((test_name, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUITE SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 Results: {passed} passed, {failed} failed")
    success_rate = (passed / (passed + failed) * 100) if (passed + failed) > 0 else 0
    print(f"📊 Success Rate: {success_rate:.1f}%")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Your API is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check the logs above for details.")

if __name__ == "__main__":
    main()