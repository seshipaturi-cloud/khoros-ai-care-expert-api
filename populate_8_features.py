"""
Script to populate 8 AI features with proper data structure
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from config.settings import settings
import random

SAMPLE_COMPANY_ID = "company_123"


async def get_db():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    return client[settings.mongodb_database]


async def get_existing_model_ids():
    """Get existing AI model IDs to attach to features"""
    db = await get_db()
    models_collection = db["ai_models"]

    models = await models_collection.find({"company_id": SAMPLE_COMPANY_ID}).to_list(length=None)
    model_ids = [str(model["_id"]) for model in models]
    print(f"📋 Found {len(model_ids)} existing AI models")
    return model_ids


async def populate_features():
    """Populate 8 AI features with realistic data"""
    db = await get_db()
    collection = db["ai_features"]

    # Get existing model IDs to attach
    model_ids = await get_existing_model_ids()

    if not model_ids:
        print("⚠️  No AI models found. Please populate AI models first.")
        return

    features = [
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Sentiment Analysis",
            "feature_type": "Analysis",
            "description": "Detect customer emotions and urgency levels in conversations using advanced NLP",
            "icon": "😊",
            "status": "active",
            "enabled": True,
            "attached_models": random.sample(model_ids, min(3, len(model_ids))),
            "attached_model_names": [],
            "config": {
                "sensitivity": "high",
                "threshold": 0.85,
                "categories": ["Positive", "Neutral", "Negative", "Urgent"]
            },
            "tags": ["production", "nlp", "analysis"],
            "metadata": {},
            "total_conversations": 12543,
            "total_analyses": 12543,
            "accuracy_rate": 94.2,
            "success_rate": 98.5,
            "avg_processing_time_ms": 320.0,
            "last_used": datetime.utcnow(),
            "conversations_this_month": 4521,
            "analyses_this_month": 4521,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin",
            "updated_by": "admin"
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Auto-Tagging",
            "feature_type": "Classification",
            "description": "Automatically categorize conversations with relevant tags and topics",
            "icon": "🏷️",
            "status": "active",
            "enabled": True,
            "attached_models": random.sample(model_ids, min(2, len(model_ids))),
            "attached_model_names": [],
            "config": {
                "max_tags": 5,
                "confidence_threshold": 0.8,
                "custom_categories": ["Product", "Billing", "Technical", "Shipping", "Returns"]
            },
            "tags": ["production", "automation"],
            "metadata": {},
            "total_conversations": 15234,
            "total_analyses": 15234,
            "accuracy_rate": 91.8,
            "success_rate": 99.2,
            "avg_processing_time_ms": 280.0,
            "last_used": datetime.utcnow(),
            "conversations_this_month": 5432,
            "analyses_this_month": 5432,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin",
            "updated_by": "admin"
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Response Generation",
            "feature_type": "Generation",
            "description": "Generate AI-powered draft responses for customer inquiries",
            "icon": "✍️",
            "status": "active",
            "enabled": True,
            "attached_models": random.sample(model_ids, min(4, len(model_ids))),
            "attached_model_names": [],
            "config": {
                "tone": "professional",
                "max_length": 500,
                "include_signature": True
            },
            "tags": ["production", "generation"],
            "metadata": {},
            "total_conversations": 8932,
            "total_analyses": 8932,
            "accuracy_rate": 88.5,
            "success_rate": 96.3,
            "avg_processing_time_ms": 850.0,
            "last_used": datetime.utcnow(),
            "conversations_this_month": 3245,
            "analyses_this_month": 3245,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin",
            "updated_by": "admin"
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Bot Detection",
            "feature_type": "Detection",
            "description": "Filter spam and bot messages with advanced pattern recognition",
            "icon": "🤖",
            "status": "active",
            "enabled": True,
            "attached_models": random.sample(model_ids, min(2, len(model_ids))),
            "attached_model_names": [],
            "config": {
                "strictness": "high",
                "auto_block": True,
                "confidence_threshold": 0.95
            },
            "tags": ["production", "security"],
            "metadata": {},
            "total_conversations": 23445,
            "total_analyses": 23445,
            "accuracy_rate": 96.7,
            "success_rate": 99.5,
            "avg_processing_time_ms": 150.0,
            "last_used": datetime.utcnow(),
            "conversations_this_month": 8765,
            "analyses_this_month": 8765,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin",
            "updated_by": "admin"
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Urgency Classification",
            "feature_type": "Priority",
            "description": "Prioritize critical conversations and escalate urgent issues",
            "icon": "🎯",
            "status": "active",
            "enabled": True,
            "attached_models": random.sample(model_ids, min(2, len(model_ids))),
            "attached_model_names": [],
            "config": {
                "levels": 5,
                "escalation_threshold": 4,
                "auto_escalate": True
            },
            "tags": ["production", "priority"],
            "metadata": {},
            "total_conversations": 7821,
            "total_analyses": 7821,
            "accuracy_rate": 89.3,
            "success_rate": 97.8,
            "avg_processing_time_ms": 290.0,
            "last_used": datetime.utcnow(),
            "conversations_this_month": 2934,
            "analyses_this_month": 2934,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin",
            "updated_by": "admin"
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Intent Detection",
            "feature_type": "Analysis",
            "description": "Understand customer intent and route to appropriate workflows",
            "icon": "🧠",
            "status": "active",
            "enabled": True,
            "attached_models": random.sample(model_ids, min(3, len(model_ids))),
            "attached_model_names": [],
            "config": {
                "intent_types": 25,
                "confidence_threshold": 0.8,
                "custom_intents": ["refund_request", "product_inquiry", "complaint", "feedback"]
            },
            "tags": ["production", "routing"],
            "metadata": {},
            "total_conversations": 11234,
            "total_analyses": 11234,
            "accuracy_rate": 90.1,
            "success_rate": 97.5,
            "avg_processing_time_ms": 310.0,
            "last_used": datetime.utcnow(),
            "conversations_this_month": 4123,
            "analyses_this_month": 4123,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin",
            "updated_by": "admin"
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Language Detection",
            "feature_type": "NLP",
            "description": "Automatically detect conversation language and route to appropriate agents",
            "icon": "🌍",
            "status": "active",
            "enabled": True,
            "attached_models": random.sample(model_ids, min(1, len(model_ids))),
            "attached_model_names": [],
            "config": {
                "supported_languages": ["en", "es", "fr", "de", "pt", "zh", "ja"],
                "auto_translate": False,
                "confidence_threshold": 0.9
            },
            "tags": ["production", "i18n"],
            "metadata": {},
            "total_conversations": 9456,
            "total_analyses": 9456,
            "accuracy_rate": 98.2,
            "success_rate": 99.8,
            "avg_processing_time_ms": 120.0,
            "last_used": datetime.utcnow(),
            "conversations_this_month": 3456,
            "analyses_this_month": 3456,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin",
            "updated_by": "admin"
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Conversation Summarization",
            "feature_type": "Generation",
            "description": "Generate concise summaries of customer conversations",
            "icon": "📝",
            "status": "active",
            "enabled": True,
            "attached_models": random.sample(model_ids, min(2, len(model_ids))),
            "attached_model_names": [],
            "config": {
                "max_summary_length": 150,
                "include_action_items": True,
                "highlight_sentiment": True
            },
            "tags": ["production"],
            "metadata": {},
            "total_conversations": 5432,
            "total_analyses": 5432,
            "accuracy_rate": 87.9,
            "success_rate": 96.3,
            "avg_processing_time_ms": 800.0,
            "last_used": datetime.utcnow(),
            "conversations_this_month": 1987,
            "analyses_this_month": 1987,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin",
            "updated_by": "admin"
        }
    ]

    # Insert features
    if features:
        result = await collection.insert_many(features)
        print(f"✅ Inserted {len(result.inserted_ids)} AI features")

        # Print feature names
        print("\n📝 Created features:")
        for feature in features:
            print(f"  - {feature['icon']} {feature['name']} ({feature['feature_type']})")
            print(f"    Attached models: {len(feature['attached_models'])}")


async def main():
    print("🚀 Starting AI Features population...")
    print(f"📊 Database: {settings.mongodb_database}")
    print(f"🏢 Company ID: {SAMPLE_COMPANY_ID}\n")

    await populate_features()

    print("\n✨ Population complete!")


if __name__ == "__main__":
    asyncio.run(main())
