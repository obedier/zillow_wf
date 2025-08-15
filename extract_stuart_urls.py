#!/usr/bin/env python3
"""
Simple script to extract property URLs from the Stuart, FL search results.
This will get the 35 property URLs that the main script found but didn't save.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the zillow_wf directory to the path
sys.path.insert(0, 'zillow_wf')

from zillow_wf.flexible_waterfront_extractor import FlexibleWaterfrontExtractor

async def main():
    """Extract property URLs from Stuart, FL search results and save them"""
    
    # The Stuart, FL search URL that contains 35 properties
    search_url = "https://www.zillow.com/homes/for_sale/?searchQueryState=%7B%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22north%22%3A27.26511486192419%2C%22south%22%3A27.011528898981783%2C%22east%22%3A-80.0609523955078%2C%22west%22%3A-80.41114160449217%7D%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C%22sf%22%3A%7B%22value%22%3Afalse%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22mf%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%7D%2C%22isListVisible%22%3Atrue%2C%22mapZoom%22%3A12%2C%22usersSearchTerm%22%3A%22Stuart%2C%20FL%22%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A54592%2C%22regionType%22%3A6%7D%5D%7D"
    
    print(f"🔍 Extracting property URLs from: {search_url}")
    
    # Create extractor instance
    extractor = FlexibleWaterfrontExtractor()
    
    # Extract property URLs from the search results
    property_urls = await extractor._extract_property_urls_from_search_page(search_url)
    
    if property_urls:
        print(f"✅ Found {len(property_urls)} property URLs")
        
        # Save URLs to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"zillow_wf/data/urls_list_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write(f"# URLs extracted from: {search_url}\n")
            f.write(f"# Total properties: {len(property_urls)}\n")
            f.write(f"# Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for url in property_urls:
                f.write(f"{url}\n")
        
        print(f"💾 Saved {len(property_urls)} URLs to: {filename}")
        
        # Show first few URLs
        print("\n📋 First 5 URLs:")
        for i, url in enumerate(property_urls[:5]):
            print(f"  {i+1}. {url}")
            
    else:
        print("❌ No property URLs found")

if __name__ == "__main__":
    asyncio.run(main())
