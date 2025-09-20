# Custom DEGIRO Trading API

Production-ready FastAPI server for automated DEGIRO trading with 5-endpoint API design.

## 🚀 Features

- **5-Endpoint Trading API**: Complete workflow - search stocks → find leveraged products → validate → place orders
- **Stock Disambiguation**: Returns ALL matching stocks for precise selection
- **Leveraged Product Discovery**: Dynamic search using specific stock IDs as underlying assets
- **Advanced Filtering**: Leverage range, direction (LONG/SHORT), issuer, and limit controls
- **Real-time Pricing**: Live bid/ask/last prices for both stocks and leveraged products
- **Order Management**: Two-step validation (check → confirm) for safety
- **Security**: Bearer token authentication with secure credential management
- **Production Ready**: VPS deployment with auto-restart capabilities

## 📁 Structure
```
custom-trading/
├── api/                 # FastAPI trading server
├── scripts/             # Deployment and utility scripts  
├── config/              # Environment configuration (gitignored)
├── openapi.json         # API specification
└── README.md           # This documentation
```

## ⚡ Quick Start

### 1. Environment Setup
```bash
# Copy and configure environment
cp config/.env.example config/.env
# Edit config/.env with your DEGIRO credentials
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Test DEGIRO Connection
```bash
python ../examples/trading/login_2fa.py
```

### 4. Run API
```bash
# Local development
python api/main.py

# Production deployment
./scripts/deploy_to_vps.sh
```

## 🔐 Authentication

All endpoints (except `/api/health`) require Bearer token authentication:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     http://your-server:7731/api/endpoint
```

## 📡 API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check and status |
| `/api/stocks/search` | POST | Search for stocks |
| `/api/leveraged/search` | POST | Find leveraged products |
| `/api/products/search` | POST | Universal search (alternative) |
| `/api/orders/check` | POST | Validate order before placing |
| `/api/orders/place` | POST | Execute validated order |

### Health Check
```http
GET /api/health
```
**Response:**
```json
{
  "status": "healthy",
  "degiro_connection": "connected",
  "api_version": "2.0.0",
  "timestamp": "2025-01-15T10:30:00.123456"
}
```

## 🎯 API WORKFLOW

### Step 1: Stock Search
```http
POST /api/stocks/search
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "q": "AAPL",
  "limit": 10
}
```

**Parameters:**
- `q` (string, required): Search query (ticker symbol like "AAPL", "TSLA", "META" work best)
- `limit` (integer, optional): Maximum stocks to return (default: 20)

**💡 Search Tips:**
- Use ticker symbols: "AAPL", "TSLA", "META", "NVDA"  
- Try company names: "Apple", "Tesla", "Microsoft"
- Use ISINs for exact matches: "US0378331005"

**Response:**
```json
{
  "query": "AAPL",
  "stocks": [
    {
      "product_id": "1533610",
      "name": "Apple Inc",
      "isin": "US0378331005",
      "symbol": "AAPL",
      "currency": "USD",
      "exchange_id": "663",
      "current_price": {
        "bid": 150.83,
        "ask": 151.13,
        "last": 150.98
      },
      "tradable": true
    }
  ],
  "total_found": 1,
  "timestamp": "2025-09-19T17:55:40.675561"
}
```

### Step 2: Leveraged Products Search
```http
POST /api/leveraged/search
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "underlying_id": "1533610",
  "action": "LONG",
  "min_leverage": 5.0,
  "max_leverage": 10.0,
  "limit": 5
}
```

**Parameters:**
- `underlying_id` (string, required): Stock product ID from Step 1
- `action` (string, optional): "LONG" or "SHORT" (default: "LONG")
- `min_leverage` (number, optional): Minimum leverage (default: 2.0)
- `max_leverage` (number, optional): Maximum leverage (default: 10.0)
- `limit` (integer, optional): Max leveraged products to return (default: 10)
- `issuer_id` (integer, optional): Issuer filter (-1=all)

**Response:**
```json
{
  "query": {
    "underlying_id": "1533610",
    "action": "LONG",
    "min_leverage": 5.0,
    "max_leverage": 10.0,
    "limit": 5
  },
  "underlying_stock": {
    "product_id": "1533610",
    "name": "Apple Inc",
    "isin": "US0378331005",
    "symbol": "AAPL",
    "currency": "USD",
    "exchange_id": "663",
    "current_price": {
      "bid": 150.64,
      "ask": 150.79,
      "last": 150.64
    },
    "tradable": true
  },
  "leveraged_products": [
    {
      "product_id": "101113656",
      "name": "BNP APPLE Call STR 1000 R 0.100 18/06/2026 LV 5.73",
      "isin": "DE000PL63GN8",
      "leverage": 5.732,
      "direction": "LONG",
      "currency": "EUR",
      "exchange_id": "191",
      "current_price": {
        "bid": 48.36,
        "ask": 48.85,
        "last": 48.61
      },
      "tradable": true,
      "expiration_date": "18-6-2026",
      "issuer": "BNP"
    }
  ],
  "total_found": 5,
  "timestamp": "2025-09-19T18:03:40.794046"
}
```

