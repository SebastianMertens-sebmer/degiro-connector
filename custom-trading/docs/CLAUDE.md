# DEGIRO Trading API - Claude Documentation

## Project Overview
Production-ready FastAPI server for automated DEGIRO trading with leveraged products support.

## Key Features
- Universal product search (ISIN, name, ticker symbols)
- Leveraged products filtering by underlying assets
- Two-step order validation (check → confirm)
- Bearer token authentication
- VPS deployment with auto-restart capabilities

## API Endpoints

### Core Endpoints
- `GET /api/health` - Health check (public)
- `POST /api/products/search` - **Universal product search with real-time pricing**
- `POST /api/orders/check` - Validate order parameters  
- `POST /api/orders/confirm` - Execute validated order

### Product Search API
**`POST /api/products/search`** - Find stocks and leveraged products with real-time pricing

**Request Body:**
```json
{
  "q": "chevron",           // Stock name, symbol, or ISIN
  "action": "SHORT",        // "LONG" or "SHORT" 
  "min_leverage": 2.0,      // Minimum leverage (default: 2.0)
  "max_leverage": 10.0,     // Maximum leverage (default: 10.0)
  "limit": 50              // Max leveraged products (default: 50)
}
```

**Response:**
```json
{
  "query": {
    "q": "chevron",
    "action": "SHORT", 
    "min_leverage": 2.0,
    "max_leverage": 10.0,
    "limit": 50
  },
  "direct_stock": {
    "product_id": "331785",
    "name": "Chevron Corp",
    "isin": "US1667641005", 
    "currency": "USD",
    "exchange_id": "676",
    "current_price": {
      "bid": 155.98,
      "ask": 156.29, 
      "last": 156.13
    },
    "tradable": true
  },
  "leveraged_products": [
    {
      "product_id": "24395646",
      "name": "BNP CHEVRON Faktor 2 Short R 1",
      "isin": "DE000PN2CVP1",
      "leverage": 2.0,
      "direction": "SHORT",
      "currency": "EUR", 
      "exchange_id": "191",
      "current_price": {
        "bid": 7.58,
        "ask": 7.59,
        "last": 7.58
      },
      "tradable": true,
      "expiration_date": "31-12-9999",
      "issuer": "BNP"
    }
  ],
  "total_found": {
    "direct_stock": 1,
    "leveraged_products": 1
  },
  "timestamp": "2025-09-20T23:43:45.730325"
}
```

**Key Features:**
- ✅ **Real-time pricing** via DEGIRO quotecast API (no mock data)
- ✅ **Reliable filtering** using DEGIRO's native fields (leverage, direction, tradability)
- ✅ **Universal search** supports company names, tickers, symbols, and ISINs
- ✅ **Leveraged products** include Faktor certificates, Mini products, and options
- ✅ **Direction filtering** LONG/SHORT with proper validation
- ✅ **Leverage range** filtering for risk management

### Usage Examples

**Find Chevron SHORT products with 2-10x leverage:**
```bash
curl -X POST "http://152.53.200.195:7731/api/products/search" \
  -H "Authorization: Bearer $TRADING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "q": "chevron",
    "action": "SHORT", 
    "min_leverage": 2.0,
    "max_leverage": 10.0,
    "limit": 10
  }'
```

**Find Apple LONG products with 3-5x leverage:**
```bash
curl -X POST "http://152.53.200.195:7731/api/products/search" \
  -H "Authorization: Bearer $TRADING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "q": "AAPL",
    "action": "LONG",
    "min_leverage": 3.0, 
    "max_leverage": 5.0,
    "limit": 5
  }'
```

**Search by ISIN:**
```bash
curl -X POST "http://152.53.200.195:7731/api/products/search" \
  -H "Authorization: Bearer $TRADING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "q": "US1667641005",
    "action": "SHORT",
    "min_leverage": 2.0,
    "max_leverage": 10.0
  }'
```

## Production Deployment
**VPS**: 152.53.200.195:7731  
**Auth**: Bearer `[FROM .ENV FILE]`  
**Docs**: http://152.53.200.195:7731/docs

