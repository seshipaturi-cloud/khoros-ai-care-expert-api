"""
Populate MongoDB with realistic AI Models and AI Features data
Creates 20-30 AI models and 10 AI features for testing
"""

import asyncio
from datetime import datetime, timedelta
import random
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
from bson import ObjectId

# Sample company ID (replace with actual company ID from your DB)
SAMPLE_COMPANY_ID = "company_123"


async def get_db():
    """Get database connection"""
    client = AsyncIOMotorClient(settings.mongodb_uri)
    return client[settings.mongodb_database]


async def populate_ai_models():
    """Populate 25 AI models covering all provider types"""
    db = await get_db()
    collection = db["ai_models"]

    # Clear existing data (optional - comment out to keep existing)
    # await collection.delete_many({"company_id": SAMPLE_COMPANY_ID})

    ai_models = [
        # OpenAI Models
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "OpenAI GPT-4 Turbo",
            "provider_type": "openai",
            "models": [{
                "model_id": "gpt-4-turbo-2024-04-09",
                "display_name": "GPT-4 Turbo",
                "max_tokens": 128000,
                "max_input_tokens": 128000,
                "max_output_tokens": 4096,
                "input_cost_per_1k_tokens": 0.01,
                "output_cost_per_1k_tokens": 0.03,
                "default_temperature": 0.7,
                "supports_streaming": True,
                "supports_functions": True
            }],
            "default_model_id": "gpt-4-turbo-2024-04-09",
            "credentials": {
                "api_key": "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx",
                "custom_endpoint_url": "https://api.openai.com/v1"
            },
            "rate_limits": {
                "requests_per_minute": 500,
                "requests_per_hour": 10000,
                "tokens_per_minute": 150000,
                "concurrent_requests": 20
            },
            "status": "active",
            "auto_fallback_enabled": True,
            "retry_attempts": 3,
            "timeout_seconds": 30,
            "total_requests": random.randint(50000, 150000),
            "total_tokens": random.randint(5000000, 15000000),
            "total_errors": random.randint(100, 500),
            "avg_latency_ms": round(random.uniform(0.5, 1.5), 2),
            "success_rate": round(random.uniform(97.0, 99.9), 2),
            "tokens_used_this_month": random.randint(500000, 2000000),
            "requests_this_month": random.randint(5000, 20000),
            "cost_this_month": round(random.uniform(500, 2000), 2),
            "last_used": datetime.utcnow() - timedelta(minutes=random.randint(1, 60)),
            "description": "Primary GPT-4 Turbo for complex analysis and generation tasks",
            "tags": ["production", "high-priority", "analysis"],
            "created_at": datetime.utcnow() - timedelta(days=90),
            "updated_at": datetime.utcnow() - timedelta(days=1),
            "created_by": "admin"
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "OpenAI GPT-4o",
            "provider_type": "openai",
            "models": [{
                "model_id": "gpt-4o",
                "display_name": "GPT-4o",
                "max_tokens": 128000,
                "input_cost_per_1k_tokens": 0.005,
                "output_cost_per_1k_tokens": 0.015,
                "default_temperature": 0.7,
                "supports_streaming": True,
                "supports_functions": True
            }],
            "default_model_id": "gpt-4o",
            "credentials": {
                "api_key": "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx"
            },
            "rate_limits": {
                "requests_per_minute": 500,
                "tokens_per_minute": 150000
            },
            "status": "active",
            "retry_attempts": 3,
            "timeout_seconds": 30,
            "total_requests": random.randint(80000, 200000),
            "avg_latency_ms": round(random.uniform(0.3, 0.8), 2),
            "success_rate": round(random.uniform(98.0, 99.9), 2),
            "cost_this_month": round(random.uniform(300, 1500), 2),
            "last_used": datetime.utcnow() - timedelta(seconds=30),
            "description": "Fast and efficient GPT-4o for real-time responses",
            "created_at": datetime.utcnow() - timedelta(days=60),
            "updated_at": datetime.utcnow()
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "OpenAI GPT-3.5 Turbo",
            "provider_type": "openai",
            "models": [{
                "model_id": "gpt-3.5-turbo",
                "display_name": "GPT-3.5 Turbo",
                "max_tokens": 16385,
                "input_cost_per_1k_tokens": 0.0005,
                "output_cost_per_1k_tokens": 0.0015,
                "default_temperature": 0.7
            }],
            "default_model_id": "gpt-3.5-turbo",
            "credentials": {
                "api_key": "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx"
            },
            "status": "active",
            "total_requests": random.randint(200000, 500000),
            "avg_latency_ms": round(random.uniform(0.2, 0.5), 2),
            "success_rate": round(random.uniform(98.5, 99.9), 2),
            "cost_this_month": round(random.uniform(100, 400), 2),
            "last_used": datetime.utcnow() - timedelta(minutes=1),
            "description": "Cost-effective model for simple queries and classifications",
            "created_at": datetime.utcnow() - timedelta(days=120),
            "updated_at": datetime.utcnow()
        },

        # Anthropic Models
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Claude 3.5 Sonnet",
            "provider_type": "anthropic",
            "models": [{
                "model_id": "claude-3-5-sonnet-20241022",
                "display_name": "Claude 3.5 Sonnet",
                "max_tokens": 200000,
                "input_cost_per_1k_tokens": 0.003,
                "output_cost_per_1k_tokens": 0.015,
                "default_temperature": 0.7
            }],
            "default_model_id": "claude-3-5-sonnet-20241022",
            "credentials": {
                "api_key": "sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxx",
                "custom_endpoint_url": "https://api.anthropic.com/v1"
            },
            "status": "active",
            "total_requests": random.randint(60000, 120000),
            "avg_latency_ms": round(random.uniform(0.6, 1.2), 2),
            "success_rate": round(random.uniform(98.0, 99.5), 2),
            "cost_this_month": round(random.uniform(400, 1200), 2),
            "last_used": datetime.utcnow() - timedelta(minutes=2),
            "description": "Claude 3.5 Sonnet for balanced performance and reasoning",
            "created_at": datetime.utcnow() - timedelta(days=45),
            "updated_at": datetime.utcnow()
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Claude 3 Opus",
            "provider_type": "anthropic",
            "models": [{
                "model_id": "claude-3-opus-20240229",
                "display_name": "Claude 3 Opus",
                "max_tokens": 200000,
                "input_cost_per_1k_tokens": 0.015,
                "output_cost_per_1k_tokens": 0.075,
                "default_temperature": 0.7
            }],
            "default_model_id": "claude-3-opus-20240229",
            "credentials": {
                "api_key": "sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxx"
            },
            "status": "active",
            "total_requests": random.randint(20000, 50000),
            "avg_latency_ms": round(random.uniform(1.0, 2.0), 2),
            "success_rate": round(random.uniform(97.5, 99.0), 2),
            "cost_this_month": round(random.uniform(800, 2500), 2),
            "last_used": datetime.utcnow() - timedelta(minutes=5),
            "description": "Most capable Claude model for complex reasoning tasks",
            "created_at": datetime.utcnow() - timedelta(days=75),
            "updated_at": datetime.utcnow()
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Claude 3 Haiku",
            "provider_type": "anthropic",
            "models": [{
                "model_id": "claude-3-haiku-20240307",
                "display_name": "Claude 3 Haiku",
                "max_tokens": 200000,
                "input_cost_per_1k_tokens": 0.00025,
                "output_cost_per_1k_tokens": 0.00125,
                "default_temperature": 0.7
            }],
            "default_model_id": "claude-3-haiku-20240307",
            "credentials": {
                "api_key": "sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxx"
            },
            "status": "active",
            "total_requests": random.randint(100000, 300000),
            "avg_latency_ms": round(random.uniform(0.2, 0.4), 2),
            "success_rate": round(random.uniform(99.0, 99.9), 2),
            "cost_this_month": round(random.uniform(50, 200), 2),
            "last_used": datetime.utcnow() - timedelta(seconds=45),
            "description": "Fast and affordable Claude model for high-volume tasks",
            "created_at": datetime.utcnow() - timedelta(days=60),
            "updated_at": datetime.utcnow()
        },

        # Google Models
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Gemini 1.5 Pro",
            "provider_type": "google",
            "models": [{
                "model_id": "gemini-1.5-pro",
                "display_name": "Gemini 1.5 Pro",
                "max_tokens": 1000000,
                "input_cost_per_1k_tokens": 0.00125,
                "output_cost_per_1k_tokens": 0.005,
                "default_temperature": 0.7
            }],
            "default_model_id": "gemini-1.5-pro",
            "credentials": {
                "api_key": "AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxx",
                "custom_endpoint_url": "https://generativelanguage.googleapis.com/v1"
            },
            "status": "active",
            "total_requests": random.randint(40000, 100000),
            "avg_latency_ms": round(random.uniform(0.7, 1.5), 2),
            "success_rate": round(random.uniform(97.0, 99.0), 2),
            "cost_this_month": round(random.uniform(200, 800), 2),
            "last_used": datetime.utcnow() - timedelta(minutes=4),
            "description": "Gemini 1.5 Pro with 1M token context window",
            "created_at": datetime.utcnow() - timedelta(days=50),
            "updated_at": datetime.utcnow()
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Gemini 1.5 Flash",
            "provider_type": "google",
            "models": [{
                "model_id": "gemini-1.5-flash",
                "display_name": "Gemini 1.5 Flash",
                "max_tokens": 1000000,
                "input_cost_per_1k_tokens": 0.000125,
                "output_cost_per_1k_tokens": 0.000375,
                "default_temperature": 0.7
            }],
            "default_model_id": "gemini-1.5-flash",
            "credentials": {
                "api_key": "AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxx"
            },
            "status": "active",
            "total_requests": random.randint(150000, 400000),
            "avg_latency_ms": round(random.uniform(0.2, 0.5), 2),
            "success_rate": round(random.uniform(98.5, 99.9), 2),
            "cost_this_month": round(random.uniform(80, 250), 2),
            "last_used": datetime.utcnow() - timedelta(minutes=2),
            "description": "Fastest Gemini model for high-throughput applications",
            "created_at": datetime.utcnow() - timedelta(days=40),
            "updated_at": datetime.utcnow()
        },

        # Azure OpenAI Models
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Azure GPT-4 East US",
            "provider_type": "azure_openai",
            "models": [{
                "model_id": "gpt-4",
                "display_name": "GPT-4",
                "max_tokens": 8192,
                "input_cost_per_1k_tokens": 0.03,
                "output_cost_per_1k_tokens": 0.06
            }],
            "default_model_id": "gpt-4",
            "credentials": {
                "api_key": "xxxxxxxxxxxxxxxxxxxxxxxxxx",
                "azure_endpoint": "https://your-resource-eastus.openai.azure.com",
                "azure_deployment_name": "gpt-4-deployment",
                "azure_api_version": "2024-02-15-preview"
            },
            "status": "active",
            "total_requests": random.randint(30000, 80000),
            "avg_latency_ms": round(random.uniform(0.8, 1.8), 2),
            "success_rate": round(random.uniform(97.0, 99.0), 2),
            "cost_this_month": round(random.uniform(600, 1800), 2),
            "last_used": datetime.utcnow() - timedelta(minutes=12),
            "description": "Azure-hosted GPT-4 for enterprise compliance",
            "created_at": datetime.utcnow() - timedelta(days=100),
            "updated_at": datetime.utcnow()
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Azure GPT-3.5 Turbo",
            "provider_type": "azure_openai",
            "models": [{
                "model_id": "gpt-35-turbo",
                "display_name": "GPT-3.5 Turbo",
                "max_tokens": 4096,
                "input_cost_per_1k_tokens": 0.0005,
                "output_cost_per_1k_tokens": 0.0015
            }],
            "default_model_id": "gpt-35-turbo",
            "credentials": {
                "api_key": "xxxxxxxxxxxxxxxxxxxxxxxxxx",
                "azure_endpoint": "https://your-resource-westus.openai.azure.com",
                "azure_deployment_name": "gpt-35-turbo-deployment"
            },
            "status": "active",
            "total_requests": random.randint(100000, 300000),
            "avg_latency_ms": round(random.uniform(0.3, 0.7), 2),
            "success_rate": round(random.uniform(98.0, 99.5), 2),
            "cost_this_month": round(random.uniform(150, 500), 2),
            "last_used": datetime.utcnow() - timedelta(minutes=3),
            "description": "Cost-effective Azure GPT-3.5 for high-volume workloads",
            "created_at": datetime.utcnow() - timedelta(days=110),
            "updated_at": datetime.utcnow()
        },

        # Meta Llama Models (Local/Self-hosted)
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Llama 3.1 405B (Local)",
            "provider_type": "custom",
            "models": [{
                "model_id": "llama-3.1-405b-instruct",
                "display_name": "Llama 3.1 405B Instruct",
                "max_tokens": 128000,
                "input_cost_per_1k_tokens": 0.0,
                "output_cost_per_1k_tokens": 0.0,
                "default_temperature": 0.7
            }],
            "default_model_id": "llama-3.1-405b-instruct",
            "credentials": {
                "custom_endpoint_url": "http://localhost:8000/v1"
            },
            "status": "active",
            "total_requests": random.randint(25000, 60000),
            "avg_latency_ms": round(random.uniform(1.5, 3.0), 2),
            "success_rate": round(random.uniform(95.0, 98.0), 2),
            "cost_this_month": 0.0,
            "last_used": datetime.utcnow() - timedelta(minutes=10),
            "description": "Self-hosted Llama 3.1 405B for data privacy and zero cost",
            "tags": ["offline", "self-hosted", "free"],
            "created_at": datetime.utcnow() - timedelta(days=30),
            "updated_at": datetime.utcnow()
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Llama 3.1 70B (Local)",
            "provider_type": "custom",
            "models": [{
                "model_id": "llama-3.1-70b-instruct",
                "display_name": "Llama 3.1 70B Instruct",
                "max_tokens": 128000,
                "input_cost_per_1k_tokens": 0.0,
                "output_cost_per_1k_tokens": 0.0
            }],
            "default_model_id": "llama-3.1-70b-instruct",
            "credentials": {
                "custom_endpoint_url": "http://localhost:8001/v1"
            },
            "status": "active",
            "total_requests": random.randint(50000, 120000),
            "avg_latency_ms": round(random.uniform(0.8, 1.5), 2),
            "success_rate": round(random.uniform(96.0, 99.0), 2),
            "cost_this_month": 0.0,
            "last_used": datetime.utcnow() - timedelta(minutes=3),
            "description": "Faster Llama 3.1 70B for high-throughput local inference",
            "tags": ["offline", "self-hosted", "free"],
            "created_at": datetime.utcnow() - timedelta(days=30),
            "updated_at": datetime.utcnow()
        },

        # Mistral AI Models
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Mistral Large",
            "provider_type": "custom",
            "models": [{
                "model_id": "mistral-large-latest",
                "display_name": "Mistral Large",
                "max_tokens": 32000,
                "input_cost_per_1k_tokens": 0.004,
                "output_cost_per_1k_tokens": 0.012
            }],
            "default_model_id": "mistral-large-latest",
            "credentials": {
                "api_key": "xxxxxxxxxxxxxxxxxxxxxxxx",
                "custom_endpoint_url": "https://api.mistral.ai/v1"
            },
            "status": "active",
            "total_requests": random.randint(15000, 40000),
            "avg_latency_ms": round(random.uniform(0.6, 1.2), 2),
            "success_rate": round(random.uniform(96.0, 98.5), 2),
            "cost_this_month": round(random.uniform(150, 450), 2),
            "last_used": datetime.utcnow() - timedelta(minutes=8),
            "description": "Mistral's flagship model for multilingual tasks",
            "created_at": datetime.utcnow() - timedelta(days=35),
            "updated_at": datetime.utcnow()
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Mistral 7B (Local)",
            "provider_type": "custom",
            "models": [{
                "model_id": "mistral-7b-instruct-v0.2",
                "display_name": "Mistral 7B Instruct",
                "max_tokens": 32000,
                "input_cost_per_1k_tokens": 0.0,
                "output_cost_per_1k_tokens": 0.0
            }],
            "default_model_id": "mistral-7b-instruct-v0.2",
            "credentials": {
                "custom_endpoint_url": "http://127.0.0.1:8002/v1"
            },
            "status": "inactive",
            "total_requests": random.randint(5000, 15000),
            "avg_latency_ms": round(random.uniform(0.3, 0.6), 2),
            "success_rate": round(random.uniform(94.0, 97.0), 2),
            "cost_this_month": 0.0,
            "last_used": datetime.utcnow() - timedelta(days=2),
            "description": "Lightweight Mistral 7B for testing and development",
            "tags": ["offline", "testing", "free"],
            "created_at": datetime.utcnow() - timedelta(days=25),
            "updated_at": datetime.utcnow()
        },

        # Cohere Models
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Cohere Command R+",
            "provider_type": "custom",
            "models": [{
                "model_id": "command-r-plus",
                "display_name": "Command R+",
                "max_tokens": 128000,
                "input_cost_per_1k_tokens": 0.003,
                "output_cost_per_1k_tokens": 0.015
            }],
            "default_model_id": "command-r-plus",
            "credentials": {
                "api_key": "xxxxxxxxxxxxxxxxxxxxxxxx",
                "custom_endpoint_url": "https://api.cohere.ai/v1"
            },
            "status": "active",
            "total_requests": random.randint(20000, 55000),
            "avg_latency_ms": round(random.uniform(0.5, 1.0), 2),
            "success_rate": round(random.uniform(97.0, 99.0), 2),
            "cost_this_month": round(random.uniform(200, 600), 2),
            "last_used": datetime.utcnow() - timedelta(minutes=6),
            "description": "Cohere's advanced model for RAG applications",
            "created_at": datetime.utcnow() - timedelta(days=40),
            "updated_at": datetime.utcnow()
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Cohere Command",
            "provider_type": "custom",
            "models": [{
                "model_id": "command",
                "display_name": "Command",
                "max_tokens": 64000,
                "input_cost_per_1k_tokens": 0.0015,
                "output_cost_per_1k_tokens": 0.0075
            }],
            "default_model_id": "command",
            "credentials": {
                "api_key": "xxxxxxxxxxxxxxxxxxxxxxxx",
                "custom_endpoint_url": "https://api.cohere.ai/v1"
            },
            "status": "active",
            "total_requests": random.randint(40000, 90000),
            "avg_latency_ms": round(random.uniform(0.4, 0.8), 2),
            "success_rate": round(random.uniform(97.5, 99.2), 2),
            "cost_this_month": round(random.uniform(150, 450), 2),
            "last_used": datetime.utcnow() - timedelta(minutes=7),
            "description": "Balanced Cohere model for general tasks",
            "created_at": datetime.utcnow() - timedelta(days=55),
            "updated_at": datetime.utcnow()
        },

        # AWS Bedrock Models
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "AWS Bedrock - Claude 3 Sonnet",
            "provider_type": "aws_bedrock",
            "models": [{
                "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
                "display_name": "Claude 3 Sonnet (Bedrock)",
                "max_tokens": 200000,
                "input_cost_per_1k_tokens": 0.003,
                "output_cost_per_1k_tokens": 0.015
            }],
            "default_model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
            "credentials": {
                "aws_region": "us-east-1",
                "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
                "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
            },
            "status": "active",
            "total_requests": random.randint(25000, 65000),
            "avg_latency_ms": round(random.uniform(0.7, 1.4), 2),
            "success_rate": round(random.uniform(97.0, 99.0), 2),
            "cost_this_month": round(random.uniform(300, 900), 2),
            "last_used": datetime.utcnow() - timedelta(minutes=15),
            "description": "Claude via AWS Bedrock for regulatory compliance",
            "created_at": datetime.utcnow() - timedelta(days=70),
            "updated_at": datetime.utcnow()
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "AWS Bedrock - Titan Express",
            "provider_type": "aws_bedrock",
            "models": [{
                "model_id": "amazon.titan-text-express-v1",
                "display_name": "Titan Text Express",
                "max_tokens": 8192,
                "input_cost_per_1k_tokens": 0.0002,
                "output_cost_per_1k_tokens": 0.0006
            }],
            "default_model_id": "amazon.titan-text-express-v1",
            "credentials": {
                "aws_region": "us-west-2",
                "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
                "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
            },
            "status": "inactive",
            "total_requests": random.randint(5000, 15000),
            "avg_latency_ms": round(random.uniform(0.4, 0.8), 2),
            "success_rate": round(random.uniform(95.0, 97.5), 2),
            "cost_this_month": round(random.uniform(20, 80), 2),
            "last_used": datetime.utcnow() - timedelta(days=5),
            "description": "AWS native Titan model for basic text generation",
            "created_at": datetime.utcnow() - timedelta(days=50),
            "updated_at": datetime.utcnow()
        },

        # Hugging Face Models
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Hugging Face - FLAN-T5 XXL",
            "provider_type": "huggingface",
            "models": [{
                "model_id": "google/flan-t5-xxl",
                "display_name": "FLAN-T5 XXL",
                "max_tokens": 2048,
                "input_cost_per_1k_tokens": 0.0001,
                "output_cost_per_1k_tokens": 0.0003
            }],
            "default_model_id": "google/flan-t5-xxl",
            "credentials": {
                "api_key": "hf_xxxxxxxxxxxxxxxxxxxxxxxx",
                "custom_endpoint_url": "https://api-inference.huggingface.co/models"
            },
            "status": "inactive",
            "total_requests": random.randint(3000, 10000),
            "avg_latency_ms": round(random.uniform(1.0, 2.5), 2),
            "success_rate": round(random.uniform(92.0, 96.0), 2),
            "cost_this_month": round(random.uniform(10, 40), 2),
            "last_used": datetime.utcnow() - timedelta(days=7),
            "description": "Open-source FLAN-T5 for experimentation",
            "created_at": datetime.utcnow() - timedelta(days=45),
            "updated_at": datetime.utcnow()
        },

        # Additional OpenAI models
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "OpenAI GPT-4 32K",
            "provider_type": "openai",
            "models": [{
                "model_id": "gpt-4-32k",
                "display_name": "GPT-4 32K",
                "max_tokens": 32768,
                "input_cost_per_1k_tokens": 0.06,
                "output_cost_per_1k_tokens": 0.12
            }],
            "default_model_id": "gpt-4-32k",
            "credentials": {
                "api_key": "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx"
            },
            "status": "active",
            "total_requests": random.randint(10000, 30000),
            "avg_latency_ms": round(random.uniform(1.2, 2.0), 2),
            "success_rate": round(random.uniform(96.5, 98.5), 2),
            "cost_this_month": round(random.uniform(400, 1200), 2),
            "last_used": datetime.utcnow() - timedelta(minutes=20),
            "description": "Extended context GPT-4 for long documents",
            "created_at": datetime.utcnow() - timedelta(days=95),
            "updated_at": datetime.utcnow()
        }
    ]

    # Add more variations
    more_models = [
        # Testing/Development models
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "OpenAI GPT-4o-mini",
            "provider_type": "openai",
            "models": [{"model_id": "gpt-4o-mini", "display_name": "GPT-4o Mini", "max_tokens": 128000, "input_cost_per_1k_tokens": 0.00015, "output_cost_per_1k_tokens": 0.0006}],
            "status": "active",
            "description": "Affordable GPT-4o mini for development and testing",
            "created_at": datetime.utcnow() - timedelta(days=20)
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Gemini Pro (Legacy)",
            "provider_type": "google",
            "models": [{"model_id": "gemini-pro", "display_name": "Gemini Pro", "max_tokens": 32000, "input_cost_per_1k_tokens": 0.000125, "output_cost_per_1k_tokens": 0.000375}],
            "status": "inactive",
            "description": "Legacy Gemini Pro (deprecated)",
            "created_at": datetime.utcnow() - timedelta(days=150),
            "is_deprecated": True
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Custom Mixtral 8x7B",
            "provider_type": "custom",
            "models": [{"model_id": "mixtral-8x7b-instruct", "display_name": "Mixtral 8x7B", "max_tokens": 32000, "input_cost_per_1k_tokens": 0.0, "output_cost_per_1k_tokens": 0.0}],
            "credentials": {"custom_endpoint_url": "http://localhost:8003/v1"},
            "status": "inactive",
            "description": "Self-hosted Mixtral 8x7B MoE model",
            "tags": ["offline", "testing"],
            "created_at": datetime.utcnow() - timedelta(days=15)
        }
    ]

    # Add default values to more_models
    for model in more_models:
        model.setdefault("default_model_id", model["models"][0]["model_id"])
        model.setdefault("credentials", {})
        model.setdefault("rate_limits", {"requests_per_minute": 60, "tokens_per_minute": 90000})
        model.setdefault("auto_fallback_enabled", False)
        model.setdefault("retry_attempts", 3)
        model.setdefault("timeout_seconds", 30)
        model.setdefault("total_requests", random.randint(1000, 10000))
        model.setdefault("total_tokens", random.randint(100000, 1000000))
        model.setdefault("total_errors", random.randint(10, 100))
        model.setdefault("avg_latency_ms", round(random.uniform(0.5, 1.5), 2))
        model.setdefault("success_rate", round(random.uniform(95.0, 99.0), 2))
        model.setdefault("tokens_used_this_month", random.randint(10000, 100000))
        model.setdefault("requests_this_month", random.randint(1000, 10000))
        model.setdefault("cost_this_month", round(random.uniform(10, 200), 2))
        model.setdefault("last_used", datetime.utcnow() - timedelta(hours=random.randint(1, 48)))
        model.setdefault("tags", [])
        model.setdefault("metadata", {})
        model.setdefault("updated_at", datetime.utcnow())
        model.setdefault("created_by", "admin")

    ai_models.extend(more_models)

    # Insert models
    if ai_models:
        result = await collection.insert_many(ai_models)
        print(f"✅ Inserted {len(result.inserted_ids)} AI models")
        return len(result.inserted_ids)
    return 0


