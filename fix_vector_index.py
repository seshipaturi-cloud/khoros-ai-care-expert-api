#!/usr/bin/env python3
"""
Script to fix MongoDB Atlas Vector Search Index
This script will help you delete the old index and create the correct one
"""

import os
import json
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection details from .env
MONGODB_URI = os.getenv('MONGODB_URI')
DATABASE_NAME = os.getenv('MONGODB_DATABASE', 'ai-care-expert')

# Check if environment variables are loaded
if not MONGODB_URI:
    logger.error("❌ MONGODB_URI not found in environment variables")
    logger.info("Please ensure .env file exists and contains MONGODB_URI")
    exit(1)

# Parse MongoDB URI to extract cluster name
import re
cluster_match = re.match(r'mongodb\+srv://[^@]+@([^.]+)\.([^/]+)/?(.*)$', MONGODB_URI)
if cluster_match:
    CLUSTER_NAME = cluster_match.group(1)
    CLUSTER_DOMAIN = cluster_match.group(2)
    logger.info(f"✅ Detected MongoDB Atlas cluster: {CLUSTER_NAME}")
else:
    # Try standard MongoDB URI
    standard_match = re.match(r'mongodb://[^@]+@([^:]+):([^/]+)/?(.*)$', MONGODB_URI)
    if standard_match:
        logger.warning("⚠️  Using standard MongoDB URI. Atlas Search requires MongoDB Atlas.")
        CLUSTER_NAME = "local-cluster"
    else:
        CLUSTER_NAME = "unknown-cluster"
        logger.warning("⚠️  Could not parse cluster name from URI")

# Index configurations
VECTOR_INDEX_CONFIG = {
    "name": "kb_index",
    "type": "vectorSearch",
    "definition": {
        "fields": [
            {
                "path": "embeddings",
                "dimensions": 384,  # HuggingFace dimensions
                "similarity": "cosine",
                "type": "vector"
            }
        ]
    }
}

VECTOR_INDEX_CONFIG_CHUNKS = {
    "name": "kb_vectors_index",
    "type": "vectorSearch", 
    "definition": {
        "fields": [
            {
                "path": "embeddings",
                "dimensions": 384,  # HuggingFace dimensions
                "similarity": "cosine",
                "type": "vector"
            }
        ]
    }
}

