"""
Create initial super_admin user
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import getpass

sys.path.append(str(Path(__file__).parent.parent))

from app.utils import connect_to_mongo, close_mongo_connection, get_database
from app.services.auth_service import auth_service


async def create_super_admin():
    """Create initial super_admin user"""
    await connect_to_mongo()
    db = get_database()
    
    print("\n=== Create Super Admin User ===\n")
    
    # Check if super_admin already exists
    existing_super_admin = await db.users.find_one({"is_superuser": True})
    if existing_super_admin:
        print("⚠️  A super admin user already exists!")
        print(f"   Email: {existing_super_admin.get('email')}")
        print(f"   Username: {existing_super_admin.get('username')}")
        
        response = input("\nDo you want to create another super admin? (yes/no): ").lower()
        if response != 'yes':
            await close_mongo_connection()
            return
    
    # Get user input
    email = input("Enter email: ").strip()
    username = input("Enter username: ").strip()
    full_name = input("Enter full name: ").strip()
    password = getpass.getpass("Enter password (min 8 chars): ")
    confirm_password = getpass.getpass("Confirm password: ")
    
    # Validate input
    if not email or not username or not full_name:
        print("❌ All fields are required!")
        await close_mongo_connection()
        return
    
    if len(password) < 8:
        print("❌ Password must be at least 8 characters!")
        await close_mongo_connection()
        return
    
    if password != confirm_password:
        print("❌ Passwords do not match!")
        await close_mongo_connection()
        return
    
    # Check if user already exists
    existing_user = await db.users.find_one({
        "$or": [
            {"email": email},
            {"username": username}
        ]
    })
    
    if existing_user:
        print("❌ User with this email or username already exists!")
        await close_mongo_connection()
        return
    
    # Get super_admin role
    super_admin_role = await db.roles.find_one({
        "role_type": "super_admin",
        "is_system_role": True
    })
    
    if not super_admin_role:
        print("❌ Super admin role not found!")
        print("   Please run: python scripts/init_roles.py")
        await close_mongo_connection()
        return
    
    # Create super admin user
    user_data = {
        "email": email,
        "username": username,
        "full_name": full_name,
        "hashed_password": auth_service.get_password_hash(password),
        "is_active": True,
        "is_superuser": True,
        "role_ids": [str(super_admin_role["_id"])],
        "company_id": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": "system",
        "last_login": None
    }
    
    result = await db.users.insert_one(user_data)
    
    print("\n✅ Super admin user created successfully!")
    print(f"   User ID: {result.inserted_id}")
    print(f"   Email: {email}")
    print(f"   Username: {username}")
    print(f"   Role: Super Admin")
    print("\nYou can now login with these credentials.")
    
    await close_mongo_connection()


async def list_super_admins():
    """List all super admin users"""
    await connect_to_mongo()
    db = get_database()
    
    print("\n=== Super Admin Users ===\n")
    
    super_admins = []
    async for user in db.users.find({"is_superuser": True}):
        super_admins.append(user)
    
    if not super_admins:
        print("No super admin users found.")
    else:
        print(f"Found {len(super_admins)} super admin(s):\n")
        for i, admin in enumerate(super_admins, 1):
            print(f"{i}. Email: {admin.get('email')}")
            print(f"   Username: {admin.get('username')}")
            print(f"   Full Name: {admin.get('full_name')}")
            print(f"   Created: {admin.get('created_at')}")
            print(f"   Last Login: {admin.get('last_login', 'Never')}")
            print()
    
    await close_mongo_connection()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage super admin users")
    parser.add_argument('action', choices=['create', 'list'], 
                        help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'create':
        asyncio.run(create_super_admin())
    elif args.action == 'list':
        asyncio.run(list_super_admins())