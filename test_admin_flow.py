"""
Test script for super_admin flow:
1. Create super_admin
2. Login as super_admin
3. Create company
4. Create company_admin for that company
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


class AdminFlowTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.super_admin_token = None
        self.company_id = None
        self.company_admin_id = None

    def test_create_super_admin(self):
        """Create initial super_admin if none exists"""
        print("\n=== Creating Super Admin ===")
        
        # First, try to create without authentication (initial setup)
        data = {
            "email": "superadmin@khoros.com",
            "password": "SuperAdmin123!",
            "full_name": "Super Administrator",
            "username": "superadmin"
        }
        
        response = requests.post(f"{self.base_url}/api/admin/create-super-admin", json=data)
        
        if response.status_code == 200:
            print("✓ Super admin created successfully")
            user_data = response.json()
            print(f"  User ID: {user_data.get('_id')}")
            print(f"  Email: {user_data.get('email')}")
            return True
        elif response.status_code == 400:
            print("✓ Super admin already exists")
            return True
        else:
            print(f"✗ Failed to create super admin: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def test_super_admin_login(self):
        """Login as super_admin"""
        print("\n=== Super Admin Login ===")
        
        data = {
            "email": "superadmin@khoros.com",
            "password": "SuperAdmin123!"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=data)
        
        if response.status_code == 200:
            print("✓ Super admin logged in successfully")
            token_data = response.json()
            self.super_admin_token = token_data.get("access_token")
            print(f"  Token received (first 20 chars): {self.super_admin_token[:20]}...")
            return True
        else:
            print(f"✗ Login failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def test_create_company(self):
        """Create a company as super_admin"""
        print("\n=== Creating Company ===")
        
        if not self.super_admin_token:
            print("✗ No super_admin token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        
        data = {
            "name": "Acme Corporation",
            "domain": "acme.com",
            "industry": "Technology",
            "size": "enterprise",
            "status": "active",
            "plan": "enterprise",
            "contact_email": "contact@acme.com",
            "contact_name": "John Doe",
            "contact_phone": "+1-555-0100",
            "address": {
                "street": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "country": "USA",
                "postal_code": "94105"
            },
            "settings": {
                "max_brands": 10,
                "max_agents": 100,
                "max_users": 500,
                "max_knowledge_base_items": 10000,
                "allow_custom_llm": True,
                "allow_multi_language": True,
                "allow_api_access": True,
                "storage_quota_gb": 100,
                "api_rate_limit": 10000,
                "allowed_llm_providers": ["openai", "anthropic"]
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/companies/",
            json=data,
            headers=headers
        )
        
        if response.status_code == 201:
            print("✓ Company created successfully")
            company_data = response.json()
            self.company_id = company_data.get("id")
            print(f"  Company ID: {self.company_id}")
            print(f"  Company Name: {company_data.get('name')}")
            return True
        elif response.status_code == 400:
            # Company might already exist, try to get it
            print("  Company might already exist, fetching...")
            list_response = requests.get(
                f"{self.base_url}/api/companies/",
                headers=headers,
                params={"search": "Acme"}
            )
            if list_response.status_code == 200:
                companies = list_response.json().get("companies", [])
                if companies:
                    self.company_id = companies[0].get("id")
                    print(f"✓ Found existing company: {self.company_id}")
                    return True
            return False
        else:
            print(f"✗ Failed to create company: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def test_create_company_admin(self):
        """Create a company_admin user for the company"""
        print("\n=== Creating Company Admin ===")
        
        if not self.super_admin_token:
            print("✗ No super_admin token available")
            return False
        
        if not self.company_id:
            print("✗ No company ID available")
            return False
        
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        
        data = {
            "email": "admin@acme.com",
            "password": "Admin123!",
            "full_name": "Company Administrator",
            "username": "acmeadmin",
            "company_id": self.company_id,
            "role_type": "company_admin",
            "is_active": True
        }
        
        response = requests.post(
            f"{self.base_url}/api/admin/create-company-admin",
            json=data,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✓ Company admin created successfully")
            admin_data = response.json()
            self.company_admin_id = admin_data.get("_id")
            print(f"  Admin ID: {self.company_admin_id}")
            print(f"  Email: {admin_data.get('email')}")
            print(f"  Assigned to Company: {self.company_id}")
            return True
        elif response.status_code == 400:
            print("✓ Company admin might already exist")
            return True
        else:
            print(f"✗ Failed to create company admin: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def test_company_admin_login(self):
        """Test login as company_admin"""
        print("\n=== Company Admin Login ===")
        
        data = {
            "email": "admin@acme.com",
            "password": "Admin123!"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=data)
        
        if response.status_code == 200:
            print("✓ Company admin logged in successfully")
            token_data = response.json()
            company_admin_token = token_data.get("access_token")
            
            # Get user info
            headers = {"Authorization": f"Bearer {company_admin_token}"}
            me_response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
            
            if me_response.status_code == 200:
                user_data = me_response.json()
                print(f"  User: {user_data.get('email')}")
                print(f"  Roles: {[r.get('display_name') for r in user_data.get('roles', [])]}")
            
            return True
        else:
            print(f"✗ Login failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def test_get_company_users(self):
        """Get all users in the company"""
        print("\n=== Getting Company Users ===")
        
        if not self.super_admin_token or not self.company_id:
            print("✗ Missing required data")
            return False
        
        headers = {"Authorization": f"Bearer {self.super_admin_token}"}
        
        response = requests.get(
            f"{self.base_url}/api/admin/users-by-company/{self.company_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            users = response.json()
            print(f"✓ Found {len(users)} user(s) in company")
            for user in users:
                roles = [r.get('display_name', r.get('name', '')) for r in user.get('roles', [])]
                print(f"  - {user.get('email')} ({', '.join(roles)})")
            return True
        else:
            print(f"✗ Failed to get company users: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def run_all_tests(self):
        """Run complete admin flow tests"""
        print("=" * 50)
        print("SUPER ADMIN FLOW TEST SUITE")
        print("=" * 50)
        
        tests = [
            self.test_create_super_admin,
            self.test_super_admin_login,
            self.test_create_company,
            self.test_create_company_admin,
            self.test_company_admin_login,
            self.test_get_company_users
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
            print("\nYou can now:")
            print("1. Login to the web portal at http://localhost:8081/auth/signin")
            print("   - Super Admin: superadmin@khoros.com / SuperAdmin123!")
            print("   - Company Admin: admin@acme.com / Admin123!")
            print("2. Super admin can create more companies and assign admins")
            print("3. Company admin can manage users within their company")
        else:
            print(f"\n⚠️  {failed} test(s) failed")


if __name__ == "__main__":
    print("Starting Admin Flow tests...")
    print(f"Testing against: {BASE_URL}")
    print("\nMake sure the API server is running on port 8000")
    print("Starting tests in 2 seconds...")
    
    time.sleep(2)
    
    tester = AdminFlowTester()
    tester.run_all_tests()