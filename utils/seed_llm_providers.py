#!/usr/bin/env python3
"""
Utility script to seed LLM providers data into MongoDB via API
Usage: python utils/seed_llm_providers.py
"""

import asyncio
import httpx
import json
from datetime import datetime
import sys
import os
from typing import List, Dict, Any

# Add parent directory to path to import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN", "")  # Add your auth token if required

# Set a timeout for HTTP requests
REQUEST_TIMEOUT = 10.0

# Sample LLM Providers Data
LLM_PROVIDERS_DATA = [
    {
        "company_id": "default_company_001",  # You'll need to update with actual company ID
        "name": "OpenAI Production",
        "provider_type": "openai",
        "description": "Primary OpenAI provider for production workloads",
        "api_key": "sk-proj-test123456789",  # Replace with actual API key
        "api_endpoint": "https://api.openai.com/v1",
        "api_version": "v1",
        "credentials": {},  # OpenAI only needs API key
        "models": [
            {
                "model_id": "gpt-4-turbo-preview",
                "display_name": "GPT-4 Turbo",
                "capabilities": ["text_generation", "chat", "function_calling"],
                "max_tokens": 128000,
                "context_window": 128000,
                "supports_streaming": True,
                "supports_function_calling": True
            },
            {
                "model_id": "gpt-4",
                "display_name": "GPT-4",
                "capabilities": ["text_generation", "chat", "function_calling"],
                "max_tokens": 8192,
                "context_window": 8192,
                "supports_streaming": True,
                "supports_function_calling": True
            },
            {
                "model_id": "gpt-3.5-turbo",
                "display_name": "GPT-3.5 Turbo",
                "capabilities": ["text_generation", "chat", "function_calling"],
                "max_tokens": 4096,
                "context_window": 16385,
                "supports_streaming": True,
                "supports_function_calling": True
            }
        ],
        "default_model": "gpt-4-turbo-preview",
        "rate_limits": {
            "requests_per_minute": 500,
            "tokens_per_minute": 150000,
            "concurrent_requests": 50
        },
        "cost_config": {
            "input_token_cost": 0.01,  # per 1K tokens
            "output_token_cost": 0.03,  # per 1K tokens
            "monthly_budget": 5000.0,
            "alert_threshold": 80.0
        },
        "is_default": True,
        "auto_retry": True,
        "max_retries": 3,
        "timeout_seconds": 30,
        "status": "active"
    },
    {
        "company_id": "default_company_001",
        "name": "Anthropic Claude",
        "provider_type": "anthropic",
        "description": "Claude 3 for advanced reasoning and analysis tasks",
        "api_key": "sk-ant-test123456789",  # Replace with actual API key
        "api_endpoint": "https://api.anthropic.com/v1",
        "api_version": "2023-06-01",
        "credentials": {},  # Anthropic only needs API key
        "models": [
            {
                "model_id": "claude-3-opus-20240229",
                "display_name": "Claude 3 Opus",
                "capabilities": ["text_generation", "chat", "vision"],
                "max_tokens": 200000,
                "context_window": 200000,
                "supports_streaming": True,
                "supports_vision": True
            },
            {
                "model_id": "claude-3-sonnet-20240229",
                "display_name": "Claude 3 Sonnet",
                "capabilities": ["text_generation", "chat", "vision"],
                "max_tokens": 200000,
                "context_window": 200000,
                "supports_streaming": True,
                "supports_vision": True
            },
            {
                "model_id": "claude-3-haiku-20240307",
                "display_name": "Claude 3 Haiku",
                "capabilities": ["text_generation", "chat"],
                "max_tokens": 200000,
                "context_window": 200000,
                "supports_streaming": True
            }
        ],
        "default_model": "claude-3-sonnet-20240229",
        "rate_limits": {
            "requests_per_minute": 100,
            "tokens_per_minute": 100000,
            "concurrent_requests": 25
        },
        "cost_config": {
            "input_token_cost": 0.015,
            "output_token_cost": 0.075,
            "monthly_budget": 3000.0,
            "alert_threshold": 75.0
        },
        "is_default": False,
        "auto_retry": True,
        "max_retries": 3,
        "timeout_seconds": 60,
        "status": "active"
    },
    {
        "company_id": "default_company_001",
        "name": "Azure OpenAI Service",
        "provider_type": "azure_openai",
        "description": "Azure-hosted OpenAI models for enterprise compliance",
        "api_key": "azure-key-test123456789",  # Replace with actual API key
        "api_endpoint": "https://your-resource.openai.azure.com",
        "api_version": "2024-02-15-preview",
        "organization_id": "your-azure-resource",
        "credentials": {
            "deployment_name": "gpt-4-deployment",
            "resource_name": "your-resource"
        },
        "models": [
            {
                "model_id": "gpt-4",
                "display_name": "Azure GPT-4",
                "capabilities": ["text_generation", "chat", "function_calling"],
                "max_tokens": 8192,
                "context_window": 8192,
                "supports_streaming": True,
                "supports_function_calling": True
            },
            {
                "model_id": "gpt-35-turbo",
                "display_name": "Azure GPT-3.5 Turbo",
                "capabilities": ["text_generation", "chat"],
                "max_tokens": 4096,
                "context_window": 16385,
                "supports_streaming": True
            }
        ],
        "default_model": "gpt-4",
        "rate_limits": {
            "requests_per_minute": 300,
            "tokens_per_minute": 120000,
            "concurrent_requests": 30
        },
        "cost_config": {
            "input_token_cost": 0.01,
            "output_token_cost": 0.03,
            "monthly_budget": 4000.0,
            "alert_threshold": 80.0
        },
        "is_default": False,
        "auto_retry": True,
        "max_retries": 3,
        "timeout_seconds": 30,
        "status": "active"
    },
    {
        "company_id": "default_company_001",
        "name": "AWS Bedrock",
        "provider_type": "aws_bedrock",
        "description": "AWS Bedrock for diverse model access and scalability",
        "api_key": "AKIAIOSFODNN7EXAMPLE",  # Replace with actual AWS access key
        "api_endpoint": "https://bedrock-runtime.us-east-1.amazonaws.com",
        "api_version": "2023-09-30",
        "credentials": {
            "aws_secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",  # Replace
            "aws_region": "us-east-1"
        },
        "models": [
            {
                "model_id": "anthropic.claude-v2",
                "display_name": "Claude 2 (Bedrock)",
                "capabilities": ["text_generation", "chat"],
                "max_tokens": 100000,
                "context_window": 100000,
                "supports_streaming": True
            },
            {
                "model_id": "amazon.titan-text-express-v1",
                "display_name": "Amazon Titan Text",
                "capabilities": ["text_generation", "chat"],
                "max_tokens": 8192,
                "context_window": 8192,
                "supports_streaming": True
            },
            {
                "model_id": "meta.llama2-70b-chat-v1",
                "display_name": "Llama 2 70B Chat",
                "capabilities": ["text_generation", "chat"],
                "max_tokens": 4096,
                "context_window": 4096,
                "supports_streaming": True
            }
        ],
        "default_model": "anthropic.claude-v2",
        "rate_limits": {
            "requests_per_minute": 200,
            "tokens_per_minute": 80000,
            "concurrent_requests": 20
        },
        "cost_config": {
            "input_token_cost": 0.008,
            "output_token_cost": 0.024,
            "monthly_budget": 2500.0,
            "alert_threshold": 70.0
        },
        "is_default": False,
        "auto_retry": True,
        "max_retries": 3,
        "timeout_seconds": 45,
        "status": "active"
    },
    {
        "company_id": "default_company_001",
        "name": "Google Vertex AI",
        "provider_type": "google",
        "description": "Google's Vertex AI for Gemini and PaLM models",
        "api_key": "google-api-key-test123456789",  # Replace with actual API key
        "api_endpoint": "https://generativelanguage.googleapis.com/v1",
        "api_version": "v1",
        "organization_id": "your-gcp-project",
        "credentials": {
            "project_id": "your-gcp-project",
            "location": "us-central1"
        },
        "models": [
            {
                "model_id": "gemini-pro",
                "display_name": "Gemini Pro",
                "capabilities": ["text_generation", "chat", "vision"],
                "max_tokens": 32768,
                "context_window": 32768,
                "supports_streaming": True,
                "supports_vision": True
            },
            {
                "model_id": "gemini-pro-vision",
                "display_name": "Gemini Pro Vision",
                "capabilities": ["text_generation", "chat", "vision"],
                "max_tokens": 32768,
                "context_window": 32768,
                "supports_streaming": True,
                "supports_vision": True
            },
            {
                "model_id": "text-bison",
                "display_name": "PaLM 2 Text Bison",
                "capabilities": ["text_generation", "chat"],
                "max_tokens": 8192,
                "context_window": 8192,
                "supports_streaming": False
            }
        ],
        "default_model": "gemini-pro",
        "rate_limits": {
            "requests_per_minute": 60,
            "tokens_per_minute": 60000,
            "concurrent_requests": 10
        },
        "cost_config": {
            "input_token_cost": 0.00025,
            "output_token_cost": 0.0005,
            "monthly_budget": 1500.0,
            "alert_threshold": 70.0
        },
        "is_default": False,
        "auto_retry": True,
        "max_retries": 3,
        "timeout_seconds": 30,
        "status": "active"
    }
]


