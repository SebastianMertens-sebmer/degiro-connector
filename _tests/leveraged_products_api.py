#!/usr/bin/env python3
"""
Leveraged Products Trading API
Searches for knockout certificates (leveraged products) with 4-5x leverage
Places 200 EUR orders and returns execution details including vwd_ids
"""

import json
import sys
from typing import Dict, List, Optional, Tuple
from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.trading_pb2 import Credentials, ProductSearch, Order, ProductsInfo

def connect_to_degiro() -> TradingAPI:
    """Connect to DEGIRO using saved credentials"""
    with open('config/config.json', 'r') as f:
        config = json.load(f)
    
    credentials = Credentials()
    credentials.username = config['username']
    credentials.password = config['password']
    credentials.totp_secret_key = config['totp_secret_key']
    credentials.int_account = config['int_account']
    
    trading_api = TradingAPI(credentials=credentials)
    trading_api.connect()
    return trading_api

def search_underlying_stock(trading_api: TradingAPI, stock_identifier: str) -> Optional[Dict]:
    """
    Search for the underlying stock by name/ticker/ISIN
    Returns stock info needed for leveraged product search
    """
    print(f"🔍 Searching for underlying stock: {stock_identifier}")
    
    # Try lookup by name/ticker first
    lookup_request = ProductSearch.RequestLookup()
    lookup_request.search_text = stock_identifier
    lookup_request.limit = 10
    lookup_request.offset = 0
    lookup_request.product_type_id = 1  # Stocks
    
    try:
        search_results = trading_api.product_search(request=lookup_request, raw=True)
        
        if isinstance(search_results, dict) and 'products' in search_results:
            for product in search_results['products']:
                name = product.get('name', '').upper()
                symbol = product.get('symbol', '').upper()
                isin = product.get('isin', '').upper()
                
                # Check if this matches our search
                search_upper = stock_identifier.upper()
                if (search_upper in name or 
                    search_upper == symbol or 
                    search_upper == isin):
                    
                    print(f"   ✅ Found underlying: {product.get('name')} ({product.get('symbol')})")
                    return {
                        'id': product.get('id'),
                        'name': product.get('name'),
                        'symbol': product.get('symbol'),
                        'isin': product.get('isin'),
                        'vwd_id': product.get('vwdId') or product.get('vwdIdSecondary'),
                    }
        
        print(f"   ❌ No underlying stock found for: {stock_identifier}")
        return None
        
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
        return None

