"""
Test script for authentication and role management APIs
"""

import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"


class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.role_id: Optional[str] = None

    def test_register(self):
        """Test user registration"""
        print("\n=== Testing User Registration ===")
        
        data = {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "full_name": "Test User",
            "username": "testuser"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/register", json=data)
        
        if response.status_code == 201:
            print("✓ User registered successfully")
            user_data = response.json()
            self.user_id = user_data.get("_id")
            print(f"  User ID: {self.user_id}")
            return True
        elif response.status_code == 400:
            print("✓ User already exists (expected if running test multiple times)")
            return True
        else:
            print(f"✗ Registration failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def test_login(self):
        """Test user login"""
        print("\n=== Testing User Login ===")
        
        data = {
            "email": "test@example.com",
            "password": "TestPassword123!"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=data)
        
        if response.status_code == 200:
            print("✓ Login successful")
            token_data = response.json()
            self.token = token_data.get("access_token")
            print(f"  Token received (first 20 chars): {self.token[:20]}...")
            return True
        else:
            print(f"✗ Login failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def test_get_current_user(self):
        """Test getting current user info"""
        print("\n=== Testing Get Current User ===")
        
        if not self.token:
            print("✗ No token available, skipping test")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
        
        if response.status_code == 200:
            print("✓ Got current user info")
            user_data = response.json()
            print(f"  Email: {user_data.get('email')}")
            print(f"  Username: {user_data.get('username')}")
            return True
        else:
            print(f"✗ Failed to get user info: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def test_get_permissions(self):
        """Test getting user permissions"""
        print("\n=== Testing Get User Permissions ===")
        
        if not self.token:
            print("✗ No token available, skipping test")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/api/auth/permissions", headers=headers)
        
        if response.status_code == 200:
            print("✓ Got user permissions")
            data = response.json()
            print(f"  Permissions count: {len(data.get('permissions', []))}")
            print(f"  Roles count: {len(data.get('roles', []))}")
            return True
        else:
            print(f"✗ Failed to get permissions: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def test_get_roles(self):
        """Test getting roles list"""
        print("\n=== Testing Get Roles List ===")
        
        if not self.token:
            print("✗ No token available, skipping test")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/api/roles/", headers=headers)
        
        if response.status_code == 200:
            print("✓ Got roles list")
            data = response.json()
            print(f"  Total roles: {data.get('total', 0)}")
            if data.get('roles'):
                self.role_id = data['roles'][0].get('_id')
                print(f"  First role ID: {self.role_id}")
            return True
        else:
            print(f"✗ Failed to get roles: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def test_get_role_templates(self):
        """Test getting role templates"""
        print("\n=== Testing Get Role Templates ===")
        
        if not self.token:
            print("✗ No token available, skipping test")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/api/roles/templates", headers=headers)
        
        if response.status_code == 200:
            print("✓ Got role templates")
            templates = response.json()
            print(f"  Total templates: {len(templates)}")
            for template in templates[:3]:
                print(f"    - {template.get('display_name')} ({template.get('type')})")
            return True
        else:
            print(f"✗ Failed to get templates: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def test_get_all_permissions(self):
        """Test getting all available permissions"""
        print("\n=== Testing Get All Permissions ===")
        
        if not self.token:
            print("✗ No token available, skipping test")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/api/roles/permissions", headers=headers)
        
        if response.status_code == 200:
            print("✓ Got all permissions")
            permissions = response.json()
            print(f"  Total permissions: {len(permissions)}")
            print(f"  Sample permissions: {permissions[:5]}")
            return True
        else:
            print(f"✗ Failed to get permissions: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def test_refresh_token(self):
        """Test token refresh"""
        print("\n=== Testing Token Refresh ===")
        
        if not self.token:
            print("✗ No token available, skipping test")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{self.base_url}/api/auth/refresh-token", headers=headers)
        
        if response.status_code == 200:
            print("✓ Token refreshed successfully")
            token_data = response.json()
            new_token = token_data.get("access_token")
            print(f"  New token received (first 20 chars): {new_token[:20]}...")
            self.token = new_token
            return True
        else:
            print(f"✗ Token refresh failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def test_verify_token(self):
        """Test token verification"""
        print("\n=== Testing Token Verification ===")
        
        if not self.token:
            print("✗ No token available, skipping test")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{self.base_url}/api/auth/verify-token", headers=headers)
        
        if response.status_code == 200:
            print("✓ Token verified successfully")
            data = response.json()
            print(f"  Valid: {data.get('valid')}")
            print(f"  User ID: {data.get('user_id')}")
            return True
        else:
            print(f"✗ Token verification failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def test_logout(self):
        """Test logout"""
        print("\n=== Testing Logout ===")
        
        if not self.token:
            print("✗ No token available, skipping test")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{self.base_url}/api/auth/logout", headers=headers)
        
        if response.status_code == 200:
            print("✓ Logout successful")
            return True
        else:
            print(f"✗ Logout failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("=" * 50)
        print("AUTHENTICATION API TEST SUITE")
        print("=" * 50)
        
        tests = [
            self.test_register,
            self.test_login,
            self.test_get_current_user,
            self.test_get_permissions,
            self.test_get_roles,
            self.test_get_role_templates,
            self.test_get_all_permissions,
            self.test_refresh_token,
            self.test_verify_token,
            self.test_logout
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"✗ Test crashed: {e}")
                failed += 1
        
        print("\n" + "=" * 50)
        print("TEST RESULTS")
        print("=" * 50)
        print(f"✓ Passed: {passed}")
        print(f"✗ Failed: {failed}")
        print(f"Total: {passed + failed}")
        
        if failed == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {failed} test(s) failed")


if __name__ == "__main__":
    print("Starting API tests...")
    print(f"Testing against: {BASE_URL}")
    print("\nMake sure the API server is running on port 8000")
    print("You can start it with: python main.py")
    print("\nStarting tests in 2 seconds...")
    
    import time
    time.sleep(2)
    
    tester = APITester()
    tester.run_all_tests()