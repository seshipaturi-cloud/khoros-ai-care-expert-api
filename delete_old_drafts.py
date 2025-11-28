#!/usr/bin/env python3
"""
Delete old draft responses for a specific case to trigger regeneration
"""
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection details
MONGODB_URI = "mongodb+srv://srp:SiX3ofWhhhjzC2Bz@cluster0.badm4i9.mongodb.net/"
DATABASE_NAME = "ai-care-expert"

async def delete_draft_responses_for_case(case_id):
    """Delete draft responses for a specific case ID"""
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    collection = db.draft_responses

    try:
        # Delete all draft responses for the case
        result = await collection.delete_many({"case_id": case_id})

        print(f"✅ Deleted {result.deleted_count} draft responses for case: {case_id}")

        if result.deleted_count == 0:
            print(f"⚠️  No draft responses found for case: {case_id}")

        return result.deleted_count

    except Exception as e:
        print(f"❌ Error deleting draft responses: {e}")
        return 0
    finally:
        client.close()

async def main():
    case_id = "32305"
    print(f"🗑️  Deleting old draft responses for case: {case_id}")
    print(f"📍 MongoDB: {DATABASE_NAME}")
    print(f"📍 Collection: draft_responses")
    print("-" * 50)

    deleted_count = await delete_draft_responses_for_case(case_id)

    print("-" * 50)
    print(f"✨ Done! Deleted {deleted_count} draft responses")
    print(f"🔄 Now reload the page to trigger regeneration with new bilingual logic")

if __name__ == "__main__":
    asyncio.run(main())
