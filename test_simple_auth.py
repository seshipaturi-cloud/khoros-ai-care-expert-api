"""
Simple authentication test
"""

import requests
import json
import getpass

BASE_URL = "http://localhost:8000"


def test_login():
    """Test login with credentials"""
    print("\n=== Login Test ===")
    print("Please enter your credentials:")
    
    email = input("Email: ").strip()
    password = getpass.getpass("Password: ")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password}
    )
    
    if response.status_code == 200:
        print("✅ Login successful!")
        token_data = response.json()
        token = token_data.get("access_token")
        
        # Get user info
        headers = {"Authorization": f"Bearer {token}"}
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        if me_response.status_code == 200:
            user = me_response.json()
            print(f"\nLogged in as:")
            print(f"  Email: {user.get('email')}")
            print(f"  Username: {user.get('username')}")
            print(f"  Full Name: {user.get('full_name')}")
            print(f"  Is Super Admin: {user.get('is_superuser')}")
            print(f"  Roles: {[r.get('display_name') for r in user.get('roles', [])]}")
        
        return token
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"Response: {response.json()}")
        return None


def create_first_super_admin():
    """Create the first super admin"""
    print("\n=== Create First Super Admin ===")
    print("This will create the first super admin user.")
    
    email = input("Email: ").strip()
    username = input("Username: ").strip()
    full_name = input("Full Name: ").strip()
    password = getpass.getpass("Password (min 8 chars): ")
    confirm = getpass.getpass("Confirm Password: ")
    
    if password != confirm:
        print("❌ Passwords do not match!")
        return
    
    if len(password) < 8:
        print("❌ Password must be at least 8 characters!")
        return
    
    response = requests.post(
        f"{BASE_URL}/api/admin/create-super-admin",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "username": username
        }
    )
    
    if response.status_code == 200:
        print("✅ Super admin created successfully!")
        user = response.json()
        print(f"  User ID: {user.get('_id')}")
        print(f"  Email: {user.get('email')}")
        print("\nYou can now login with these credentials.")
    else:
        print(f"❌ Failed to create super admin: {response.status_code}")
        print(f"Response: {response.json()}")


def main():
    print("=" * 50)
    print("AUTHENTICATION TEST")
    print("=" * 50)
    print(f"Testing against: {BASE_URL}")
    print("\nOptions:")
    print("1. Test login with existing credentials")
    print("2. Create first super admin (if none exists)")
    print("3. Check API health")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        test_login()
    elif choice == "2":
        create_first_super_admin()
    elif choice == "3":
        response = requests.get(f"{BASE_URL}/api/health/")
        if response.status_code == 200:
            print("✅ API is healthy!")
            print(f"Response: {response.json()}")
        else:
            print("❌ API health check failed!")
    else:
        print("Invalid option")


if __name__ == "__main__":
    main()