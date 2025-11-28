#!/usr/bin/env python3
"""
Script to update brand_ids in documents to match search queries
"""

import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_brand_ids(target_brand_id=None):
    """Update brand_ids in all documents"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    collection = db.knowledge_base_items
    
    try:
        logger.info("Checking current brand_ids in documents...")
        
        # First, get all unique brand_ids and company_ids
        docs = await collection.find(
            {"indexing_status": "completed"},
            {"company_id": 1, "brand_id": 1, "brand_ids": 1, "title": 1}
        ).to_list(None)
        
        logger.info(f"\n📚 Found {len(docs)} completed documents\n")
        
        # Collect unique IDs
        company_ids = set()
        brand_ids = set()
        
        for doc in docs:
            if doc.get('company_id'):
                company_ids.add(doc['company_id'])
            if doc.get('brand_id'):
                brand_ids.add(doc['brand_id'])
            if doc.get('brand_ids'):
                for bid in doc['brand_ids']:
                    brand_ids.add(bid)
        
        logger.info("Unique company_ids found:")
        for cid in company_ids:
            count = await collection.count_documents({"company_id": cid})
            logger.info(f"  - {cid}: {count} documents")
        
        logger.info("\nUnique brand_ids found:")
        for bid in brand_ids:
            count = await collection.count_documents({"brand_id": bid})
            logger.info(f"  - {bid}: {count} documents")
        
        if target_brand_id:
            logger.info(f"\n🔄 Updating all documents to use brand_id: {target_brand_id}")
            
            # Update all documents to use the target brand_id
            result = await collection.update_many(
                {"indexing_status": "completed"},
                {
                    "$set": {
                        "company_id": target_brand_id,
                        "brand_id": target_brand_id,
                        "brand_ids": [target_brand_id]
                    }
                }
            )
            
            logger.info(f"✅ Updated {result.modified_count} documents")
            
            # Verify the update
            updated_count = await collection.count_documents({
                "company_id": target_brand_id,
                "indexing_status": "completed"
            })
            logger.info(f"📊 Verification: {updated_count} documents now have company_id = {target_brand_id}")
            
        else:
            # If no target brand_id provided, suggest what to do
            if len(company_ids) == 1:
                existing_id = list(company_ids)[0]
                logger.info(f"\n💡 All documents use company_id: {existing_id}")
                logger.info(f"   Your API calls should use: company_id='{existing_id}'")
            elif len(company_ids) > 1:
                logger.info("\n⚠️  Multiple company_ids found. To standardize, run:")
                logger.info(f"   python update_brand_ids.py <target_brand_id>")
            else:
                logger.info("\n⚠️  No company_ids found in documents")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        
    finally:
        client.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        asyncio.run(update_brand_ids(target))
    else:
        asyncio.run(update_brand_ids())