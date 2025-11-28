#!/usr/bin/env python
"""
Script to check AI agents stored in MongoDB
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
from datetime import datetime
import json

async def check_agents():
    """Check AI agents in MongoDB"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    collection = db.ai_agents
    
    print(f"\n🔍 Checking MongoDB Database: {settings.database_name}")
    print(f"📦 Collection: ai_agents")
    print("=" * 60)
    
    # Count total documents
    count = await collection.count_documents({})
    print(f"\n📊 Total AI Agents in MongoDB: {count}")
    
    if count > 0:
        print("\n📋 AI Agents List:")
        print("-" * 60)
        
        # Fetch all agents
        async for agent in collection.find():
            print(f"\n🤖 Agent: {agent.get('name', 'Unknown')}")
            print(f"   ID: {str(agent['_id'])}")
            print(f"   Description: {agent.get('description', 'N/A')}")
            print(f"   LLM Provider: {agent.get('llm_provider', 'N/A')}")
            print(f"   LLM Model: {agent.get('llm_model', 'N/A')}")
            print(f"   Active: {agent.get('active', False)}")
            print(f"   Created: {agent.get('created_at', 'Unknown')}")
            print(f"   Brand IDs: {agent.get('brand_ids', [])}")
            print(f"   Temperature: {agent.get('temperature', 'N/A')}")
            print(f"   Max Tokens: {agent.get('max_tokens', 'N/A')}")
            
        # Show sample document structure
        print("\n📄 Sample Document Structure:")
        print("-" * 60)
        sample = await collection.find_one()
        if sample:
            sample['_id'] = str(sample['_id'])  # Convert ObjectId to string for JSON
            if 'created_at' in sample and isinstance(sample['created_at'], datetime):
                sample['created_at'] = sample['created_at'].isoformat()
            if 'updated_at' in sample and isinstance(sample['updated_at'], datetime):
                sample['updated_at'] = sample['updated_at'].isoformat()
            print(json.dumps(sample, indent=2, default=str))
    else:
        print("\n❌ No AI agents found in MongoDB")
        print("💡 Create an agent from the UI at http://localhost:8081/ai-agents")
    
    # Check if collection exists
    collections = await db.list_collection_names()
    print(f"\n📚 Available Collections in {settings.database_name}:")
    for coll in collections:
        doc_count = await db[coll].count_documents({})
        print(f"   - {coll}: {doc_count} documents")
    
    client.close()
    print("\n✅ MongoDB check complete!")

if __name__ == "__main__":
    asyncio.run(check_agents())