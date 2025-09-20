#!/usr/bin/env python3
"""
Analyze Apple leveraged products to understand different types:
- Faktor 
- Optionsscheine
- Knockouts
"""

import os
import sys
sys.path.append('/Users/sebastianmertens/Documents/GitHub/degiro-connector')

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials
from degiro_connector.trading.models.product_search import LeveragedsRequest

def analyze_apple_leveraged_products():
    """Analyze Apple leveraged products to understand product types"""
    print("🔍 Analyzing Apple Leveraged Products")
    print("=" * 60)
    
    try:
        # Create credentials and connect
        credentials = Credentials(
            username="bastiheye",
            password="!c3c6kdG5j6NFB7R", 
            totp_secret_key="5ADDODASZT7CHKD273VFMJMJZNAUHVBH",
            int_account=31043411
        )
        
        api = TradingAPI(credentials=credentials)
        print("✅ API instance created")
        
        connection_result = api.connect()
        print(f"✅ Connected: {connection_result}")
        
        # Search for Apple leveraged products (Apple stock ID from previous tests: 331868)
        print(f"\n🍎 Searching for Apple leveraged products...")
        
        # Create leveraged search request
        leveraged_request = LeveragedsRequest(
            popular_only=False,
            input_aggregate_types="",
            input_aggregate_values="",
            search_text="",
            offset=0,
            limit=50,  # Get many products to analyze
            require_total=True,
            sort_columns="name",
            sort_types="asc",
            underlying_product_id=None  # Get all leveraged products, not just Apple
        )
        
        # Perform leveraged search
        leveraged_results = api.product_search(leveraged_request, raw=True)
        print(f"📊 Raw leveraged results type: {type(leveraged_results)}")
        
        if isinstance(leveraged_results, dict) and 'products' in leveraged_results:
            products = leveraged_results['products']
            print(f"📊 Found {len(products)} Apple leveraged products")
            
            # Analyze each product to understand types
            product_types = {}
            issuers = set()
            name_patterns = set()
            
            for i, product in enumerate(products[:20]):  # Analyze first 20
                product_id = product.get('id')
                name = product.get('name', '')
                isin = product.get('isin', '')
                product_type = product.get('productType', '')
                product_type_id = product.get('productTypeId')
                category = product.get('category', '')
                
                print(f"\n📋 Product {i+1}:")
                print(f"   ID: {product_id}")
                print(f"   Name: {name}")
                print(f"   ISIN: {isin}")
                print(f"   Product Type: {product_type}")
                print(f"   Product Type ID: {product_type_id}")
                print(f"   Category: {category}")
                
                # Analyze name patterns
                name_lower = name.lower()
                if 'faktor' in name_lower:
                    product_types['Faktor'] = product_types.get('Faktor', 0) + 1
                    name_patterns.add('faktor')
                elif 'optionsschein' in name_lower:
                    product_types['Optionsscheine'] = product_types.get('Optionsscheine', 0) + 1
                    name_patterns.add('optionsschein')
                elif 'knockout' in name_lower:
                    product_types['Knockouts'] = product_types.get('Knockouts', 0) + 1
                    name_patterns.add('knockout')
                elif 'turbo' in name_lower:
                    product_types['Turbo'] = product_types.get('Turbo', 0) + 1
                    name_patterns.add('turbo')
                elif 'warrant' in name_lower:
                    product_types['Warrant'] = product_types.get('Warrant', 0) + 1
                    name_patterns.add('warrant')
                elif 'call' in name_lower or 'put' in name_lower:
                    product_types['Call/Put'] = product_types.get('Call/Put', 0) + 1
                    name_patterns.add('call/put')
                else:
                    product_types['Other'] = product_types.get('Other', 0) + 1
                
                # Extract issuer
                if name.startswith("SG "):
                    issuers.add("SG")
                elif name.startswith("BNP "):
                    issuers.add("BNP")
                elif name.startswith("CS "):
                    issuers.add("CS")
                elif name.startswith("MS "):
                    issuers.add("MS")
                else:
                    # Try to extract first word as issuer
                    first_word = name.split(' ')[0] if ' ' in name else name[:3]
                    issuers.add(first_word)
                
                # Check for other product fields that might help categorize
                print(f"   All fields: {list(product.keys())}")
            
            print(f"\n📊 ANALYSIS SUMMARY:")
            print(f"🏷️  Product Types Found:")
            for ptype, count in product_types.items():
                print(f"   {ptype}: {count} products")
            
            print(f"\n🏢 Issuers Found:")
            for issuer in sorted(issuers):
                print(f"   {issuer}")
            
            print(f"\n🔤 Name Patterns Found:")
            for pattern in sorted(name_patterns):
                print(f"   {pattern}")
            
            # Check if there are any product type IDs or categories that differ
            type_ids = set()
            categories = set()
            
            for product in products[:20]:
                type_ids.add(product.get('productTypeId'))
                categories.add(product.get('category'))
            
            print(f"\n🆔 Product Type IDs Found: {sorted(type_ids)}")
            print(f"📂 Categories Found: {sorted(categories)}")
        
        else:
            print("❌ No products found or invalid response format")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    analyze_apple_leveraged_products()