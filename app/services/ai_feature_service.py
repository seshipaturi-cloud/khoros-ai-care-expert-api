"""
AI Feature Service
Handles business logic for AI feature management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.models.ai_feature import (
    AIFeatureCreate,
    AIFeatureUpdate,
    AIFeatureResponse,
    AIFeatureListResponse,
    AIFeatureStats,
    FeatureStatus
)
from app.utils import get_database
import logging

logger = logging.getLogger(__name__)


class AIFeatureService:
    """Service for managing AI features"""

    def __init__(self):
        self.collection_name = "ai_features"

    async def create_feature(
        self,
        feature_data: AIFeatureCreate,
        created_by: str = "system"
    ) -> AIFeatureResponse:
        """Create a new AI feature"""
        db = get_database()
        collection = db[self.collection_name]

        # Create feature document
        feature_doc = {
            **feature_data.model_dump(),
            "status": FeatureStatus.ACTIVE if feature_data.enabled else FeatureStatus.INACTIVE,
            "total_conversations": 0,
            "total_analyses": 0,
            "accuracy_rate": 0.0,
            "success_rate": 100.0,
            "avg_processing_time_ms": 0.0,
            "conversations_this_month": 0,
            "analyses_this_month": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": created_by,
            "updated_by": created_by
        }

        result = await collection.insert_one(feature_doc)
        feature_doc["_id"] = str(result.inserted_id)

        return AIFeatureResponse(**feature_doc)

    async def list_features(
        self,
        company_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        feature_type: Optional[str] = None,
        status: Optional[FeatureStatus] = None,
        enabled: Optional[bool] = None
    ) -> AIFeatureListResponse:
        """List AI features with pagination and filtering"""
        db = get_database()
        collection = db[self.collection_name]

        # Build query
        query = {}
        if company_id:
            query["company_id"] = company_id
        if feature_type:
            query["feature_type"] = feature_type
        if status:
            query["status"] = status
        if enabled is not None:
            query["enabled"] = enabled

        # Get total count
        total = await collection.count_documents(query)

        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size

        # Get features
        cursor = collection.find(query).skip(skip).limit(page_size).sort("name", 1)
        features = []

        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            features.append(AIFeatureResponse(**doc))

        return AIFeatureListResponse(
            features=features,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    async def get_feature(self, feature_id: str) -> Optional[AIFeatureResponse]:
        """Get a single AI feature by ID"""
        db = get_database()
        collection = db[self.collection_name]

        try:
            doc = await collection.find_one({"_id": ObjectId(feature_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
                return AIFeatureResponse(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting feature {feature_id}: {e}")
            return None

    async def update_feature(
        self,
        feature_id: str,
        feature_data: AIFeatureUpdate,
        updated_by: str = "system"
    ) -> Optional[AIFeatureResponse]:
        """Update an AI feature"""
        db = get_database()
        collection = db[self.collection_name]

        # Build update document
        update_doc = {
            **{k: v for k, v in feature_data.model_dump().items() if v is not None},
            "updated_at": datetime.utcnow(),
            "updated_by": updated_by
        }

        # Update status based on enabled flag if changed
        if "enabled" in update_doc:
            update_doc["status"] = FeatureStatus.ACTIVE if update_doc["enabled"] else FeatureStatus.INACTIVE

        try:
            result = await collection.find_one_and_update(
                {"_id": ObjectId(feature_id)},
                {"$set": update_doc},
                return_document=True
            )

            if result:
                result["_id"] = str(result["_id"])
                return AIFeatureResponse(**result)
            return None
        except Exception as e:
            logger.error(f"Error updating feature {feature_id}: {e}")
            return None

    async def delete_feature(self, feature_id: str) -> bool:
        """Delete an AI feature"""
        db = get_database()
        collection = db[self.collection_name]

        try:
            result = await collection.delete_one({"_id": ObjectId(feature_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting feature {feature_id}: {e}")
            return False

    async def toggle_feature(self, feature_id: str) -> Optional[AIFeatureResponse]:
        """Toggle feature enabled status"""
        feature = await self.get_feature(feature_id)
        if not feature:
            return None

        update_data = AIFeatureUpdate(enabled=not feature.enabled)
        return await self.update_feature(feature_id, update_data)

    async def get_feature_stats(self, feature_id: str, period: str = "monthly") -> Optional[AIFeatureStats]:
        """Get feature statistics"""
        feature = await self.get_feature(feature_id)
        if not feature:
            return None

        # In real implementation, aggregate from usage logs
        # For now, return mock stats
        return AIFeatureStats(
            feature_id=feature_id,
            feature_name=feature.name,
            period=period,
            total_conversations=feature.total_conversations,
            total_analyses=feature.total_analyses,
            successful_analyses=int(feature.total_analyses * feature.success_rate / 100),
            failed_analyses=int(feature.total_analyses * (100 - feature.success_rate) / 100),
            avg_processing_time_ms=feature.avg_processing_time_ms,
            accuracy_rate=feature.accuracy_rate,
            calculated_at=datetime.utcnow()
        )

    async def get_features_by_company(
        self,
        company_id: str,
        include_inactive: bool = False
    ) -> List[AIFeatureResponse]:
        """Get all features for a company"""
        db = get_database()
        collection = db[self.collection_name]

        query = {"company_id": company_id}
        if not include_inactive:
            query["enabled"] = True

        features = []
        cursor = collection.find(query).sort("name", 1)

        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            features.append(AIFeatureResponse(**doc))

        return features

    async def log_feature_usage(
        self,
        feature_id: str,
        success: bool,
        processing_time_ms: float,
        accuracy_score: Optional[float] = None
    ) -> bool:
        """Log feature usage for statistics"""
        db = get_database()
        collection = db[self.collection_name]

        try:
            update_doc = {
                "$inc": {
                    "total_conversations": 1,
                    "total_analyses": 1,
                    "conversations_this_month": 1,
                    "analyses_this_month": 1
                },
                "$set": {
                    "last_used": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }

            # Update avg processing time (simple moving average)
            # In production, use proper time-series data
            if processing_time_ms:
                # This is simplified - should use aggregation pipeline
                update_doc["$set"]["avg_processing_time_ms"] = processing_time_ms

            await collection.update_one(
                {"_id": ObjectId(feature_id)},
                update_doc
            )

            return True
        except Exception as e:
            logger.error(f"Error logging feature usage: {e}")
            return False


# Singleton instance
ai_feature_service = AIFeatureService()
