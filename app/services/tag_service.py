"""
Tag Service
Handles business logic for tag management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.models.tag import (
    TagCreate,
    TagUpdate,
    TagResponse,
    TagListResponse,
    TagCategory
)
from app.utils import get_database
import logging

logger = logging.getLogger(__name__)


class TagService:
    """Service for managing tags"""

    def __init__(self):
        self.collection_name = "tags"

    async def create_tag(
        self,
        tag_data: TagCreate,
        created_by: str = "system"
    ) -> TagResponse:
        """Create a new tag"""
        db = get_database()
        collection = db[self.collection_name]

        # Check if tag name already exists
        existing_tag = await collection.find_one({"name": tag_data.name})
        if existing_tag:
            raise ValueError(f"Tag with name '{tag_data.name}' already exists")

        # Create tag document
        tag_doc = {
            **tag_data.model_dump(),
            "usage_count": 0,
            "last_used": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": created_by,
            "updated_by": created_by
        }

        result = await collection.insert_one(tag_doc)
        tag_doc["_id"] = str(result.inserted_id)

        return TagResponse(**tag_doc)

    async def list_tags(
        self,
        page: int = 1,
        page_size: int = 100,
        category: Optional[TagCategory] = None,
        enabled: Optional[bool] = None,
        search: Optional[str] = None
    ) -> TagListResponse:
        """List tags with pagination and filtering"""
        db = get_database()
        collection = db[self.collection_name]

        # Build query
        query = {}
        if category:
            query["category"] = category
        if enabled is not None:
            query["enabled"] = enabled
        if search:
            query["name"] = {"$regex": search, "$options": "i"}

        # Get total count
        total = await collection.count_documents(query)

        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size

        # Get tags
        cursor = collection.find(query).skip(skip).limit(page_size).sort("name", 1)
        tags = []

        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            tags.append(TagResponse(**doc))

        return TagListResponse(
            tags=tags,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    async def get_tag(self, tag_id: str) -> Optional[TagResponse]:
        """Get a single tag by ID"""
        db = get_database()
        collection = db[self.collection_name]

        try:
            doc = await collection.find_one({"_id": ObjectId(tag_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
                return TagResponse(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting tag {tag_id}: {e}")
            return None

    async def update_tag(
        self,
        tag_id: str,
        tag_data: TagUpdate,
        updated_by: str = "system"
    ) -> Optional[TagResponse]:
        """Update a tag"""
        db = get_database()
        collection = db[self.collection_name]

        # Build update document
        update_dict = {k: v for k, v in tag_data.model_dump().items() if v is not None}

        # Check if name is being updated and ensure it's unique
        if "name" in update_dict:
            existing_tag = await collection.find_one({
                "name": update_dict["name"],
                "_id": {"$ne": ObjectId(tag_id)}
            })
            if existing_tag:
                raise ValueError(f"Tag with name '{update_dict['name']}' already exists")

        update_doc = {
            **update_dict,
            "updated_at": datetime.utcnow(),
            "updated_by": updated_by
        }

        try:
            result = await collection.find_one_and_update(
                {"_id": ObjectId(tag_id)},
                {"$set": update_doc},
                return_document=True
            )

            if result:
                result["_id"] = str(result["_id"])
                return TagResponse(**result)
            return None
        except Exception as e:
            logger.error(f"Error updating tag {tag_id}: {e}")
            return None

    async def delete_tag(self, tag_id: str) -> bool:
        """Delete a tag"""
        db = get_database()
        collection = db[self.collection_name]

        try:
            result = await collection.delete_one({"_id": ObjectId(tag_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting tag {tag_id}: {e}")
            return False

    async def toggle_tag(self, tag_id: str) -> Optional[TagResponse]:
        """Toggle tag enabled status"""
        tag = await self.get_tag(tag_id)
        if not tag:
            return None

        update_data = TagUpdate(enabled=not tag.enabled)
        return await self.update_tag(tag_id, update_data)

    async def increment_usage(self, tag_id: str) -> bool:
        """Increment tag usage count"""
        db = get_database()
        collection = db[self.collection_name]

        try:
            await collection.update_one(
                {"_id": ObjectId(tag_id)},
                {
                    "$inc": {"usage_count": 1},
                    "$set": {
                        "last_used": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error incrementing tag usage: {e}")
            return False

    async def get_tags_by_category(self, category: TagCategory) -> List[TagResponse]:
        """Get all tags in a specific category"""
        db = get_database()
        collection = db[self.collection_name]

        tags = []
        cursor = collection.find({"category": category, "enabled": True}).sort("name", 1)

        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            tags.append(TagResponse(**doc))

        return tags

    async def get_popular_tags(self, limit: int = 10) -> List[TagResponse]:
        """Get most frequently used tags"""
        db = get_database()
        collection = db[self.collection_name]

        tags = []
        cursor = collection.find({"enabled": True}).sort("usage_count", -1).limit(limit)

        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            tags.append(TagResponse(**doc))

        return tags


# Singleton instance
tag_service = TagService()
