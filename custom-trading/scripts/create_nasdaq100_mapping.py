#!/usr/bin/env python3
"""
Create a JSON mapping of NASDAQ 100 stocks with their DEGIRO vwdIds
"""

import json
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path to access degiro-connector
sys.path.append('/Users/sebastianmertens/Documents/GitHub/degiro-connector')

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials
from degiro_connector.trading.models.product_search import StocksRequest

# NASDAQ 100 stocks (symbol, name)
NASDAQ_100 = [
    ("AAPL", "Apple Inc."),
    ("ABNB", "Airbnb, Inc."),
    ("ADBE", "Adobe Inc."),
    ("ADI", "Analog Devices, Inc."),
    ("ADP", "Automatic Data Processing, Inc."),
    ("ADSK", "Autodesk, Inc."),
    ("AEP", "American Electric Power Company, Inc."),
    ("AMAT", "Applied Materials, Inc."),
    ("AMD", "Advanced Micro Devices, Inc."),
    ("AMGN", "Amgen Inc."),
    ("AMZN", "Amazon.com, Inc."),
    ("APP", "AppLovin Corporation"),
    ("ARM", "Arm Holdings plc"),
    ("ASML", "ASML Holding N.V."),
    ("AVGO", "Broadcom Inc."),
    ("AXON", "Axon Enterprise, Inc."),
    ("AZN", "AstraZeneca PLC"),
    ("BIIB", "Biogen Inc."),
    ("BKNG", "Booking Holdings Inc."),
    ("BKR", "Baker Hughes Company"),
    ("CCEP", "Coca-Cola Europacific Partners plc"),
    ("CDNS", "Cadence Design Systems, Inc."),
    ("CDW", "CDW Corporation"),
    ("CEG", "Constellation Energy Corporation"),
    ("CHTR", "Charter Communications, Inc."),
    ("CMCSA", "Comcast Corporation"),
    ("COST", "Costco Wholesale Corporation"),
    ("CPRT", "Copart, Inc."),
    ("CRWD", "CrowdStrike Holdings, Inc."),
    ("CSCO", "Cisco Systems, Inc."),
    ("CSGP", "CoStar Group, Inc."),
    ("CSX", "CSX Corporation"),
    ("CTAS", "Cintas Corporation"),
    ("CTSH", "Cognizant Technology Solutions Corporation"),
    ("DASH", "DoorDash, Inc."),
    ("DDOG", "Datadog, Inc."),
    ("DXCM", "DexCom, Inc."),
    ("EA", "Electronic Arts Inc."),
    ("EXC", "Exelon Corporation"),
    ("FANG", "Diamondback Energy, Inc."),
    ("FAST", "Fastenal Company"),
    ("FTNT", "Fortinet, Inc."),
    ("GEHC", "GE HealthCare Technologies Inc."),
    ("GFS", "GlobalFoundries Inc."),
    ("GILD", "Gilead Sciences, Inc."),
    ("GOOG", "Alphabet Inc. Class C"),
    ("GOOGL", "Alphabet Inc. Class A"),
    ("HON", "Honeywell International Inc."),
    ("IDXX", "IDEXX Laboratories, Inc."),
    ("INTC", "Intel Corporation"),
    ("INTU", "Intuit Inc."),
    ("ISRG", "Intuitive Surgical, Inc."),
    ("KDP", "Keurig Dr Pepper Inc."),
    ("KHC", "The Kraft Heinz Company"),
    ("KLAC", "KLA Corporation"),
    ("LIN", "Linde plc"),
    ("LRCX", "Lam Research Corporation"),
    ("LULU", "lululemon athletica inc."),
    ("MAR", "Marriott International"),
    ("MCHP", "Microchip Technology Incorporated"),
    ("MDLZ", "Mondelez International, Inc."),
    ("MELI", "MercadoLibre, Inc."),
    ("META", "Meta Platforms, Inc."),
    ("MNST", "Monster Beverage Corporation"),
    ("MRVL", "Marvell Technology, Inc."),
    ("MSFT", "Microsoft Corporation"),
    ("MSTR", "MicroStrategy Inc."),
    ("MU", "Micron Technology, Inc."),
    ("NFLX", "Netflix, Inc."),
    ("NVDA", "NVIDIA Corporation"),
    ("NXPI", "NXP Semiconductors N.V."),
    ("ODFL", "Old Dominion Freight Line, Inc."),
    ("ON", "ON Semiconductor Corporation"),
    ("ORLY", "O'Reilly Automotive, Inc."),
    ("PANW", "Palo Alto Networks, Inc."),
    ("PAYX", "Paychex, Inc."),
    ("PCAR", "PACCAR Inc."),
    ("PDD", "PDD Holdings Inc."),
    ("PEP", "PepsiCo, Inc."),
    ("PLTR", "Palantir Technologies Inc."),
    ("PYPL", "PayPal Holdings, Inc."),
    ("QCOM", "QUALCOMM Incorporated"),
    ("REGN", "Regeneron Pharmaceuticals, Inc."),
    ("ROP", "Roper Technologies, Inc."),
    ("ROST", "Ross Stores, Inc."),
    ("SBUX", "Starbucks Corporation"),
    ("SHOP", "Shopify Inc."),
    ("SNPS", "Synopsys, Inc."),
    ("TEAM", "Atlassian Corporation"),
    ("TMUS", "T-Mobile US, Inc."),
    ("TRI", "Thomson Reuters Corporation"),
    ("TSLA", "Tesla, Inc."),
    ("TTD", "The Trade Desk, Inc."),
    ("TTWO", "Take-Two Interactive Software, Inc."),
    ("TXN", "Texas Instruments Incorporated"),
    ("VRSK", "Verisk Analytics, Inc."),
    ("VRTX", "Vertex Pharmaceuticals Incorporated"),
    ("WBD", "Warner Bros. Discovery, Inc."),
    ("WDAY", "Workday, Inc."),
    ("XEL", "Xcel Energy Inc."),
    ("ZS", "Zscaler, Inc.")
]

