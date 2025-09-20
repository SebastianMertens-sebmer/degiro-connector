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
from degiro_connector.trading.models.credentials import Credentials
from degiro_connector.trading.models.product_search import StocksRequest, LeveragedsRequest
from degiro_connector.trading.models.order import Order

# Load environment variables
load_dotenv('config/.env')

# FastAPI app
app = FastAPI(
    title="DEGIRO Trading API",
    description="Production API for DEGIRO trading: search products, place orders, manage positions",
    version="2.0.0",
    docs_url=None,  # Disable public docs
    redoc_url=None  # Disable public redoc
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
API_KEY = os.getenv("TRADING_API_KEY")
if not API_KEY:
    raise Exception("TRADING_API_KEY environment variable is required")

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

# NEW API MODELS

# Stock Search Models
class StockSearchRequest(BaseModel):
    q: str = Field(..., description="Search query - ISIN, company name, ticker, or symbol")
    limit: int = Field(default=50, description="Maximum number of stocks to return")

class StockOption(BaseModel):
    product_id: str
    name: str
    isin: str
    symbol: Optional[str] = None
    currency: str
    exchange_id: str
    current_price: PriceInfo
    tradable: bool

class StockSearchResponse(BaseModel):
    query: str
    stocks: List[StockOption]
    total_found: int
    timestamp: str

# Leveraged Products Search Models
class LeveragedSearchRequest(BaseModel):
    underlying_id: str = Field(..., description="Stock product ID from stocks search")
    action: str = Field(default="LONG", description="LONG or SHORT")
    min_leverage: float = Field(default=2.0, description="Minimum leverage")
    max_leverage: float = Field(default=10.0, description="Maximum leverage")
    limit: int = Field(default=50, description="Max leveraged products to return")
    issuer_id: Optional[int] = Field(default=None, description="Issuer filter (-1=all)")
    product_subtype: str = Field(default="ALL", description="Product subtype filter: ALL, CALL_PUT (Optionsscheine), MINI (Knockouts), UNLIMITED (Faktor)")

class LeveragedSearchResponse(BaseModel):
    query: Dict[str, Any]
    underlying_stock: StockOption
    leveraged_products: List[LeveragedProduct]
    total_found: int
    timestamp: str

# Legacy combined search (deprecated)
class ProductSearchRequest(BaseModel):
    q: str = Field(..., description="Universal search - ISIN, company name, ticker, or symbol")
    action: str = Field(default="LONG", description="LONG or SHORT")
    min_leverage: float = Field(default=2.0, description="Minimum leverage")
    max_leverage: float = Field(default=10.0, description="Maximum leverage")
    limit: int = Field(default=50, description="Max leveraged products to return")
    
    # Enhanced leveraged product parameters
    product_type: Optional[int] = Field(default=None, description="Product type (14=leveraged)")
    sub_product_type: Optional[int] = Field(default=None, description="Sub product type (14=leveraged)")
    short_long: Optional[int] = Field(default=None, description="Direction filter (-1=all, 1=LONG, 0=SHORT)")
    issuer_id: Optional[int] = Field(default=None, description="Issuer filter (-1=all)")
    underlying_id: Optional[int] = Field(default=None, description="Underlying stock product ID")

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
            # Try environment variables first (secure)
            username = os.getenv('DEGIRO_USERNAME')
            password = os.getenv('DEGIRO_PASSWORD')
            totp_secret_key = os.getenv('DEGIRO_TOTP_SECRET')
            int_account = os.getenv('DEGIRO_INT_ACCOUNT')
            
            # Create credentials with pydantic syntax
            credentials_data = {
                'username': username,
                'password': password,
                'totp_secret_key': totp_secret_key
            }
            
            if int_account:
                credentials_data['int_account'] = int(int_account)
                
            credentials = Credentials(**credentials_data)
            
            # Fallback to config file if env vars not set
            if not all([username, password, totp_secret_key]):
                try:
                    with open(DEGIRO_CONFIG_PATH, 'r') as f:
                        config = json.load(f)
                    
                    credentials = Credentials(
                        username=config['username'],
                        password=config['password'],
                        totp_secret_key=config['totp_secret_key'],
                        int_account=config['int_account']
                    )
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

# === DYNAMIC LEVERAGED SEARCH ===

# === HELPER FUNCTIONS ===

def extract_leverage_from_name(product_name: str) -> Optional[float]:
    """Extract leverage value from product name"""
    import re
    if not product_name:
        return None
    
    # Look for patterns like "LV 2.44", "Leverage 5.0", etc.
    patterns = [
        r'LV\s+(\d+\.?\d*)',
        r'leverage\s+(\d+\.?\d*)',
        r'x(\d+\.?\d*)',
        r'(\d+\.?\d*)x'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, product_name, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    
    return None

def search_stocks_multiple(api: TradingAPI, query: str, limit: int = 20) -> List[Dict]:
    """Search for multiple stocks - returns ALL matching options"""
    try:
        stock_request = StocksRequest(
            search_text=query,
            offset=0,
            limit=limit,
            require_total=True,
            sort_columns="name",
            sort_types="asc"
        )
        
        search_results = api.product_search(stock_request, raw=True)
        
        if isinstance(search_results, dict) and 'products' in search_results:
            products = search_results['products']
            return products if products else []
        
        return []
        
    except Exception as e:
        print(f"Stock search failed: {e}")
        return []

def search_stock_universal(api: TradingAPI, query: str) -> Optional[Dict]:
    """Universal stock search with multiple strategies (legacy function)"""
    try:
        stock_request = StocksRequest(
            search_text=query,
            offset=0,
            limit=20,
            require_total=True,
            sort_columns="name",
            sort_types="asc"
        )
        
        search_results = api.product_search(stock_request, raw=True)
        
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

def search_leveraged_products_dynamic(api: TradingAPI, stock_product: Optional[Dict], request: ProductSearchRequest) -> List[Dict]:
    """Dynamic leveraged products search - uses stock product ID as underlying ID"""
    try:
        # Use provided underlying_id or get from stock search
        underlying_id = request.underlying_id
        if not underlying_id and stock_product:
            try:
                underlying_id = int(stock_product.get('id'))
            except (ValueError, TypeError):
                return []
        
        if not underlying_id:
            return []
        
        # RESTORED: Complete LeveragedsRequest from working commit 513b531
        leveraged_request = LeveragedsRequest(
            popular_only=False,
            input_aggregate_types="",
            input_aggregate_values="",
            search_text=request.q,
            offset=0,
            limit=100,
            require_total=True,
            sort_columns="leverage",
            sort_types="asc"
        )
        
        search_results = api.product_search(leveraged_request, raw=True)
        
        if isinstance(search_results, dict) and 'products' in search_results:
            products = search_results['products']
            
            suitable_products = []
            target_direction = "L" if request.action.upper() == "LONG" else "S"
            
            for product in products:
                # Use DEGIRO fields for reliable filtering
                leverage = product.get('leverage', 0)
                shortlong = product.get('shortlong')
                tradable = product.get('tradable', False)
                
                # Filter by leverage range, direction, and tradability
                if (request.min_leverage <= leverage <= request.max_leverage and 
                    shortlong == target_direction and 
                    tradable):
                    suitable_products.append(product)
                
                if len(suitable_products) >= request.limit:
                    break
            
            return suitable_products
        
        return []
        
    except Exception as e:
        return []

def search_leveraged_products(api: TradingAPI, search_term: str, action: str, min_leverage: float, max_leverage: float, limit: int) -> List[Dict]:
    """Search for leveraged products"""
    try:
        leveraged_request = LeveragedsRequest(
            popular_only=False,
            input_aggregate_types="",
            input_aggregate_values="",
            search_text=search_term,
            offset=0,
            limit=100,
            require_total=True,
            sort_columns="leverage",
            sort_types="asc"
        )
        
        search_results = api.product_search(leveraged_request, raw=True)
        
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

def get_real_prices_batch(product_ids: list[str]) -> dict[str, PriceInfo]:
    """Get real price data for multiple products from DEGIRO using quotecast API"""
    try:
        # First get user token from config file
        try:
            with open(DEGIRO_CONFIG_PATH, 'r') as f:
                config_dict = json.load(f)
            user_token = config_dict.get("user_token")
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Unable to load user token from config: {str(e)}"
            )
        
        if not user_token:
            raise HTTPException(
                status_code=503,
                detail="No valid user token found in config for real-time pricing"
            )

        # Get trading API instance to fetch product metadata
        api = get_trading_api()
        
        # Get product info for all products to determine vwdIds
        product_info = api.get_products_info(
            product_list=[int(pid) for pid in product_ids],
            raw=True
        )
        
        if not isinstance(product_info, dict) or 'data' not in product_info:
            raise HTTPException(
                status_code=503,
                detail="Unable to fetch product metadata"
            )
        
        # Build vwdId mapping for products that support real-time pricing
        vwd_id_to_product_id = {}
        valid_product_ids = []
        
        for product_id in product_ids:
            product_data = product_info['data'].get(str(product_id))
            if product_data:
                vwd_id = product_data.get('vwdId')
                if vwd_id:
                    vwd_id_to_product_id[vwd_id] = product_id
                    valid_product_ids.append(product_id)
        
        if not vwd_id_to_product_id:
            return {}  # No products support real-time pricing
        
        # Import quotecast components
        from degiro_connector.quotecast.models.ticker import TickerRequest
        from degiro_connector.quotecast.tools.ticker_fetcher import TickerFetcher
        from degiro_connector.quotecast.tools.ticker_to_df import TickerToDF
        import pandas as pd
        
        # Build session and get session ID
        session = TickerFetcher.build_session()
        session_id = TickerFetcher.get_session_id(user_token=user_token)
        
        if not session_id:
            raise HTTPException(
                status_code=503,
                detail="Unable to establish quotecast session"
            )
        
        # Create ticker request for all products with vwdIds
        request_map = {}
        for vwd_id in vwd_id_to_product_id.keys():
            request_map[vwd_id] = ["LastPrice", "BidPrice", "AskPrice"]
        
        ticker_request = TickerRequest(
            request_type="subscription",
            request_map=request_map
        )
        
        # Subscribe and fetch ticker data
        logger = TickerFetcher.build_logger()
        
        TickerFetcher.subscribe(
            ticker_request=ticker_request,
            session_id=session_id,
            session=session,
            logger=logger,
        )
        
        ticker = TickerFetcher.fetch_ticker(
            session_id=session_id,
            session=session,
            logger=logger,
        )
        
        if not ticker:
            return {}  # No real-time data available
        
        # Parse ticker data
        ticker_to_df = TickerToDF()
        df = ticker_to_df.parse(ticker=ticker)
        
        if df is None or len(df) == 0:
            return {}  # Empty price data
        
        # Extract prices for each product
        results = {}
        pandas_df = df.to_pandas()
        
        for index, row in pandas_df.iterrows():
            last_price = row.get('LastPrice', None)
            bid_price = row.get('BidPrice', None)
            ask_price = row.get('AskPrice', None)
            
            # Only include products with valid last price
            if last_price is not None and not pd.isna(last_price):
                # Find corresponding product_id (since df doesn't include vwd_id directly)
                # We'll match by position or look for vwd_key if available
                if len(pandas_df) == len(valid_product_ids):
                    product_id = valid_product_ids[index]
                else:
                    # Fallback: try to match first valid product
                    product_id = valid_product_ids[0] if valid_product_ids else None
                
                if product_id:
                    last = float(last_price)
                    bid = float(bid_price) if bid_price is not None and not pd.isna(bid_price) else last * 0.999
                    ask = float(ask_price) if ask_price is not None and not pd.isna(ask_price) else last * 1.001
                    
                    results[product_id] = PriceInfo(
                        bid=round(bid, 2),
                        ask=round(ask, 2),
                        last=round(last, 2)
                    )
        
        return results
        
    except HTTPException:
        raise  # Re-raise HTTPException as-is
    except Exception as e:
        print(f"Batch price fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return {}  # Return empty dict instead of raising error

def get_real_price(product_id: str) -> PriceInfo:
    """Get real price data from DEGIRO using quotecast API"""
    try:
        # First get user token from trading API session
        api = get_trading_api()
        
        # Get product info to determine the correct vwdId for quotecast
        product_info = api.get_products_info(
            product_list=[int(product_id)],
            raw=True
        )
        
        if not isinstance(product_info, dict) or 'data' not in product_info:
            raise HTTPException(
                status_code=503,
                detail=f"Unable to fetch product metadata for {product_id}"
            )
            
        product_data = product_info['data'].get(str(product_id))
        if not product_data:
            raise HTTPException(
                status_code=404,
                detail=f"Product {product_id} not found"
            )
        
        # Check if product has a vwdId for real-time pricing
        vwd_id = product_data.get('vwdId')
        if not vwd_id:
            raise HTTPException(
                status_code=503,
                detail=f"Product {product_id} does not support real-time pricing (no vwdId)"
            )
        
        # Import quotecast components
        from degiro_connector.quotecast.models.ticker import TickerRequest
        from degiro_connector.quotecast.tools.ticker_fetcher import TickerFetcher
        from degiro_connector.quotecast.tools.ticker_to_df import TickerToDF
        import pandas as pd
        
        # Get user token from config file
        try:
            with open(DEGIRO_CONFIG_PATH, 'r') as f:
                config_dict = json.load(f)
            user_token = config_dict.get("user_token")
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Unable to load user token from config: {str(e)}"
            )
        
        if not user_token:
            raise HTTPException(
                status_code=503,
                detail="No valid user token found in config for real-time pricing"
            )
        
        # Build session and get session ID
        session = TickerFetcher.build_session()
        session_id = TickerFetcher.get_session_id(user_token=user_token)
        
        if not session_id:
            raise HTTPException(
                status_code=503,
                detail="Unable to establish quotecast session"
            )
        
        # Create ticker request for this product
        ticker_request = TickerRequest(
            request_type="subscription",
            request_map={
                vwd_id: [
                    "LastPrice",
                    "BidPrice", 
                    "AskPrice"
                ]
            }
        )
        
        # Subscribe and fetch ticker data
        logger = TickerFetcher.build_logger()
        
        TickerFetcher.subscribe(
            ticker_request=ticker_request,
            session_id=session_id,
            session=session,
            logger=logger,
        )
        
        ticker = TickerFetcher.fetch_ticker(
            session_id=session_id,
            session=session,
            logger=logger,
        )
        
        if not ticker:
            raise HTTPException(
                status_code=503,
                detail=f"No real-time data available for product {product_id}"
            )
        
        # Parse ticker data
        ticker_to_df = TickerToDF()
        df = ticker_to_df.parse(ticker=ticker)
        
        if df is None or df.empty:
            raise HTTPException(
                status_code=503,
                detail=f"Empty price data received for product {product_id}"
            )
        
        # Extract price data from dataframe (we only requested one product)
        if len(df) == 0:
            raise HTTPException(
                status_code=503,
                detail=f"No price data returned for product {product_id}"
            )
        
        # Get first row data
        row_dict = df.to_pandas().iloc[0].to_dict()
        last_price = row_dict.get('LastPrice', None)
        bid_price = row_dict.get('BidPrice', None) 
        ask_price = row_dict.get('AskPrice', None)
        
        # Validate that we have at least a last price
        if last_price is None or pd.isna(last_price):
            raise HTTPException(
                status_code=503,
                detail=f"No valid last price available for product {product_id}"
            )
        
        # Convert to float and handle missing bid/ask
        last = float(last_price)
        bid = float(bid_price) if bid_price is not None and not pd.isna(bid_price) else last * 0.999
        ask = float(ask_price) if ask_price is not None and not pd.isna(ask_price) else last * 1.001
        
        return PriceInfo(
            bid=round(bid, 2),
            ask=round(ask, 2),
            last=round(last, 2)
        )
        
    except HTTPException:
        raise  # Re-raise HTTPException as-is
    except Exception as e:
        print(f"Real price fetch failed for {product_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=503, 
            detail=f"Unable to fetch real-time price for product {product_id}. Error: {str(e)}"
        )

def extract_issuer(product_name: str) -> str:
    """Extract issuer from product name"""
    if product_name.startswith("BNP"):
        return "BNP"
    elif product_name.startswith("SG"):
        return "SG"
    else:
        return "Unknown"

def filter_by_product_subtype(products: list, subtype: str) -> list:
    """Filter leveraged products by subtype"""
    if subtype == "ALL":
        return products
    
    filtered_products = []
    
    for product in products:
        name = product.get('name', '').lower()
        
        if subtype == "CALL_PUT":
            # Optionsscheine: Traditional Call/Put options with STR (Strike) pattern
            if ('call str' in name or 'put str' in name) and 'mini' not in name and 'unlimited' not in name:
                filtered_products.append(product)
        
        elif subtype == "MINI":
            # Knockouts: Mini Long/Short products with Stop Loss
            if 'mini long' in name or 'mini short' in name:
                filtered_products.append(product)
        
        elif subtype == "UNLIMITED":
            # Faktor: Unlimited Long/Short products (factor certificates)
            if 'unlimited long' in name or 'unlimited short' in name:
                filtered_products.append(product)
    
    return filtered_products

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
            "stock_search": "POST /api/stocks/search",
            "leveraged_search": "POST /api/leveraged/search",
            "legacy_search": "POST /api/products/search",
            "check_order": "POST /api/orders/check",
            "place_order": "POST /api/orders/place"
        },
        "documentation": "/docs",
        "timestamp": datetime.now().isoformat()
    }

