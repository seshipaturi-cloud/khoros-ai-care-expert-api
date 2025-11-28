#!/usr/bin/env python3
"""
Check user's company_id
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_users():
    """Check users and their company_ids"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    users_collection = db.users
    
    try:
        logger.info("Checking users and their company_ids...")
        
        # Get all users
        users = await users_collection.find(
            {},
            {"email": 1, "name": 1, "company_id": 1, "is_active": 1}
        ).to_list(None)
        
        logger.info(f"\n📚 Found {len(users)} users:\n")
        
        for user in users:
            logger.info(f"User: {user.get('email', 'No email')}")
            logger.info(f"  Name: {user.get('name', 'No name')}")
            logger.info(f"  Company ID: {user.get('company_id', 'NONE')}")
            logger.info(f"  Active: {user.get('is_active', False)}")
            logger.info("")
            
            if not user.get('company_id'):
                logger.warning(f"  ⚠️  User {user.get('email')} has NO company_id!")
        
        # Update users without company_id
        target_company_id = "68c6a8c80fa016e20482025f"
        
        logger.info("-" * 50)
        logger.info(f"Updating users without company_id to use: {target_company_id}")
        
        result = await users_collection.update_many(
            {"$or": [
                {"company_id": None},
                {"company_id": ""},
                {"company_id": {"$exists": False}}
            ]},
            {"$set": {"company_id": target_company_id}}
        )
        
        logger.info(f"✅ Updated {result.modified_count} users with company_id")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_users())