## Quick Commands
```bash
# Deploy to VPS
./scripts/deploy_to_vps.sh

# Connect to VPS
ssh -i ~/.ssh/rockettrader_key basti@152.53.200.195

# Pull latest changes (NEW REPOSITORY PATH)
cd /home/basti/degiro-trading-api-new && git pull origin main

# Start API (NEW REPOSITORY PATH)
cd /home/basti/degiro-trading-api-new/custom-trading
source venv/bin/activate
gunicorn api.main:app --bind 0.0.0.0:7731 --workers 4 --worker-class uvicorn.workers.UvicornWorker --daemon

# Test API (replace $TRADING_API_KEY with actual key from .env)
curl -H "Authorization: Bearer $TRADING_API_KEY" \
     http://152.53.200.195:7731/api/health

# Or load from .env file first:
source config/.env
curl -H "Authorization: Bearer $TRADING_API_KEY" \
     http://152.53.200.195:7731/api/health
```

## Environment Setup
- Credentials in `.env` file (DEGIRO_USERNAME, DEGIRO_PASSWORD, DEGIRO_TOTP_SECRET)
- Custom port 7731 for security  
- Firewall configured for port access
- Python 3.12 virtual environment

## Project Structure (v2.1.0)
The custom-trading API is now **completely standalone** and works on any computer:

```
custom-trading/
├── api/
│   ├── main.py          # Main FastAPI application
│   ├── config.py        # Smart config management
│   └── __init__.py      # Package init
├── config/
│   ├── config.json      # DEGIRO credentials
│   └── .env             # Environment variables
├── scripts/
│   ├── fix_imports.py   # Remove hardcoded paths
│   └── update_upstream.py # Sync with upstream
├── tests/               # Clean test files (no hardcoded paths)
├── setup.py            # Proper Python package
└── requirements.txt    # Uses degiro-connector from GitHub

# Parent directory connection
../                     # Main degiro-connector repository
├── upstream remote     # Connected to Chavithra/degiro-connector
└── origin remote       # Your fork
```

## Smart Features
- **Auto-detects config paths** - Works from any directory
- **No hardcoded sys.path** - Proper Python package imports
- **Upstream sync script** - Keep updated with latest degiro-connector
- **Environment flexibility** - Config via files or environment variables

## Security
- Secure 32-character API tokens
- Environment variable credential management
- VPS firewall protection
- Bearer token authentication

## Testing
- Run `python -m pytest tests/` from custom-trading directory
- Test specific functionality: `python tests/test_subtype_filtering.py`
- Health endpoint shows connection status: `/api/health`
- Complete API documentation at `/docs`

## Maintenance
```bash
# Update from upstream degiro-connector
cd custom-trading && python3 scripts/update_upstream.py

# Fix any import issues after updates
python3 scripts/fix_imports.py

# Install in development mode
pip install -e .
```

## Dependencies
- FastAPI, uvicorn, pydantic
- degiro-connector (trading API)
- python-dotenv (environment management)
- polars, pandas, pyarrow (real-time pricing)

## Latest Updates (v2.1.1)

### 🔧 Fixed Leveraged Products Search
**Issue Resolved:** Leveraged product search was returning 0 results due to broken filtering logic.

**Root Cause:** The filtering logic was changed from using DEGIRO's reliable native fields to unreliable name-based keyword parsing.

**Solution Applied:**
- ✅ **Restored DEGIRO field-based filtering** from commit 513b531
- ✅ **Fixed LeveragedsRequest validation** by adding all required parameters
- ✅ **Proper action→short_long mapping** (SHORT=0, LONG=1)
- ✅ **Removed unreliable keyword filtering** that rejected valid products

**Before (Broken):**
```python
# ❌ Name-based keyword filtering
leverage = extract_leverage_from_name(product.get('name', ''))
if "PUT" in name or "SHORT" in name or "BEAR" in name:
    suitable_products.append(product)
```

**After (Working):**
```python
# ✅ DEGIRO field-based filtering  
leverage = product.get('leverage', 0)
shortlong = product.get('shortlong')
tradable = product.get('tradable', False)

if (min_leverage <= leverage <= max_leverage and 
    shortlong == target_direction and tradable):
    suitable_products.append(product)
```