# NEW API ENDPOINTS

@app.post("/api/stocks/search", response_model=StockSearchResponse)
async def search_stocks(
    request: StockSearchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Search for stocks - returns ALL matching stock options for disambiguation
    
    - **q**: Search query (ISIN, company name, ticker, symbol)
    - **limit**: Maximum number of stocks to return (default: 50)
    
    Returns list of all matching stocks for user/agent selection.
    """
    
    if not request.q or not request.q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter 'q' is required"
        )
    
    api = get_trading_api()
    
    # Search for all matching stocks
    stock_products = search_stocks_multiple(api, request.q.strip(), request.limit)
    
    # Get real prices for all stock products in batch
    stock_product_ids = [str(product.get('id', '')) for product in stock_products if product.get('id')]
    stock_real_prices = get_real_prices_batch(stock_product_ids)
    
    # Convert to response format, excluding products without pricing data
    stock_options = []
    for product in stock_products:
        product_id = str(product.get('id', ''))
        
        # Only include products that have real pricing data
        if product_id in stock_real_prices:
            stock_option = StockOption(
                product_id=product_id,
                name=product.get('name', ''),
                isin=product.get('isin', ''),
                symbol=product.get('symbol'),
                currency=product.get('currency', 'EUR'),
                exchange_id=str(product.get('exchangeId', '')),
                current_price=stock_real_prices[product_id],
                tradable=product.get('tradable', True)
            )
            stock_options.append(stock_option)
    
    return StockSearchResponse(
        query=request.q,
        stocks=stock_options,
        total_found=len(stock_options),
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/leveraged/search", response_model=LeveragedSearchResponse)
async def search_leveraged_products(
    request: LeveragedSearchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Search for leveraged products based on specific underlying stock
    
    - **underlying_id**: Stock product ID from stocks search
    - **action**: LONG or SHORT (default: LONG)
    - **min_leverage**: Minimum leverage (default: 2.0)
    - **max_leverage**: Maximum leverage (default: 10.0)
    - **limit**: Max leveraged products to return (default: 50)
    - **product_subtype**: Filter by product type:
      - **ALL**: All leveraged products (default)
      - **CALL_PUT**: Optionsscheine (traditional call/put options)
      - **MINI**: Knockouts (mini long/short with stop loss)
      - **UNLIMITED**: Faktor certificates (unlimited long/short)
    
    Returns leveraged products for the specified underlying stock.
    """
    
    api = get_trading_api()
    
    try:
        # Get the underlying stock info first
        underlying_id_int = int(request.underlying_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid underlying_id format"
        )
    
    # Create enhanced leveraged request
    leveraged_request = LeveragedsRequest(
        popular_only=False,
        input_aggregate_types="",
        input_aggregate_values="",
        search_text="",  # Use empty search when we have underlying_id
        offset=0,
        limit=request.limit * 5,  # Get more to filter by leverage
        require_total=True,
        sort_columns="name",
        sort_types="asc",
        underlying_product_id=underlying_id_int
    )
    
    # Add direction filter
    if request.action.upper() == "LONG":
        leveraged_request.shortlong = "LONG"
    elif request.action.upper() == "SHORT":
        leveraged_request.shortlong = "SHORT"
    
    try:
        search_results = api.product_search(leveraged_request, raw=True)
        
        leveraged_products_data = []
        if isinstance(search_results, dict) and 'products' in search_results:
            products = search_results['products']
            
            target_direction = "L" if request.action.upper() == "LONG" else "S"
            
            for product in products:
                # Extract leverage from name (if available)
                leverage = extract_leverage_from_name(product.get('name', ''))
                
                # Filter by leverage range
                if leverage and request.min_leverage <= leverage <= request.max_leverage:
                    # Filter by direction in product name
                    name = product.get('name', '').upper()
                    if target_direction == "L" and ("CALL" in name or "LONG" in name or "BULL" in name):
                        leveraged_products_data.append(product)
                    elif target_direction == "S" and ("PUT" in name or "SHORT" in name or "BEAR" in name):
                        leveraged_products_data.append(product)
                
                if len(leveraged_products_data) >= request.limit:
                    break
        
        # Filter by product subtype if specified
        if hasattr(request, 'product_subtype') and request.product_subtype != "ALL":
            leveraged_products_data = filter_by_product_subtype(leveraged_products_data, request.product_subtype)
        
        # Get underlying stock info for response
        # We need to search for it since we only have the ID
        stock_request = StocksRequest(
            search_text="",  # Search by ID instead
            offset=0,
            limit=1,
            require_total=True,
            sort_columns="name",
            sort_types="asc"
        )
        
        # Get real price for the underlying stock
        underlying_prices = get_real_prices_batch([request.underlying_id])
        
        # Only create underlying stock if we have real pricing data
        underlying_stock = None
        if request.underlying_id in underlying_prices:
            underlying_stock = StockOption(
                product_id=request.underlying_id,
                name=f"Stock ID {request.underlying_id}",
                isin="Unknown",
                symbol=None,
                currency="EUR",
                exchange_id="Unknown",
                current_price=underlying_prices[request.underlying_id],
                tradable=True
            )
        
        # Get real prices for all products in batch
        product_ids = [str(product.get('id', '')) for product in leveraged_products_data if product.get('id')]
        real_prices = get_real_prices_batch(product_ids)
        
        # Convert to response format, excluding products without pricing data
        leveraged_products = []
        for product in leveraged_products_data:
            product_id = str(product.get('id', ''))
            
            # Only include products that have real pricing data
            if product_id in real_prices:
                leveraged_product = LeveragedProduct(
                    product_id=product_id,
                    name=product.get('name', ''),
                    isin=product.get('isin', ''),
                    leverage=product.get('leverage', 0.0),
                    direction="LONG" if product.get('shortlong') == "L" else "SHORT",
                    currency=product.get('currency', 'EUR'),
                    exchange_id=str(product.get('exchangeId', '')),
                    current_price=real_prices[product_id],
                    tradable=product.get('tradable', False),
                    expiration_date=product.get('expirationDate'),
                    issuer=extract_issuer(product.get('name', ''))
                )
                leveraged_products.append(leveraged_product)
        
        return LeveragedSearchResponse(
            query={
                "underlying_id": request.underlying_id,
                "action": request.action,
                "min_leverage": request.min_leverage,
                "max_leverage": request.max_leverage,
                "limit": request.limit
            },
            underlying_stock=underlying_stock,
            leveraged_products=leveraged_products,
            total_found=len(leveraged_products),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Leveraged products search failed: {str(e)}"
        )

# LEGACY ENDPOINT (deprecated but maintained for backward compatibility)
@app.post("/api/products/search", response_model=ProductSearchResponse)
async def search_products(
    request: ProductSearchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    DEPRECATED: Universal product search - use /api/stocks/search + /api/leveraged/search instead
    
    This endpoint is maintained for backward compatibility but will be removed in future versions.
    Please migrate to the new 3-endpoint workflow:
    1. POST /api/stocks/search - Get list of stocks
    2. POST /api/leveraged/search - Get leveraged products for specific stock
    3. POST /api/orders/check + /api/orders/place - Place orders
    """
    
    if not request.q or not request.q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter 'q' is required"
        )
    
    api = get_trading_api()
    
    # Search for underlying stock (unless specific underlying_id provided)
    stock_product = None
    if not request.underlying_id:
        stock_product = search_stock_universal(api, request.q.strip())
    
    # Prepare direct stock info with real pricing
    direct_stock = None
    if stock_product:
        stock_id = str(stock_product.get('id', ''))
        stock_prices = get_real_prices_batch([stock_id])
        
        # Only create DirectStock if we have real pricing data
        if stock_id in stock_prices:
            direct_stock = DirectStock(
                product_id=stock_id,
                name=stock_product.get('name', ''),
                isin=stock_product.get('isin', ''),
                currency=stock_product.get('currency', 'EUR'),
                exchange_id=str(stock_product.get('exchangeId', '')),
                current_price=stock_prices[stock_id],
                tradable=stock_product.get('tradable', True)
            )
    
    # Set short_long parameter based on action
    if request.short_long is None:
        if request.action.upper() == "SHORT":
            request.short_long = 0
        elif request.action.upper() == "LONG":
            request.short_long = 1

    # Dynamic leveraged products search - uses stock ID as underlying ID
    leveraged_products_data = search_leveraged_products_dynamic(
        api, 
        stock_product,
        request
    )
    
    # Filter by product subtype if specified
    if hasattr(request, 'product_subtype') and request.product_subtype != "ALL":
        leveraged_products_data = filter_by_product_subtype(leveraged_products_data, request.product_subtype)
    
    # Get real prices for all leveraged products in batch
    leveraged_product_ids = [str(product.get('id', '')) for product in leveraged_products_data if product.get('id')]
    leveraged_real_prices = get_real_prices_batch(leveraged_product_ids)
    
    # Convert to response format, excluding products without pricing data
    leveraged_products = []
    for product in leveraged_products_data:
        product_id = str(product.get('id', ''))
        
        # Only include products that have real pricing data
        if product_id in leveraged_real_prices:
            leveraged_product = LeveragedProduct(
                product_id=product_id,
                name=product.get('name', ''),
                isin=product.get('isin', ''),
                leverage=product.get('leverage', 0.0),
                direction="LONG" if product.get('shortlong') == "L" else "SHORT",
                currency=product.get('currency', 'EUR'),
                exchange_id=str(product.get('exchangeId', '')),
                current_price=leveraged_real_prices[product_id],
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