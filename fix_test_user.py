#!/usr/bin/env python3
"""
Fix the test user to have all required fields
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
import logging
from passlib.context import CryptContext
from datetime import datetime, timezone
from bson import ObjectId

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def fix_test_user():
    """Fix the test user with all required fields"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    users_collection = db.users
    
    try:
        # The company_id from your documents
        company_id = "68c6a8c80fa016e20482025f"
        
        # Delete existing test user if exists
        await users_collection.delete_one({"email": "test@example.com"})
        logger.info("Deleted existing test user (if any)")
        
        # Create new test user with all required fields
        test_user = {
            "_id": str(ObjectId()),
            "email": "test@example.com",
            "password": pwd_context.hash("test123"),  # Password: test123
            "name": "Test User",
            "company_id": company_id,
            "is_active": True,
            "is_verified": True,  # Add verified status
            "is_superuser": False,
            "roles": [],  # Empty roles array
            "permissions": [],  # Empty permissions
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "last_login": None,
            "failed_login_attempts": 0,
            "account_locked_until": None
        }
        
        result = await users_collection.insert_one(test_user)
        logger.info("✅ Created test user with all fields:")
        logger.info(f"   Email: test@example.com")
        logger.info(f"   Password: test123")
        logger.info(f"   Company ID: {company_id}")
        logger.info(f"   User ID: {test_user['_id']}")
        
        # Verify the user was created
        created_user = await users_collection.find_one({"email": "test@example.com"})
        if created_user:
            logger.info("\n📋 User fields:")
            for key, value in created_user.items():
                if key != "password":  # Don't print password hash
                    logger.info(f"   {key}: {value}")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_test_user())