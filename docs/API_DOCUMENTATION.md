# DEGIRO Trading API v2.0

Complete production-ready API for DEGIRO trading with product search and order management.

## Features

- ✅ **Universal Product Search** - Search by ISIN, company name, or ticker symbol
- ✅ **Leveraged Products Discovery** - Find certificates and knockout products
- ✅ **Complete Order Management** - LIMIT, MARKET, STOP_LOSS, STOP_LIMIT orders
- ✅ **Order Validation** - Pre-flight checks with cost estimation
- ✅ **Secure Authentication** - API key protection
- ✅ **Production Ready** - Comprehensive error handling and logging

## Quick Start

### 1. Start the API

```bash
# Set API key (production)
export TRADING_API_KEY="your-secure-api-key"

# Start server
python api/main.py
```

### 2. API Documentation

- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/health

## Authentication

All endpoints require API key authentication via Authorization header:

```bash
Authorization: Bearer your-secure-api-key
```

## Endpoints

### 🔍 Product Search

**`POST /api/products/search`**

Universal search for stocks and leveraged products.

**Request:**
```json
{
  "q": "CISCO",
  "action": "LONG",
  "min_leverage": 2.0,
  "max_leverage": 6.0,
  "limit": 10
}
```

**Response:**
```json
{
  "query": {
    "q": "CISCO",
    "action": "LONG",
    "min_leverage": 2.0,
    "max_leverage": 6.0,
    "limit": 10
  },
  "direct_stock": {
    "product_id": "123456",
    "name": "Cisco Systems",
    "isin": "US17275R1023",
    "currency": "USD",
    "exchange_id": "200",
    "current_price": {
      "bid": 52.45,
      "ask": 52.50,
      "last": 52.48
    },
    "tradable": true
  },
  "leveraged_products": [
    {
      "product_id": "789123",
      "name": "BNP CISCO SYSTEMS Faktor 4 Long",
      "isin": "DE000PC4CSC1",
      "leverage": 4.0,
      "direction": "LONG",
      "currency": "EUR",
      "current_price": {
        "bid": 8.45,
        "ask": 8.50,
        "last": 8.48
      },
      "tradable": true,
      "issuer": "BNP"
    }
  ],
  "total_found": {
    "direct_stock": 1,
    "leveraged_products": 5
  }
}
```

### ✅ Order Validation

**`POST /api/orders/check`**

Validate order parameters and get cost estimation.

**Request:**
```json
{
  "product_id": "789123",
  "action": "BUY",
  "order_type": "LIMIT",
  "quantity": 35,
  "price": 8.67,
  "time_type": "DAY"
}
```

**Response:**
```json
{
  "valid": true,
  "confirmation_id": "abc123def456",
  "estimated_fee": 2.50,
  "total_cost": 306.45,
  "free_space_new": 1245.67,
  "message": "Order validation successful"
}
```

### 📈 Place Order

**`POST /api/orders/place`**

Execute validated order.

**Request:**
```json
{
  "product_id": "789123",
  "action": "BUY",
  "order_type": "LIMIT",
  "quantity": 35,
  "price": 8.67,
  "time_type": "DAY"
}
```

**Response:**
```json
{
  "success": true,
  "order_id": "d46e3eb6-22c0-472d-a8bd-c90f88034290",
  "confirmation_id": "abc123def456",
  "message": "Order placed successfully",
  "product_id": "789123",
  "action": "BUY",
  "order_type": "LIMIT",
  "quantity": 35,
  "price": 8.67,
  "estimated_fee": 2.50,
  "total_cost": 306.45,
  "created_at": "2025-09-15T20:56:06.505294"
}
```

## Order Types

### LIMIT Order
- **Required**: `price`
- **Description**: Buy/sell at specified price or better

### MARKET Order  
- **Required**: None
- **Description**: Execute immediately at best available price

### STOP_LOSS Order
- **Required**: `stop_price`
- **Description**: Sell when price falls to stop price

