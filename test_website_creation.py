#!/usr/bin/env python3
"""
Test script for website knowledge base item creation
"""

import requests
import json

# API endpoint
url = "http://localhost:8081/api/knowledge-base/websites"

# Test data
data = {
    "urls": ["https://www.example.com"],
    "title": "Example Website Test",
    "description": "Testing website crawling and ingestion",
    "agent_ids": ["agent-1", "agent-2"],
    "crawl_depth": 1,
    "refresh_frequency": "manual",
    "follow_redirects": "true",
    "respect_robots_txt": "true",
    "extract_metadata": "true"
}

# Make request
try:
    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Website knowledge base item created successfully!")
        print(json.dumps(result, indent=2))
    else:
        print(f"❌ Failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")