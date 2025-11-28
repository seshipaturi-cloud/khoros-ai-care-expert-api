#!/usr/bin/env python3
"""
Check what agent-related fields are in the documents
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_agent_fields():
    """Check agent-related fields in documents"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    collection = db.knowledge_base_items
    
    try:
        logger.info("Checking agent-related fields in documents...")
        
        # Get a few documents to see their structure
        docs = await collection.find(
            {"indexing_status": "completed"},
            {}
        ).limit(5).to_list(None)
        
        logger.info(f"\n📚 Found {len(docs)} documents\n")
        
        # Check what agent fields exist
        agent_fields = set()
        
        for i, doc in enumerate(docs, 1):
            logger.info(f"Document {i}: {doc.get('title', 'No title')[:50]}...")
            
            # Check various possible agent field names
            possible_fields = [
                'agent_id', 'agent_ids', 
                'ai_agent_id', 'ai_agent_ids',
                'agentId', 'agentIds'
            ]
            
            for field in possible_fields:
                if field in doc:
                    value = doc[field]
                    agent_fields.add(field)
                    logger.info(f"  ✅ {field}: {value}")
            
            # Also check all fields that contain 'agent'
            for key in doc.keys():
                if 'agent' in key.lower() and key not in possible_fields:
                    logger.info(f"  📌 {key}: {doc[key]}")
                    agent_fields.add(key)
            
            logger.info("")
        
        # Summary
        logger.info("=" * 50)
        logger.info("📊 Summary of agent fields found:")
        for field in agent_fields:
            count = await collection.count_documents({field: {"$exists": True}})
            logger.info(f"  - {field}: {count} documents")
        
        # Check specific agent_id
        target_agent_id = "68c5b3a37742559e25e0fdf3"  # The one from frontend
        logger.info(f"\n🔍 Looking for documents with agent_id: {target_agent_id}")
        
        for field in agent_fields:
            # Check if it's an array field or single value
            if 'ids' in field:
                count = await collection.count_documents({field: target_agent_id})
            else:
                count = await collection.count_documents({field: target_agent_id})
            
            if count > 0:
                logger.info(f"  ✅ Found {count} documents with {field} = {target_agent_id}")
                
                # Show a sample
                sample = await collection.find_one({field: target_agent_id})
                if sample:
                    logger.info(f"     Sample: {sample.get('title', 'No title')[:50]}...")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_agent_fields())