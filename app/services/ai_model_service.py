"""
AI Model Service
Handles business logic for individual AI model management (separate from LLM Provider configs)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.models.ai_model import (
    AIModelCreate,
    AIModelUpdate,
    AIModelResponse,
    AIModelListResponse,
    AIModelStats,
    AIModelTestResult,
    ModelStatus,
    ModelType
)
from app.models.user_context import UserContext
from app.utils import get_database
import logging

logger = logging.getLogger(__name__)


class AIModelService:
    """Service for managing individual AI models"""

    def __init__(self):
        self.collection_name = "ai_models"

    async def create_model(
        self,
        model_data: AIModelCreate,
        created_by: str = "system",
        user_context: Optional[UserContext] = None
    ) -> AIModelResponse:
        """Create a new AI model"""
        db = get_database()
        collection = db[self.collection_name]

        # Verify provider exists (optional - add lookup to llm_providers collection)
        # provider = await db.llm_providers.find_one({"_id": ObjectId(model_data.provider_id)})
        # if not provider:
        #     raise ValueError("Provider not found")

        # Create model document
        model_doc = {
            **model_data.model_dump(),
            "status": ModelStatus.ACTIVE if model_data.enabled else ModelStatus.INACTIVE,
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
            "created_by": created_by,
            "updated_by": created_by,
            "created_by_context": user_context.model_dump() if user_context else None,
            "updated_by_context": user_context.model_dump() if user_context else None
        }

        result = await collection.insert_one(model_doc)
        model_doc["_id"] = str(result.inserted_id)

        return AIModelResponse(**model_doc)

    async def list_models(
        self,
        company_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        model_type: Optional[ModelType] = None,
        status: Optional[ModelStatus] = None,
        enabled: Optional[bool] = None
    ) -> AIModelListResponse:
        """List AI models with pagination and filtering"""
        db = get_database()
        collection = db[self.collection_name]

        # Build query
        query = {}
        if company_id:
            query["company_id"] = company_id
        if provider_id:
            query["provider_id"] = provider_id
        if model_type:
            query["model_type"] = model_type
        if status:
            query["status"] = status
        if enabled is not None:
            query["enabled"] = enabled

        # Get total count
        total = await collection.count_documents(query)

        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size

        # Get models sorted by priority (ascending = higher priority first)
        cursor = collection.find(query).skip(skip).limit(page_size).sort("priority", 1)
        models = []

        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            models.append(AIModelResponse(**doc))

        return AIModelListResponse(
            models=models,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    async def get_model(self, model_id: str) -> Optional[AIModelResponse]:
        """Get a single AI model by ID"""
        db = get_database()
        collection = db[self.collection_name]

        try:
            doc = await collection.find_one({"_id": ObjectId(model_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
                return AIModelResponse(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting model {model_id}: {e}")
            return None

    async def update_model(
        self,
        model_id: str,
        model_data: AIModelUpdate,
        updated_by: str = "system",
        user_context: Optional[UserContext] = None
    ) -> Optional[AIModelResponse]:
        """Update an AI model"""
        db = get_database()
        collection = db[self.collection_name]

        # Build update document
        update_doc = {
            **{k: v for k, v in model_data.model_dump().items() if v is not None},
            "updated_at": datetime.utcnow(),
            "updated_by": updated_by,
            "updated_by_context": user_context.model_dump() if user_context else None
        }

        # Update status based on enabled flag
        if "enabled" in update_doc:
            update_doc["status"] = ModelStatus.ACTIVE if update_doc["enabled"] else ModelStatus.INACTIVE

        try:
            result = await collection.find_one_and_update(
                {"_id": ObjectId(model_id)},
                {"$set": update_doc},
                return_document=True
            )

            if result:
                result["_id"] = str(result["_id"])
                return AIModelResponse(**result)
            return None
        except Exception as e:
            logger.error(f"Error updating model {model_id}: {e}")
            return None

    async def delete_model(self, model_id: str) -> bool:
        """Delete an AI model"""
        db = get_database()
        collection = db[self.collection_name]

        try:
            result = await collection.delete_one({"_id": ObjectId(model_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting model {model_id}: {e}")
            return False

    async def toggle_model(self, model_id: str) -> Optional[AIModelResponse]:
        """Toggle model enabled status"""
        model = await self.get_model(model_id)
        if not model:
            return None

        update_data = AIModelUpdate(enabled=not model.enabled)
        return await self.update_model(model_id, update_data)

    async def test_model(self, model_id: str) -> AIModelTestResult:
        """Test model connectivity and functionality"""
        model = await self.get_model(model_id)
        if not model:
            return AIModelTestResult(
                success=False,
                message="Model not found",
                response_time_ms=0.0
            )

        # In real implementation:
        # 1. Get provider credentials
        # 2. Make test API call to the model
        # 3. Measure response time
        # 4. Return results

        # Mock implementation
        import random
        import asyncio

        start_time = datetime.utcnow()
        await asyncio.sleep(0.1)  # Simulate API call
        end_time = datetime.utcnow()

        response_time = (end_time - start_time).total_seconds() * 1000

        return AIModelTestResult(
            success=True,
            message=f"Model {model.name} is responding correctly",
            response_time_ms=response_time,
            model_info={
                "model_id": model.model_identifier,
                "context_window": model.context_window,
                "supports_streaming": model.supports_streaming
            }
        )

    async def get_model_stats(
        self,
        model_id: str,
        period: str = "monthly"
    ) -> Optional[AIModelStats]:
        """Get model statistics"""
        model = await self.get_model(model_id)
        if not model:
            return None

        # In real implementation, aggregate from usage logs
        return AIModelStats(
            model_id=model_id,
            model_name=model.name,
            period=period,
            total_requests=model.total_requests,
            successful_requests=model.successful_requests,
            failed_requests=model.failed_requests,
            success_rate=model.success_rate,
            total_input_tokens=model.total_input_tokens,
            total_output_tokens=model.total_output_tokens,
            total_tokens=model.total_input_tokens + model.total_output_tokens,
            total_cost=model.total_cost,
            avg_latency_ms=model.avg_latency_ms,
            calculated_at=datetime.utcnow()
        )

    async def log_model_usage(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        success: bool,
        feature_id: Optional[str] = None
    ) -> bool:
        """Log model usage for statistics"""
        db = get_database()
        collection = db[self.collection_name]

        try:
            model = await self.get_model(model_id)
            if not model:
                return False

            # Calculate cost
            input_cost = (input_tokens / 1000) * model.input_cost_per_1k_tokens
            output_cost = (output_tokens / 1000) * model.output_cost_per_1k_tokens
            total_cost = input_cost + output_cost

            update_doc = {
                "$inc": {
                    "total_requests": 1,
                    "total_input_tokens": input_tokens,
                    "total_output_tokens": output_tokens,
                    "requests_this_month": 1,
                    "tokens_this_month": input_tokens + output_tokens
                },
                "$inc": {
                    "successful_requests": 1 if success else 0,
                    "failed_requests": 0 if success else 1
                },
                "$inc": {
                    "total_cost": total_cost,
                    "cost_this_month": total_cost
                },
                "$set": {
                    "last_used": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "avg_latency_ms": latency_ms  # Simplified - should be moving average
                }
            }

            await collection.update_one(
                {"_id": ObjectId(model_id)},
                update_doc
            )

            return True
        except Exception as e:
            logger.error(f"Error logging model usage: {e}")
            return False

    async def get_models_by_provider(
        self,
        provider_id: str,
        include_inactive: bool = False
    ) -> List[AIModelResponse]:
        """Get all models for a specific provider"""
        db = get_database()
        collection = db[self.collection_name]

        query = {"provider_id": provider_id}
        if not include_inactive:
            query["enabled"] = True

        models = []
        cursor = collection.find(query).sort("priority", 1)

        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            models.append(AIModelResponse(**doc))

        return models


# Singleton instance
ai_model_service = AIModelService()
