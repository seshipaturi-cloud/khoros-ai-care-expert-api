#!/usr/bin/env python3
"""
Test metadata serialization for MongoDB
"""

from app.services.website_ingestion_service import website_ingestion_service

def test_metadata_serialization():
    """Test that Firecrawl metadata can be serialized for MongoDB"""
    
    test_url = "https://en.wikipedia.org/wiki/Heart_failure"
    
    print("Testing metadata serialization with Firecrawl...")
    print("-" * 50)
    
    # Test crawling with metadata extraction
    result = website_ingestion_service.crawl_website(
        urls=[test_url],
        crawl_depth=1,
        extract_metadata=True,
        force_crawler='firecrawl' if website_ingestion_service.firecrawl_app else 'custom'
    )
    
    if result and result.get('metadata'):
        print(f"✓ Metadata extracted: {len(result['metadata'])} items")
        
        # Check first metadata item
        if result['metadata']:
            first_meta = result['metadata'][0]
            print(f"✓ First metadata type: {type(first_meta)}")
            
            if isinstance(first_meta, dict) and 'metadata' in first_meta:
                meta_content = first_meta['metadata']
                print(f"✓ Metadata content type: {type(meta_content)}")
                
                # Check if it's serializable
                try:
                    import json
                    json_str = json.dumps(meta_content, default=str)
                    print(f"✓ Metadata is JSON serializable")
                    print(f"✓ Metadata keys: {list(meta_content.keys())[:5]}...")
                except Exception as e:
                    print(f"✗ Metadata serialization failed: {e}")
    else:
        print("✗ No metadata extracted")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_metadata_serialization()