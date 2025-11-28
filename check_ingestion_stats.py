#!/usr/bin/env python3
"""
Script to check if ingestion_stats are stored in MongoDB
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pprint import pprint
from config.settings import settings

async def check_ingestion_stats():
    """Check MongoDB for documents with ingestion_stats"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    collection = db.knowledge_base_items
    
    print("=" * 80)
    print("Checking MongoDB for documents with ingestion_stats...")
    print("=" * 80)
    
    # Find all documents with ingestion_stats
    cursor = collection.find(
        {"ingestion_stats": {"$exists": True}},
        {
            "title": 1,
            "indexing_status": 1,
            "ingestion_stats": 1,
            "total_tokens": 1,
            "embedding_provider": 1,
            "embedding_model": 1
        }
    )
    
    docs_with_stats = []
    async for doc in cursor:
        docs_with_stats.append(doc)
    
    if docs_with_stats:
        print(f"\nFound {len(docs_with_stats)} documents with ingestion_stats:\n")
        for doc in docs_with_stats:
            print(f"Document: {doc.get('title', 'Unknown')}")
            print(f"ID: {doc['_id']}")
            print(f"Status: {doc.get('indexing_status', 'Unknown')}")
            if 'ingestion_stats' in doc:
                print("Ingestion Stats:")
                pprint(doc['ingestion_stats'], indent=2)
            print("-" * 40)
    else:
        print("\nNo documents found with ingestion_stats.")
        
    # Also check for documents with completed status but no stats
    print("\n" + "=" * 80)
    print("Checking for completed documents without ingestion_stats...")
    print("=" * 80)
    
    cursor2 = collection.find(
        {
            "indexing_status": "completed",
            "ingestion_stats": {"$exists": False}
        },
        {"title": 1, "indexing_status": 1, "updated_at": 1}
    )
    
    docs_without_stats = []
    async for doc in cursor2:
        docs_without_stats.append(doc)
    
    if docs_without_stats:
        print(f"\nFound {len(docs_without_stats)} completed documents WITHOUT ingestion_stats:")
        for doc in docs_without_stats:
            print(f"- {doc.get('title', 'Unknown')} (ID: {doc['_id']})")
    else:
        print("\nAll completed documents have ingestion_stats.")
    
    # Check a random document structure
    print("\n" + "=" * 80)
    print("Sample document structure:")
    print("=" * 80)
    
    sample = await collection.find_one({"indexing_status": "completed"})
    if sample:
        print("\nKeys in document:")
        for key in sorted(sample.keys()):
            value_type = type(sample[key]).__name__
            if key == 'ingestion_stats' and isinstance(sample[key], dict):
                print(f"  {key}: {value_type}")
                for subkey in sorted(sample[key].keys()):
                    print(f"    - {subkey}: {type(sample[key][subkey]).__name__}")
            else:
                print(f"  {key}: {value_type}")

if __name__ == "__main__":
    asyncio.run(check_ingestion_stats())