#!/usr/bin/env python3
"""
MongoDB Collections Initialization Script
Creates all collections with proper indexes and validation rules
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "khoros_care")


class MongoDBInitializer:
    """Initialize MongoDB collections with schemas and indexes"""
    
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGODB_URI)
        self.db = self.client[DATABASE_NAME]
    
    async def create_companies_collection(self):
        """Create and configure companies collection"""
        try:
            # Create collection with validation
            await self.db.create_collection(
                "companies",
                validator={
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": ["name", "code", "subscription", "metadata"],
                        "properties": {
                            "name": {"bsonType": "string"},
                            "code": {"bsonType": "string"},
                            "domain": {"bsonType": "string"},
                            "subscription": {
                                "bsonType": "object",
                                "required": ["plan", "status"],
                                "properties": {
                                    "plan": {"enum": ["starter", "professional", "enterprise", "custom"]},
                                    "status": {"enum": ["active", "suspended", "trial", "expired"]}
                                }
                            }
                        }
                    }
                }
            )
            logger.info("✅ Created companies collection with validation")
        except Exception as e:
            if "already exists" in str(e):
                logger.info("ℹ️ Companies collection already exists")
            else:
                raise
        
        # Create indexes
        collection = self.db.companies
        await collection.create_index("code", unique=True, name="idx_company_code")
        await collection.create_index("subscription.status", name="idx_subscription_status")
        await collection.create_index("metadata.created_at", name="idx_created_at")
        logger.info("✅ Created indexes for companies collection")
    
    async def create_brands_collection(self):
        """Create and configure brands collection"""
        try:
            await self.db.create_collection(
                "brands",
                validator={
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": ["company_id", "name", "code", "status", "metadata"],
                        "properties": {
                            "company_id": {"bsonType": "objectId"},
                            "name": {"bsonType": "string"},
                            "code": {"bsonType": "string"},
                            "status": {"enum": ["active", "inactive", "archived"]}
                        }
                    }
                }
            )
            logger.info("✅ Created brands collection with validation")
        except Exception as e:
            if "already exists" in str(e):
                logger.info("ℹ️ Brands collection already exists")
            else:
                raise
        
        # Create indexes
        collection = self.db.brands
        await collection.create_index("company_id", name="idx_company_id")
        await collection.create_index("code", unique=True, name="idx_brand_code")
        await collection.create_index([("company_id", 1), ("status", 1)], name="idx_company_status")
        logger.info("✅ Created indexes for brands collection")
    
    async def create_users_collection(self):
        """Create and configure users collection"""
        try:
            await self.db.create_collection(
                "users",
                validator={
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": ["company_id", "email", "username", "status", "type", "metadata"],
                        "properties": {
                            "company_id": {"bsonType": "objectId"},
                            "email": {"bsonType": "string"},
                            "username": {"bsonType": "string"},
                            "status": {"enum": ["active", "inactive", "suspended", "pending"]},
                            "type": {"enum": ["internal", "external", "system", "api"]}
                        }
                    }
                }
            )
            logger.info("✅ Created users collection with validation")
        except Exception as e:
            if "already exists" in str(e):
                logger.info("ℹ️ Users collection already exists")
            else:
                raise
        
        # Create indexes
        collection = self.db.users
        await collection.create_index("email", unique=True, name="idx_email")
        await collection.create_index("username", unique=True, name="idx_username")
        await collection.create_index("company_id", name="idx_user_company")
        await collection.create_index([("company_id", 1), ("status", 1)], name="idx_company_user_status")
        await collection.create_index("roles.role_id", name="idx_user_roles")
        await collection.create_index("assignments.teams", name="idx_user_teams")
        logger.info("✅ Created indexes for users collection")
    
    async def create_teams_collection(self):
        """Create and configure teams collection"""
        try:
            await self.db.create_collection(
                "teams",
                validator={
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": ["company_id", "name", "code", "type", "status", "metadata"],
                        "properties": {
                            "company_id": {"bsonType": "objectId"},
                            "name": {"bsonType": "string"},
                            "code": {"bsonType": "string"},
                            "type": {"enum": ["support", "sales", "technical", "social_media", "escalation"]},
                            "status": {"enum": ["active", "inactive", "archived"]}
                        }
                    }
                }
            )
            logger.info("✅ Created teams collection with validation")
        except Exception as e:
            if "already exists" in str(e):
                logger.info("ℹ️ Teams collection already exists")
            else:
                raise
        
        # Create indexes
        collection = self.db.teams
        await collection.create_index("company_id", name="idx_team_company")
        await collection.create_index("code", unique=True, name="idx_team_code")
        await collection.create_index("structure.members.user_id", name="idx_team_members")
        await collection.create_index("brands", name="idx_team_brands")
        logger.info("✅ Created indexes for teams collection")
    
    async def create_roles_collection(self):
        """Create and configure roles collection"""
        try:
            await self.db.create_collection(
                "roles",
                validator={
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": ["name", "display_name", "type", "permissions", "status", "metadata"],
                        "properties": {
                            "name": {"bsonType": "string"},
                            "display_name": {"bsonType": "string"},
                            "type": {"enum": ["system", "company", "custom"]},
                            "status": {"enum": ["active", "inactive", "deprecated"]}
                        }
                    }
                }
            )
            logger.info("✅ Created roles collection with validation")
        except Exception as e:
            if "already exists" in str(e):
                logger.info("ℹ️ Roles collection already exists")
            else:
                raise
        
        # Create indexes
        collection = self.db.roles
        await collection.create_index("name", unique=True, name="idx_role_name")
        await collection.create_index("company_id", name="idx_role_company")
        await collection.create_index("type", name="idx_role_type")
        logger.info("✅ Created indexes for roles collection")
    
    async def create_ai_agents_collection(self):
        """Create and configure ai_agents collection"""
        try:
            await self.db.create_collection(
                "ai_agents",
                validator={
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": ["company_id", "brand_id", "name", "llm_config", "status", "metadata"],
                        "properties": {
                            "company_id": {"bsonType": "objectId"},
                            "brand_id": {"bsonType": "objectId"},
                            "name": {"bsonType": "string"},
                            "status": {"enum": ["active", "inactive", "training", "error"]}
                        }
                    }
                }
            )
            logger.info("✅ Created ai_agents collection with validation")
        except Exception as e:
            if "already exists" in str(e):
                logger.info("ℹ️ AI agents collection already exists")
            else:
                raise
        
        # Create indexes
        collection = self.db.ai_agents
        await collection.create_index("brand_id", unique=True, name="idx_agent_brand")
        await collection.create_index("company_id", name="idx_agent_company")
        await collection.create_index([("company_id", 1), ("status", 1)], name="idx_company_agent_status")
        logger.info("✅ Created indexes for ai_agents collection")
    
    async def create_default_roles(self):
        """Create default system roles"""
        default_roles = [
            {
                "name": "super_admin",
                "display_name": "Super Administrator",
                "description": "Full system access",
                "type": "system",
                "level": 1,
                "permissions": {
                    "messages": {"view": True, "create": True, "edit": True, "delete": True, "assign": True, "close": True},
                    "knowledge_base": {"view": True, "create": True, "edit": True, "delete": True, "approve": True},
                    "ai": {"use_suggestions": True, "override_ai": True, "train_model": True, "configure_ai": True},
                    "brands": {"view": True, "create": True, "edit": True, "delete": True, "configure": True},
                    "teams": {"view": True, "manage_members": True, "configure": True, "view_metrics": True},
                    "users": {"view": True, "create": True, "edit": True, "delete": True, "assign_roles": True},
                    "reports": {"view_own": True, "view_team": True, "view_all": True, "export": True, "create_custom": True},
                    "system": {"access_api": True, "manage_integrations": True, "view_logs": True, "manage_settings": True}
                },
                "config": {
                    "is_system": True,
                    "is_default": False,
                    "can_be_deleted": False,
                    "can_be_modified": False
                },
                "status": "active",
                "metadata": {
                    "created_at": datetime.utcnow(),
                    "created_by": "system",
                    "updated_at": datetime.utcnow(),
                    "updated_by": "system",
                    "version": 1
                }
            },
            {
                "name": "company_admin",
                "display_name": "Company Administrator",
                "description": "Company-level administration",
                "type": "system",
                "level": 2,
                "permissions": {
                    "messages": {"view": True, "create": True, "edit": True, "delete": True, "assign": True, "close": True},
                    "knowledge_base": {"view": True, "create": True, "edit": True, "delete": True, "approve": True},
                    "ai": {"use_suggestions": True, "override_ai": True, "train_model": False, "configure_ai": True},
                    "brands": {"view": True, "create": True, "edit": True, "delete": False, "configure": True},
                    "teams": {"view": True, "manage_members": True, "configure": True, "view_metrics": True},
                    "users": {"view": True, "create": True, "edit": True, "delete": False, "assign_roles": True},
                    "reports": {"view_own": True, "view_team": True, "view_all": True, "export": True, "create_custom": True},
                    "system": {"access_api": True, "manage_integrations": True, "view_logs": False, "manage_settings": False}
                },
                "config": {
                    "is_system": True,
                    "is_default": False,
                    "can_be_deleted": False,
                    "can_be_modified": True
                },
                "status": "active",
                "metadata": {
                    "created_at": datetime.utcnow(),
                    "created_by": "system",
                    "updated_at": datetime.utcnow(),
                    "updated_by": "system",
                    "version": 1
                }
            },
            {
                "name": "support_agent",
                "display_name": "Support Agent",
                "description": "Customer support agent",
                "type": "system",
                "level": 4,
                "permissions": {
                    "messages": {"view": True, "create": True, "edit": True, "delete": False, "assign": True, "close": True},
                    "knowledge_base": {"view": True, "create": False, "edit": False, "delete": False, "approve": False},
                    "ai": {"use_suggestions": True, "override_ai": True, "train_model": False, "configure_ai": False},
                    "brands": {"view": True, "create": False, "edit": False, "delete": False, "configure": False},
                    "teams": {"view": True, "manage_members": False, "configure": False, "view_metrics": True},
                    "users": {"view": True, "create": False, "edit": False, "delete": False, "assign_roles": False},
                    "reports": {"view_own": True, "view_team": False, "view_all": False, "export": False, "create_custom": False},
                    "system": {"access_api": True, "manage_integrations": False, "view_logs": False, "manage_settings": False}
                },
                "config": {
                    "is_system": True,
                    "is_default": True,
                    "can_be_deleted": False,
                    "can_be_modified": True
                },
                "status": "active",
                "metadata": {
                    "created_at": datetime.utcnow(),
                    "created_by": "system",
                    "updated_at": datetime.utcnow(),
                    "updated_by": "system",
                    "version": 1
                }
            }
        ]
        
        # Insert default roles if they don't exist
        for role in default_roles:
            existing = await self.db.roles.find_one({"name": role["name"]})
            if not existing:
                await self.db.roles.insert_one(role)
                logger.info(f"✅ Created default role: {role['display_name']}")
            else:
                logger.info(f"ℹ️ Role already exists: {role['display_name']}")
    
    async def create_sample_data(self):
        """Create sample data for testing"""
        # Check if sample data already exists
        existing_company = await self.db.companies.find_one({"code": "DEMO"})
        if existing_company:
            logger.info("ℹ️ Sample data already exists")
            return
        
        # Create sample company
        company = {
            "name": "Demo Company",
            "code": "DEMO",
            "domain": "demo.example.com",
            "industry": "Technology",
            "size": "medium",
            "contact": {
                "primary_email": "admin@demo.example.com",
                "support_email": "support@demo.example.com",
                "phone": "+1-555-0123"
            },
            "subscription": {
                "plan": "professional",
                "status": "active",
                "billing_cycle": "monthly",
                "start_date": datetime.utcnow()
            },
            "limits": {
                "max_brands": 5,
                "max_users": 50,
                "max_agents": 10,
                "max_teams": 10,
                "storage_quota_gb": 100
            },
            "stats": {
                "total_brands": 1,
                "total_users": 3,
                "total_agents": 1,
                "total_teams": 1
            },
            "metadata": {
                "created_at": datetime.utcnow(),
                "created_by": "system",
                "updated_at": datetime.utcnow(),
                "updated_by": "system",
                "version": 1
            }
        }
        
        company_result = await self.db.companies.insert_one(company)
        company_id = company_result.inserted_id
        logger.info(f"✅ Created sample company: {company['name']}")
        
        # Create sample brand
        brand = {
            "company_id": company_id,
            "name": "Demo Support",
            "code": "DEMO_SUPPORT",
            "description": "Demo customer support brand",
            "website": "https://support.demo.example.com",
            "voice": {
                "tone": "professional",
                "personality_traits": ["helpful", "knowledgeable"],
                "language": {
                    "primary": "en",
                    "supported": ["en"]
                }
            },
            "ai_settings": {
                "enabled": True,
                "llm_provider": "openai",
                "model": "gpt-3.5-turbo",
                "temperature": 0.7
            },
            "status": "active",
            "stats": {
                "total_conversations": 0,
                "avg_response_time_minutes": 0,
                "satisfaction_score": 0
            },
            "metadata": {
                "created_at": datetime.utcnow(),
                "created_by": company_id,
                "updated_at": datetime.utcnow(),
                "updated_by": company_id
            }
        }
        
        brand_result = await self.db.brands.insert_one(brand)
        brand_id = brand_result.inserted_id
        logger.info(f"✅ Created sample brand: {brand['name']}")
        
        # Get admin role
        admin_role = await self.db.roles.find_one({"name": "company_admin"})
        agent_role = await self.db.roles.find_one({"name": "support_agent"})
        
        # Create sample users
        users = [
            {
                "company_id": company_id,
                "email": "admin@demo.example.com",
                "username": "demo_admin",
                "password_hash": "$2b$10$YourHashHere",  # In production, use proper hashing
                "profile": {
                    "first_name": "Demo",
                    "last_name": "Admin",
                    "display_name": "Demo Admin",
                    "job_title": "Administrator"
                },
                "auth": {
                    "email_verified": True,
                    "two_factor_enabled": False
                },
                "roles": [
                    {
                        "role_id": admin_role["_id"],
                        "role_name": "company_admin",
                        "assigned_at": datetime.utcnow(),
                        "assigned_by": "system"
                    }
                ],
                "assignments": {
                    "brands": [brand_id]
                },
                "status": "active",
                "type": "internal",
                "metadata": {
                    "created_at": datetime.utcnow(),
                    "created_by": "system",
                    "updated_at": datetime.utcnow(),
                    "updated_by": "system"
                }
            },
            {
                "company_id": company_id,
                "email": "agent@demo.example.com",
                "username": "demo_agent",
                "password_hash": "$2b$10$YourHashHere",
                "profile": {
                    "first_name": "Demo",
                    "last_name": "Agent",
                    "display_name": "Demo Agent",
                    "job_title": "Support Agent"
                },
                "auth": {
                    "email_verified": True,
                    "two_factor_enabled": False
                },
                "roles": [
                    {
                        "role_id": agent_role["_id"],
                        "role_name": "support_agent",
                        "assigned_at": datetime.utcnow(),
                        "assigned_by": "system"
                    }
                ],
                "assignments": {
                    "brands": [brand_id]
                },
                "status": "active",
                "type": "internal",
                "metadata": {
                    "created_at": datetime.utcnow(),
                    "created_by": "system",
                    "updated_at": datetime.utcnow(),
                    "updated_by": "system"
                }
            }
        ]
        
        for user in users:
            await self.db.users.insert_one(user)
            logger.info(f"✅ Created sample user: {user['email']}")
    
    async def initialize_all(self):
        """Initialize all collections and data"""
        logger.info("🚀 Starting MongoDB initialization...")
        
        try:
            # Create collections
            await self.create_companies_collection()
            await self.create_brands_collection()
            await self.create_users_collection()
            await self.create_teams_collection()
            await self.create_roles_collection()
            await self.create_ai_agents_collection()
            
            # Create default data
            await self.create_default_roles()
            await self.create_sample_data()
            
            logger.info("✨ MongoDB initialization completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error during initialization: {e}")
            raise
        finally:
            self.client.close()


async def main():
    """Main execution"""
    initializer = MongoDBInitializer()
    await initializer.initialize_all()


if __name__ == "__main__":
    asyncio.run(main())