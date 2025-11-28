#!/usr/bin/env python3
"""
Update documents to include the agent_id being sent by frontend
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_agent_ids():
    """Add frontend's agent_id to all documents"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    collection = db.knowledge_base_items
    
    try:
        # The agent_id from frontend
        frontend_agent_id = "68c5b3a37742559e25e0fdf3"
        
        logger.info(f"Adding agent_id {frontend_agent_id} to all documents...")
        
        # Get all completed documents
        docs = await collection.find(
            {"indexing_status": "completed"},
            {"_id": 1, "title": 1, "ai_agent_ids": 1}
        ).to_list(None)
        
        logger.info(f"Found {len(docs)} documents to update\n")
        
        updated_count = 0
        
        for doc in docs:
            current_agent_ids = doc.get('ai_agent_ids', [])
            
            # Add the frontend agent_id if not already present
            if frontend_agent_id not in current_agent_ids:
                new_agent_ids = current_agent_ids + [frontend_agent_id]
                
                result = await collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"ai_agent_ids": new_agent_ids}}
                )
                
                if result.modified_count > 0:
                    updated_count += 1
                    logger.info(f"✅ Updated: {doc.get('title', 'Unknown')[:50]}...")
                    logger.info(f"   Old agent_ids: {current_agent_ids}")
                    logger.info(f"   New agent_ids: {new_agent_ids}")
            else:
                logger.info(f"⏭️  Skipped (already has agent_id): {doc.get('title', 'Unknown')[:50]}...")
        
        logger.info(f"\n✨ Updated {updated_count} documents")
        
        # Verify
        count = await collection.count_documents({
            "ai_agent_ids": frontend_agent_id,
            "indexing_status": "completed"
        })
        
        logger.info(f"📊 Verification: {count} documents now have agent_id {frontend_agent_id}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(update_agent_ids())