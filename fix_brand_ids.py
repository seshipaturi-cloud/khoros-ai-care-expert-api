#!/usr/bin/env python3
"""
Fix brand_ids in documents to match the company_id being used
"""

import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_brand_ids():
    """Fix brand_ids in all documents"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    kb_collection = db.knowledge_base_items
    
    try:
        logger.info("🔍 Checking documents in knowledge base...")
        
        # Get all documents with indexing_status: completed
        docs = await kb_collection.find(
            {"indexing_status": "completed"},
            {"_id": 1, "title": 1, "company_id": 1, "brand_id": 1, "brand_ids": 1}
        ).to_list(None)
        
        logger.info(f"📚 Found {len(docs)} completed documents")
        
        if len(docs) == 0:
            logger.warning("No documents found with indexing_status: 'completed'")
            return
        
        # Find the most common company_id
        company_ids = {}
        for doc in docs:
            cid = doc.get('company_id', 'none')
            company_ids[cid] = company_ids.get(cid, 0) + 1
        
        # Get the most common company_id
        most_common_id = max(company_ids, key=company_ids.get)
        
        logger.info(f"\n📊 Company ID distribution:")
        for cid, count in company_ids.items():
            logger.info(f"  - {cid}: {count} documents")
        
        logger.info(f"\n✨ Will standardize all documents to use: {most_common_id}")
        
        # Update all documents to use the same company_id
        update_count = 0
        for doc in docs:
            doc_id = doc['_id']
            current_company = doc.get('company_id')
            
            if current_company != most_common_id:
                result = await kb_collection.update_one(
                    {"_id": doc_id},
                    {
                        "$set": {
                            "company_id": most_common_id,
                            "brand_id": most_common_id,  
                            "brand_ids": [most_common_id]
                        }
                    }
                )
                if result.modified_count > 0:
                    update_count += 1
                    logger.info(f"  ✅ Updated: {doc.get('title', 'Unknown')[:50]}...")
        
        logger.info(f"\n🎉 Updated {update_count} documents")
        
        # Verify the update
        verified_count = await kb_collection.count_documents({
            "company_id": most_common_id,
            "indexing_status": "completed"
        })
        
        logger.info(f"📊 Verification: {verified_count} documents now have company_id = {most_common_id}")
        logger.info(f"\n💡 When calling the API, use company_id = '{most_common_id}'")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_brand_ids())