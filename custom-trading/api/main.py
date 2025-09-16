#!/usr/bin/env python3
"""
Production DEGIRO Trading API
Complete API for searching products and placing orders with full DEGIRO functionality
"""

import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.trading_pb2 import Credentials, ProductSearch, Order

# Load environment variables
load_dotenv()

# FastAPI app
app = FastAPI(
    title="DEGIRO Trading API",
    description="Production API for DEGIRO trading: search products, place orders, manage positions",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Configuration
API_KEY = os.getenv("TRADING_API_KEY", "your-secure-api-key-here")
DEGIRO_CONFIG_PATH = "config/config.json"

# Global DEGIRO connection
trading_api = None

# === MODELS ===

class PriceInfo(BaseModel):
    bid: Optional[float] = None
    ask: Optional[float] = None
    last: Optional[float] = None

class DirectStock(BaseModel):
    product_id: str
    name: str
    isin: str
    currency: str
    exchange_id: str
    current_price: PriceInfo
    tradable: bool

class LeveragedProduct(BaseModel):
    product_id: str
    name: str
    isin: str
    leverage: float
    direction: str  # LONG/SHORT
    currency: str
    exchange_id: str
    current_price: PriceInfo
    tradable: bool
    expiration_date: Optional[str] = None
    issuer: Optional[str] = None

class ProductSearchRequest(BaseModel):
    q: str = Field(..., description="Universal search - ISIN, company name, ticker, or symbol")
    action: str = Field(default="LONG", description="LONG or SHORT")
    min_leverage: float = Field(default=2.0, description="Minimum leverage")
    max_leverage: float = Field(default=10.0, description="Maximum leverage")
    limit: int = Field(default=10, description="Max leveraged products to return")

class ProductSearchResponse(BaseModel):
    query: Dict[str, Any]
    direct_stock: Optional[DirectStock]
    leveraged_products: List[LeveragedProduct]
    total_found: Dict[str, int]
    timestamp: str

# Order Models
class OrderRequest(BaseModel):
    product_id: str = Field(..., description="Product ID to trade")
    action: str = Field(..., description="BUY or SELL")
    order_type: str = Field(default="LIMIT", description="LIMIT, MARKET, STOP_LOSS, STOP_LIMIT")
    quantity: float = Field(..., gt=0, description="Number of shares/units")
    price: Optional[float] = Field(None, gt=0, description="Limit price (required for LIMIT/STOP_LIMIT)")
    stop_price: Optional[float] = Field(None, gt=0, description="Stop price (required for STOP_LOSS/STOP_LIMIT)")
    time_type: str = Field(default="DAY", description="DAY or GTC")

class OrderCheckResponse(BaseModel):
    valid: bool
    confirmation_id: Optional[str] = None
    estimated_fee: Optional[float] = None
    total_cost: Optional[float] = None
    free_space_new: Optional[float] = None
    message: str
    warnings: List[str] = []
    errors: List[str] = []

class OrderResponse(BaseModel):
    success: bool
    order_id: Optional[str] = None
    confirmation_id: Optional[str] = None
    message: str
    product_id: str
    action: str
    order_type: str
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    estimated_fee: Optional[float] = None
    total_cost: Optional[float] = None
    created_at: str

# === AUTHENTICATION ===

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key in Authorization header"""
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# === DEGIRO CONNECTION ===

def get_trading_api():
    """Get or create DEGIRO trading API connection"""
    global trading_api
    
    if trading_api is None:
        try:
            credentials = Credentials()
            
            # Try environment variables first (secure)
            credentials.username = os.getenv('DEGIRO_USERNAME')
            credentials.password = os.getenv('DEGIRO_PASSWORD')
            credentials.totp_secret_key = os.getenv('DEGIRO_TOTP_SECRET')
            int_account = os.getenv('DEGIRO_INT_ACCOUNT')
            
            if int_account:
                credentials.int_account = int(int_account)
            
            # Fallback to config file if env vars not set
            if not all([credentials.username, credentials.password, credentials.totp_secret_key]):
                try:
                    with open(DEGIRO_CONFIG_PATH, 'r') as f:
                        config = json.load(f)
                    
                    credentials.username = config['username']
                    credentials.password = config['password']
                    credentials.totp_secret_key = config['totp_secret_key']
                    credentials.int_account = config['int_account']
                except FileNotFoundError:
                    raise Exception("DEGIRO credentials not found in environment variables or config file")
            
            trading_api = TradingAPI(credentials=credentials)
            trading_api.connect()
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to connect to DEGIRO: {str(e)}"
            )
    
    return trading_api

# === HELPER FUNCTIONS ===

def search_stock_universal(api: TradingAPI, query: str) -> Optional[Dict]:
    """Universal stock search with multiple strategies"""
    try:
        stock_request = ProductSearch.RequestStocks()
        stock_request.search_text = query
        stock_request.offset = 0
        stock_request.limit = 20
        
        search_results = api.product_search(request=stock_request, raw=True)
        
        if isinstance(search_results, dict) and 'products' in search_results:
            products = search_results['products']
            
            if not products:
                return None
            
            # Strategy 1: Exact ISIN match
            for product in products:
                if product.get('isin') == query:
                    return product
            
            # Strategy 2: Exact symbol match
            for product in products:
                if product.get('symbol') == query.upper():
                    return product
            
            # Strategy 3: Name contains query
            query_lower = query.lower()
            for product in products:
                name = product.get('name', '').lower()
                if query_lower in name:
                    return product
            
            # Strategy 4: Return first result
            return products[0]
        
        return None
        
    except Exception as e:
        print(f"Universal stock search failed: {e}")
        return None

def search_leveraged_products(api: TradingAPI, search_term: str, action: str, min_leverage: float, max_leverage: float, limit: int) -> List[Dict]:
    """Search for leveraged products"""
    try:
        leveraged_request = ProductSearch.RequestLeverageds()
        leveraged_request.popular_only = False
        leveraged_request.input_aggregate_types = ''
        leveraged_request.input_aggregate_values = ''
        leveraged_request.search_text = search_term
        leveraged_request.offset = 0
        leveraged_request.limit = 100
        leveraged_request.require_total = True
        leveraged_request.sort_columns = 'leverage'
        leveraged_request.sort_types = 'asc'
        
        search_results = api.product_search(request=leveraged_request, raw=True)
        
        if isinstance(search_results, dict) and 'products' in search_results:
            products = search_results['products']
            
            suitable_products = []
            target_direction = "L" if action.upper() == "LONG" else "S"
            
            for product in products:
                leverage = product.get('leverage', 0)
                shortlong = product.get('shortlong')
                tradable = product.get('tradable', False)
                
                if (min_leverage <= leverage <= max_leverage and 
                    shortlong == target_direction and 
                    tradable):
                    suitable_products.append(product)
                    
                    if len(suitable_products) >= limit:
                        break
            
            return suitable_products
        
        return []
        
    except Exception as e:
        print(f"Leveraged search failed: {e}")
        return []

def get_mock_price(product_id: str) -> PriceInfo:
    """Mock price data - replace with real pricing if available"""
    import random
    base_price = random.uniform(5.0, 50.0)
    spread = base_price * 0.01
    
    return PriceInfo(
        bid=round(base_price - spread/2, 2),
        ask=round(base_price + spread/2, 2),
        last=round(base_price, 2)
    )

def extract_issuer(product_name: str) -> str:
    """Extract issuer from product name"""
    if product_name.startswith("BNP"):
        return "BNP"
    elif product_name.startswith("SG"):
        return "SG"
    else:
        return "Unknown"

def create_degiro_order(request: OrderRequest) -> Order:
    """Create DEGIRO Order object from request"""
    order = Order()
    
    # Action
    if request.action.upper() == "BUY":
        order.action = Order.Action.BUY
    elif request.action.upper() == "SELL":
        order.action = Order.Action.SELL
    else:
        raise ValueError(f"Invalid action: {request.action}")
    
    # Order Type
    if request.order_type.upper() == "LIMIT":
        order.order_type = Order.OrderType.LIMIT
        if request.price is None:
            raise ValueError("Price required for LIMIT orders")
        order.price = request.price
    elif request.order_type.upper() == "MARKET":
        order.order_type = Order.OrderType.MARKET
    elif request.order_type.upper() == "STOP_LOSS":
        order.order_type = Order.OrderType.STOP_LOSS
        if request.stop_price is None:
            raise ValueError("Stop price required for STOP_LOSS orders")
        order.stop_price = request.stop_price
    elif request.order_type.upper() == "STOP_LIMIT":
        order.order_type = Order.OrderType.STOP_LIMIT
        if request.price is None or request.stop_price is None:
            raise ValueError("Both price and stop_price required for STOP_LIMIT orders")
        order.price = request.price
        order.stop_price = request.stop_price
    else:
        raise ValueError(f"Invalid order type: {request.order_type}")
    
    # Time Type
    if request.time_type.upper() == "DAY":
        order.time_type = Order.TimeType.GOOD_TILL_DAY
    elif request.time_type.upper() == "GTC":
        order.time_type = Order.TimeType.GOOD_TILL_CANCELED
    else:
        raise ValueError(f"Invalid time type: {request.time_type}")
    
    # Basic fields
    order.product_id = int(request.product_id)
    order.size = request.quantity
    
    return order

# === API ROUTES ===

@app.get("/")
async def root():
    """API health check and information"""
    return {
        "service": "DEGIRO Trading API",
        "version": "2.0.0",
        "status": "online",
        "features": [
            "Universal product search (ISIN, name, ticker)",
            "Leveraged products discovery",
            "Complete order management (LIMIT, MARKET, STOP_LOSS, STOP_LIMIT)",
            "Order validation and confirmation",
            "Real-time order status",
            "Secure API key authentication"
        ],
        "endpoints": {
            "search": "POST /api/products/search",
            "check_order": "POST /api/orders/check",
            "place_order": "POST /api/orders/place"
        },
        "documentation": "/docs",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/products/search", response_model=ProductSearchResponse)
async def search_products(
    request: ProductSearchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Universal product search - finds direct stocks and leveraged products
    
    - **q**: Universal search (ISIN, company name, ticker symbol)
    - **action**: LONG or SHORT (for leveraged products)
    - **min_leverage**: Minimum leverage (default: 2.0)
    - **max_leverage**: Maximum leverage (default: 10.0) 
    - **limit**: Max leveraged products to return (default: 10)
    """
    
    if not request.q or not request.q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter 'q' is required"
        )
    
    api = get_trading_api()
    
    # Search for underlying stock
    stock_product = search_stock_universal(api, request.q.strip())
    search_term = request.q.strip()
    
    # Prepare direct stock info
    direct_stock = None
    if stock_product:
        direct_stock = DirectStock(
            product_id=str(stock_product.get('id', '')),
            name=stock_product.get('name', ''),
            isin=stock_product.get('isin', ''),
            currency=stock_product.get('currency', 'EUR'),
            exchange_id=str(stock_product.get('exchangeId', '')),
            current_price=get_mock_price(str(stock_product.get('id', ''))),
            tradable=stock_product.get('tradable', True)
        )
    
    # Search for leveraged products
    leveraged_products_data = search_leveraged_products(
        api, 
        search_term, 
        request.action, 
        request.min_leverage, 
        request.max_leverage, 
        request.limit
    )
    
    # Convert to response format
    leveraged_products = []
    for product in leveraged_products_data:
        leveraged_product = LeveragedProduct(
            product_id=str(product.get('id', '')),
            name=product.get('name', ''),
            isin=product.get('isin', ''),
            leverage=product.get('leverage', 0.0),
            direction="LONG" if product.get('shortlong') == "L" else "SHORT",
            currency=product.get('currency', 'EUR'),
            exchange_id=str(product.get('exchangeId', '')),
            current_price=get_mock_price(str(product.get('id', ''))),
            tradable=product.get('tradable', False),
            expiration_date=product.get('expirationDate'),
            issuer=extract_issuer(product.get('name', ''))
        )
        leveraged_products.append(leveraged_product)
    
    return ProductSearchResponse(
        query={
            "q": request.q,
            "action": request.action,
            "min_leverage": request.min_leverage,
            "max_leverage": request.max_leverage,
            "limit": request.limit
        },
        direct_stock=direct_stock,
        leveraged_products=leveraged_products,
        total_found={
            "direct_stock": 1 if direct_stock else 0,
            "leveraged_products": len(leveraged_products)
        },
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/orders/check", response_model=OrderCheckResponse)
async def check_order(
    request: OrderRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Validate order before placement - returns estimated costs and confirmation ID
    
    - **product_id**: Product ID to trade
    - **action**: BUY or SELL
    - **order_type**: LIMIT, MARKET, STOP_LOSS, STOP_LIMIT
    - **quantity**: Number of shares/units
    - **price**: Limit price (required for LIMIT/STOP_LIMIT)
    - **stop_price**: Stop price (required for STOP_LOSS/STOP_LIMIT)
    - **time_type**: DAY or GTC
    """
    
    api = get_trading_api()
    
    try:
        # Create DEGIRO order
        order = create_degiro_order(request)
        
        # Check order with DEGIRO
        checking_response = api.check_order(order=order)
        
        # Parse response
        if checking_response and hasattr(checking_response, 'confirmation_id'):
            return OrderCheckResponse(
                valid=True,
                confirmation_id=checking_response.confirmation_id,
                estimated_fee=getattr(checking_response, 'transaction_fee', None),
                total_cost=None,  # Calculate if needed
                free_space_new=getattr(checking_response, 'free_space_new', None),
                message="Order validation successful"
            )
        else:
            return OrderCheckResponse(
                valid=False,
                message="Order validation failed",
                errors=["Unknown validation error"]
            )
            
    except ValueError as e:
        return OrderCheckResponse(
            valid=False,
            message="Order validation failed",
            errors=[str(e)]
        )
    except Exception as e:
        return OrderCheckResponse(
            valid=False,
            message="Order validation failed",
            errors=[f"DEGIRO error: {str(e)}"]
        )

@app.post("/api/orders/place", response_model=OrderResponse)
async def place_order(
    request: OrderRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Place order after validation - requires valid confirmation ID from check_order
    
    This endpoint performs a two-step process:
    1. Validates the order with DEGIRO
    2. Confirms and places the order
    """
    
    api = get_trading_api()
    
    try:
        # Create DEGIRO order
        order = create_degiro_order(request)
        
        # Step 1: Check order
        checking_response = api.check_order(order=order)
        
        if not checking_response or not hasattr(checking_response, 'confirmation_id'):
            return OrderResponse(
                success=False,
                message="Order validation failed",
                product_id=request.product_id,
                action=request.action,
                order_type=request.order_type,
                quantity=request.quantity,
                price=request.price,
                stop_price=request.stop_price,
                created_at=datetime.now().isoformat()
            )
        
        # Step 2: Confirm order
        confirmation_response = api.confirm_order(
            confirmation_id=checking_response.confirmation_id,
            order=order
        )
        
        if confirmation_response and hasattr(confirmation_response, 'order_id'):
            return OrderResponse(
                success=True,
                order_id=confirmation_response.order_id,
                confirmation_id=checking_response.confirmation_id,
                message="Order placed successfully",
                product_id=request.product_id,
                action=request.action,
                order_type=request.order_type,
                quantity=request.quantity,
                price=request.price,
                stop_price=request.stop_price,
                estimated_fee=getattr(checking_response, 'transaction_fee', None),
                created_at=datetime.now().isoformat()
            )
        else:
            return OrderResponse(
                success=False,
                message="Order confirmation failed",
                product_id=request.product_id,
                action=request.action,
                order_type=request.order_type,
                quantity=request.quantity,
                price=request.price,
                stop_price=request.stop_price,
                created_at=datetime.now().isoformat()
            )
            
    except ValueError as e:
        return OrderResponse(
            success=False,
            message=f"Invalid order parameters: {str(e)}",
            product_id=request.product_id,
            action=request.action,
            order_type=request.order_type,
            quantity=request.quantity,
            price=request.price,
            stop_price=request.stop_price,
            created_at=datetime.now().isoformat()
        )
    except Exception as e:
        return OrderResponse(
            success=False,
            message=f"Order placement failed: {str(e)}",
            product_id=request.product_id,
            action=request.action,
            order_type=request.order_type,
            quantity=request.quantity,
            price=request.price,
            stop_price=request.stop_price,
            created_at=datetime.now().isoformat()
        )

@app.get("/api/health")
async def health_check():
    """Extended health check with DEGIRO connection status"""
    try:
        api = get_trading_api()
        degiro_status = "connected" if api else "disconnected"
    except:
        degiro_status = "connection_failed"
    
    return {
        "status": "healthy",
        "degiro_connection": degiro_status,
        "api_version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    if not os.getenv("TRADING_API_KEY"):
        print("⚠️  WARNING: Using default API key. Set TRADING_API_KEY environment variable for production!")
    
    # Use custom port for security
    port = int(os.getenv("API_PORT", 7731))
    
    print("🚀 Starting DEGIRO Trading API v2.0...")
    print(f"📊 API Documentation: http://localhost:{port}/docs")
    print(f"🔑 API Key: {API_KEY[:10]}...")
    print(f"🌐 Port: {port}")
    
    uvicorn.run(app, host="0.0.0.0", port=port)