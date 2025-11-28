#!/usr/bin/env python3
"""
Populate Agent Feedback Collection with Sample Data
Run this script to insert sample feedback into MongoDB
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import random

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

# Sample agent names
AGENT_NAMES = [
    "Sarah Johnson",
    "Michael Chen",
    "Emily Rodriguez",
    "David Kim",
    "Jessica Thompson",
    "Robert Martinez",
    "Amanda Lee",
    "Christopher Brown"
]

# Sample feedback data
SAMPLE_FEEDBACK = [
    {
        "agent_name": "Sarah Johnson",
        "case_id": "32456",
        "category": "improvement",
        "content": "The AI sentiment analysis is great, but it would be helpful to have a confidence score displayed so I know how much to trust the analysis.",
        "rating": 4,
        "source_type": "ai_analysis",
        "is_resolved": False,
        "metadata": {
            "feature_name": "Sentiment Analysis",
            "suggested_improvement": "Add confidence score display"
        }
    },
    {
        "agent_name": "Michael Chen",
        "case_id": "32487",
        "category": "bug",
        "content": "The draft response generator sometimes produces responses in the wrong language. Customer was speaking Spanish but got an English response.",
        "rating": 2,
        "source_type": "draft_response",
        "is_resolved": False,
        "metadata": {
            "feature_name": "Response Generation",
            "error_type": "Language mismatch",
            "expected_language": "Spanish",
            "received_language": "English"
        }
    },
    {
        "agent_name": "Emily Rodriguez",
        "case_id": "32501",
        "category": "praise",
        "content": "The AI analysis saved me so much time today! I was able to handle 3x more cases than usual. The urgency detection is spot on!",
        "rating": 5,
        "source_type": "ai_analysis",
        "is_resolved": True,
        "metadata": {
            "feature_name": "Urgency Detection",
            "time_saved_estimate": "2 hours"
        }
    },
    {
        "agent_name": "David Kim",
        "case_id": "32512",
        "category": "question",
        "content": "How do I customize the tone of the AI-generated draft responses? Some customers prefer more formal language.",
        "rating": 3,
        "source_type": "draft_response",
        "is_resolved": False,
        "metadata": {
            "feature_name": "Response Generation",
            "question_type": "How-to"
        }
    },
    {
        "agent_name": "Jessica Thompson",
        "case_id": "32534",
        "category": "improvement",
        "content": "It would be great if the AI could suggest knowledge base articles to link in the response. Currently I have to search manually.",
        "rating": 4,
        "source_type": "draft_response",
        "is_resolved": False,
        "metadata": {
            "feature_name": "Response Generation",
            "suggested_improvement": "Knowledge base integration"
        }
    },
    {
        "agent_name": "Robert Martinez",
        "case_id": "32567",
        "category": "bug",
        "content": "The sentiment analysis marked a customer as 'angry' when they were just asking a straightforward question. False positive issue.",
        "rating": 2,
        "source_type": "ai_analysis",
        "is_resolved": True,
        "metadata": {
            "feature_name": "Sentiment Analysis",
            "error_type": "False positive",
            "actual_sentiment": "Neutral",
            "detected_sentiment": "Negative/Angry"
        }
    },
    {
        "agent_name": "Amanda Lee",
        "case_id": "32589",
        "category": "praise",
        "content": "Love the multi-language support in draft responses! Helped me respond to a French customer perfectly. Thank you!",
        "rating": 5,
        "source_type": "draft_response",
        "is_resolved": True,
        "metadata": {
            "feature_name": "Multi-language Support",
            "language_used": "French"
        }
    },
    {
        "agent_name": "Christopher Brown",
        "case_id": "32601",
        "category": "improvement",
        "content": "The AI analysis is helpful but takes a bit long to load sometimes (5-10 seconds). Could this be optimized?",
        "rating": 3,
        "source_type": "ai_analysis",
        "is_resolved": False,
        "metadata": {
            "feature_name": "AI Analysis",
            "performance_issue": "Slow loading",
            "avg_load_time": "7 seconds"
        }
    },
    {
        "agent_name": "Sarah Johnson",
        "case_id": "32623",
        "category": "question",
        "content": "Can the draft response AI reference previous conversations with the same customer for better context?",
        "rating": 4,
        "source_type": "draft_response",
        "is_resolved": False,
        "metadata": {
            "feature_name": "Response Generation",
            "question_type": "Feature request",
            "suggested_feature": "Conversation history context"
        }
    },
    {
        "agent_name": "Michael Chen",
        "case_id": "32645",
        "category": "praise",
        "content": "The bot detection feature is amazing! It automatically filtered out 15 spam messages this morning. Big time saver!",
        "rating": 5,
        "source_type": "ai_analysis",
        "is_resolved": True,
        "metadata": {
            "feature_name": "Bot Detection",
            "spam_filtered": 15
        }
    },
    {
        "agent_name": "Emily Rodriguez",
        "case_id": "32678",
        "category": "bug",
        "content": "The draft response included incorrect product information. Need better knowledge base integration to ensure accuracy.",
        "rating": 2,
        "source_type": "draft_response",
        "is_resolved": False,
        "metadata": {
            "feature_name": "Response Generation",
            "error_type": "Incorrect information",
            "issue": "Outdated knowledge base"
        }
    },
    {
        "agent_name": "David Kim",
        "case_id": "32689",
        "category": "improvement",
        "content": "Would love to see the AI suggest which tone to use (professional, friendly, empathetic) based on the customer's sentiment.",
        "rating": 4,
        "source_type": "draft_response",
        "is_resolved": False,
        "metadata": {
            "feature_name": "Response Generation",
            "suggested_improvement": "Automatic tone suggestion"
        }
    },
    {
        "agent_name": "Jessica Thompson",
        "case_id": "32701",
        "category": "praise",
        "content": "The topic extraction is incredibly accurate! It properly categorized a complex multi-issue conversation.",
        "rating": 5,
        "source_type": "ai_analysis",
        "is_resolved": True,
        "metadata": {
            "feature_name": "Topic Extraction",
            "topics_detected": ["Billing", "Technical Support"]
        }
    },
    {
        "agent_name": "Robert Martinez",
        "case_id": "32723",
        "category": "question",
        "content": "Is there a way to train the AI on our company's specific terminology and abbreviations?",
        "rating": 3,
        "source_type": "ai_analysis",
        "is_resolved": False,
        "metadata": {
            "feature_name": "AI Analysis",
            "question_type": "Training/customization"
        }
    },
    {
        "agent_name": "Amanda Lee",
        "case_id": "32745",
        "category": "improvement",
        "content": "Please add a 'copy to clipboard' button for the AI-generated responses. Currently have to select and copy manually.",
        "rating": 4,
        "source_type": "draft_response",
        "is_resolved": True,
        "metadata": {
            "feature_name": "Response Generation",
            "suggested_improvement": "Copy to clipboard button",
            "implementation_status": "Completed"
        }
    }
]


async def populate_feedback():
    """Insert sample feedback into MongoDB"""
    print("🚀 Starting feedback population script...")

    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    collection = db["agent_feedback"]

    print(f"📊 Connected to database: {settings.database_name}")
    print(f"📁 Collection: agent_feedback")

    # Check if feedback already exists
    existing_count = await collection.count_documents({})
    print(f"📝 Current feedback items in database: {existing_count}")

    if existing_count > 0:
        print("⚠️  Feedback already exists. Deleting them and starting fresh...")
        result = await collection.delete_many({})
        print(f"🗑️  Deleted {result.deleted_count} existing feedback items")

    # Add timestamps and ensure all fields
    current_time = datetime.utcnow()
    for i, feedback in enumerate(SAMPLE_FEEDBACK):
        # Add timestamps relative to now (spread over last 7 days)
        days_ago = random.randint(0, 7)
        hours_ago = random.randint(0, 23)
        created_at = current_time - timedelta(days=days_ago, hours=hours_ago)

        feedback["created_at"] = created_at
        feedback["updated_at"] = created_at
        feedback["submitted_by"] = feedback["agent_name"]

        # Add resolved timestamp if resolved
        if feedback["is_resolved"]:
            feedback["resolved_at"] = created_at + timedelta(hours=random.randint(1, 48))
            feedback["resolved_by"] = "admin"

    # Insert feedback
    try:
        result = await collection.insert_many(SAMPLE_FEEDBACK)
        print(f"✅ Successfully inserted {len(result.inserted_ids)} feedback items!")

        # Print summary statistics
        print("\n📊 Feedback Summary:")

        # By category
        categories = {}
        for feedback in SAMPLE_FEEDBACK:
            category = feedback["category"]
            categories[category] = categories.get(category, 0) + 1

        print("\n  By Category:")
        for category, count in sorted(categories.items()):
            print(f"    • {category.capitalize()}: {count}")

        # By source type
        sources = {}
        for feedback in SAMPLE_FEEDBACK:
            source = feedback["source_type"]
            sources[source] = sources.get(source, 0) + 1

        print("\n  By Source:")
        for source, count in sorted(sources.items()):
            source_name = "AI Analysis" if source == "ai_analysis" else "Draft Response"
            print(f"    • {source_name}: {count}")

        # By status
        resolved = sum(1 for f in SAMPLE_FEEDBACK if f["is_resolved"])
        pending = len(SAMPLE_FEEDBACK) - resolved
        print(f"\n  By Status:")
        print(f"    • Pending: {pending}")
        print(f"    • Resolved: {resolved}")

        # By rating
        print(f"\n  By Rating:")
        for rating in range(5, 0, -1):
            count = sum(1 for f in SAMPLE_FEEDBACK if f["rating"] == rating)
            if count > 0:
                print(f"    • {'⭐' * rating}: {count}")

        # Print total count
        total_count = await collection.count_documents({})
        print(f"\n📈 Total feedback in database: {total_count}")

    except Exception as e:
        print(f"❌ Error inserting feedback: {e}")
        import traceback
        traceback.print_exc()

    # Close connection
    client.close()
    print("\n🎉 Feedback population complete!")
    print("\n💡 You can now view the feedback at: http://localhost:8080/aicareexpert/ → Agent Feedback")


if __name__ == "__main__":
    asyncio.run(populate_feedback())
