#!/usr/bin/env python3
"""
Test if the API server is running
"""

import requests

API_BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    
    print("Testing API Server Health")
    print("=" * 50)
    
    try:
        # Test root endpoint
        response = requests.get(f"{API_BASE_URL}/")
        print(f"Root endpoint (/) - Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        
        print()
        
        # Test health endpoint
        response = requests.get(f"{API_BASE_URL}/api/health")
        print(f"Health endpoint (/api/health) - Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        
        print()
        
        # Test docs endpoint
        response = requests.get(f"{API_BASE_URL}/docs")
        print(f"Docs endpoint (/docs) - Status: {response.status_code}")
        
        print("\n✅ API server is running!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: API server is not running")
        print(f"   Make sure the API is running on {API_BASE_URL}")
        print("\n   Run the API server with:")
        print("   python main.py")
        print("   or")
        print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_health()