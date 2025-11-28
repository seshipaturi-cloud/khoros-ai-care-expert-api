#!/usr/bin/env python3
"""
Check what brand_ids are actually in the database documents
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_document_brands():
    """Check the brand_ids of all documents in the knowledge base"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    collection = db.knowledge_base_items
    
    try:
        logger.info("Checking all documents in knowledge base...")
        
        # Get all documents
        docs = await collection.find(
            {},
            {"title": 1, "company_id": 1, "brand_id": 1, "brand_ids": 1, "indexing_status": 1, "indexed_content": 1}
        ).to_list(None)
        
        logger.info(f"\n📚 Found {len(docs)} total documents\n")
        
        for doc in docs:
            logger.info(f"Document: {doc.get('title', 'No title')}")
            logger.info(f"  - _id: {doc['_id']}")
            logger.info(f"  - company_id: {doc.get('company_id', 'None')}")
            logger.info(f"  - brand_id: {doc.get('brand_id', 'None')}")
            logger.info(f"  - brand_ids: {doc.get('brand_ids', 'None')}")
            logger.info(f"  - indexing_status: {doc.get('indexing_status', 'None')}")
            
            # Check if it contains the audio transcript
            content = doc.get('indexed_content', '')
            if '27 emotions' in content.lower():
                logger.info(f"  ✅ This document contains '27 emotions' audio transcript!")
            
            logger.info("")
        
        # Summary
        logger.info("\n📊 Summary:")
        
        # Count by company_id
        company_ids = {}
        for doc in docs:
            cid = doc.get('company_id', 'None')
            company_ids[cid] = company_ids.get(cid, 0) + 1
        
        logger.info("Documents by company_id:")
        for cid, count in company_ids.items():
            logger.info(f"  - {cid}: {count} documents")
        
        # Count by brand_id
        brand_ids = {}
        for doc in docs:
            bid = doc.get('brand_id', 'None')
            brand_ids[bid] = brand_ids.get(bid, 0) + 1
        
        logger.info("\nDocuments by brand_id:")
        for bid, count in brand_ids.items():
            logger.info(f"  - {bid}: {count} documents")
            
        logger.info("\n💡 To search these documents, use the correct brand_id/company_id in your query!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_document_brands())