class LLMProviderSeeder:
    """Utility class to seed LLM providers data"""
    
    def __init__(self, base_url: str = API_BASE_URL, token: str = API_TOKEN):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json"
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    async def test_connection(self) -> bool:
        """Test connection to the API server"""
        print(f"🔌 Testing connection to {self.base_url}...")
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                response = await client.get(f"{self.base_url}/api/health/", follow_redirects=True)
                if response.status_code == 200:
                    print(f"✅ API server is reachable")
                    return True
                else:
                    print(f"⚠️ API returned status {response.status_code}")
                    return False
            except httpx.ConnectError as e:
                print(f"❌ Cannot connect to API server at {self.base_url}")
                print(f"   Error: {str(e)}")
                print(f"   Please ensure the API server is running on the correct port")
                return False
            except httpx.TimeoutException:
                print(f"❌ Connection timeout to {self.base_url}")
                print(f"   The server is not responding")
                return False
            except Exception as e:
                print(f"❌ Connection error: {type(e).__name__}: {str(e)}")
                return False
    
    async def check_company_exists(self, company_id: str) -> bool:
        """Check if company exists"""
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/companies/{company_id}/",
                    headers=self.headers,
                    follow_redirects=True
                )
                return response.status_code == 200
            except Exception as e:
                print(f"⚠️ Error checking company: {str(e)}")
                return False
    
    async def create_default_company(self) -> str:
        """Create a default company if needed"""
        company_data = {
            "_id": "default_company_001",
            "name": "Demo Company",
            "domain": "demo.company.com",
            "industry": "Technology",
            "size": "1000-5000",
            "status": "active",
            "contact": {
                "name": "John Doe",
                "primary_email": "admin@demo.company.com",
                "phone": "+1-555-0100"
            },
            "settings": {
                "ai_enabled": True,
                "default_language": "en",
                "timezone": "UTC"
            },
            "subscription": {
                "plan": "enterprise",
                "limits": {
                    "brands": 10,
                    "users": 1000,
                    "ai_agents": 20,
                    "monthly_messages": 100000
                }
            }
        }
        
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/companies/",
                    headers=self.headers,
                    json=company_data,
                    follow_redirects=True
                )
                if response.status_code in [200, 201]:
                    print(f"✅ Created default company: {company_data['name']}")
                    return company_data["_id"]
                else:
                    print(f"⚠️ Failed to create company: Status {response.status_code} - {response.text}")
                    return company_data["_id"]  # Return ID anyway to continue
            except Exception as e:
                print(f"⚠️ Error creating company: {str(e)}")
                return company_data["_id"]
    
    async def seed_provider(self, provider_data: Dict[str, Any]) -> bool:
        """Seed a single LLM provider"""
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                # First check if provider already exists (by name and company)
                response = await client.get(
                    f"{self.base_url}/api/llm-providers/",
                    headers=self.headers,
                    params={"company_id": provider_data["company_id"]},
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    existing_providers = response.json().get("providers", [])
                    if any(p["name"] == provider_data["name"] for p in existing_providers):
                        print(f"⏭️  Provider '{provider_data['name']}' already exists, skipping...")
                        return True
                
                # Create the provider
                response = await client.post(
                    f"{self.base_url}/api/llm-providers/",
                    headers=self.headers,
                    json=provider_data,
                    follow_redirects=True
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    print(f"✅ Created LLM provider: {provider_data['name']} (ID: {result.get('id', 'N/A')})")
                    return True
                else:
                    print(f"❌ Failed to create provider '{provider_data['name']}': Status {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error creating provider '{provider_data['name']}': {str(e)}")
                return False
    
    async def seed_all_providers(self, providers: List[Dict[str, Any]]) -> None:
        """Seed all LLM providers"""
        print("\n" + "="*60)
        print("🚀 Starting LLM Providers Seeding Process")
        print("="*60 + "\n")
        
        # Use one of the existing company IDs from the database
        # The company service now handles missing fields with defaults
        company_id = "68c69d043ccf03abb3bc3810"
        print(f"✅ Using company ID: {company_id}")
        
        # Update all providers with the company ID
        for provider in providers:
            provider["company_id"] = company_id
        
        print(f"\n📝 Seeding {len(providers)} LLM providers...\n")
        
        success_count = 0
        for i, provider in enumerate(providers, 1):
            print(f"[{i}/{len(providers)}] Processing: {provider['name']}")
            if await self.seed_provider(provider):
                success_count += 1
            await asyncio.sleep(0.5)  # Small delay to avoid rate limiting
        
        print("\n" + "="*60)
        print(f"✨ Seeding Complete!")
        print(f"📊 Results: {success_count}/{len(providers)} providers created successfully")
        print("="*60 + "\n")
    
    async def test_providers(self) -> None:
        """Test all seeded providers by fetching them"""
        print("\n🔍 Testing: Fetching all providers...\n")
        
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/llm-providers/",
                    headers=self.headers,
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    data = response.json()
                    providers = data.get("providers", [])
                    print(f"📋 Found {len(providers)} providers in the system:")
                    for provider in providers:
                        status_emoji = "🟢" if provider.get("status") == "active" else "🔴"
                        default_badge = " [DEFAULT]" if provider.get("is_default") else ""
                        print(f"  {status_emoji} {provider['name']} ({provider['provider_type']}){default_badge}")
                else:
                    print(f"❌ Failed to fetch providers: Status {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"❌ Error fetching providers: {str(e)}")


async def main():
    """Main execution function"""
    seeder = LLMProviderSeeder()
    
    # Test connection first
    if not await seeder.test_connection():
        print("\n⛔ Cannot proceed without API connection.")
        print("Please start the API server with: uvicorn main:app --reload --port 8000")
        return
    
    # Seed the providers
    await seeder.seed_all_providers(LLM_PROVIDERS_DATA)
    
    # Test by fetching all providers
    await seeder.test_providers()
    
    print("\n💡 Note: Remember to update the API keys with real values before using in production!")
    print("📌 Default company ID used: default_company_001")
    print("\n")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())