**Results:**
- ✅ **Chevron SHORT**: Now finds 3 Faktor products (2x leverage)
- ✅ **BASF SHORT**: Now finds 2 Faktor products (2x leverage)  
- ✅ **Real-time pricing**: All products include live bid/ask/last prices
- ✅ **Reliable filtering**: Uses DEGIRO's native leverage/direction fields

# 🔐 Security Guidelines

## ⚠️ CRITICAL SECURITY RULES

### 🚨 **NEVER COMMIT CREDENTIALS TO GIT**

1. **NO HARDCODED CREDENTIALS** in any file committed to git
   - ❌ `password = "mypassword"`
   - ❌ `api_key = "abc123"`
   - ✅ `password = os.getenv("DEGIRO_PASSWORD")`

2. **ALL CREDENTIALS MUST USE ENVIRONMENT VARIABLES**
   ```python
   # ✅ CORRECT - Use environment variables
   username = os.getenv("DEGIRO_USERNAME")
   password = os.getenv("DEGIRO_PASSWORD")
   totp_secret = os.getenv("DEGIRO_TOTP_SECRET")
   int_account = int(os.getenv("DEGIRO_INT_ACCOUNT", 0))
   api_key = os.getenv("TRADING_API_KEY")
   ```

3. **PROTECTED FILES (.gitignore)**
   - ✅ `config/.env` - Protected by .gitignore
   - ✅ `config/config.json` - Protected by .gitignore
   - ✅ All `.env*` files - Protected by .gitignore

## 📋 **Rules for Test Scripts**

### ✅ **DO THIS:**
```python
import os

# Load from environment variables
credentials = Credentials(
    username=os.getenv("DEGIRO_USERNAME"),
    password=os.getenv("DEGIRO_PASSWORD"),
    totp_secret_key=os.getenv("DEGIRO_TOTP_SECRET"),
    int_account=int(os.getenv("DEGIRO_INT_ACCOUNT", 0))
)

# Load from config system
from api.config import get_config
config = get_config()
user_token = config.get("user_token")
```

### ❌ **NEVER DO THIS:**
```python
# ❌ HARDCODED CREDENTIALS
username = "bastiheye"
password = "mypassword"
api_key = "abc123"

# ❌ HARDCODED IN DOCUMENTATION
curl -H "Authorization: Bearer abc123xyz"
```

## 🔧 **Setting Up Credentials**

### **1. Environment Variables**
```bash
export DEGIRO_USERNAME='your_username'
export DEGIRO_PASSWORD='your_secure_password'
export DEGIRO_TOTP_SECRET='your_totp_secret'
export DEGIRO_INT_ACCOUNT='your_account_id'
export TRADING_API_KEY='your_api_key'
```

### **2. Config File (Protected by .gitignore)**
```json
{
  "username": "your_username",
  "password": "your_secure_password", 
  "totp_secret_key": "your_totp_secret",
  "int_account": 12345678,
  "user_token": "your_user_token"
}
```

### **3. .env File (Protected by .gitignore)**
```bash
DEGIRO_USERNAME=your_username
DEGIRO_PASSWORD=your_secure_password
DEGIRO_TOTP_SECRET=your_totp_secret
DEGIRO_INT_ACCOUNT=12345678
TRADING_API_KEY=your_api_key
```

## 🛡️ **Security Checklist**

Before committing any code:

- [ ] No hardcoded usernames, passwords, or API keys
- [ ] All sensitive data uses `os.getenv()` or config system
- [ ] Test files load credentials from environment
- [ ] Documentation uses placeholders like `[FROM .ENV FILE]`
- [ ] Sensitive files are in `.gitignore`
- [ ] Run security scan: `python3 scripts/security_cleanup.py`

## 🚨 **If You Find Hardcoded Credentials**

1. **Immediate Action:**
   ```bash
   python3 scripts/security_cleanup.py
   ```

2. **Change All Passwords:**
   - Update DEGIRO password
   - Regenerate API keys
   - Update TOTP secrets if compromised

3. **Clean Git History (if needed):**
   ```bash
   # Remove sensitive data from git history
   git filter-branch --force --index-filter \
   "git rm --cached --ignore-unmatch path/to/sensitive/file" \
   --prune-empty --tag-name-filter cat -- --all
   ```