def connect_to_degiro() -> TradingAPI:
    """Connect to DEGIRO using config"""
    print("🔗 Connecting to DEGIRO...")
    
    config_path = '/Users/sebastianmertens/Documents/GitHub/degiro-connector/custom-trading/config/config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    credentials = Credentials(
        username=config['username'],
        password=config['password'],
        totp_secret_key=config['totp_secret_key'],
        int_account=config['int_account']
    )
    
    api = TradingAPI(credentials=credentials)
    api.connect()
    print("✅ Connected to DEGIRO")
    return api

def find_degiro_info(api: TradingAPI, symbol: str, name: str) -> Optional[Dict[str, str]]:
    """Find DEGIRO product info for a stock symbol and name"""
    try:
        # Strategy 1: Search by symbol
        stock_request = StocksRequest(
            search_text=symbol,
            offset=0,
            limit=10,
            require_total=True,
            sort_columns="name",
            sort_types="asc"
        )
        
        results = api.product_search(stock_request, raw=True)
        
        if isinstance(results, dict) and 'products' in results:
            products = results['products']
            
            for product in products:
                product_symbol = product.get('symbol', '')
                
                # Exact symbol match
                if product_symbol == symbol:
                    vwd_id = product.get('vwdId', '')
                    return {
                        'degiro_id': str(product.get('id', '')),
                        'degiro_name': product.get('name', ''),
                        'degiro_symbol': product_symbol,
                        'degiro_isin': product.get('isin', ''),
                        'degiro_vwd_id': vwd_id,
                        'currency': product.get('currency', ''),
                        'exchange_id': str(product.get('exchangeId', '')),
                        'tradable': product.get('tradable', False),
                        'product_type': product.get('productType', ''),
                        'feed_quality': product.get('feedQuality', ''),
                        'search_method': 'symbol'
                    }
        
        # Strategy 2: Search by company name
        # Extract company name (remove "Inc.", "Corp.", etc. for better matching)
        search_name = name.split(',')[0]  # Remove trailing descriptions
        search_name = search_name.replace(' Inc.', '').replace(' Corp.', '').replace(' Corporation', '')
        search_name = search_name.replace(' plc', '').replace(' Ltd.', '').replace(' Company', '')
        search_name = search_name.replace(' Holdings', '').replace(' Group', '')
        
        stock_request = StocksRequest(
            search_text=search_name,
            offset=0,
            limit=20,  # More results for name search
            require_total=True,
            sort_columns="name",
            sort_types="asc"
        )
        
        results = api.product_search(stock_request, raw=True)
        
        if isinstance(results, dict) and 'products' in results:
            products = results['products']
            
            for product in products:
                product_symbol = product.get('symbol', '')
                product_name = product.get('name', '').upper()
                search_name_upper = search_name.upper()
                
                # Check if our target symbol appears or name contains key words
                if (product_symbol == symbol or 
                    search_name_upper in product_name or
                    any(word in product_name for word in search_name_upper.split() if len(word) > 3)):
                    
                    vwd_id = product.get('vwdId', '')
                    return {
                        'degiro_id': str(product.get('id', '')),
                        'degiro_name': product.get('name', ''),
                        'degiro_symbol': product_symbol,
                        'degiro_isin': product.get('isin', ''),
                        'degiro_vwd_id': vwd_id,
                        'currency': product.get('currency', ''),
                        'exchange_id': str(product.get('exchangeId', '')),
                        'tradable': product.get('tradable', False),
                        'product_type': product.get('productType', ''),
                        'feed_quality': product.get('feedQuality', ''),
                        'search_method': 'name'
                    }
        
        # Strategy 3: Alternative symbol searches for known mappings
        alternative_searches = []
        
        # Known alternative symbols/names
        if symbol == "META":
            alternative_searches = ["FB", "Facebook", "Meta Platforms"]
        elif symbol == "MU":
            alternative_searches = ["Micron"]
        elif symbol == "EA":
            alternative_searches = ["Electronic Arts"]
        elif symbol == "HON":
            alternative_searches = ["Honeywell"]
        elif symbol == "LIN":
            alternative_searches = ["Linde", "Praxair"]
        elif symbol == "ADI":
            alternative_searches = ["Analog Devices"]
        elif symbol == "APP":
            alternative_searches = ["AppLovin"]
        elif symbol == "ON":
            alternative_searches = ["ON Semi"]
        elif symbol == "MAR":
            alternative_searches = ["Marriott"]
        
        for alt_search in alternative_searches:
            stock_request = StocksRequest(
                search_text=alt_search,
                offset=0,
                limit=10,
                require_total=True,
                sort_columns="name",
                sort_types="asc"
            )
            
            results = api.product_search(stock_request, raw=True)
            
            if isinstance(results, dict) and 'products' in results:
                products = results['products']
                
                for product in products:
                    product_symbol = product.get('symbol', '')
                    product_name = product.get('name', '').upper()
                    
                    # Check for matches
                    if (product_symbol == symbol or 
                        alt_search.upper() in product_name):
                        
                        vwd_id = product.get('vwdId', '')
                        return {
                            'degiro_id': str(product.get('id', '')),
                            'degiro_name': product.get('name', ''),
                            'degiro_symbol': product_symbol,
                            'degiro_isin': product.get('isin', ''),
                            'degiro_vwd_id': vwd_id,
                            'currency': product.get('currency', ''),
                            'exchange_id': str(product.get('exchangeId', '')),
                            'tradable': product.get('tradable', False),
                            'product_type': product.get('productType', ''),
                            'feed_quality': product.get('feedQuality', ''),
                            'search_method': f'alternative:{alt_search}'
                        }
        
        return None
        
    except Exception as e:
        print(f"❌ Error searching for {symbol}: {e}")
        return None

