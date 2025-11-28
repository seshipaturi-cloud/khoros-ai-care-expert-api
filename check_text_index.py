#!/usr/bin/env python3
"""
Check and create text indexes for knowledge base search
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_and_create_indexes():
    """Check existing indexes and create text index if needed"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    collection = db.knowledge_base_items
    
    try:
        # List existing indexes
        logger.info("Checking existing indexes...")
        indexes = await collection.list_indexes().to_list(None)
        
        logger.info("Current indexes:")
        for idx in indexes:
            logger.info(f"  - {idx['name']}: {idx.get('key', {})}")
        
        # Check if text index exists
        has_text_index = any('text' in str(idx.get('key', {})) for idx in indexes)
        
        if not has_text_index:
            logger.info("\n⚠️  No text index found. Creating text index...")
            
            # Create compound text index on searchable fields
            await collection.create_index([
                ("title", "text"),
                ("description", "text"),
                ("indexed_content", "text"),
                ("content", "text"),
                ("chunks.content", "text")
            ])
            
            logger.info("✅ Text index created successfully")
        else:
            logger.info("✅ Text index already exists")
        
        # Also ensure we have indexes for common query fields
        logger.info("\nEnsuring other important indexes...")
        
        # Index for company_id and indexing_status
        await collection.create_index([
            ("company_id", 1),
            ("indexing_status", 1)
        ])
        
        # Index for brand_id and indexing_status
        await collection.create_index([
            ("brand_id", 1),
            ("indexing_status", 1)
        ])
        
        # Index for brand_ids array
        await collection.create_index([
            ("brand_ids", 1),
            ("indexing_status", 1)
        ])
        
        logger.info("✅ All indexes verified/created")
        
        # Test search on a sample query
        logger.info("\n🔍 Testing text search...")
        
        # Search for "27 emotions" 
        test_query = "27 emotions"
        results = await collection.find(
            {"$text": {"$search": test_query}},
            {"title": 1, "indexed_content": 1}
        ).limit(5).to_list(None)
        
        logger.info(f"Found {len(results)} results for '{test_query}':")
        for doc in results:
            title = doc.get('title', 'No title')
            content_preview = doc.get('indexed_content', '')[:200]
            logger.info(f"  - {title}: {content_preview}...")
            
            # Check if "27 emotions" is in the content
            if '27 emotions' in doc.get('indexed_content', '').lower():
                logger.info("    ✅ Contains '27 emotions'!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_and_create_indexes())