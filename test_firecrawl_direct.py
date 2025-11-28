#!/usr/bin/env python3
"""
Test Firecrawl directly
"""

from firecrawl import FirecrawlApp

# Initialize Firecrawl
app = FirecrawlApp(api_key="fc-23f86a273d79400ca1069aa99f084f02")

# Test scrape
print("Testing scrape...")
try:
    result = app.scrape("https://docs.firecrawl.dev")
    print(f"Type of result: {type(result)}")
    print(f"Result attributes: {dir(result)}")
    if hasattr(result, 'markdown'):
        print(f"Markdown content length: {len(result.markdown) if result.markdown else 0}")
    if hasattr(result, 'html'):
        print(f"HTML content length: {len(result.html) if result.html else 0}")
    if hasattr(result, 'url'):
        print(f"URL: {result.url}")
except Exception as e:
    print(f"Error: {e}")

# Test crawl  
print("\n\nTesting crawl...")
try:
    result = app.crawl("https://docs.firecrawl.dev", {'limit': 2})
    print(f"Type of result: {type(result)}")
    if hasattr(result, 'data'):
        print(f"Number of pages: {len(result.data) if result.data else 0}")
        if result.data and len(result.data) > 0:
            page = result.data[0]
            print(f"First page type: {type(page)}")
            print(f"First page attributes: {dir(page)}")
except Exception as e:
    print(f"Error: {e}")