def create_nasdaq100_mapping() -> List[Dict]:
    """Create mapping for NASDAQ 100 stocks"""
    
    # Connect to DEGIRO
    api = connect_to_degiro()
    
    # Create mapping
    mapping = []
    found_count = 0
    
    print(f"🔍 Looking up DEGIRO info for {len(NASDAQ_100)} NASDAQ 100 stocks...")
    print("=" * 80)
    
    for i, (symbol, name) in enumerate(NASDAQ_100, 1):
        print(f"[{i:3d}/{len(NASDAQ_100)}] {symbol:6s} - {name[:45]:45s}...", end="")
        
        degiro_info = find_degiro_info(api, symbol, name)
        
        if degiro_info:
            mapping.append({
                'symbol': symbol,
                'name': name,
                **degiro_info
            })
            found_count += 1
            vwd_id = degiro_info.get('degiro_vwd_id', 'N/A')
            if vwd_id:
                print(f" ✅ Found (vwdId: {vwd_id})")
            else:
                print(f" ✅ Found (no vwdId)")
        else:
            mapping.append({
                'symbol': symbol,
                'name': name,
                'degiro_id': None,
                'degiro_name': None,
                'degiro_symbol': None,
                'degiro_isin': None,
                'degiro_vwd_id': None,
                'currency': None,
                'exchange_id': None,
                'tradable': None,
                'product_type': None,
                'feed_quality': None
            })
            print(" ❌ Not found")
        
        # Progress update every 25 stocks
        if i % 25 == 0:
            print("─" * 80)
            print(f"📊 Progress: {i}/{len(NASDAQ_100)} ({found_count}/{i} found, {found_count/i*100:.1f}%)")
            print("─" * 80)
    
    print("=" * 80)
    print(f"✅ Mapping complete! Found DEGIRO data for {found_count}/{len(NASDAQ_100)} stocks ({found_count/len(NASDAQ_100)*100:.1f}%)")
    return mapping

