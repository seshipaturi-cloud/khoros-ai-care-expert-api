#!/usr/bin/env python3
"""
Script to create company_admin and regular users for each company in the system.
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

async def create_company_users():
    """Create company_admin and regular users for each company"""
    db = get_database()
    
    print("Getting all companies...")
    companies = await db.companies.find({}).to_list(None)
    
    if not companies:
        print("No companies found in the database!")
        return
    
    print(f"Found {len(companies)} companies")
    
    # Define user templates
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
            }
        ]
    }
    
    # Default password for all users
    default_password = "Pandu01#"
    hashed_password = pwd_context.hash(default_password)
    
    for company in companies:
        company_name = company.get("name")
        company_id = str(company["_id"])
        
        print(f"\nProcessing company: {company_name} (ID: {company_id})")
        
        # Get user templates for this company
        templates = user_templates.get(company_name, [])
        
        if not templates:
            print(f"  No user templates found for {company_name}, creating generic users...")
            # Create generic users if no template exists
            templates = [
                {
                    "email": f"admin@{company_name.lower().replace(' ', '')}.com",
                    "username": f"admin_{company_name.lower().replace(' ', '_')}",
                    "full_name": f"Admin {company_name}",
                    "role": "company_admin",
                    "is_admin": True
                },
                {
                    "email": f"supervisor@{company_name.lower().replace(' ', '')}.com",
                    "username": f"supervisor_{company_name.lower().replace(' ', '_')}",
                    "full_name": f"Supervisor {company_name}",
                    "role": "supervisor",
                    "is_admin": False
                },
                {
                    "email": f"agent@{company_name.lower().replace(' ', '')}.com",
                    "username": f"agent_{company_name.lower().replace(' ', '_')}",
                    "full_name": f"Agent {company_name}",
                    "role": "agent",
                    "is_admin": False
                }
            ]
        
        # Find or create role documents
        roles_collection = db.roles
        
        for user_template in templates:
            try:
                # Check if user already exists
                existing_user = await db.users.find_one({
                    "$or": [
                        {"email": user_template["email"]},
                        {"username": user_template["username"]}
                    ]
                })
                
                if existing_user:
                    print(f"  User {user_template['email']} already exists, updating company info...")
                    
                    # Update existing user with company info
                    await db.users.update_one(
                        {"_id": existing_user["_id"]},
                        {
                            "$set": {
                                "company_id": company_id,
                                "role": user_template["role"],
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                else:
                    # Find the role document
                    role_doc = await roles_collection.find_one({"role_name": user_template["role"]})
                    role_ids = []
                    roles = []
                    
                    if role_doc:
                        role_ids = [str(role_doc["_id"])]
                        roles = [{
                            "id": str(role_doc["_id"]),
                            "role_name": role_doc["role_name"],
                            "role_type": role_doc.get("role_type", user_template["role"])
                        }]
                    
                    # Create new user
                    user_data = {
                        "email": user_template["email"],
                        "username": user_template["username"],
                        "full_name": user_template["full_name"],
                        "hashed_password": hashed_password,
                        "is_active": True,
                        "is_superuser": False,
                        "role": user_template["role"],
                        "role_ids": role_ids,
                        "roles": roles,
                        "company_id": company_id,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "last_login": None
                    }
                    
                    result = await db.users.insert_one(user_data)
                    print(f"  Created user: {user_template['email']} with role: {user_template['role']}")
                    
            except Exception as e:
                print(f"  Error creating user {user_template['email']}: {e}")
    
    print("\n✅ Company users creation completed!")
    print(f"Default password for all new users: {default_password}")

async def main():
    # Connect to MongoDB
    from app.utils import connect_to_mongo, close_mongo_connection
    
    try:
        await connect_to_mongo()
        await create_company_users()
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main())