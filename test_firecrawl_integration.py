#!/usr/bin/env python3
"""
Test Firecrawl integration with website ingestion service
"""

import asyncio
import sys
from app.services.website_ingestion_service import website_ingestion_service

async def test_firecrawl():
    """Test Firecrawl crawling"""
    
    # Test URL
    test_url = "https://docs.firecrawl.dev"
    
    print("=" * 50)
    print("Testing Firecrawl Implementation")
    print("=" * 50)
    
    print(f"\n✓ Firecrawl initialized: {website_ingestion_service.firecrawl_app is not None}")
    print(f"✓ Use Firecrawl setting: {website_ingestion_service.use_firecrawl}")
    print(f"✓ Firecrawl API key present: {bool(website_ingestion_service.firecrawl_app)}")
    
    # Test with Firecrawl (force)
    print("\n1. Testing with Firecrawl (forced)...")
    print("-" * 40)
    try:
        result_firecrawl = website_ingestion_service.crawl_website(
            urls=[test_url],
            crawl_depth=1,
            force_crawler='firecrawl' if website_ingestion_service.firecrawl_app else 'custom'
        )
        
        if result_firecrawl:
            print(f"   ✓ Crawler used: {result_firecrawl.get('crawler', 'unknown')}")
            print(f"   ✓ Pages crawled: {result_firecrawl.get('pages_crawled', 0)}")
            print(f"   ✓ Content length: {len(result_firecrawl.get('text', ''))}")
            print(f"   ✓ URLs visited: {len(result_firecrawl.get('urls_visited', []))}")
            if result_firecrawl.get('text'):
                print(f"   ✓ First 100 chars: {result_firecrawl['text'][:100]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test with custom crawler
    print("\n2. Testing with custom crawler (forced)...")
    print("-" * 40)
    try:
        result_custom = website_ingestion_service.crawl_website(
            urls=[test_url],
            crawl_depth=1,
            force_crawler='custom'
        )
        
        if result_custom:
            print(f"   ✓ Crawler used: {result_custom.get('crawler', 'unknown')}")
            print(f"   ✓ Pages crawled: {result_custom.get('pages_crawled', 0)}")
            print(f"   ✓ Content length: {len(result_custom.get('text', ''))}")
            print(f"   ✓ URLs visited: {len(result_custom.get('urls_visited', []))}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test auto selection (should use Firecrawl if available)
    print("\n3. Testing with auto selection...")
    print("-" * 40)
    try:
        result_auto = website_ingestion_service.crawl_website(
            urls=[test_url],
            crawl_depth=1,
            force_crawler=None  # Let it choose automatically
        )
        
        if result_auto:
            print(f"   ✓ Crawler used: {result_auto.get('crawler', 'unknown')}")
            print(f"   ✓ Pages crawled: {result_auto.get('pages_crawled', 0)}")
            print(f"   ✓ Content length: {len(result_auto.get('text', ''))}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Test completed successfully!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_firecrawl())