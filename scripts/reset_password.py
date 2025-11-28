"""
Reset password for a user
"""

import asyncio
import sys
from pathlib import Path
import getpass

sys.path.append(str(Path(__file__).parent.parent))

from app.utils import connect_to_mongo, close_mongo_connection, get_database
from app.services.auth_service import auth_service


async def reset_password():
    """Reset password for a user"""
    await connect_to_mongo()
    db = get_database()
    
    print("\n=== Reset User Password ===\n")
    
    email = input("Enter user email: ").strip()
    
    if not email:
        print("❌ Email is required!")
        await close_mongo_connection()
        return
    
    # Find user
    user = await db.users.find_one({"email": email})
    
    if not user:
        print(f"❌ User with email '{email}' not found!")
        await close_mongo_connection()
        return
    
    print(f"\nFound user:")
    print(f"  Email: {user.get('email')}")
    print(f"  Username: {user.get('username')}")
    print(f"  Full Name: {user.get('full_name')}")
    print(f"  Is Super Admin: {user.get('is_superuser', False)}")
    
    confirm = input("\nReset password for this user? (yes/no): ").lower()
    if confirm != 'yes':
        print("Cancelled.")
        await close_mongo_connection()
        return
    
    # Get new password
    new_password = getpass.getpass("Enter new password (min 8 chars): ")
    confirm_password = getpass.getpass("Confirm new password: ")
    
    if len(new_password) < 8:
        print("❌ Password must be at least 8 characters!")
        await close_mongo_connection()
        return
    
    if new_password != confirm_password:
        print("❌ Passwords do not match!")
        await close_mongo_connection()
        return
    
    # Update password
    hashed_password = auth_service.get_password_hash(new_password)
    
    await db.users.update_one(
        {"email": email},
        {"$set": {"hashed_password": hashed_password}}
    )
    
    print("\n✅ Password reset successfully!")
    print(f"   User can now login with email: {email}")
    
    await close_mongo_connection()


async def quick_reset_super_admin():
    """Quick reset for super admin with default password"""
    await connect_to_mongo()
    db = get_database()
    
    print("\n=== Quick Reset Super Admin Password ===\n")
    
    # Find super admin
    super_admin = await db.users.find_one({"is_superuser": True})
    
    if not super_admin:
        print("❌ No super admin user found!")
        print("   Run: python scripts/create_super_admin.py create")
        await close_mongo_connection()
        return
    
    print(f"Found super admin: {super_admin.get('email')}")
    
    # Set default password
    default_password = "SuperAdmin123!"
    hashed_password = auth_service.get_password_hash(default_password)
    
    await db.users.update_one(
        {"_id": super_admin["_id"]},
        {"$set": {"hashed_password": hashed_password}}
    )
    
    print("\n✅ Password reset successfully!")
    print(f"   Email: {super_admin.get('email')}")
    print(f"   Password: {default_password}")
    print("\n⚠️  Please change this password after logging in!")
    
    await close_mongo_connection()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Reset user password")
    parser.add_argument('--quick', action='store_true',
                        help='Quick reset super admin to default password')
    
    args = parser.parse_args()
    
    if args.quick:
        asyncio.run(quick_reset_super_admin())
    else:
        asyncio.run(reset_password())