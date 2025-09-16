#!/usr/bin/env python3
"""
Extract underlying company IDs and names from DEGIRO HTML dropdown
"""

import json
import re
from bs4 import BeautifulSoup

def extract_companies_from_html():
    print("🔍 Parsing HTML file to extract underlying companies...")
    
    # Read the HTML file
    with open('html.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"   📄 HTML file size: {len(html_content)} characters")
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all button elements with data-index
    buttons = soup.find_all('button', {'data-index': True})
    
    print(f"   🔢 Found {len(buttons)} buttons with data-index")
    
    companies = {}
    
    for button in buttons:
        data_index = button.get('data-index')
        
        # Get company name from the div inside the button
        div_element = button.find('div')
        if div_element:
            company_name = div_element.get_text(strip=True)
            
            # Clean up HTML entities
            company_name = company_name.replace('&amp;', '&')
            
            if data_index and company_name:
                companies[data_index] = {
                    'id': int(data_index),
                    'name': company_name
                }
    
    print(f"   ✅ Extracted {len(companies)} companies")
    
    # Sort by ID for better readability
    sorted_companies = dict(sorted(companies.items(), key=lambda x: x[1]['id']))
    
    # Convert to array format as requested
    companies_array = []
    for key, data in sorted_companies.items():
        companies_array.append({
            'id': data['id'],
            'name': data['name']
        })
    
    # Export to JSON as array
    output_file = 'underlying_companies_from_html.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(companies_array, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ SUCCESS!")
    print(f"   • Total companies extracted: {len(sorted_companies)}")
    print(f"   • Output file: {output_file}")
    
    # Show first 10 entries
    print(f"\n📋 Sample entries:")
    for i, (key, data) in enumerate(sorted_companies.items()):
        if i < 10:
            print(f"   ID {data['id']}: {data['name']}")
    
    # Look for key companies from trading signals
    print(f"\n🎯 Looking for trading signal companies:")
    signal_companies = ['cisco', 'micron', 'oracle', 'caterpillar', 'vistra', 'xylem', 'alphabet', 'google', 'microsoft', 'apple']
    
    for search_term in signal_companies:
        found = []
        for key, data in sorted_companies.items():
            if search_term.lower() in data['name'].lower():
                found.append(f"ID {data['id']}: {data['name']}")
        
        if found:
            print(f"   {search_term.upper()}:")
            for item in found[:3]:  # Show first 3 matches
                print(f"      {item}")
    
    return sorted_companies

if __name__ == "__main__":
    extract_companies_from_html()