### STOP_LIMIT Order
- **Required**: `price`, `stop_price`
- **Description**: Place limit order when stop price is reached

## Time Types

- **DAY**: Order valid until end of trading day
- **GTC**: Good Till Canceled (valid until manually canceled)

## Usage Examples

### Search and Trade Pipeline

```python
import requests

API_URL = "http://localhost:8000"
headers = {"Authorization": "Bearer your-api-key"}

# 1. Search for products
search_response = requests.post(f"{API_URL}/api/products/search", 
    json={"q": "Commerzbank", "action": "LONG"},
    headers=headers
)

products = search_response.json()
leveraged = products["leveraged_products"][0]  # Best option

# 2. Validate order
check_response = requests.post(f"{API_URL}/api/orders/check",
    json={
        "product_id": leveraged["product_id"],
        "action": "BUY",
        "order_type": "LIMIT", 
        "quantity": 35,
        "price": 8.67
    },
    headers=headers
)

if check_response.json()["valid"]:
    # 3. Place order
    order_response = requests.post(f"{API_URL}/api/orders/place",
        json={
            "product_id": leveraged["product_id"],
            "action": "BUY",
            "order_type": "LIMIT",
            "quantity": 35,
            "price": 8.67
        },
        headers=headers
    )
    
    print(f"Order placed: {order_response.json()['order_id']}")
```

### Trading Signals Integration

```python
# Example: Process trading signals
signals = [
    {
        "symbol": "DE000CBK1001",  # ISIN
        "company_name": "Commerzbank",
        "action": "LONG",
        "signal_strength": 4,
        "entry_price": 33.01
    }
]

for signal in signals:
    # Calculate investment amount by signal strength
    investment = 250 if signal["signal_strength"] == 3 else (
                 300 if signal["signal_strength"] == 4 else 400)
    
    # Search for leveraged products
    search_response = requests.post(f"{API_URL}/api/products/search",
        json={
            "q": signal["symbol"],
            "action": signal["action"],
            "min_leverage": 3.0,
            "max_leverage": 6.0
        },
        headers=headers
    )
    
    products = search_response.json()
    
    if products["leveraged_products"]:
        best_product = products["leveraged_products"][0]
        current_price = best_product["current_price"]["ask"]
        
        # Calculate quantity and limit price
        quantity = int(investment / current_price)
        limit_price = round(current_price * 1.02, 2)  # +2%
        
        # Place order
        order_response = requests.post(f"{API_URL}/api/orders/place",
            json={
                "product_id": best_product["product_id"],
                "action": "BUY",
                "order_type": "LIMIT",
                "quantity": quantity,
                "price": limit_price,
                "time_type": "DAY"
            },
            headers=headers
        )
        
        print(f"Placed {signal['company_name']} order: {order_response.json()}")
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "detail": "Error description",
  "status_code": 400
}
```

Common error codes:
- **400**: Bad Request - Invalid parameters
- **401**: Unauthorized - Invalid API key
- **500**: Internal Server Error - DEGIRO connection issues

## Production Deployment

### Environment Variables

```bash
export TRADING_API_KEY="your-production-api-key"
export DEGIRO_CONFIG_PATH="/path/to/config.json"
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY api/ ./api/
COPY config/ ./config/

EXPOSE 8000
CMD ["python", "api/main.py"]
```

### Security Considerations

1. **Use strong API keys** (32+ characters, random)
2. **Enable HTTPS** in production
3. **Restrict CORS origins** for production
4. **Monitor API usage** and implement rate limiting
5. **Secure DEGIRO credentials** with environment variables
6. **Regular security audits** of dependencies

## Support

- **API Issues**: Check `/api/health` endpoint
- **DEGIRO Connection**: Verify credentials in config.json
- **Order Failures**: Review order validation response
- **Rate Limits**: Implement backoff strategies

---

**⚠️ Trading Risk Warning**: Leveraged products carry high risk. This API is for authorized use only. Users are responsible for all trading decisions and losses.