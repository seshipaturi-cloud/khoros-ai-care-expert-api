"""
Simple script to populate AI models with correct schema
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from config.settings import settings

SAMPLE_COMPANY_ID = "company_123"


async def get_db():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    return client[settings.mongodb_database]


async def populate_ai_models():
    """Populate AI models with correct schema matching AIModelCreate"""
    db = await get_db()
    collection = db["ai_models"]

    # Clear existing data
    await collection.delete_many({"company_id": SAMPLE_COMPANY_ID})

    ai_models = [
        # OpenAI GPT-4 Turbo
        {
            "company_id": SAMPLE_COMPANY_ID,
            "provider_id": "provider_openai_001",
            "name": "GPT-4 Turbo",
            "model_identifier": "gpt-4-turbo-2024-04-09",
            "version": "2024-04-09",
            "model_type": "chat",
            "capabilities": ["function_calling", "streaming", "vision", "json_mode"],
            "description": "Most capable GPT-4 model with 128K context window, optimized for chat and reasoning tasks",
            "context_window": 128000,
            "max_output_tokens": 4096,
            "default_temperature": 0.7,
            "default_top_p": 1.0,
            "default_frequency_penalty": 0.0,
            "default_presence_penalty": 0.0,
            "input_cost_per_1k_tokens": 0.01,
            "output_cost_per_1k_tokens": 0.03,
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_vision": True,
            "supports_audio": False,
            "monthly_request_quota": 100000,
            "monthly_token_quota": 10000000,
            "max_cost_per_month": 1000.0,
            "priority": 1,
            "enabled": True,
            "tags": ["production", "gpt4", "vision"],
            "metadata": {"provider": "OpenAI", "release_date": "2024-04-09"},
            "status": "active",
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "avg_latency_ms": 0.0,
            "success_rate": 100.0,
            "requests_this_month": 0,
            "tokens_this_month": 0,
            "cost_this_month": 0.0,
            "quota_exceeded": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin",
            "updated_by": "admin"
        },

        # OpenAI GPT-3.5 Turbo
        {
            "company_id": SAMPLE_COMPANY_ID,
            "provider_id": "provider_openai_001",
            "name": "GPT-3.5 Turbo",
            "model_identifier": "gpt-3.5-turbo",
            "version": "0125",
            "model_type": "chat",
            "capabilities": ["function_calling", "streaming", "json_mode"],
            "description": "Fast and cost-effective model for most conversational and text generation tasks",
            "context_window": 16385,
            "max_output_tokens": 4096,
            "default_temperature": 0.7,
            "default_top_p": 1.0,
            "default_frequency_penalty": 0.0,
            "default_presence_penalty": 0.0,
            "input_cost_per_1k_tokens": 0.0005,
            "output_cost_per_1k_tokens": 0.0015,
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_vision": False,
            "supports_audio": False,
            "monthly_request_quota": 500000,
            "monthly_token_quota": 50000000,
            "max_cost_per_month": 500.0,
            "priority": 2,
            "enabled": True,
            "tags": ["production", "cost-effective"],
            "metadata": {"provider": "OpenAI"},
            "status": "active",
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "avg_latency_ms": 0.0,
            "success_rate": 100.0,
            "requests_this_month": 0,
            "tokens_this_month": 0,
            "cost_this_month": 0.0,
            "quota_exceeded": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin",
            "updated_by": "admin"
        },

        # Anthropic Claude 3.5 Sonnet
        {
            "company_id": SAMPLE_COMPANY_ID,
            "provider_id": "provider_anthropic_001",
            "name": "Claude 3.5 Sonnet",
            "model_identifier": "claude-3-5-sonnet-20241022",
            "version": "20241022",
            "model_type": "chat",
            "capabilities": ["function_calling", "streaming", "vision", "tool_use"],
            "description": "Most intelligent Claude model with 200K context, excellent for complex reasoning and coding",
            "context_window": 200000,
            "max_output_tokens": 8192,
            "default_temperature": 1.0,
            "default_top_p": 1.0,
            "default_top_k": 5,
            "default_frequency_penalty": 0.0,
            "default_presence_penalty": 0.0,
            "input_cost_per_1k_tokens": 0.003,
            "output_cost_per_1k_tokens": 0.015,
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_vision": True,
            "supports_audio": False,
            "monthly_request_quota": 100000,
            "monthly_token_quota": 20000000,
            "max_cost_per_month": 2000.0,
            "priority": 1,
            "enabled": True,
            "tags": ["production", "claude", "reasoning"],
            "metadata": {"provider": "Anthropic", "release_date": "2024-10-22"},
            "status": "active",
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "avg_latency_ms": 0.0,
            "success_rate": 100.0,
            "requests_this_month": 0,
            "tokens_this_month": 0,
            "cost_this_month": 0.0,
            "quota_exceeded": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin",
            "updated_by": "admin"
        },

        # Anthropic Claude 3.5 Haiku
        {
            "company_id": SAMPLE_COMPANY_ID,
            "provider_id": "provider_anthropic_001",
            "name": "Claude 3.5 Haiku",
            "model_identifier": "claude-3-5-haiku-20241022",
            "version": "20241022",
            "model_type": "chat",
            "capabilities": ["function_calling", "streaming", "vision"],
            "description": "Fast and cost-effective Claude model for quick responses and high-volume tasks",
            "context_window": 200000,
            "max_output_tokens": 8192,
            "default_temperature": 1.0,
            "default_top_p": 1.0,
            "default_top_k": 5,
            "default_frequency_penalty": 0.0,
            "default_presence_penalty": 0.0,
            "input_cost_per_1k_tokens": 0.0008,
            "output_cost_per_1k_tokens": 0.004,
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_vision": True,
            "supports_audio": False,
            "monthly_request_quota": 500000,
            "monthly_token_quota": 50000000,
            "max_cost_per_month": 1000.0,
            "priority": 2,
            "enabled": True,
            "tags": ["production", "fast", "cost-effective"],
            "metadata": {"provider": "Anthropic", "release_date": "2024-10-22"},
            "status": "active",
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "avg_latency_ms": 0.0,
            "success_rate": 100.0,
            "requests_this_month": 0,
            "tokens_this_month": 0,
            "cost_this_month": 0.0,
            "quota_exceeded": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin",
            "updated_by": "admin"
        },

        # Google Gemini 1.5 Pro
        {
            "company_id": SAMPLE_COMPANY_ID,
            "provider_id": "provider_google_001",
            "name": "Gemini 1.5 Pro",
            "model_identifier": "gemini-1.5-pro",
            "version": "latest",
            "model_type": "multimodal",
            "capabilities": ["function_calling", "streaming", "vision", "audio", "code"],
            "description": "Google's most capable multimodal model with 2M context window",
            "context_window": 2000000,
            "max_output_tokens": 8192,
            "default_temperature": 1.0,
            "default_top_p": 0.95,
            "default_top_k": 40,
            "default_frequency_penalty": 0.0,
            "default_presence_penalty": 0.0,
            "input_cost_per_1k_tokens": 0.00125,
            "output_cost_per_1k_tokens": 0.005,
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_vision": True,
            "supports_audio": True,
            "monthly_request_quota": 200000,
            "monthly_token_quota": 100000000,
            "max_cost_per_month": 1500.0,
            "priority": 1,
            "enabled": True,
            "tags": ["production", "multimodal", "long-context"],
            "metadata": {"provider": "Google", "max_context": "2M"},
            "status": "active",
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "avg_latency_ms": 0.0,
            "success_rate": 100.0,
            "requests_this_month": 0,
            "tokens_this_month": 0,
            "cost_this_month": 0.0,
            "quota_exceeded": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin",
            "updated_by": "admin"
        },

        # OpenAI Embeddings
        {
            "company_id": SAMPLE_COMPANY_ID,
            "provider_id": "provider_openai_001",
            "name": "Text Embedding 3 Large",
            "model_identifier": "text-embedding-3-large",
            "version": "large",
            "model_type": "embeddings",
            "capabilities": [],
            "description": "Most capable embedding model for semantic search and retrieval",
            "context_window": 8191,
            "max_output_tokens": 3072,
            "default_temperature": 0.0,
            "default_top_p": 1.0,
            "default_frequency_penalty": 0.0,
            "default_presence_penalty": 0.0,
            "input_cost_per_1k_tokens": 0.00013,
            "output_cost_per_1k_tokens": 0.0,
            "supports_streaming": False,
            "supports_function_calling": False,
            "supports_vision": False,
            "supports_audio": False,
            "monthly_request_quota": 1000000,
            "monthly_token_quota": 100000000,
            "max_cost_per_month": 100.0,
            "priority": 1,
            "enabled": True,
            "tags": ["production", "embeddings", "rag"],
            "metadata": {"provider": "OpenAI", "dimensions": 3072},
            "status": "active",
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "avg_latency_ms": 0.0,
            "success_rate": 100.0,
            "requests_this_month": 0,
            "tokens_this_month": 0,
            "cost_this_month": 0.0,
            "quota_exceeded": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin",
            "updated_by": "admin"
        },
    ]

    # Insert models
    if ai_models:
        result = await collection.insert_many(ai_models)
        print(f"✅ Inserted {len(result.inserted_ids)} AI models")

        # Get the inserted IDs
        model_ids = [str(id) for id in result.inserted_ids]
        print(f"📝 Model IDs: {model_ids}")
        return model_ids
    else:
        print("⚠️  No models to insert")
        return []


async def update_ai_features_with_models(model_ids):
    """Update AI features to attach real model IDs"""
    db = await get_db()
    features_collection = db["ai_features"]

    # Get all features
    features = await features_collection.find({"company_id": SAMPLE_COMPANY_ID}).to_list(length=None)

    if not features or not model_ids:
        print("⚠️  No features or models to update")
        return

    # Attach 1-3 random models to each feature
    import random

    for feature in features:
        num_models = random.randint(1, min(3, len(model_ids)))
        attached_models = random.sample(model_ids, num_models)

        await features_collection.update_one(
            {"_id": feature["_id"]},
            {"$set": {"attached_models": attached_models}}
        )

    print(f"✅ Updated {len(features)} features with attached model IDs")


async def main():
    print("🚀 Starting AI Models population...")
    print(f"📊 Database: {settings.mongodb_database}")
    print(f"🏢 Company ID: {SAMPLE_COMPANY_ID}\n")

    # Populate AI models
    model_ids = await populate_ai_models()

    # Update AI features with model IDs
    if model_ids:
        print("\n🔗 Updating AI Features with model IDs...")
        await update_ai_features_with_models(model_ids)

    print("\n✨ Population complete!")


if __name__ == "__main__":
    asyncio.run(main())
