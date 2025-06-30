#!/usr/bin/env python3
"""
Debug script to test source text extraction and validate content
"""

import json
import os
from document_extractor import DocumentExtractor

def debug_source_extraction():
    """Debug source text extraction for troubleshooting"""
    
    # Load config
    if not os.path.exists('config.json'):
        print("❌ config.json not found!")
        return
    
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    extractor = DocumentExtractor()
    
    print("🔍 DEBUGGING SOURCE TEXT EXTRACTION")
    print("="*60)
    
    # Test each company
    for company in config['companies']:
        company_name = company['name']
        print(f"\n📊 Testing {company_name}:")
        print("-" * 40)
        
        if 'source_files' not in company:
            print("⚠️ No source_files in config")
            continue
        
        # Process source files
        source_data = extractor.process_source_files(company['source_files'])
        combined_text = source_data.get('combined_source_text', '')
        
        print(f"📄 Combined source text length: {len(combined_text):,} characters")
        
        if len(combined_text) > 0:
            # Show first 1000 characters
            print(f"\n📝 First 1000 characters:")
            print("-" * 30)
            print(combined_text[:1000])
            print("-" * 30)
            
            # Extract and show key information
            key_info = extractor.extract_key_information(combined_text)
            print(f"\n🔍 Key Information Extracted:")
            for category, items in key_info.items():
                if items:
                    print(f"  {category}: {len(items)} items")
                    for item in items[:3]:  # Show first 3 items
                        print(f"    - {item}")
            
            # Test specific searches for this company
            print(f"\n🔎 Searching for specific information:")
            
            # Test searches
            test_searches = [
                ('company_name', ['brightband', 'company name', company_name.lower()]),
                ('industry', ['industry', 'sector', 'media', 'information services']),
                ('location', ['san francisco', 'location', 'based', 'headquarters']),
                ('founders', ['julian green', 'founder', 'ceo', 'green']),
                ('funding', ['series a', '$10', 'million', 'raised', 'prelude']),
                ('valuation', ['$38', 'valuation', 'post-money', '38 million'])
            ]
            
            for search_type, terms in test_searches:
                found_terms = []
                for term in terms:
                    if term.lower() in combined_text.lower():
                        found_terms.append(term)
                
                if found_terms:
                    print(f"  ✅ {search_type}: Found {found_terms}")
                else:
                    print(f"  ❌ {search_type}: Not found")
        
        else:
            print("❌ No source text extracted!")
            
        print(f"\n{'='*60}")

if __name__ == "__main__":
    debug_source_extraction()