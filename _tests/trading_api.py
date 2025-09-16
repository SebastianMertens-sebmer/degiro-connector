#!/usr/bin/env python3
"""
FastAPI Trading API for DEGIRO leveraged products
Secure API with API key authentication
"""

import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.trading_pb2 import Credentials, ProductSearch

# FastAPI app
app = FastAPI(
    title="DEGIRO Trading API",
    description="API for searching and trading leveraged products on DEGIRO",
    version="1.0.0"
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
API_KEY = os.getenv("TRADING_API_KEY", "your-secure-api-key-here")  # Set this in environment
DEGIRO_CONFIG_PATH = "config/config.json"

# Global DEGIRO connection
trading_api = None

# Pydantic models
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

class ProductSearchResponse(BaseModel):
    query: Dict[str, Any]
    direct_stock: Optional[DirectStock]
    leveraged_products: List[LeveragedProduct]
    total_found: Dict[str, int]
    timestamp: str

class SearchRequest(BaseModel):
    q: str  # Universal search - ISIN, company name, ticker, or symbol
    action: str = "LONG"  # LONG/SHORT
    min_leverage: float = 2.0
    max_leverage: float = 10.0
    limit: int = 10

# Authentication
def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key in Authorization header"""
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# DEGIRO connection
def get_trading_api():
    """Get or create DEGIRO trading API connection"""
    global trading_api
    
    if trading_api is None:
        try:
            with open(DEGIRO_CONFIG_PATH, 'r') as f:
                config = json.load(f)
            
            credentials = Credentials()
            credentials.username = config['username']
            credentials.password = config['password']
            credentials.totp_secret_key = config['totp_secret_key']
            credentials.int_account = config['int_account']
            
            trading_api = TradingAPI(credentials=credentials)
            trading_api.connect()
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to connect to DEGIRO: {str(e)}"
            )
    
    return trading_api

def search_stock_universal(api: TradingAPI, query: str) -> Optional[Dict]:
    """Universal stock search - tries ISIN exact match first, then name/ticker search"""
    try:
        stock_request = ProductSearch.RequestStocks()
        stock_request.search_text = query
        stock_request.offset = 0
        stock_request.limit = 20  # Get more results to find best match
        
        search_results = api.product_search(request=stock_request, raw=True)
        
        if isinstance(search_results, dict) and 'products' in search_results:
            products = search_results['products']
            
            if not products:
                return None
            
            # Strategy 1: Exact ISIN match (highest priority)
            for product in products:
                if product.get('isin') == query:
                    print(f"Found exact ISIN match: {product.get('name')}")
                    return product
            
            # Strategy 2: Exact symbol/ticker match
            for product in products:
                if product.get('symbol') == query.upper():
                    print(f"Found exact symbol match: {product.get('name')}")
                    return product
            
            # Strategy 3: Name contains query (case insensitive)
            query_lower = query.lower()
            for product in products:
                name = product.get('name', '').lower()
                if query_lower in name:
                    print(f"Found name match: {product.get('name')}")
                    return product
            
            # Strategy 4: Symbol contains query
            for product in products:
                symbol = product.get('symbol', '').lower()
                if query_lower in symbol:
                    print(f"Found symbol match: {product.get('name')}")
                    return product
            
            # Strategy 5: Return best match (first result)
            print(f"Using first result: {products[0].get('name')}")
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
        leveraged_request.limit = 100  # Get more to filter
        leveraged_request.require_total = True
        leveraged_request.sort_columns = 'leverage'
        leveraged_request.sort_types = 'asc'
        
        search_results = api.product_search(request=leveraged_request, raw=True)
        
        if isinstance(search_results, dict) and 'products' in search_results:
            products = search_results['products']
            
            # Filter products
            suitable_products = []
            
            for product in products:
                leverage = product.get('leverage', 0)
                shortlong = product.get('shortlong')
                tradable = product.get('tradable', False)
                
                # Convert action to shortlong format
                target_direction = "L" if action.upper() == "LONG" else "S"
                
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

def extract_issuer(product_name: str) -> str:
    """Extract issuer from product name (BNP, SG, etc.)"""
    if product_name.startswith("BNP"):
        return "BNP"
    elif product_name.startswith("SG"):
        return "SG"
    elif "SOCIETE GENERALE" in product_name.upper():
        return "SG"
    else:
        return "Unknown"

def get_mock_price(product_id: str) -> PriceInfo:
    """Mock price data - replace with real pricing if available"""
    # In production, you'd fetch real prices here
    import random
    base_price = random.uniform(5.0, 50.0)
    spread = base_price * 0.01  # 1% spread
    
    return PriceInfo(
        bid=round(base_price - spread/2, 2),
        ask=round(base_price + spread/2, 2),
        last=round(base_price, 2)
    )

# API Routes
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "DEGIRO Trading API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/products/search", response_model=ProductSearchResponse)
async def search_products(
    request: SearchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Search for trading products (direct stock + leveraged products)
    
    Universal search: q can be ISIN, company name, ticker symbol, or any identifier
    
    Requires API key in Authorization header: Bearer your-api-key
    """
    
    if not request.q or not request.q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter 'q' is required"
        )
    
    api = get_trading_api()
    
    # Universal search for underlying stock
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
    
    # Build response
    response = ProductSearchResponse(
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
    
    return response

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
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    # Set API key from environment or use default
    if not os.getenv("TRADING_API_KEY"):
        print("⚠️  WARNING: Using default API key. Set TRADING_API_KEY environment variable for production!")
    
    print("🚀 Starting DEGIRO Trading API...")
    print(f"📊 API Documentation: http://localhost:8000/docs")
    print(f"🔑 API Key: {API_KEY}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)