#!/usr/bin/env python3
"""
Populate Tags Collection with Sample Data
Run this script to insert sample tags into MongoDB
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

# Sample tags data
SAMPLE_TAGS = [
    # Sentiment Tags
    {
        "name": "Positive",
        "description": "Positive customer sentiment or feedback",
        "category": "Sentiment",
        "color": "#22d3ee",
        "enabled": True,
        "usage_count": 145,
        "last_used": datetime.utcnow(),
        "metadata": {"priority": "medium"}
    },
    {
        "name": "Negative",
        "description": "Negative customer sentiment or complaint",
        "category": "Sentiment",
        "color": "#ef4444",
        "enabled": True,
        "usage_count": 89,
        "last_used": datetime.utcnow(),
        "metadata": {"priority": "high"}
    },
    {
        "name": "Neutral",
        "description": "Neutral customer sentiment",
        "category": "Sentiment",
        "color": "#94a3b8",
        "enabled": True,
        "usage_count": 203,
        "last_used": datetime.utcnow(),
        "metadata": {"priority": "low"}
    },

    # Priority Tags
    {
        "name": "Urgent",
        "description": "Requires immediate attention",
        "category": "Priority",
        "color": "#dc2626",
        "enabled": True,
        "usage_count": 67,
        "last_used": datetime.utcnow(),
        "metadata": {"sla": "1 hour"}
    },
    {
        "name": "High Priority",
        "description": "Important but not urgent",
        "category": "Priority",
        "color": "#f59e0b",
        "enabled": True,
        "usage_count": 112,
        "last_used": datetime.utcnow(),
        "metadata": {"sla": "4 hours"}
    },
    {
        "name": "Low Priority",
        "description": "Can be handled when time permits",
        "category": "Priority",
        "color": "#10b981",
        "enabled": True,
        "usage_count": 234,
        "last_used": datetime.utcnow(),
        "metadata": {"sla": "24 hours"}
    },

    # Topic Tags
    {
        "name": "Billing",
        "description": "Questions or issues related to billing",
        "category": "Topic",
        "color": "#8b5cf6",
        "enabled": True,
        "usage_count": 178,
        "last_used": datetime.utcnow(),
        "metadata": {"department": "finance"}
    },
    {
        "name": "Technical Support",
        "description": "Technical issues or support requests",
        "category": "Topic",
        "color": "#3b82f6",
        "enabled": True,
        "usage_count": 456,
        "last_used": datetime.utcnow(),
        "metadata": {"department": "engineering"}
    },
    {
        "name": "Account Management",
        "description": "Account settings and management",
        "category": "Topic",
        "color": "#06b6d4",
        "enabled": True,
        "usage_count": 89,
        "last_used": datetime.utcnow(),
        "metadata": {"department": "customer_success"}
    },
    {
        "name": "Feature Request",
        "description": "Customer requesting new features",
        "category": "Topic",
        "color": "#14b8a6",
        "enabled": True,
        "usage_count": 134,
        "last_used": datetime.utcnow(),
        "metadata": {"department": "product"}
    },

    # Product Tags
    {
        "name": "AI Features",
        "description": "Related to AI-powered features",
        "category": "Product",
        "color": "#a855f7",
        "enabled": True,
        "usage_count": 267,
        "last_used": datetime.utcnow(),
        "metadata": {"product_line": "ai"}
    },
    {
        "name": "Knowledge Base",
        "description": "Knowledge base related inquiries",
        "category": "Product",
        "color": "#ec4899",
        "enabled": True,
        "usage_count": 156,
        "last_used": datetime.utcnow(),
        "metadata": {"product_line": "kb"}
    },
    {
        "name": "Analytics",
        "description": "Analytics and reporting features",
        "category": "Product",
        "color": "#f97316",
        "enabled": True,
        "usage_count": 98,
        "last_used": datetime.utcnow(),
        "metadata": {"product_line": "analytics"}
    },

    # Issue Tags
    {
        "name": "Bug",
        "description": "Software bug or error",
        "category": "Issue",
        "color": "#dc2626",
        "enabled": True,
        "usage_count": 87,
        "last_used": datetime.utcnow(),
        "metadata": {"severity": "medium"}
    },
    {
        "name": "Performance Issue",
        "description": "Slow performance or latency",
        "category": "Issue",
        "color": "#ea580c",
        "enabled": True,
        "usage_count": 45,
        "last_used": datetime.utcnow(),
        "metadata": {"severity": "high"}
    },
    {
        "name": "Integration Issue",
        "description": "Problems with third-party integrations",
        "category": "Issue",
        "color": "#d97706",
        "enabled": True,
        "usage_count": 67,
        "last_used": datetime.utcnow(),
        "metadata": {"severity": "medium"}
    },

    # General Tags
    {
        "name": "Follow-up Required",
        "description": "Needs follow-up action",
        "category": "General",
        "color": "#0891b2",
        "enabled": True,
        "usage_count": 234,
        "last_used": datetime.utcnow(),
        "metadata": {}
    },
    {
        "name": "Resolved",
        "description": "Issue has been resolved",
        "category": "General",
        "color": "#16a34a",
        "enabled": True,
        "usage_count": 567,
        "last_used": datetime.utcnow(),
        "metadata": {}
    },
    {
        "name": "Escalated",
        "description": "Escalated to higher support tier",
        "category": "General",
        "color": "#dc2626",
        "enabled": True,
        "usage_count": 34,
        "last_used": datetime.utcnow(),
        "metadata": {}
    },
    {
        "name": "Feedback",
        "description": "Customer feedback or suggestions",
        "category": "General",
        "color": "#6366f1",
        "enabled": True,
        "usage_count": 189,
        "last_used": datetime.utcnow(),
        "metadata": {}
    }
]


async def populate_tags():
    """Insert sample tags into MongoDB"""
    print("🚀 Starting tags population script...")

    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    collection = db["tags"]

    print(f"📊 Connected to database: {settings.database_name}")

    # Check if tags already exist
    existing_count = await collection.count_documents({})
    print(f"📝 Current tags in database: {existing_count}")

    if existing_count > 0:
        # Auto-delete existing tags
        print("⚠️  Tags already exist. Deleting them and starting fresh...")
        result = await collection.delete_many({})
        print(f"🗑️  Deleted {result.deleted_count} existing tags")

    # Add timestamps
    for tag in SAMPLE_TAGS:
        tag["created_at"] = datetime.utcnow()
        tag["updated_at"] = datetime.utcnow()
        tag["created_by"] = "system"
        tag["updated_by"] = "system"

    # Insert tags
    try:
        result = await collection.insert_many(SAMPLE_TAGS)
        print(f"✅ Successfully inserted {len(result.inserted_ids)} tags!")

        # Print summary by category
        print("\n📊 Tags Summary by Category:")
        categories = {}
        for tag in SAMPLE_TAGS:
            category = tag["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(tag["name"])

        for category, tag_names in sorted(categories.items()):
            print(f"\n  {category} ({len(tag_names)} tags):")
            for name in tag_names:
                print(f"    • {name}")

        # Print total count
        total_count = await collection.count_documents({})
        print(f"\n📈 Total tags in database: {total_count}")

    except Exception as e:
        print(f"❌ Error inserting tags: {e}")

    # Close connection
    client.close()
    print("\n🎉 Tags population complete!")


if __name__ == "__main__":
    asyncio.run(populate_tags())
