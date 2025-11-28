import requests
import json

# First login to get token
login_response = requests.post(
    'http://localhost:8000/api/auth/login',
    json={'email': 'seshi.paturi@ignitetech.com', 'password': 'Pandu01#'}
)

if login_response.status_code == 200:
    token = login_response.json()['access_token']
    print("✅ Logged in successfully")
    
    # Get current user info
    user_response = requests.get(
        'http://localhost:8000/api/auth/me',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if user_response.status_code == 200:
        user_data = user_response.json()
        print(f"Current user: {user_data.get('email')}")
        print(f"  ID: {user_data.get('id')}")
        print(f"  Role: {user_data.get('role')}")
        print(f"  Roles: {user_data.get('roles')}")
        
        # Try to update via admin endpoint
        # Since we need to be super_admin to update, let's first try to create a role
        role_data = {
            "role_name": "super_admin",
            "role_type": "system",
            "description": "Super Administrator with full system access",
            "permissions": ["*"],
            "scope": "system",
            "is_active": True,
            "can_be_delegated": True
        }
        
        role_response = requests.post(
            'http://localhost:8000/api/roles',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            json=role_data
        )
        
        if role_response.status_code in [200, 201]:
            print("✅ Created super_admin role")
        else:
            print(f"Role creation response: {role_response.status_code}")
            if role_response.status_code != 409:  # Not a conflict (already exists)
                print(role_response.text)
    else:
        print(f"Failed to get user info: {user_response.status_code}")
else:
    print(f"Login failed: {login_response.status_code}")