### Alternative: Universal Product Search
```http
POST /api/products/search
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "q": "AAPL"
}
```
Returns both stock info and leveraged products in one call.

### Step 3: Order Validation
```http
POST /api/orders/check
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "product_id": "101113656",
  "action": "BUY",
  "order_type": "LIMIT",
  "quantity": 5,
  "price": 48.50,
  "time_type": "DAY"
}
```

**Parameters:**
- `product_id` (string, required): Product ID from leveraged search results
- `action` (string, required): "BUY" or "SELL"
- `order_type` (string, optional): "LIMIT", "MARKET", "STOP_LOSS", "STOP_LIMIT" (default: "LIMIT")
- `quantity` (number, required): Number of shares/units
- `price` (number, optional): Limit price (required for LIMIT orders)
- `stop_price` (number, optional): Stop price (required for STOP_LOSS/STOP_LIMIT)
- `time_type` (string, optional): "DAY", "GTC" (default: "DAY")

**Response:**
```json
{
  "valid": true,
  "confirmation_id": "temp_order_789",
  "estimated_fee": 2.50,
  "total_cost": 245.00,
  "free_space_new": 9750.00,
  "message": "Order validation successful",
  "warnings": [],
  "errors": []
}
```

### Step 4: Order Execution
```http
POST /api/orders/place
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "product_id": "101113656",
  "action": "BUY",
  "order_type": "LIMIT",
  "quantity": 5,
  "price": 48.50,
  "time_type": "DAY"
}
```

**Response:**
```json
{
  "success": true,
  "order_id": "real_order_456",
  "confirmation_id": "temp_order_789",
  "message": "Order placed successfully",
  "product_id": "101113656",
  "action": "BUY",
  "order_type": "LIMIT",
  "quantity": 5,
  "price": 48.50,
  "estimated_fee": 2.50,
  "total_cost": 245.00,
  "created_at": "2025-09-19T18:05:00.123456"
}
```

## 🚀 Production Deployment

### VPS Configuration
- **Host**: Your VPS IP
- **Port**: 7731 (configurable)
- **SSL**: Not included (use reverse proxy)
- **Auto-restart**: Systemd service + cron job

### Deployment Commands
```bash
# Deploy to VPS
./scripts/deploy_to_vps.sh

# Manual VPS management
ssh -i ~/.ssh/your_key user@your.vps.ip

# Start API
cd /path/to/degiro-trading-api && ./start_api.sh

# Check status
curl -H "Authorization: Bearer YOUR_KEY" http://your.vps.ip:7731/api/health

# View logs
tail -f logs/api.log
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# API Security
TRADING_API_KEY=your_secure_32_char_token

# DEGIRO Credentials  
DEGIRO_USERNAME=your_username
DEGIRO_PASSWORD=your_password
DEGIRO_TOTP_SECRET=your_2fa_secret
DEGIRO_INT_ACCOUNT=your_account_id

# Application Settings
API_PORT=7731
DEBUG=false
LOG_LEVEL=INFO
MAX_WORKERS=4

# VPS Deployment
VPS_HOST=your.vps.ip
VPS_USER=your_vps_user
VPS_PATH=/home/user/degiro-trading-api
```

## 🔄 Upstream Updates

This fork structure allows seamless updates from the main degiro-connector:

```bash
# Get latest upstream changes
git fetch upstream
git merge upstream/main  # No conflicts with custom-trading/
git push origin main
```

Your custom trading API stays isolated while benefiting from upstream improvements!

## 🛡️ Security Features

- **No Public Documentation**: API docs disabled in production
- **Bearer Token Auth**: Secure 32-character tokens
- **Environment Variables**: No hardcoded credentials
- **Gitignored Secrets**: .env files never committed
- **VPS Firewall**: Custom port with restricted access
- **Two-Step Orders**: Validation before execution

## 📊 Error Handling

Common error responses:

**401 Unauthorized:**
```json
{"detail": "Invalid API key"}
```

**400 Bad Request:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "q"],
      "msg": "Field required"
    }
  ]
}
```

**500 Internal Server Error:**
```json
{
  "detail": "DEGIRO connection failed",
  "error_code": "DEGIRO_CONNECTION_ERROR"
}
```

## 🧪 Testing

```bash
# Test DEGIRO connection
python ../examples/trading/login_2fa.py

# Test API endpoints
python tests/test_api_endpoints.py

# Health check
curl http://localhost:7731/api/health
```