## 📝 **For New Test Scripts**

Always start with this template:

```python
#!/usr/bin/env python3
"""
Test script - Uses environment variables for security
"""

import os
from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials

def main():
    # ✅ SECURE: Load from environment
    credentials = Credentials(
        username=os.getenv("DEGIRO_USERNAME"),
        password=os.getenv("DEGIRO_PASSWORD"),
        totp_secret_key=os.getenv("DEGIRO_TOTP_SECRET"),
        int_account=int(os.getenv("DEGIRO_INT_ACCOUNT", 0))
    )
    
    if not all([credentials.username, credentials.password]):
        print("❌ Set DEGIRO_USERNAME and DEGIRO_PASSWORD environment variables")
        return
    
    # Your test code here...

if __name__ == "__main__":
    main()
```

## 🎯 **Remember**

**The golden rule: If it's sensitive, it goes in .env or config files, NEVER in git!** 🔐

---

# 🚀 Latest Updates (v2.2.0) - Real-Time Volume & Price API

## 📊 New ORB Strategy Endpoints

### Volume Data Endpoint
```http
GET /api/volume/opening/{symbol}
Authorization: Bearer YOUR_API_KEY
```

**Features:**
- ✅ **Real-time daily volume data** for NASDAQ 100 stocks
- ✅ **No time restrictions** - caller controls timing logic
- ✅ **Volume rate calculations** (shares per minute)
- ✅ **Live data parsing** from DEGIRO quotecast API

**Response Example:**
```json
{
  "symbol": "WBD",
  "current_time": "2025-09-26T14:37:10-04:00",
  "market_open_time": "2025-09-26T09:30:00-04:00",
  "elapsed_minutes": 307.2,
  "cumulative_volume": 25743956,
  "last_volume": 100,
  "volume_rate_per_minute": 83808,
  "degiro_vwd_id": "600236482",
  "degiro_id": "22187048",
  "timestamp": "2025-09-26T18:37:10.569848Z"
}
```

### Price Data Endpoint
```http
GET /api/price/opening/{symbol}
Authorization: Bearer YOUR_API_KEY
```

**Features:**
- ✅ **Real-time OHLCV price data** for NASDAQ 100 stocks
- ✅ **VWAP calculations** (volume-weighted average price)
- ✅ **Live market data** during trading hours
- ✅ **No mocks or fake data** - pure DEGIRO feed

**Response Example:**
```json
{
  "symbol": "WBD",
  "current_price": 19.77,
  "open_price": 19.34,
  "high_price": 19.95,
  "low_price": 19.34,
  "volume": 25798141,
  "vwap": 19.68,
  "market_open_time": "2025-09-26T09:30:00-04:00",
  "current_time": "2025-09-26T14:37:34-04:00",
  "degiro_vwd_id": "600236482"
}
```

## 🔧 Technical Implementation

### Fixed DEGIRO JSON Parsing
- **Issue**: `ticker.data` property wasn't working correctly
- **Solution**: Manual JSON parsing of DEGIRO's quotecast response
- **Result**: Real-time data extraction for volume and price metrics

### NASDAQ 100 Symbol Mapping
- **File**: `docs/nasdaq100_degiro_mapping.json`
- **Coverage**: 101 NASDAQ stocks with DEGIRO product IDs and vwdIds
- **Success Rate**: 91.1% found in DEGIRO, 89.1% with real-time data

### Performance Optimizations
- **Response Time**: < 500ms per endpoint
- **Real-time Updates**: Every few seconds during market hours
- **Concurrent Requests**: Supported for multiple symbols

## 🎯 ORB Strategy Integration

### Usage Pattern
```bash
# 1. Get volume data at any time
curl -H "Authorization: Bearer $TRADING_API_KEY" \
     "http://152.53.200.195:7731/api/volume/opening/WBD"

# 2. Get price data for OHLC analysis
curl -H "Authorization: Bearer $TRADING_API_KEY" \
     "http://152.53.200.195:7731/api/price/opening/WBD"

# 3. Caller handles timing logic (e.g., 9:35 AM ET for ORB)
```

