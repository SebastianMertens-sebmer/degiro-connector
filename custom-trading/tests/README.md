# DEGIRO Trading API Tests

Comprehensive test suite for all 5 API endpoints. Tests validate functionality locally before using with Make.com or other integrations.

## 🚀 Quick Start

### 1. Setup Environment
```bash
# From custom-trading directory
source config/.env  # Load API key
```

### 2. Run All Tests
```bash
cd tests
python run_all_tests.py
```

### 3. Run Individual Tests
```bash
python test_stock_search.py      # Test stock search
python test_leveraged_search.py  # Test leveraged products
python test_product_search.py    # Test universal search
python test_order_check.py       # Test order validation
python test_order_place.py       # Test order placement (DRY RUN)
```

## 📋 Test Scripts

| Script | Endpoint | Purpose | Safety |
|--------|----------|---------|--------|
| `test_stock_search.py` | `/api/stocks/search` | Search for stocks | ✅ Safe |
| `test_leveraged_search.py` | `/api/leveraged/search` | Find leveraged products | ✅ Safe |
| `test_product_search.py` | `/api/products/search` | Universal search | ✅ Safe |
| `test_order_check.py` | `/api/orders/check` | Validate orders | ✅ Safe |
| `test_order_place.py` | `/api/orders/place` | Place orders | ⚠️ DRY RUN by default |

## 🔍 What Each Test Does

### Stock Search Test
- Tests various ticker symbols (AAPL, TSLA, META, etc.)
- Tests company names (Apple, Tesla, Microsoft)
- Tests European stocks (ASML, SAP)
- Tests ISINs and partial matches
- **Purpose**: Find working search queries

### Leveraged Search Test  
- Uses stock IDs from stock search
- Tests LONG and SHORT positions
- Tests different leverage ranges (2x-10x)
- Tests multiple underlying stocks
- **Purpose**: Verify leveraged product discovery

### Product Search Test
- Tests universal search endpoint
- Combines stock + leveraged product search
- Tests various parameter combinations
- **Purpose**: Validate legacy endpoint compatibility

### Order Check Test
- Validates orders WITHOUT placing them
- Tests BUY/SELL orders
- Tests MARKET/LIMIT order types
- Tests different quantities and prices
- **Purpose**: Ensure order validation works

### Order Place Test
- **DRY RUN by default** - no real orders placed
- Tests complete order workflow (check → place)
- Can be enabled for real orders (use caution!)
- **Purpose**: Verify order placement functionality

## ⚠️ Safety Features

### Order Placement Safety
```python
# In test_order_place.py
DRY_RUN = True  # Change to False for real orders
```

When `DRY_RUN = True`:
- Shows what WOULD be sent to API
- No real orders placed
- Safe for testing

When `DRY_RUN = False`:
- **Requires multiple confirmations**
- **Places REAL orders with REAL money**
- **Use only with test accounts**

## 📊 Expected Results

### If API is Working Correctly:
```
✅ PASS - Stock Search        # Found stocks for various queries
✅ PASS - Leveraged Search    # Found leveraged products
✅ PASS - Product Search      # Universal search working
✅ PASS - Order Check         # Order validation working  
✅ PASS - Order Place         # Order placement working (dry run)
```

### If Issues Exist:
```
❌ FAIL - Stock Search        # No stocks found - check DEGIRO connection
✅ PASS - Leveraged Search    # Depends on stock search results
✅ PASS - Product Search      # May work even if stock search fails
❌ FAIL - Order Check         # Check DEGIRO authentication
❌ FAIL - Order Place         # Depends on order check
```

## 🔧 Troubleshooting

### No Stocks Found
```bash
# Test DEGIRO connection manually
python ../examples/trading/login_2fa.py
```

### API Key Issues
```bash
# Check environment variable
echo $TRADING_API_KEY

# Reload environment
source config/.env
```

### Connection Issues
```bash
# Check API health
curl http://localhost:7731/api/health
```

### Permission Issues
```bash
# Check DEGIRO account status
# Ensure 2FA is properly configured
# Verify account has trading permissions
```

## 📈 Using Results for Make.com

After tests pass, use the working queries in Make.com:

### Working Stock Symbols
Find symbols that returned results in stock search test:
- Use these in Make.com product search modules
- Replace "apple" with working symbols like "AAPL"

### Working Product IDs
Get product IDs from successful searches:
- Use for leveraged product searches
- Use for order validation and placement

### Working Price Ranges
Note realistic price ranges from test results:
- Use for order quantity calculations
- Set appropriate limit prices

## 🎯 Next Steps

1. **Run tests locally** to verify API functionality
2. **Note working search terms** from test output
3. **Update Make.com modules** with working parameters
4. **Test Make.com integration** with validated endpoints
5. **Monitor order execution** if using real orders

---

**Remember**: Always test thoroughly in a safe environment before using with real money!