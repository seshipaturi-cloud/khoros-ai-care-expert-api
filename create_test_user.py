#!/usr/bin/env python3
"""
Create a test user for testing the chat API
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
import logging
from passlib.context import CryptContext
from datetime import datetime
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_user():
    """Create a test user"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    users_collection = db.users
    
    try:
        # The company_id from your documents
        company_id = "68c6a8c80fa016e20482025f"
        
        # Check if test user already exists
        existing_user = await users_collection.find_one({"email": "test@example.com"})
        
        if existing_user:
            logger.info("✅ Test user already exists:")
            logger.info(f"   Email: test@example.com")
            logger.info(f"   Company ID: {existing_user.get('company_id')}")
            
            # Update company_id if needed
            if existing_user.get('company_id') != company_id:
                await users_collection.update_one(
                    {"email": "test@example.com"},
                    {"$set": {"company_id": company_id}}
                )
                logger.info(f"   Updated company_id to: {company_id}")
        else:
            # Create new test user
            test_user = {
                "email": "test@example.com",
                "password": pwd_context.hash("test123"),  # Password: test123
                "name": "Test User",
                "company_id": company_id,
                "is_active": True,
                "is_superuser": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await users_collection.insert_one(test_user)
            logger.info("✅ Created test user:")
            logger.info(f"   Email: test@example.com")
            logger.info(f"   Password: test123")
            logger.info(f"   Company ID: {company_id}")
            logger.info(f"   User ID: {result.inserted_id}")
        
        # List all users
        logger.info("\n📚 All users in database:")
        users = await users_collection.find({}, {"email": 1, "name": 1, "company_id": 1, "is_active": 1}).to_list(None)
        for user in users:
            logger.info(f"   - {user.get('email', 'No email')} ({user.get('name', 'No name')})")
            logger.info(f"     Company: {user.get('company_id', 'No company')}")
            logger.info(f"     Active: {user.get('is_active', False)}")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_test_user())