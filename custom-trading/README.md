# Custom DEGIRO Trading API

Production-ready FastAPI server for automated DEGIRO trading with leveraged products support.

## 🚀 Features

- **Universal Product Search**: Search by ISIN, company name, or ticker symbol
- **Leveraged Products**: Automatic filtering by underlying assets  
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

## 📡 API Endpoints

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

### Product Search
```http
POST /api/products/search
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "q": "AAPL",
  "leverage_type": "long"
}
```

**Parameters:**
- `q` (string, required): Search query (ISIN, name, ticker)
- `leverage_type` (string, optional): "long", "short", or "both" (default: "both")

**Response:**
```json
{
  "query": "AAPL",
  "results": {
    "stocks": [
      {
        "id": "96008",
        "name": "APPLE INC. - COMMON STOCK",
        "isin": "US0378331005",
        "symbol": "AAPL",
        "exchange": "NASDAQ",
        "currency": "USD"
      }
    ],
    "leveraged_products": [
      {
        "id": "13496074",
        "name": "TURBO24 LONG APPLE 165.00",
        "isin": "DE000VQ8Z8K5",
        "leverage_type": "long",
        "underlying_id": "96008",
        "strike_price": 165.00
      }
    ]
  },
  "total_count": 15,
  "search_strategies_used": ["isin_exact", "symbol_match", "name_contains"]
}
```

### Order Validation
```http
POST /api/orders/check
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "product_id": "13496074",
  "order_type": "LIMIT",
  "side": "BUY",
  "quantity": 10,
  "price": 1.25,
  "time_type": "DAY"
}
```

**Parameters:**
- `product_id` (string, required): Product ID from search results
- `order_type` (string, required): "LIMIT", "MARKET", "STOP_LOSS", "STOP_LIMIT"
- `side` (string, required): "BUY" or "SELL"
- `quantity` (integer, required): Number of shares/units
- `price` (number, optional): Limit price (required for LIMIT orders)
- `time_type` (string, optional): "DAY", "GTC" (default: "DAY")

**Response:**
```json
{
  "validation_id": "temp_order_789",
  "status": "valid",
  "product": {
    "name": "TURBO24 LONG APPLE 165.00",
    "current_price": 1.23
  },
  "order_details": {
    "estimated_total": 12.50,
    "fees": 2.00,
    "currency": "EUR"
  },
  "warnings": []
}
```

### Order Execution
```http
POST /api/orders/confirm
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "validation_id": "temp_order_789"
}
```

**Response:**
```json
{
  "order_id": "real_order_456",
  "status": "confirmed",
  "execution_details": {
    "executed_quantity": 10,
    "average_price": 1.24,
    "total_amount": 12.40,
    "fees": 2.00,
    "timestamp": "2025-01-15T10:35:00.123456"
  }
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
python _tests/test_production_api.py

# Health check
curl http://localhost:7731/api/health
```