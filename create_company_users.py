import asyncio
import random
from datetime import datetime
from app.utils import connect_to_mongo, close_mongo_connection, get_database
from app.services.auth_service import auth_service

# Sample user data for each company
company_users = {
    "company_admin": {
        "first_names": ["John", "Sarah", "Michael", "Emily", "David"],
        "last_names": ["Smith", "Johnson", "Williams", "Brown", "Davis"],
        "password": "Admin123!"
    },
    "regular_users": [
        {
            "first_names": ["Alice", "Bob", "Carol", "Dan", "Eve"],
            "last_names": ["Anderson", "Baker", "Clark", "Edwards", "Fisher"],
            "role": "agent",
            "password": "Agent123!"
        },
        {
            "first_names": ["Frank", "Grace", "Henry", "Iris", "Jack"],
            "last_names": ["Garcia", "Hall", "Irving", "Jones", "King"],
            "role": "supervisor",
            "password": "Super123!"
        }
    ]
}

async def create_company_users():
    await connect_to_mongo()
    db = get_database()
    
    print("Creating users for each company...")
    print("-" * 50)
    
    # Get all companies
    companies = []
    async for company in db.companies.find():
        companies.append(company)
    
    print(f"Found {len(companies)} companies")
    
    for idx, company in enumerate(companies):
        company_id = str(company["_id"])
        company_name = company.get("name", "Unknown")
        print(f"\n{idx + 1}. Creating users for company: {company_name}")
        
        # Create company_admin user
        admin_first = company_users["company_admin"]["first_names"][idx % 5]
        admin_last = company_users["company_admin"]["last_names"][idx % 5]
        admin_email = f"{admin_first.lower()}.{admin_last.lower()}@{company_name.lower().replace(' ', '').replace('-', '')}.com"
        admin_username = f"{admin_first.lower()}{admin_last.lower()[0]}"
        
        # Check if admin already exists
        existing_admin = await db.users.find_one({"email": admin_email})
        if not existing_admin:
            admin_user = {
                "email": admin_email,
                "username": admin_username,
                "hashed_password": auth_service.get_password_hash(company_users["company_admin"]["password"]),
                "full_name": f"{admin_first} {admin_last}",
                "first_name": admin_first,
                "last_name": admin_last,
                "role": "company_admin",
                "roles": [{
                    "role_id": f"ca_{idx}",
                    "role_name": "company_admin",
                    "assigned_at": datetime.utcnow().isoformat(),
                    "is_primary": True
                }],
                "company_id": company_id,
                "company_name": company_name,
                "is_active": True,
                "is_superuser": False,
                "email_verified": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await db.users.insert_one(admin_user)
            print(f"  ✅ Created company_admin: {admin_email} (Password: {company_users['company_admin']['password']})")
        else:
            print(f"  ⚠️  Company admin already exists: {admin_email}")
        
        # Create regular users (2 agents and 1 supervisor per company)
        for user_idx, user_type in enumerate(company_users["regular_users"]):
            # Create 2 agents
            num_users = 2 if user_type["role"] == "agent" else 1
            for i in range(num_users):
                user_first = user_type["first_names"][(idx * 2 + i) % 5]
                user_last = user_type["last_names"][(idx * 2 + i) % 5]
                user_email = f"{user_first.lower()}.{user_last.lower()}{i+1 if num_users > 1 else ''}@{company_name.lower().replace(' ', '').replace('-', '')}.com"
                user_username = f"{user_first.lower()}{user_last.lower()[0]}{i+1 if num_users > 1 else ''}"
                
                # Check if user already exists
                existing_user = await db.users.find_one({"email": user_email})
                if not existing_user:
                    regular_user = {
                        "email": user_email,
                        "username": user_username,
                        "hashed_password": auth_service.get_password_hash(user_type["password"]),
                        "full_name": f"{user_first} {user_last}",
                        "first_name": user_first,
                        "last_name": user_last,
                        "role": user_type["role"],
                        "roles": [{
                            "role_id": f"{user_type['role'][:2]}_{idx}_{i}",
                            "role_name": user_type["role"],
                            "assigned_at": datetime.utcnow().isoformat(),
                            "is_primary": True
                        }],
                        "company_id": company_id,
                        "company_name": company_name,
                        "is_active": True,
                        "is_superuser": False,
                        "email_verified": True,
                        "status": "active",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    result = await db.users.insert_one(regular_user)
                    print(f"  ✅ Created {user_type['role']}: {user_email} (Password: {user_type['password']})")
                else:
                    print(f"  ⚠️  User already exists: {user_email}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("Summary of all users:")
    print("=" * 50)
    
    user_count = await db.users.count_documents({})
    print(f"Total users in database: {user_count}")
    
    print("\nUsers by role:")
    for role in ["super_admin", "company_admin", "supervisor", "agent"]:
        count = await db.users.count_documents({"role": role})
        print(f"  {role}: {count}")
    
    print("\nUsers by company:")
    for company in companies:
        company_id = str(company["_id"])
        company_name = company.get("name", "Unknown")
        count = await db.users.count_documents({"company_id": company_id})
        print(f"  {company_name}: {count} users")
    
    print("\n" + "=" * 50)
    print("Login credentials:")
    print("=" * 50)
    print("Company Admins: Password = Admin123!")
    print("Supervisors: Password = Super123!")
    print("Agents: Password = Agent123!")
    
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(create_company_users())