def save_mapping(mapping: List[Dict], filename: str = "nasdaq100_degiro_mapping.json"):
    """Save mapping to JSON file"""
    output_path = f"/Users/sebastianmertens/Documents/GitHub/degiro-connector/custom-trading/docs/{filename}"
    
    # Create docs directory if it doesn't exist
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    found_stocks = [stock for stock in mapping if stock['degiro_id']]
    stocks_with_vwd = [stock for stock in found_stocks if stock['degiro_vwd_id']]
    
    result = {
        'description': 'NASDAQ 100 stocks with DEGIRO product information and vwdIds',
        'source': 'NASDAQ 100 index components',
        'total_stocks': len(mapping),
        'found_in_degiro': len(found_stocks),
        'with_vwd_id': len(stocks_with_vwd),
        'success_rate': f"{len(found_stocks)/len(mapping)*100:.1f}%",
        'vwd_coverage': f"{len(stocks_with_vwd)/len(mapping)*100:.1f}%",
        'generated_date': datetime.now().isoformat(),
        'all_stocks': mapping,
        'found_stocks_only': found_stocks,
        'stocks_with_vwd_only': stocks_with_vwd
    }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"💾 Saved mapping to {output_path}")
    return output_path

def print_summary(mapping: List[Dict]):
    """Print detailed summary of results"""
    found_stocks = [stock for stock in mapping if stock['degiro_id']]
    stocks_with_vwd = [stock for stock in found_stocks if stock['degiro_vwd_id']]
    
    print(f"\n📊 NASDAQ 100 → DEGIRO Mapping Results:")
    print(f"   📈 Total NASDAQ 100 stocks: {len(mapping)}")
    print(f"   ✅ Found in DEGIRO: {len(found_stocks)} ({len(found_stocks)/len(mapping)*100:.1f}%)")
    print(f"   🆔 With vwdId (pricing support): {len(stocks_with_vwd)} ({len(stocks_with_vwd)/len(mapping)*100:.1f}%)")
    
    print(f"\n🎯 Major stocks with vwdIds (first 15):")
    count = 0
    for stock in stocks_with_vwd:
        if count >= 15:
            break
        vwd_id = stock.get('degiro_vwd_id', 'N/A')
        currency = stock.get('currency', 'N/A')
        print(f"   {stock['symbol']:6s} - {vwd_id:15s} ({currency})")
        count += 1
    
    if len(stocks_with_vwd) > 15:
        print(f"   ... and {len(stocks_with_vwd) - 15} more with vwdIds")
    
    print(f"\n❌ Not found in DEGIRO:")
    not_found = [stock for stock in mapping if not stock['degiro_id']]
    for stock in not_found[:10]:
        print(f"   {stock['symbol']:6s} - {stock['name']}")
    if len(not_found) > 10:
        print(f"   ... and {len(not_found) - 10} more")

if __name__ == "__main__":
    print("🚀 Creating NASDAQ 100 → DEGIRO vwdId mapping")
    print(f"📋 Processing {len(NASDAQ_100)} stocks from NASDAQ 100 index")
    
    mapping = create_nasdaq100_mapping()
    output_file = save_mapping(mapping)
    print_summary(mapping)
    
    print(f"\n📄 Complete results saved to: {output_file}")
    print("\n🔥 This mapping can be used to:")
    print("   • Quickly lookup DEGIRO product IDs for NASDAQ 100 stocks")
    print("   • Get vwdIds for real-time pricing via quotecast API")
    print("   • Validate stock symbols before trading")
    print("   • Build automated trading systems with reliable product data")