#!/usr/bin/env python3
"""
List all available API endpoints
"""

import requests

API_BASE_URL = "http://localhost:8000"

def list_endpoints():
    """Get the OpenAPI schema to list endpoints"""
    
    print("Fetching API Endpoints from OpenAPI Schema")
    print("=" * 50)
    
    try:
        # Get OpenAPI schema
        response = requests.get(f"{API_BASE_URL}/openapi.json")
        
        if response.status_code == 200:
            schema = response.json()
            paths = schema.get("paths", {})
            
            print(f"Found {len(paths)} endpoints:\n")
            
            # Group by authentication endpoints first
            auth_endpoints = []
            other_endpoints = []
            
            for path, methods in paths.items():
                for method, details in methods.items():
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        endpoint = f"{method.upper():6} {path}"
                        summary = details.get('summary', 'No description')
                        
                        if 'auth' in path.lower() or 'login' in path.lower() or 'register' in path.lower():
                            auth_endpoints.append((endpoint, summary))
                        else:
                            other_endpoints.append((endpoint, summary))
            
            # Print auth endpoints
            print("🔐 Authentication Endpoints:")
            print("-" * 50)
            for endpoint, summary in sorted(auth_endpoints):
                print(f"{endpoint:40} - {summary}")
            
            print("\n📚 Other Endpoints (first 20):")
            print("-" * 50)
            for endpoint, summary in sorted(other_endpoints)[:20]:
                print(f"{endpoint:40} - {summary}")
                
        else:
            print(f"❌ Failed to get OpenAPI schema: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: API server is not running")
        print(f"   Make sure the API is running on {API_BASE_URL}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    list_endpoints()