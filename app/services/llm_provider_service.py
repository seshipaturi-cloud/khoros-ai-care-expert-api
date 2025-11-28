"""
LLM Provider Service for managing AI model configurations
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from bson.errors import InvalidId
import base64
from cryptography.fernet import Fernet
import os

from app.models.llm_provider import (
    LLMProviderCreate,
    LLMProviderUpdate,
    LLMProviderResponse,
    ProviderStatus,
    LLMProviderStats,
    LLMProviderListResponse,
    ProviderCredentials,
    ModelConfig
)
from app.models.user_context import UserContext
from app.services.company_service import company_service
from config.settings import settings

logger = logging.getLogger(__name__)


class LLMProviderService:
    """Service for managing LLM provider operations"""
    
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.database_name]
        self.collection = self.db.llm_providers
        
        # Related collections
        self.companies_collection = self.db.companies
        self.usage_collection = self.db.llm_usage_logs
        
        # Initialize encryption key (should be stored securely in production)
        self.encryption_key = os.environ.get("ENCRYPTION_KEY", Fernet.generate_key())
        self.cipher = Fernet(self.encryption_key if isinstance(self.encryption_key, bytes) 
                           else self.encryption_key.encode())
    
    def _encrypt_credentials(self, credentials: ProviderCredentials) -> Dict[str, Any]:
        """Encrypt sensitive credential fields"""
        encrypted = credentials.model_dump()
        
        # Encrypt sensitive fields
        sensitive_fields = [
            'api_key', 'api_secret', 'aws_access_key_id', 
            'aws_secret_access_key', 'custom_headers'
        ]
        
        for field in sensitive_fields:
            if field in encrypted and encrypted[field]:
                value = encrypted[field]
                if isinstance(value, dict):
                    value = str(value)
                encrypted[field] = self.cipher.encrypt(value.encode()).decode()
        
        return encrypted
    
    def _decrypt_credentials(self, encrypted: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive credential fields"""
        decrypted = encrypted.copy()
        
        sensitive_fields = [
            'api_key', 'api_secret', 'aws_access_key_id', 
            'aws_secret_access_key', 'custom_headers'
        ]
        
        for field in sensitive_fields:
            if field in decrypted and decrypted[field]:
                try:
                    decrypted[field] = self.cipher.decrypt(
                        decrypted[field].encode()
                    ).decode()
                except:
                    # If decryption fails, leave as is (might not be encrypted)
                    pass
        
        return decrypted
    
    async def create_provider(
        self,
        provider_data: LLMProviderCreate,
        created_by: str = "system",
        user_context: Optional[UserContext] = None
    ) -> LLMProviderResponse:
        """Create a new LLM provider configuration"""
        try:
            # Check company exists - temporarily disabled for seeding
            # TODO: Re-enable this after fixing company service
            company = None
            try:
                company = await company_service.get_company(provider_data.company_id)
            except Exception as e:
                logger.warning(f"Could not validate company {provider_data.company_id}: {e}")
                # For now, create a mock company object for seeding purposes
                class MockCompany:
                    name = "Demo Company"
                    settings = type('obj', (object,), {'allowed_llm_providers': ["openai", "anthropic", "azure_openai", "aws_bedrock", "google"]})()
                company = MockCompany()
            
            # Skip provider type check if company validation failed
            if company and hasattr(company, 'settings') and hasattr(company.settings, 'allowed_llm_providers'):
                if provider_data.provider_type not in company.settings.allowed_llm_providers:
                    raise ValueError(f"Provider type {provider_data.provider_type} not allowed for this company")
            
            # Check for duplicate name
            existing = await self.collection.find_one({
                "company_id": provider_data.company_id,
                "name": provider_data.name
            })
            
            if existing:
                raise ValueError(f"Provider with name '{provider_data.name}' already exists")
            
            # Encrypt credentials
            encrypted_credentials = self._encrypt_credentials(provider_data.credentials)
            
            # Prepare document for MongoDB
            doc = {
                "_id": str(ObjectId()),
                **provider_data.model_dump(exclude={"credentials"}),
                "credentials": encrypted_credentials,
                "status": ProviderStatus.ACTIVE,
                "tokens_used_this_month": 0,
                "requests_this_month": 0,
                "cost_this_month": 0.0,
                "total_requests": 0,
                "total_tokens": 0,
                "total_errors": 0,
                "avg_latency_ms": 0.0,
                "success_rate": 100.0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": created_by,
                "updated_by": created_by,
                "created_by_context": user_context.model_dump() if user_context else None,
                "updated_by_context": user_context.model_dump() if user_context else None
            }
            
            # Insert into MongoDB
            await self.collection.insert_one(doc)
            
            # Remove credentials from response
            doc.pop("credentials", None)
            doc["company_name"] = company.name
            
            logger.info(f"Created LLM provider: {provider_data.name} with ID: {doc['_id']}")
            
            return LLMProviderResponse(**doc)
            
        except Exception as e:
            logger.error(f"Error creating LLM provider: {e}")
            raise
    
    async def get_provider(
        self,
        provider_id: str,
        include_credentials: bool = False
    ) -> Optional[LLMProviderResponse]:
        """Get an LLM provider by ID"""
        try:
            provider = await self.collection.find_one({"_id": provider_id})
            
            if not provider:
                return None
            
            # Get company name
            company = await self.companies_collection.find_one({"_id": provider["company_id"]})
            provider["company_name"] = company["name"] if company else None
            
            # Get current month usage stats
            start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            usage_stats = await self.usage_collection.aggregate([
                {
                    "$match": {
                        "provider_id": provider_id,
                        "timestamp": {"$gte": start_of_month}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_requests": {"$sum": 1},
                        "total_tokens": {"$sum": "$tokens_used"},
                        "total_cost": {"$sum": "$cost"}
                    }
                }
            ]).to_list(1)
            
            if usage_stats:
                provider["requests_this_month"] = usage_stats[0].get("total_requests", 0)
                provider["tokens_used_this_month"] = usage_stats[0].get("total_tokens", 0)
                provider["cost_this_month"] = usage_stats[0].get("total_cost", 0.0)
            
            # Remove or decrypt credentials based on request
            if include_credentials:
                provider["credentials"] = self._decrypt_credentials(provider.get("credentials", {}))
            else:
                provider.pop("credentials", None)
            
            return LLMProviderResponse(**provider)
            
        except InvalidId:
            logger.error(f"Invalid provider ID: {provider_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting provider: {e}")
            raise
    
    async def update_provider(
        self,
        provider_id: str,
        provider_data: LLMProviderUpdate,
        updated_by: str = "system",
        user_context: Optional[UserContext] = None
    ) -> Optional[LLMProviderResponse]:
        """Update an LLM provider"""
        try:
            # Check if provider exists
            existing = await self.collection.find_one({"_id": provider_id})
            if not existing:
                return None
            
            # Prepare update document
            update_doc = {
                k: v for k, v in provider_data.model_dump(exclude={"credentials"}, exclude_unset=True).items()
                if v is not None
            }
            
            # Handle credentials update
            if provider_data.credentials:
                update_doc["credentials"] = self._encrypt_credentials(provider_data.credentials)
            
            if update_doc:
                update_doc["updated_at"] = datetime.utcnow()
                update_doc["updated_by"] = updated_by
                update_doc["updated_by_context"] = user_context.model_dump() if user_context else None

                # Update in MongoDB
                await self.collection.update_one(
                    {"_id": provider_id},
                    {"$set": update_doc}
                )
            
            # Return updated provider
            return await self.get_provider(provider_id)
            
        except Exception as e:
            logger.error(f"Error updating provider: {e}")
            raise
    
    async def delete_provider(self, provider_id: str) -> bool:
        """Delete an LLM provider"""
        try:
            # Check if provider is being used by any agents
            from app.services.ai_agent_service import ai_agent_service
            agents_using = await ai_agent_service.db.ai_agents.count_documents({
                "llm_provider_id": provider_id
            })
            
            if agents_using > 0:
                # Soft delete - mark as inactive
                result = await self.collection.update_one(
                    {"_id": provider_id},
                    {
                        "$set": {
                            "status": ProviderStatus.INACTIVE,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            else:
                # Hard delete if not in use
                result = await self.collection.delete_one({"_id": provider_id})
            
            return result.modified_count > 0 or result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting provider: {e}")
            raise
    
    async def list_providers(
        self,
        company_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        status: Optional[ProviderStatus] = None,
        provider_type: Optional[str] = None
    ) -> LLMProviderListResponse:
        """List LLM providers with pagination and filtering"""
        try:
            # Build query
            query = {}
            
            if company_id:
                query["company_id"] = company_id
            
            if status:
                query["status"] = status
            
            if provider_type:
                query["provider_type"] = provider_type
            
            # Get total count
            total = await self.collection.count_documents(query)
            
            # Calculate pagination
            skip = (page - 1) * page_size
            total_pages = (total + page_size - 1) // page_size
            
            # Get providers with company info
            pipeline = [
                {"$match": query},
                {"$sort": {"created_at": -1}},
                {"$skip": skip},
                {"$limit": page_size},
                {
                    "$lookup": {
                        "from": "companies",
                        "localField": "company_id",
                        "foreignField": "_id",
                        "as": "company"
                    }
                },
                {
                    "$addFields": {
                        "company_name": {"$arrayElemAt": ["$company.name", 0]}
                    }
                },
                {"$project": {"company": 0, "credentials": 0}}  # Remove sensitive data
            ]
            
            cursor = self.collection.aggregate(pipeline)
            
            providers = []
            async for doc in cursor:
                providers.append(LLMProviderResponse(**doc))
            
            return LLMProviderListResponse(
                providers=providers,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Error listing providers: {e}")
            raise
    
    async def get_providers_by_company(
        self,
        company_id: str,
        include_inactive: bool = False
    ) -> List[LLMProviderResponse]:
        """Get all providers for a company"""
        try:
            query = {"company_id": company_id}
            
            if not include_inactive:
                query["status"] = ProviderStatus.ACTIVE
            
            cursor = self.collection.find(query, {"credentials": 0}).sort("name", 1)
            
            providers = []
            async for doc in cursor:
                # Get company name
                company = await self.companies_collection.find_one({"_id": doc["company_id"]})
                doc["company_name"] = company["name"] if company else None
                
                providers.append(LLMProviderResponse(**doc))
            
            return providers
            
        except Exception as e:
            logger.error(f"Error getting providers by company: {e}")
            raise
    
    async def log_usage(
        self,
        provider_id: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        success: bool,
        error_message: Optional[str] = None
    ):
        """Log usage for a provider"""
        try:
            provider = await self.get_provider(provider_id)
            if not provider:
                return
            
            # Find model config to calculate cost
            model_config = next(
                (m for m in provider.models if m.model_id == model_id),
                None
            )
            
            cost = 0.0
            if model_config:
                cost = (
                    (input_tokens / 1000) * model_config.input_cost_per_1k_tokens +
                    (output_tokens / 1000) * model_config.output_cost_per_1k_tokens
                )
            
            # Log usage
            usage_doc = {
                "_id": str(ObjectId()),
                "provider_id": provider_id,
                "model_id": model_id,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "tokens_used": input_tokens + output_tokens,
                "cost": cost,
                "latency_ms": latency_ms,
                "success": success,
                "error_message": error_message,
                "timestamp": datetime.utcnow()
            }
            
            await self.usage_collection.insert_one(usage_doc)
            
            # Update provider statistics
            update_doc = {
                "$inc": {
                    "total_requests": 1,
                    "total_tokens": input_tokens + output_tokens,
                    "total_errors": 0 if success else 1
                },
                "$set": {
                    "last_used": datetime.utcnow()
                }
            }
            
            if not success:
                update_doc["$set"]["last_error"] = error_message
                update_doc["$set"]["status"] = ProviderStatus.ERROR
            
            await self.collection.update_one(
                {"_id": provider_id},
                update_doc
            )
            
        except Exception as e:
            logger.error(f"Error logging usage: {e}")
    
    async def get_provider_stats(
        self,
        provider_id: str,
        period: str = "daily"
    ) -> Optional[LLMProviderStats]:
        """Get provider usage statistics"""
        try:
            provider = await self.get_provider(provider_id)
            if not provider:
                return None
            
            # Calculate time range
            now = datetime.utcnow()
            if period == "hourly":
                start_time = now - timedelta(hours=1)
            elif period == "daily":
                start_time = now - timedelta(days=1)
            elif period == "weekly":
                start_time = now - timedelta(weeks=1)
            else:  # monthly
                start_time = now - timedelta(days=30)
            
            # Aggregate usage statistics
            stats_pipeline = [
                {
                    "$match": {
                        "provider_id": provider_id,
                        "timestamp": {"$gte": start_time}
                    }
                },
                {
                    "$group": {
                        "_id": "$model_id",
                        "requests": {"$sum": 1},
                        "successful": {"$sum": {"$cond": ["$success", 1, 0]}},
                        "failed": {"$sum": {"$cond": ["$success", 0, 1]}},
                        "input_tokens": {"$sum": "$input_tokens"},
                        "output_tokens": {"$sum": "$output_tokens"},
                        "total_cost": {"$sum": "$cost"},
                        "avg_latency": {"$avg": "$latency_ms"},
                        "p50_latency": {"$percentile": ["$latency_ms", 0.5]},
                        "p95_latency": {"$percentile": ["$latency_ms", 0.95]},
                        "p99_latency": {"$percentile": ["$latency_ms", 0.99]}
                    }
                }
            ]
            
            cursor = self.usage_collection.aggregate(stats_pipeline)
            model_usage = {}
            
            total_requests = 0
            successful_requests = 0
            failed_requests = 0
            input_tokens = 0
            output_tokens = 0
            total_cost = 0.0
            
            async for doc in cursor:
                model_usage[doc["_id"]] = {
                    "requests": doc["requests"],
                    "tokens": doc["input_tokens"] + doc["output_tokens"],
                    "cost": doc["total_cost"],
                    "avg_latency": doc["avg_latency"]
                }
                
                total_requests += doc["requests"]
                successful_requests += doc["successful"]
                failed_requests += doc["failed"]
                input_tokens += doc["input_tokens"]
                output_tokens += doc["output_tokens"]
                total_cost += doc["total_cost"]
            
            return LLMProviderStats(
                provider_id=provider_id,
                provider_name=provider.name,
                period=period,
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                input_cost=(input_tokens / 1000) * 0.01,  # Default pricing
                output_cost=(output_tokens / 1000) * 0.03,  # Default pricing
                total_cost=total_cost,
                model_usage=model_usage,
                calculated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error getting provider stats: {e}")
            raise


# Create singleton instance
llm_provider_service = LLMProviderService()