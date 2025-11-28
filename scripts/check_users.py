"""
Check existing users in the database
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from app.utils import connect_to_mongo, close_mongo_connection, get_database


async def check_users():
    """Check all users in the database"""
    await connect_to_mongo()
    db = get_database()
    
    print("\n=== All Users in Database ===\n")
    
    users = []
    async for user in db.users.find():
        users.append(user)
    
    if not users:
        print("No users found in database.")
    else:
        print(f"Found {len(users)} user(s):\n")
        for i, user in enumerate(users, 1):
            print(f"{i}. Email: {user.get('email')}")
            print(f"   Username: {user.get('username')}")
            print(f"   Full Name: {user.get('full_name')}")
            print(f"   Is Superuser: {user.get('is_superuser', False)}")
            print(f"   Is Active: {user.get('is_active', True)}")
            print(f"   Role IDs: {user.get('role_ids', [])}")
            print(f"   Company ID: {user.get('company_id')}")
            print(f"   Created: {user.get('created_at')}")
            print(f"   Has Password: {'hashed_password' in user}")
            print()
    
    print("\n=== Super Admin Users ===\n")
    
    super_admins = []
    async for user in db.users.find({"is_superuser": True}):
        super_admins.append(user)
    
    if not super_admins:
        print("No super admin users found.")
    else:
        print(f"Found {len(super_admins)} super admin(s)")
    
    await close_mongo_connection()


async def clear_users():
    """Clear all users (use with caution!)"""
    await connect_to_mongo()
    db = get_database()
    
    response = input("\n⚠️  This will delete ALL users. Are you sure? (type 'yes' to confirm): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        await close_mongo_connection()
        return
    
    result = await db.users.delete_many({})
    print(f"Deleted {result.deleted_count} users.")
    
    await close_mongo_connection()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check users in database")
    parser.add_argument('action', choices=['check', 'clear'], 
                        default='check', nargs='?',
                        help='Action to perform (default: check)')
    
    args = parser.parse_args()
    
    if args.action == 'check':
        asyncio.run(check_users())
    elif args.action == 'clear':
        asyncio.run(clear_users())