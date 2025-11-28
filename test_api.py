#!/usr/bin/env python3
"""Test script to verify Knowledge Base API is working"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_create_item():
    """Test creating a knowledge base item"""
    print("Testing: Create knowledge base item...")
    
    data = {
        "title": "Test Document",
        "description": "This is a test document",
        "content_type": "document",
        "brand_id": "test-brand-123",
        "agent_ids": ["agent-1", "agent-2"],
        "processing_options": {
            "auto_index": True,
            "enable_ocr": False,
            "extract_metadata": True,
            "generate_embeddings": False  # Disable if no OpenAI key
        }
    }
    
    response = requests.post(
        f"{API_BASE}/api/knowledge-base/items",
        json=data
    )
    
    if response.status_code == 200:
        item = response.json()
        print(f"✅ Created item: {item['id']}")
        return item['id']
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return None

def test_list_items():
    """Test listing knowledge base items"""
    print("\nTesting: List knowledge base items...")
    
    response = requests.get(f"{API_BASE}/api/knowledge-base/items?limit=10")
    
    if response.status_code == 200:
        items = response.json()
        print(f"✅ Found {len(items)} items")
        for item in items[:3]:  # Show first 3
            print(f"  - {item.get('title', 'Untitled')} ({item.get('id')})")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

def test_get_stats():
    """Test getting stats"""
    print("\nTesting: Get knowledge base stats...")
    
    response = requests.get(f"{API_BASE}/api/knowledge-base/stats")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Stats retrieved:")
        print(f"  - Total items: {stats.get('total_items', 0)}")
        print(f"  - Documents: {stats.get('documents', 0)}")
        print(f"  - Media files: {stats.get('media_files', 0)}")
        print(f"  - Websites: {stats.get('websites', 0)}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("=" * 50)
    print("Knowledge Base API Test")
    print("=" * 50)
    
    # Test endpoints
    item_id = test_create_item()
    test_list_items()
    test_get_stats()
    
    print("\n" + "=" * 50)
    print("Test Complete!")
    print("=" * 50)