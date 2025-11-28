#!/usr/bin/env python3
"""
Create necessary indexes for MongoDB collections
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_indexes():
    """Create all necessary indexes for the application"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    
    try:
        # Create text index for knowledge_base_items collection
        kb_collection = db.knowledge_base_items
        
        # Drop existing text index if it exists (to avoid conflicts)
        try:
            await kb_collection.drop_index("text_index")
            logger.info("Dropped existing text index")
        except:
            pass
        
        # Create compound text index on searchable fields
        await kb_collection.create_index(
            [
                ("title", "text"),
                ("description", "text"),
                ("indexed_content", "text")
            ],
            name="text_index",
            default_language="english"
        )
        logger.info("Created text index on knowledge_base_items collection")
        
        # Create regular indexes for frequently queried fields
        await kb_collection.create_index("brand_id")
        await kb_collection.create_index("indexing_status")
        await kb_collection.create_index("content_type")
        await kb_collection.create_index([("brand_id", 1), ("indexing_status", 1)])
        logger.info("Created regular indexes on knowledge_base_items")
        
        # Create indexes for chat_sessions collection
        chat_collection = db.chat_sessions
        await chat_collection.create_index("brand_id")
        await chat_collection.create_index("user_id")
        await chat_collection.create_index([("brand_id", 1), ("user_id", 1)])
        await chat_collection.create_index("last_updated")
        logger.info("Created indexes on chat_sessions collection")
        
        logger.info("All indexes created successfully!")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_indexes())