def fetch_product_prices(trading_api: TradingAPI, product_ids: List[int]) -> Dict[int, Dict]:
    """
    Fetch current prices for leveraged products using proper ProductsInfo.Request
    Returns dict mapping product_id to price data
    """
    try:
        print(f"💰 Fetching prices for {len(product_ids)} products...")
        
        # Create proper ProductsInfo.Request
        request = ProductsInfo.Request()
        request.products.extend(product_ids)
        
        # Get product info which includes pricing data
        products_info = trading_api.get_products_info(request=request, raw=True)
        
        price_data = {}
        if isinstance(products_info, dict) and 'data' in products_info:
            for product_id_str, data in products_info['data'].items():
                product_id = int(product_id_str)
                
                
                # Extract price fields - check many possible field names
                last_price = (data.get('lastPrice') or data.get('last_price') or 
                             data.get('price') or data.get('value'))
                bid_price = (data.get('bidPrice') or data.get('bid_price') or 
                            data.get('bid') or data.get('bidValue'))
                ask_price = (data.get('askPrice') or data.get('ask_price') or 
                            data.get('ask') or data.get('askValue'))
                close_price = (data.get('closePrice') or data.get('close_price') or 
                              data.get('previousClose') or data.get('closingPrice'))
                
                price_data[product_id] = {
                    'last_price': last_price,
                    'bid_price': bid_price, 
                    'ask_price': ask_price,
                    'close_price': close_price,
                }
                
                
        print(f"   ✅ Retrieved price data for {len(price_data)} products")
        return price_data
        
    except Exception as e:
        print(f"   ❌ Price fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return {}

def search_leveraged_products(trading_api: TradingAPI, underlying_stock: Dict, target_leverage: float = 4.5) -> List[Dict]:
    """
    Search for leveraged products (knockout certificates) for the underlying stock
    Direct filtering by underlying product ID - much more efficient!
    """
    underlying_id = underlying_stock['id']
    print(f"🔍 Searching leveraged products for {underlying_stock['name']}...")
    print(f"   Target leverage: {target_leverage}x")
    print(f"   🎯 Using underlying ID: {underlying_id} (direct filtering)")
    
    # Use direct underlying product ID filtering - much more efficient than text search
    leveraged_request = ProductSearch.RequestLeverageds()
    leveraged_request.popular_only = False
    leveraged_request.input_aggregate_types = f'underlying:{underlying_id}'  # Filter by underlying ID
    leveraged_request.input_aggregate_values = underlying_id
    leveraged_request.search_text = ''  # No text search needed
    leveraged_request.offset = 0
    leveraged_request.limit = 200  # Get more results
    leveraged_request.require_total = True
    leveraged_request.sort_columns = 'leverage'  # Sort by leverage for better targeting
    leveraged_request.sort_types = 'asc'
    
    try:
        search_results = trading_api.product_search(request=leveraged_request, raw=True)
        
        if isinstance(search_results, dict) and 'products' in search_results:
            products = search_results['products']
            print(f"   📊 Found {len(products)} leveraged products for {underlying_stock['name']}")
            
            leveraged_products = []
            
            for product in products:
                leverage = product.get('leverage', 0)
                leverage_float = float(leverage) if leverage else 0
                
                # Filter for reasonable leverage range (2-15x)
                if (leverage_float >= 2.0 and leverage_float <= 15.0 and 
                    product.get('tradable', False) and 
                    product.get('shortlong', 'L') == 'L'):  # Only Long positions
                    
                    leveraged_products.append({
                        'id': product.get('id'),
                        'name': product.get('name', 'N/A'),
                        'isin': product.get('isin', 'N/A'),
                        'leverage': leverage_float,
                        'financing_level': product.get('financingLevel', 0),
                        'shortlong': product.get('shortlong', 'L'),
                        'expiry': product.get('expirationDate', 'N/A'),
                        'currency': product.get('currency', 'EUR'),
                        'vwd_id': product.get('vwdId'),
                        'underlying_product_id': product.get('underlying_product_id'),
                        'tradable': product.get('tradable', False),
                        'issuer_id': product.get('issuer_id', 'N/A'),
                        'ratio': product.get('ratio', 1),
                    })
            
            
            if leveraged_products:
                # Sort by leverage preference (4-5x first, then closest to target)
                def leverage_priority(product):
                    lev = product['leverage']
                    if 4.0 <= lev <= 5.0:
                        return (0, abs(lev - target_leverage))  # Highest priority
                    elif 3.0 <= lev < 4.0:
                        return (1, abs(lev - target_leverage))  # Second priority
                    elif 5.0 < lev <= 7.0:
                        return (2, abs(lev - target_leverage))  # Third priority
                    else:
                        return (3, abs(lev - target_leverage))  # Lowest priority
                
                leveraged_products.sort(key=leverage_priority)
                
                # Fetch prices for top candidates (first 10)
                top_products = leveraged_products[:10]
                product_ids = [int(p['id']) for p in top_products]
                price_data = fetch_product_prices(trading_api, product_ids)
                
                # Add price data to products
                for product in top_products:
                    if int(product['id']) in price_data:
                        product.update(price_data[int(product['id'])])
                
                print(f"   ✅ Found {len(leveraged_products)} suitable leveraged products")
                for i, product in enumerate(leveraged_products[:5]):  # Show top 5 
                    price = product.get('last_price') or product.get('ask_price') or product.get('bid_price')
                    print(f"      {i+1}. Leverage: {product['leverage']}x - {product['name']}")
                    print(f"         ISIN: {product['isin']}, VWD ID: {product['vwd_id']}")
                    print(f"         Price: €{price if price else 'Fallback'}")
                
                return leveraged_products
            else:
                print(f"   ❌ No suitable leveraged products found (tradable, long positions)")
                return []
        
        print("   ❌ No leveraged products found in response")
        return []
        
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def calculate_order_quantity(price: float, order_amount: float = 200.0) -> Tuple[int, float]:
    """
    Calculate how many shares to buy with the given amount
    Returns (quantity, actual_amount_spent)
    """
    if price <= 0:
        return 0, 0.0
    
    quantity = int(order_amount / price)
    actual_amount = quantity * price
    
    return max(1, quantity), actual_amount  # At least 1 share

def place_leveraged_order(trading_api: TradingAPI, product: Dict, order_amount: float = 200.0) -> Optional[Dict]:
    """
    Place an order for the leveraged product with the specified amount
    Returns order details including execution info
    """
    print(f"📝 Placing order for {product['name']}")
    print(f"   Leverage: {product['leverage']}x")
    print(f"   Target amount: €{order_amount}")
    
    # Determine current price to use for calculation
    current_price = product.get('last_price') or product.get('ask_price') or product.get('bid_price') or product.get('close_price')
    
    if not current_price:
        print("   ⚠️ No real-time price available from get_products_info")
        print("   💡 Real-time pricing requires VWD subscription or quotecast API")
        print("   🔄 Using estimated price based on leverage and underlying")
        
        # Estimate price based on typical knockout certificate pricing (€5-15 range)
        # This is just for testing - in production, real-time pricing is essential
        estimated_price = 8.50  # Reasonable middle estimate for leveraged products
        current_price = estimated_price
        
        print(f"   ⚠️ ESTIMATED price (for testing): €{current_price}")
        print("   🚨 WARNING: Using estimated pricing - not suitable for production trading!")
    else:
        print(f"   💰 Real-time price: €{current_price}")
    
    # Calculate quantity based on current price
    quantity, actual_amount = calculate_order_quantity(current_price, order_amount)
    
    # Calculate limit price (current price + 2%)
    limit_price = current_price * 1.02
    
    print(f"   📊 Quantity: {quantity} shares")
    print(f"   💶 Actual amount: €{actual_amount:.2f}")
    print(f"   📈 Limit price: €{limit_price:.4f} (+2%)")
    
    # Create order
    order = Order()
    order.action = Order.Action.BUY
    order.order_type = Order.OrderType.LIMIT
    order.price = limit_price  # Current price + 2% for execution
    order.product_id = int(product['id'])  # Ensure product_id is integer
    order.size = quantity
    order.time_type = Order.TimeType.GOOD_TILL_DAY
    
    try:
        print("🔍 Checking order...")
        checking_response = trading_api.check_order(order=order)
        
        if checking_response:
            print("✅ Order check successful!")
            
            if hasattr(checking_response, 'confirmation_id'):
                confirmation_id = checking_response.confirmation_id
                transaction_fees = getattr(checking_response, 'transaction_fees', 0)
            else:
                confirmation_id = checking_response.get('confirmation_id')
                transaction_fees = checking_response.get('transaction_fees', 0)
            
            print(f"   • Confirmation ID: {confirmation_id}")
            print(f"   • Transaction fees: €{transaction_fees}")
            
            # Auto-confirm for API usage
            print("✅ Auto-confirming order...")
            confirmation_response = trading_api.confirm_order(
                confirmation_id=confirmation_id,
                order=order
            )
            
            if confirmation_response:
                if hasattr(confirmation_response, 'order_id'):
                    order_id = confirmation_response.order_id
                else:
                    order_id = confirmation_response.get('order_id')
                
                print(f"🎉 Order placed successfully! ID: {order_id}")
                
                return {
                    'order_id': order_id,
                    'product_id': product['id'],
                    'vwd_id': product['vwd_id'],
                    'product_name': product['name'],
                    'leverage': product['leverage'],
                    'quantity': quantity,
                    'current_price': current_price,
                    'limit_price': order.price,
                    'actual_amount': actual_amount,
                    'transaction_fees': transaction_fees,
                    'currency': product['currency'],
                    'confirmation_id': confirmation_id
                }
            else:
                print("❌ Order confirmation failed")
                return None
        else:
            print("❌ Order check failed")
            return None
            
    except Exception as e:
        print(f"❌ Order placement failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def leveraged_trading_api(stock_identifier: str, order_amount: float = 200.0, target_leverage: float = 4.5) -> Dict:
    """
    Main API function for leveraged trading
    
    Args:
        stock_identifier: Stock name, ticker, or ISIN
        order_amount: Amount in EUR to invest (default: 200)
        target_leverage: Target leverage (default: 4.5, will fallback to lower)
    
    Returns:
        Dictionary with execution details including vwd_ids and amounts
    """
    try:
        # Connect to DEGIRO
        trading_api = connect_to_degiro()
        
        # 1. Find underlying stock
        underlying = search_underlying_stock(trading_api, stock_identifier)
        if not underlying:
            return {
                'success': False,
                'error': f'Underlying stock not found: {stock_identifier}',
                'stock_identifier': stock_identifier
            }
        
        # 2. Search leveraged products
        leveraged_products = search_leveraged_products(trading_api, underlying, target_leverage)
        if not leveraged_products:
            return {
                'success': False,
                'error': f'No leveraged products found for: {underlying["name"]}',
                'underlying': underlying
            }
        
        # 3. Select best leveraged product (first in sorted list)
        selected_product = leveraged_products[0]
        
        # 4. Place order
        order_result = place_leveraged_order(trading_api, selected_product, order_amount)
        if not order_result:
            return {
                'success': False,
                'error': 'Order placement failed',
                'underlying': underlying,
                'selected_product': {
                    'name': selected_product['name'],
                    'leverage': selected_product['leverage'],
                    'id': selected_product['id']
                }
            }
        
        # 5. Return success response
        return {
            'success': True,
            'underlying': underlying,
            'leveraged_product': {
                'id': selected_product['id'],
                'vwd_id': selected_product['vwd_id'],
                'name': selected_product['name'],
                'leverage': selected_product['leverage'],
                'isin': selected_product['isin']
            },
            'order': {
                'order_id': order_result['order_id'],
                'quantity': order_result['quantity'],
                'current_price': order_result['current_price'],
                'limit_price': order_result['limit_price'],
                'actual_amount': order_result['actual_amount'],
                'transaction_fees': order_result['transaction_fees'],
                'currency': order_result['currency']
            },
            'execution_summary': f"{order_result['quantity']} shares at limit €{order_result['limit_price']:.4f} (current: €{order_result['current_price']:.4f}) = €{order_result['actual_amount']:.2f}"
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'API error: {str(e)}',
            'stock_identifier': stock_identifier
        }

def main():
    """Command line interface for testing"""
    if len(sys.argv) < 2:
        print("Usage: python leveraged_products_api.py <stock_identifier> [order_amount] [target_leverage]")
        print("Example: python leveraged_products_api.py GOOGL 200 4.5")
        sys.exit(1)
    
    stock_identifier = sys.argv[1]
    order_amount = float(sys.argv[2]) if len(sys.argv) > 2 else 200.0
    target_leverage = float(sys.argv[3]) if len(sys.argv) > 3 else 4.5
    
    print("🚀 Leveraged Products Trading API")
    print("=" * 50)
    print(f"Stock: {stock_identifier}")
    print(f"Order Amount: €{order_amount}")
    print(f"Target Leverage: {target_leverage}x")
    print()
    
    # Execute API
    result = leveraged_trading_api(stock_identifier, order_amount, target_leverage)
    
    # Print results
    print("\n📋 API Response:")
    print("=" * 30)
    print(json.dumps(result, indent=2, default=str))
    
    if result['success']:
        print(f"\n🎉 SUCCESS!")
        print(f"   • Underlying: {result['underlying']['name']}")
        print(f"   • Leveraged Product: {result['leveraged_product']['name']}")
        print(f"   • Leverage: {result['leveraged_product']['leverage']}x")
        print(f"   • VWD ID: {result['leveraged_product']['vwd_id']}")
        print(f"   • Order: {result['execution_summary']}")
        print(f"   • Order ID: {result['order']['order_id']}")
        print(f"   • Current Price: €{result['order']['current_price']:.4f}")
        print(f"   • Limit Price: €{result['order']['limit_price']:.4f} (+2%)")
    else:
        print(f"\n❌ FAILED: {result['error']}")

if __name__ == "__main__":
    main()