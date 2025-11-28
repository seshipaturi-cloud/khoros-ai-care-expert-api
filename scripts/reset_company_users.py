#!/usr/bin/env python3
"""
Script to delete all users except super admin and recreate company users.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from bson import ObjectId

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils import get_database
from app.services.auth_service import auth_service
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def reset_company_users():
    """Delete all users except super admin and recreate company users"""
    db = get_database()
    
    print("Step 1: Deleting all users except super admin...")
    # Delete all users except seshi.paturi@ignitetech.com
    result = await db.users.delete_many({
        "email": {"$ne": "seshi.paturi@ignitetech.com"}
    })
    print(f"  Deleted {result.deleted_count} users")
    
    print("\nStep 2: Getting all companies...")
    companies = await db.companies.find({}).to_list(None)
    
    if not companies:
        print("No companies found in the database!")
        return
    
    print(f"Found {len(companies)} companies")
    
    # Define user templates for each company
    user_templates = {
        "HealthPlus Medical": [
            {
                "email": "michael.williams@healthplusmedical.com",
                "username": "michael.williams",
                "full_name": "Michael Williams",
                "role": "company_admin",
                "is_admin": True
            },
            {
                "email": "sarah.johnson@healthplusmedical.com",
                "username": "sarah.johnson",
                "full_name": "Sarah Johnson",
                "role": "supervisor",
                "is_admin": False
            },
            {
                "email": "david.brown@healthplusmedical.com",
                "username": "david.brown",
                "full_name": "David Brown",
                "role": "agent",
                "is_admin": False
            },
            {
                "email": "lisa.martinez@healthplusmedical.com",
                "username": "lisa.martinez",
                "full_name": "Lisa Martinez",
                "role": "agent",
                "is_admin": False
            }
        ],
        "TechStart Solutions": [
            {
                "email": "john.smith@techstartsolutions.com",
                "username": "john.smith",
                "full_name": "John Smith",
                "role": "company_admin",
                "is_admin": True
            },
            {
                "email": "emily.davis@techstartsolutions.com",
                "username": "emily.davis",
                "full_name": "Emily Davis",
                "role": "supervisor",
                "is_admin": False
            },
            {
                "email": "james.wilson@techstartsolutions.com",
                "username": "james.wilson",
                "full_name": "James Wilson",
                "role": "agent",
                "is_admin": False
            },
            {
                "email": "maria.garcia@techstartsolutions.com",
                "username": "maria.garcia",
                "full_name": "Maria Garcia",
                "role": "agent",
                "is_admin": False
            }
        ],
        "Global Retail Inc": [
            {
                "email": "robert.taylor@globalretailinc.com",
                "username": "robert.taylor",
                "full_name": "Robert Taylor",
                "role": "company_admin",
                "is_admin": True
            },
            {
                "email": "lisa.anderson@globalretailinc.com",
                "username": "lisa.anderson",
                "full_name": "Lisa Anderson",
                "role": "supervisor",
                "is_admin": False
            },
            {
                "email": "thomas.moore@globalretailinc.com",
                "username": "thomas.moore",
                "full_name": "Thomas Moore",
                "role": "agent",
                "is_admin": False
            },
            {
                "email": "jennifer.white@globalretailinc.com",
                "username": "jennifer.white",
                "full_name": "Jennifer White",
                "role": "agent",
                "is_admin": False
            }
        ],
        "FinanceHub Corp": [
            {
                "email": "daniel.martinez@financehubcorp.com",
                "username": "daniel.martinez",
                "full_name": "Daniel Martinez",
                "role": "company_admin",
                "is_admin": True
            },
            {
                "email": "jennifer.garcia@financehubcorp.com",
                "username": "jennifer.garcia",
                "full_name": "Jennifer Garcia",
                "role": "supervisor",
                "is_admin": False
            },
            {
                "email": "christopher.lee@financehubcorp.com",
                "username": "christopher.lee",
                "full_name": "Christopher Lee",
                "role": "agent",
                "is_admin": False
            },
            {
                "email": "amanda.clark@financehubcorp.com",
                "username": "amanda.clark",
                "full_name": "Amanda Clark",
                "role": "agent",
                "is_admin": False
            }
        ],
        "EduTech Academy": [
            {
                "email": "patricia.white@edutechacademy.com",
                "username": "patricia.white",
                "full_name": "Patricia White",
                "role": "company_admin",
                "is_admin": True
            },
            {
                "email": "matthew.harris@edutechacademy.com",
                "username": "matthew.harris",
                "full_name": "Matthew Harris",
                "role": "supervisor",
                "is_admin": False
            },
            {
                "email": "ashley.clark@edutechacademy.com",
                "username": "ashley.clark",
                "full_name": "Ashley Clark",
                "role": "agent",
                "is_admin": False
            },
            {
                "email": "steven.lewis@edutechacademy.com",
                "username": "steven.lewis",
                "full_name": "Steven Lewis",
                "role": "agent",
                "is_admin": False
            }
        ]
    }
    
    # Default password for all users
    default_password = "Pandu01#"
    hashed_password = pwd_context.hash(default_password)
    
    # Get roles collection
    roles_collection = db.roles
    
    # Get all role documents
    role_docs = {}
    async for role in roles_collection.find({}):
        # Handle both role_name and name fields
        role_name = role.get("role_name") or role.get("name")
        if role_name:
            role_docs[role_name] = role
    
    print("\nStep 3: Creating users for each company...")
    total_created = 0
    
    for company in companies:
        company_name = company.get("name")
        company_id = str(company["_id"])
        
        print(f"\nProcessing company: {company_name} (ID: {company_id})")
        
        # Get user templates for this company
        templates = user_templates.get(company_name, [])
        
        if not templates:
            print(f"  No user templates found for {company_name}, creating generic users...")
            # Create generic users if no template exists
            company_slug = company_name.lower().replace(' ', '').replace('.', '')
            templates = [
                {
                    "email": f"admin@{company_slug}.com",
                    "username": f"admin_{company_slug}",
                    "full_name": f"Admin {company_name}",
                    "role": "company_admin",
                    "is_admin": True
                },
                {
                    "email": f"supervisor@{company_slug}.com",
                    "username": f"supervisor_{company_slug}",
                    "full_name": f"Supervisor {company_name}",
                    "role": "supervisor",
                    "is_admin": False
                },
                {
                    "email": f"agent1@{company_slug}.com",
                    "username": f"agent1_{company_slug}",
                    "full_name": f"Agent One {company_name}",
                    "role": "agent",
                    "is_admin": False
                },
                {
                    "email": f"agent2@{company_slug}.com",
                    "username": f"agent2_{company_slug}",
                    "full_name": f"Agent Two {company_name}",
                    "role": "agent",
                    "is_admin": False
                }
            ]
        
        for user_template in templates:
            try:
                # Get role information
                role_name = user_template["role"]
                role_doc = role_docs.get(role_name)
                
                role_ids = []
                roles = []
                
                if role_doc:
                    role_ids = [str(role_doc["_id"])]
                    roles = [{
                        "id": str(role_doc["_id"]),
                        "role_name": role_doc.get("role_name") or role_doc.get("name", role_name),
                        "role_type": role_doc.get("role_type", role_name)
                    }]
                
                # Create new user with all required fields
                user_data = {
                    "email": user_template["email"],
                    "username": user_template["username"],
                    "full_name": user_template["full_name"],
                    "hashed_password": hashed_password,
                    "is_active": True,
                    "is_superuser": False,
                    "role": role_name,  # Store the role name directly
                    "role_ids": role_ids,
                    "roles": roles,
                    "company_id": company_id,  # Store the company ID
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "last_login": None
                }
                
                result = await db.users.insert_one(user_data)
                print(f"  ✓ Created: {user_template['email']} ({role_name})")
                total_created += 1
                
            except Exception as e:
                print(f"  ✗ Error creating {user_template['email']}: {e}")
    
    print(f"\n✅ Successfully created {total_created} users!")
    print(f"📝 Default password for all users: {default_password}")
    
    # Verify the data
    print("\n📊 Verification - Users per company:")
    for company in companies:
        company_name = company.get("name")
        company_id = str(company["_id"])
        
        user_count = await db.users.count_documents({"company_id": company_id})
        print(f"  {company_name}: {user_count} users")

async def main():
    # Connect to MongoDB
    from app.utils import connect_to_mongo, close_mongo_connection
    
    try:
        await connect_to_mongo()
        await reset_company_users()
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main())