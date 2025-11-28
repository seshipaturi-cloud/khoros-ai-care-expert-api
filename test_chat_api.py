#!/usr/bin/env python3
"""
Test the chat API endpoint to see what company_id is being used
"""

import requests
import json
import sys

# API configuration
API_BASE_URL = "http://localhost:8000"  # Update if different

def test_chat(token=None):
    """Test the chat endpoint"""
    
    # Headers with authentication if token provided
    headers = {
        "Content-Type": "application/json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    # Test query
    data = {
        "query": "How many emotions does AI care expert detect?",
        "search_type": "hybrid",
        "limit": 5
    }
    
    print("Testing Chat API")
    print("=" * 50)
    print(f"Endpoint: {API_BASE_URL}/api/knowledge-base/chat")
    print(f"Query: {data['query']}")
    print()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/knowledge-base/chat",
            headers=headers,
            json=data
        )
        
        print(f"Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"Answer: {result.get('answer', 'No answer')[:200]}...")
            print(f"Sources found: {len(result.get('sources', []))}")
            if result.get('sources'):
                print("\nSources:")
                for source in result['sources'][:3]:
                    print(f"  - {source.get('title', 'Unknown')}")
        elif response.status_code == 401:
            print("❌ Authentication required")
            print("Please provide a valid JWT token")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: API server is not running")
        print(f"   Make sure the API is running on {API_BASE_URL}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_login():
    """Test login to get a token"""
    print("Testing Login")
    print("=" * 50)
    
    # Try to login with a test user
    login_data = {
        "email": "test@example.com",  # Test user email
        "password": "test123"  # Test user password
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/auth/login",
            json=login_data  # JSON data for login
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            print(f"✅ Login successful!")
            print(f"Token: {token[:50]}...")
            return token
        else:
            print(f"❌ Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return None

if __name__ == "__main__":
    print("AI Care Expert Chat API Test")
    print("=" * 50)
    print()
    
    # First try to login
    token = test_login()
    print()
    
    # Then test the chat endpoint
    if token:
        test_chat(token)
    else:
        print("Testing without authentication...")
        test_chat()