# Alternative hybrid index for better search
HYBRID_INDEX_CONFIG = {
    "name": "kb_hybrid_index",
    "type": "search",
    "definition": {
        "mappings": {
            "dynamic": False,
            "fields": {
                "title": {
                    "type": "string",
                    "analyzer": "lucene.standard"
                },
                "description": {
                    "type": "string", 
                    "analyzer": "lucene.standard"
                },
                "indexed_content": {
                    "type": "string",
                    "analyzer": "lucene.standard"
                },
                "company_id": {
                    "type": "string"
                },
                "brand_ids": {
                    "type": "string"
                },
                "ai_agent_ids": {
                    "type": "string"
                }
            }
        }
    }
}

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_current_indexes():
    """Check current indexes in MongoDB"""
    print_section("CHECKING CURRENT INDEXES")
    
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    
    # Check indexes on knowledge_base_items collection
    print("\n📋 Indexes on 'knowledge_base_items' collection:")
    try:
        indexes = db.knowledge_base_items.list_indexes()
        for idx in indexes:
            print(f"  - {idx['name']}: {idx.get('key', 'N/A')}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Check indexes on knowledge_base_vectors collection
    print("\n📋 Indexes on 'knowledge_base_vectors' collection:")
    try:
        indexes = db.knowledge_base_vectors.list_indexes()
        for idx in indexes:
            print(f"  - {idx['name']}: {idx.get('key', 'N/A')}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    client.close()

def generate_atlas_cli_commands():
    """Generate MongoDB Atlas CLI commands"""
    print_section("MONGODB ATLAS CLI COMMANDS")
    
    print("\n📌 Prerequisites:")
    print("  1. Install MongoDB Atlas CLI: https://www.mongodb.com/docs/atlas/cli/stable/install-atlas-cli/")
    print("  2. Configure authentication: atlas auth login")
    print("  3. Set your project: atlas config set project_id <YOUR_PROJECT_ID>")
    print(f"\n📍 Detected Cluster: {CLUSTER_NAME}")
    print(f"📍 Database: {DATABASE_NAME}")
    
    print("\n🗑️  Step 1: Delete existing indexes (if they exist):")
    print("  Run these commands to list and delete existing search indexes:")
    print()
    print("  # List all search indexes")
    print(f"  atlas clusters search indexes list --clusterName {CLUSTER_NAME} --db {DATABASE_NAME} --collection knowledge_base_items")
    print(f"  atlas clusters search indexes list --clusterName {CLUSTER_NAME} --db {DATABASE_NAME} --collection knowledge_base_vectors")
    print()
    print("  # Delete the old index if it exists (replace <INDEX_ID> with actual ID from list)")
    print(f"  atlas clusters search indexes delete <INDEX_ID> --clusterName {CLUSTER_NAME}")
    
    print("\n✨ Step 2: Create new vector search indexes:")
    
    # Save index configs to files
    with open('vector_index_items.json', 'w') as f:
        json.dump(VECTOR_INDEX_CONFIG, f, indent=2)
    print("\n  Created file: vector_index_items.json")
    
    with open('vector_index_chunks.json', 'w') as f:
        json.dump(VECTOR_INDEX_CONFIG_CHUNKS, f, indent=2)
    print("  Created file: vector_index_chunks.json")
    
    with open('hybrid_index.json', 'w') as f:
        json.dump(HYBRID_INDEX_CONFIG, f, indent=2)
    print("  Created file: hybrid_index.json")
    
    print("\n  # Create vector index for knowledge_base_items collection")
    print("  atlas clusters search indexes create \\")
    print(f"    --clusterName {CLUSTER_NAME} \\")
    print(f"    --db {DATABASE_NAME} \\")
    print("    --collection knowledge_base_items \\")
    print("    --file vector_index_items.json")
    
    print("\n  # Create vector index for knowledge_base_vectors collection")
    print("  atlas clusters search indexes create \\")
    print(f"    --clusterName {CLUSTER_NAME} \\")
    print(f"    --db {DATABASE_NAME} \\")
    print("    --collection knowledge_base_vectors \\")
    print("    --file vector_index_chunks.json")
    
    print("\n  # (Optional) Create hybrid search index")
    print("  atlas clusters search indexes create \\")
    print(f"    --clusterName {CLUSTER_NAME} \\")
    print(f"    --db {DATABASE_NAME} \\")
    print("    --collection knowledge_base_items \\")
    print("    --file hybrid_index.json")

def generate_atlas_ui_instructions():
    """Generate instructions for MongoDB Atlas UI"""
    print_section("MONGODB ATLAS UI INSTRUCTIONS")
    
    print("\n🌐 Using MongoDB Atlas Web Interface:")
    print("\n1. Go to your MongoDB Atlas dashboard")
    print("2. Select your cluster")
    print("3. Click on 'Search' tab (Atlas Search)")
    
    print("\n🗑️  Delete Old Index:")
    print("  a. Find index named 'kb_index'")
    print("  b. Click the trash icon to delete it")
    print("  c. Confirm deletion")
    
    print("\n✨ Create New Vector Search Index:")
    print("  a. Click 'Create Search Index'")
    print("  b. Select 'JSON Editor' (not Visual Editor)")
    print(f"  c. Select database: {DATABASE_NAME}")
    print("  d. Select collection: knowledge_base_items")
    print("  e. Paste this JSON configuration:")
    
    print("\n" + json.dumps(VECTOR_INDEX_CONFIG, indent=2))
    
    print("\n  f. Click 'Next'")
    print("  g. Review and click 'Create Search Index'")
    print("  h. Wait for status to become 'Active' (may take a few minutes)")
    
    print("\n✨ Create Vector Index for Chunks Collection:")
    print("  Repeat the above steps but:")
    print("  - Select collection: knowledge_base_vectors")
    print("  - Use this configuration:")
    
    print("\n" + json.dumps(VECTOR_INDEX_CONFIG_CHUNKS, indent=2))

async def test_vector_search():
    """Test if vector search works after fixing the index"""
    print_section("TESTING VECTOR SEARCH")
    
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        
        # Test query embedding (384 dimensions for HuggingFace)
        test_embedding = [0.1] * 384  # Dummy embedding
        
        print("\n🧪 Testing vector search on knowledge_base_vectors collection...")
        
        # Test pipeline
        pipeline = [
            {
                '$vectorSearch': {
                    'index': 'kb_vectors_index',
                    'path': 'embeddings',
                    'queryVector': test_embedding,
                    'numCandidates': 100,
                    'limit': 5
                }
            },
            {
                '$project': {
                    'chunk_text': 1,
                    'score': {'$meta': 'vectorSearchScore'}
                }
            }
        ]
        
        try:
            cursor = db.knowledge_base_vectors.aggregate(pipeline)
            results = await cursor.to_list(length=5)
            
            if results:
                print(f"  ✅ Vector search working! Found {len(results)} results")
                for i, result in enumerate(results, 1):
                    print(f"    {i}. Score: {result.get('score', 0):.4f}")
            else:
                print("  ⚠️  No results found (this is OK if collection is empty)")
                
        except Exception as e:
            print(f"  ❌ Vector search failed: {e}")
            print("     This is expected if the index hasn't been created yet")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        if 'client' in locals():
            client.close()

def generate_code_fix():
    """Show how to fix the code after index is created"""
    print_section("CODE FIX REQUIRED")
    
    print("\n📝 After creating the correct vector index, update the code:")
    print("\nFile: app/services/vector_service.py")
    print("\n1. Remove the temporary fallback code (lines 395-432)")
    print("2. Uncomment the original vector search code")
    print("3. Update the pipeline to use '$vectorSearch' instead of knnBeta:")
    
    print("""
    # Replace the knnBeta query with:
    pipeline = [
        {
            '$vectorSearch': {
                'index': 'kb_vectors_index',
                'path': 'embeddings',
                'queryVector': query_embedding,
                'numCandidates': limit * 10,
                'limit': limit * 3,
                'filter': {
                    # Add filters here if needed
                }
            }
        },
        {
            '$addFields': {
                'score': {'$meta': 'vectorSearchScore'}
            }
        },
        {
            '$match': {
                'score': {'$gte': similarity_threshold}
            }
        },
        {
            '$limit': limit
        }
    ]
    """)

async def check_embedding_dimensions():
    """Check actual embedding dimensions in the database"""
    print_section("CHECKING EMBEDDING DIMENSIONS")
    
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        
        # Check knowledge_base_items
        print("\n📊 Checking knowledge_base_items collection...")
        item = await db.knowledge_base_items.find_one({'embeddings': {'$exists': True}})
        if item and 'embeddings' in item and item['embeddings']:
            if isinstance(item['embeddings'][0], list):
                dim = len(item['embeddings'][0])
            else:
                dim = "Invalid format"
            print(f"  Embedding dimensions: {dim}")
            print(f"  Embedding provider: {item.get('embedding_provider', 'Unknown')}")
            print(f"  Embedding model: {item.get('embedding_model', 'Unknown')}")
        else:
            print("  No documents with embeddings found")
        
        # Check knowledge_base_vectors
        print("\n📊 Checking knowledge_base_vectors collection...")
        vector = await db.knowledge_base_vectors.find_one({'embeddings': {'$exists': True}})
        if vector and 'embeddings' in vector:
            dim = len(vector['embeddings']) if isinstance(vector['embeddings'], list) else "Invalid"
            print(f"  Embedding dimensions: {dim}")
            print(f"  Embedding provider: {vector.get('embedding_provider', 'Unknown')}")
            print(f"  Embedding model: {vector.get('embedding_model', 'Unknown')}")
        else:
            print("  No vector documents found")
            
    except Exception as e:
        print(f"❌ Error checking dimensions: {e}")
    finally:
        if 'client' in locals():
            client.close()

def main():
    """Main function"""
    print("\n" + "🔧 MongoDB Atlas Vector Index Fix Script 🔧".center(60))
    print("This script will help you fix the vector search index issue")
    
    # Check current state
    check_current_indexes()
    
    # Check embedding dimensions
    asyncio.run(check_embedding_dimensions())
    
    # Generate instructions
    generate_atlas_cli_commands()
    generate_atlas_ui_instructions()
    
    # Show code fix
    generate_code_fix()
    
    # Test vector search
    print("\n🧪 Would you like to test vector search? (Only works after index is created)")
    response = input("Test now? (y/n): ").lower()
    if response == 'y':
        asyncio.run(test_vector_search())
    
    print_section("NEXT STEPS")
    print("\n1. Choose either Atlas CLI or Atlas UI method above")
    print("2. Delete the old 'kb_index' if it exists")
    print("3. Create new vector search indexes as shown")
    print("4. Wait for indexes to become 'Active' (2-5 minutes)")
    print("5. Run this script again and test vector search")
    print("6. Update the code as shown in CODE FIX section")
    print("\n✅ Once complete, vector search will work properly!")

if __name__ == "__main__":
    main()