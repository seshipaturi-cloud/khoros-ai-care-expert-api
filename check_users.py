import asyncio
from app.utils import connect_to_mongo, close_mongo_connection, get_database

async def check_users():
    await connect_to_mongo()
    db = get_database()
    
    print("Checking users in database...")
    print("-" * 50)
    
    users = []
    async for user in db.users.find():
        users.append(user)
        print(f"User: {user.get('email')}")
        print(f"  ID: {user.get('_id')}")
        print(f"  Role: {user.get('role')}")
        print(f"  Roles: {user.get('roles', [])}")
        print(f"  Company ID: {user.get('company_id', 'None')}")
        print()
    
    print(f"Total users: {len(users)}")
    
    if len(users) == 0:
        print("\nNo users found. Creating a test super_admin user...")
        from app.services.auth_service import auth_service
        
        # Create a super admin user
        user_data = {
            "email": "admin@example.com",
            "username": "admin",
            "password": "Admin123!",
            "full_name": "System Admin",
            "role": "super_admin",
            "is_active": True,
            "is_superuser": True
        }
        
        hashed_password = auth_service.hash_password(user_data["password"])
        
        user_doc = {
            "email": user_data["email"],
            "username": user_data["username"],
            "hashed_password": hashed_password,
            "full_name": user_data["full_name"],
            "role": user_data["role"],
            "roles": ["super_admin"],
            "is_active": user_data["is_active"],
            "is_superuser": user_data["is_superuser"],
            "created_at": asyncio.get_event_loop().time(),
            "updated_at": asyncio.get_event_loop().time()
        }
        
        result = await db.users.insert_one(user_doc)
        print(f"Created user: {user_data['email']} with password: {user_data['password']}")
    
    await close_mongo_connection()

asyncio.run(check_users())