async def populate_ai_features():
    """Populate 10 AI features"""
    db = await get_db()
    collection = db["ai_features"]

    # Clear existing data (optional)
    # await collection.delete_many({"company_id": SAMPLE_COMPANY_ID})

    ai_features = [
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Sentiment Analysis",
            "feature_type": "Analysis",
            "description": "Detect customer emotions and urgency levels in conversations using advanced NLP",
            "icon": "😊",
            "attached_models": [],  # Will be populated with actual model IDs
            "enabled": True,
            "status": "active",
            "config": {
                "sensitivity": "high",
                "categories": ["Positive", "Neutral", "Negative", "Urgent"],
                "confidence_threshold": 0.85,
                "languages": ["en", "es", "fr", "de"]
            },
            "total_conversations": 12543,
            "total_analyses": 12543,
            "accuracy_rate": 94.2,
            "success_rate": 98.5,
            "avg_processing_time_ms": 320,
            "conversations_this_month": 4523,
            "analyses_this_month": 4523,
            "last_used": datetime.utcnow() - timedelta(minutes=2),
            "tags": ["production", "critical", "customer-service"],
            "created_at": datetime.utcnow() - timedelta(days=180),
            "updated_at": datetime.utcnow(),
            "created_by": "admin"
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Auto-Tagging",
            "feature_type": "Classification",
            "description": "Automatically categorize conversations with relevant tags and topics",
            "icon": "🏷️",
            "attached_models": [],
            "enabled": True,
            "status": "active",
            "config": {
                "max_tags": 5,
                "confidence_threshold": 0.80,
                "custom_categories": ["Product", "Billing", "Technical", "Shipping", "Returns"]
            },
            "total_conversations": 15234,
            "total_analyses": 15234,
            "accuracy_rate": 91.8,
            "success_rate": 99.2,
            "avg_processing_time_ms": 280,
            "conversations_this_month": 5432,
            "last_used": datetime.utcnow() - timedelta(minutes=1),
            "tags": ["production", "automation"],
            "created_at": datetime.utcnow() - timedelta(days=150),
            "updated_at": datetime.utcnow(),
            "created_by": "admin"
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Response Generation",
            "feature_type": "Generation",
            "description": "Generate contextual AI-powered draft responses with customizable tones",
            "icon": "✍️",
            "attached_models": [],
            "enabled": True,
            "status": "active",
            "config": {
                "tones": ["Professional", "Friendly", "Empathetic", "Concise"],
                "max_length": 500,
                "include_sources": True,
                "languages": ["en", "es", "fr"]
            },
            "total_conversations": 8932,
            "total_analyses": 8932,
            "accuracy_rate": 88.5,
            "success_rate": 96.8,
            "avg_processing_time_ms": 1200,
            "conversations_this_month": 3241,
            "last_used": datetime.utcnow() - timedelta(minutes=3),
            "tags": ["production", "high-value"],
            "created_at": datetime.utcnow() - timedelta(days=120),
            "updated_at": datetime.utcnow(),
            "created_by": "admin"
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Bot Detection",
            "feature_type": "Detection",
            "description": "Filter spam and bot messages with advanced pattern recognition",
            "icon": "🤖",
            "attached_models": [],
            "enabled": True,
            "status": "active",
            "config": {
                "strictness": "high",
                "auto_block": True,
                "confidence_threshold": 0.95
            },
            "total_conversations": 23445,
            "total_analyses": 23445,
            "accuracy_rate": 96.7,
            "success_rate": 99.5,
            "avg_processing_time_ms": 150,
            "conversations_this_month": 8765,
            "last_used": datetime.utcnow() - timedelta(seconds=45),
            "tags": ["production", "security"],
            "created_at": datetime.utcnow() - timedelta(days=200),
            "updated_at": datetime.utcnow(),
            "created_by": "admin"
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Urgency Classification",
            "feature_type": "Priority",
            "description": "Prioritize critical conversations and detect urgent customer issues",
            "icon": "🎯",
            "attached_models": [],
            "enabled": True,
            "status": "active",
            "config": {
                "priority_levels": ["Critical", "High", "Medium", "Low"],
                "escalation_threshold": "High",
                "sla_integration": True
            },
            "total_conversations": 7821,
            "total_analyses": 7821,
            "accuracy_rate": 89.3,
            "success_rate": 97.8,
            "avg_processing_time_ms": 250,
            "conversations_this_month": 2876,
            "last_used": datetime.utcnow() - timedelta(minutes=5),
            "tags": ["production", "critical"],
            "created_at": datetime.utcnow() - timedelta(days=90),
            "updated_at": datetime.utcnow(),
            "created_by": "admin"
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Entity Extraction",
            "feature_type": "NLP",
            "description": "Extract key information like names, products, locations from messages",
            "icon": "🔍",
            "attached_models": [],
            "enabled": False,
            "status": "inactive",
            "config": {
                "entity_types": ["PERSON", "PRODUCT", "LOCATION", "DATE", "MONEY"],
                "confidence_threshold": 0.75
            },
            "total_conversations": 4532,
            "total_analyses": 4532,
            "accuracy_rate": 85.1,
            "success_rate": 94.2,
            "avg_processing_time_ms": 400,
            "conversations_this_month": 234,
            "last_used": datetime.utcnow() - timedelta(days=3),
            "tags": ["testing", "nlp"],
            "created_at": datetime.utcnow() - timedelta(days=60),
            "updated_at": datetime.utcnow(),
            "created_by": "admin"
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Multilingual Support",
            "feature_type": "Translation",
            "description": "Support 50+ languages with automatic detection and translation",
            "icon": "🌍",
            "attached_models": [],
            "enabled": True,
            "status": "active",
            "config": {
                "supported_languages": 52,
                "auto_detect": True,
                "primary_languages": ["en", "es", "fr", "de", "it", "pt", "zh", "ja", "ko"]
            },
            "total_conversations": 9876,
            "total_analyses": 9876,
            "accuracy_rate": 92.4,
            "success_rate": 98.1,
            "avg_processing_time_ms": 550,
            "conversations_this_month": 3654,
            "last_used": datetime.utcnow() - timedelta(minutes=4),
            "tags": ["production", "multilingual"],
            "created_at": datetime.utcnow() - timedelta(days=100),
            "updated_at": datetime.utcnow(),
            "created_by": "admin"
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Intent Detection",
            "feature_type": "Analysis",
            "description": "Understand customer intent and route to appropriate workflows",
            "icon": "🧠",
            "attached_models": [],
            "enabled": True,
            "status": "active",
            "config": {
                "intent_types": 25,
                "confidence_threshold": 0.80,
                "custom_intents": ["refund_request", "product_inquiry", "complaint", "feedback"]
            },
            "total_conversations": 11234,
            "total_analyses": 11234,
            "accuracy_rate": 90.1,
            "success_rate": 97.5,
            "avg_processing_time_ms": 310,
            "conversations_this_month": 4123,
            "last_used": datetime.utcnow() - timedelta(minutes=6),
            "tags": ["production", "routing"],
            "created_at": datetime.utcnow() - timedelta(days=110),
            "updated_at": datetime.utcnow(),
            "created_by": "admin"
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Conversation Summarization",
            "feature_type": "Generation",
            "description": "Generate concise summaries of customer conversations",
            "icon": "📝",
            "attached_models": [],
            "enabled": True,
            "status": "active",
            "config": {
                "max_summary_length": 150,
                "include_action_items": True,
                "highlight_sentiment": True
            },
            "total_conversations": 5432,
            "total_analyses": 5432,
            "accuracy_rate": 87.9,
            "success_rate": 96.3,
            "avg_processing_time_ms": 800,
            "conversations_this_month": 1987,
            "last_used": datetime.utcnow() - timedelta(minutes=8),
            "tags": ["production"],
            "created_at": datetime.utcnow() - timedelta(days=75),
            "updated_at": datetime.utcnow(),
            "created_by": "admin"
        },
        {
            "company_id": SAMPLE_COMPANY_ID,
            "name": "Topic Categorization",
            "feature_type": "Classification",
            "description": "Automatically categorize conversations by main topics and subtopics",
            "icon": "📂",
            "attached_models": [],
            "enabled": True,
            "status": "active",
            "config": {
                "topics": ["Sales", "Support", "Billing", "Technical", "General"],
                "multi_label": True,
                "confidence_threshold": 0.75
            },
            "total_conversations": 9876,
            "total_analyses": 9876,
            "accuracy_rate": 88.6,
            "success_rate": 97.9,
            "avg_processing_time_ms": 290,
            "conversations_this_month": 3567,
            "last_used": datetime.utcnow() - timedelta(minutes=7),
            "tags": ["production"],
            "created_at": datetime.utcnow() - timedelta(days=85),
            "updated_at": datetime.utcnow(),
            "created_by": "admin"
        }
    ]

    # Insert features
    if ai_features:
        result = await collection.insert_many(ai_features)
        print(f"✅ Inserted {len(result.inserted_ids)} AI features")
        return len(result.inserted_ids)
    return 0


async def main():
    """Main function to populate all data"""
    print("=" * 60)
    print("Populating AI Data for Khoros AI Care Expert")
    print("=" * 60)
    print(f"Company ID: {SAMPLE_COMPANY_ID}")
    print(f"MongoDB: {settings.mongodb_uri}")
    print(f"Database: {settings.mongodb_database}")
    print("=" * 60)

    try:
        # Populate AI Models
        print("\n📦 Populating AI Models (LLM Providers)...")
        models_count = await populate_ai_models()
        print(f"✅ Created {models_count} AI models")

        # Populate AI Features
        print("\n⚡ Populating AI Features...")
        features_count = await populate_ai_features()
        print(f"✅ Created {features_count} AI features")

        print("\n" + "=" * 60)
        print("✅ Data population complete!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  • AI Models: {models_count}")
        print(f"  • AI Features: {features_count}")
        print(f"\nYou can now:")
        print(f"  1. Start the API: python main.py")
        print(f"  2. View data: http://localhost:9000/docs")
        print(f"  3. Access frontend: http://localhost:8080/console/aicareexpert/")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error populating data: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
