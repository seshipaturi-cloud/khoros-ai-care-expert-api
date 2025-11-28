import asyncio
from app.utils import connect_to_mongo, close_mongo_connection, get_database
from bson import ObjectId

async def check_and_fix_users():
    await connect_to_mongo()
    db = get_database()
    
    print("Checking user roles...")
    print("-" * 50)
    
    # Find the user
    user = await db.users.find_one({"email": "seshi.paturi@ignitetech.com"})
    if user:
        print(f"User: {user.get('email')}")
        print(f"  Current role field: {user.get('role')}")
        print(f"  Current roles field: {user.get('roles')}")
        print(f"  Is superuser: {user.get('is_superuser')}")
        
        # Update to have super_admin role
        update_result = await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "role": "super_admin",
                    "roles": [{"role_id": "1", "role_name": "super_admin", "assigned_at": "2024-01-01", "is_primary": True}],
                    "is_superuser": True,
                    "is_active": True
                }
            }
        )
        print(f"\nUpdated user with super_admin role: {update_result.modified_count} document(s) modified")
    
    # Check all users
    print("\nAll users in database:")
    async for user in db.users.find():
        print(f"  - {user.get('email')}: role={user.get('role')}, roles={len(user.get('roles', []))} items")
    
    await close_mongo_connection()

asyncio.run(check_and_fix_users())