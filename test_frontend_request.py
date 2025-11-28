#!/usr/bin/env python3
"""
Simulate what the frontend might be sending
"""

import requests
import json

API_BASE_URL = "http://localhost:8000"

def test_chat_like_frontend():
    """Test chat endpoint with both company_id and brand_id like frontend would"""
    
    print("Simulating Frontend Request to Chat API")
    print("=" * 50)
    
    # Simulate frontend sending both IDs
    test_cases = [
        {
            "name": "Frontend with both IDs",
            "data": {
                "query": "How many emotions does AI care expert detect?",
                "company_id": "68c6a8c80fa016e20482025f",
                "brand_id": "68c6a8c80fa016e20482025f",
                "search_type": "hybrid",
                "limit": 5
            }
        },
        {
            "name": "Frontend with only company_id",
            "data": {
                "query": "How many emotions does AI care expert detect?",
                "company_id": "68c6a8c80fa016e20482025f",
                "search_type": "hybrid",
                "limit": 5
            }
        },
        {
            "name": "Frontend with only brand_id",
            "data": {
                "query": "How many emotions does AI care expert detect?",
                "brand_id": "68c6a8c80fa016e20482025f",
                "search_type": "hybrid",
                "limit": 5
            }
        }
    ]
    
    # Try to get a token first (optional)
    token = None
    try:
        login_response = requests.post(
            f"{API_BASE_URL}/api/auth/login",
            json={"email": "test@example.com", "password": "test123"}
        )
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            print(f"✅ Got auth token")
    except:
        print("⚠️  Could not get auth token, will try without")
    
    headers = {
        "Content-Type": "application/json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    for test_case in test_cases:
        print("\n" + "-" * 50)
        print(f"Test: {test_case['name']}")
        print(f"Sending: {json.dumps(test_case['data'], indent=2)}")
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/knowledge-base/chat",
                headers=headers,
                json=test_case['data']
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('answer', 'No answer')
                if '27' in answer:
                    print("✅ Found '27 emotions' in answer!")
                else:
                    print(f"Answer: {answer[:100]}...")
            else:
                print(f"Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_chat_like_frontend()