### Key Benefits
- **No time restrictions**: API always returns current daily data
- **Caller-controlled timing**: Strategy decides when to call (9:35 AM, 11 AM, etc.)
- **Real-time volume tracking**: Perfect for ORB volume confirmation
- **Live price updates**: Current OHLC for breakout analysis

## 📊 Tested Results

### WBD (Warner Bros Discovery) Live Data
```bash
✅ Volume: 25,798,141 shares (daily cumulative)
✅ Price: $19.77 (real-time)
✅ OHLC: Open $19.34, High $19.95, Low $19.34
✅ Volume Rate: 83,808 shares/minute
✅ Response Time: ~300ms
```

## 🚨 VPS Deployment Issues

### SSH Connection Problems
```bash
# Issue: Permission denied errors
ssh -i ~/.ssh/id_rsa root@152.53.200.195  # ❌ Wrong key
ssh -i ~/.ssh/rockettrader_key root@152.53.200.195  # ❌ Wrong user

# Solution: Use correct key and user
ssh -i ~/.ssh/rockettrader_key basti@152.53.200.195  # ✅ Correct
```

### Git Pull Conflicts
```bash
# Issue: Local changes conflict with remote
error: Your local changes to the following files would be overwritten by merge:
	custom-trading/api/main.py

# Solution: Stash changes before pulling
cd degiro-trading-api-new
git stash
git pull origin main
```

### VPS Directory Structure
```bash
# Correct paths on VPS
/home/basti/degiro-trading-api-new/  # Main repository
/home/basti/degiro-trading-api-new/custom-trading/  # API directory

# Commands to deploy
cd degiro-trading-api-new && git pull origin main
cd custom-trading && source venv/bin/activate
python api/main.py  # Start API server
```

### Network Timeout Issues
```bash
# Issue: SSH timeouts during long operations
ssh: connect to host 152.53.200.195 port 22: Operation timed out

# Recommendations:
1. Use shorter commands
2. Check VPS network connectivity
3. Consider using screen/tmux for long operations
```

## 🔄 Deployment Checklist

### Before Deployment
- [ ] Code committed and pushed to GitHub
- [ ] API tests passing locally
- [ ] Volume/price endpoints validated with real data
- [ ] Documentation updated

### VPS Deployment Steps
1. **SSH to VPS**: `ssh -i ~/.ssh/rockettrader_key basti@152.53.200.195`
2. **Navigate to repo**: `cd degiro-trading-api-new`
3. **Stash local changes**: `git stash`
4. **Pull latest code**: `git pull origin main`
5. **Navigate to API**: `cd custom-trading`
6. **Activate environment**: `source venv/bin/activate`
7. **Test endpoints**: `python -c "from api.main import app; print('API ready')"`
8. **Start production server**: `gunicorn api.main:app --bind 0.0.0.0:7731 --workers 4`

### Post-Deployment Testing
```bash
# Test volume endpoint
curl -H "Authorization: Bearer $TRADING_API_KEY" \
     "http://152.53.200.195:7731/api/volume/opening/WBD"

# Test price endpoint  
curl -H "Authorization: Bearer $TRADING_API_KEY" \
     "http://152.53.200.195:7731/api/price/opening/WBD"

# Test health endpoint
curl "http://152.53.200.195:7731/api/health"
```

### Troubleshooting
- **403 Unauthorized**: Check API key in request headers
- **404 Not Found**: Verify symbol exists in NASDAQ 100 mapping
- **503 Service Unavailable**: Check DEGIRO connection and user_token
- **Timeout**: Verify VPS network connectivity and API server status

## 📈 Performance Metrics

### Response Times
- Volume endpoint: ~300ms average
- Price endpoint: ~350ms average
- Health check: ~50ms average

### Data Accuracy
- Real-time updates: Every 2-3 seconds during market hours
- Volume precision: Exact share counts
- Price precision: To 2 decimal places
- No delays or artificial restrictions

### Reliability
- DEGIRO connection: Stable during market hours
- Error handling: Graceful failures with proper HTTP codes
- Data validation: Missing data handled appropriately
- Concurrent requests: Supported without issues