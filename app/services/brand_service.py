"""
Brand Service for managing brands within companies
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from bson.errors import InvalidId

from app.models.brand import (
    BrandCreate,
    BrandUpdate,
    BrandResponse,
    BrandStatus,
    BrandStats,
    BrandListResponse
)
from app.services.company_service import company_service
from config.settings import settings

logger = logging.getLogger(__name__)


class BrandService:
    """Service for managing brand operations"""
    
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.database_name]
        self.collection = self.db.brands
        
        # Related collections
        self.companies_collection = self.db.companies
        self.agents_collection = self.db.ai_agents
        self.knowledge_collection = self.db.knowledge_base_items
        self.conversations_collection = self.db.conversations
    
    async def create_brand(
        self,
        brand_data: BrandCreate,
        created_by: str = "system"
    ) -> BrandResponse:
        """Create a new brand"""
        try:
            # Check company exists and has capacity
            limit_check = await company_service.check_company_limits(
                brand_data.company_id, "brands"
            )
            if not limit_check["allowed"]:
                raise ValueError(limit_check["reason"])
            
            # Check if brand with same code exists for this company
            existing = await self.collection.find_one({
                "company_id": brand_data.company_id,
                "code": brand_data.code
            })
            
            if existing:
                raise ValueError(f"Brand with code '{brand_data.code}' already exists for this company")
            
            # Get company name for response
            company = await self.companies_collection.find_one({"_id": brand_data.company_id})
            
            # Prepare document for MongoDB
            doc = {
                "_id": str(ObjectId()),
                **brand_data.model_dump(exclude_unset=True),
                "status": BrandStatus.ACTIVE,
                "total_agents": 0,
                "total_knowledge_items": 0,
                "total_conversations": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": created_by,
                "updated_by": created_by
            }
            
            # Insert into MongoDB
            await self.collection.insert_one(doc)
            
            # Add company name to response
            doc["company_name"] = company["name"] if company else None
            
            logger.info(f"Created brand: {brand_data.name} with ID: {doc['_id']}")
            
            return BrandResponse(**doc)
            
        except Exception as e:
            logger.error(f"Error creating brand: {e}")
            raise
    
    async def get_brand(self, brand_id: str) -> Optional[BrandResponse]:
        """Get a brand by ID"""
        try:
            # Try with string ID first (for backward compatibility)
            brand = await self.collection.find_one({"_id": brand_id})
            
            # If not found and brand_id is a valid ObjectId string, try with ObjectId
            if not brand and ObjectId.is_valid(brand_id):
                try:
                    brand = await self.collection.find_one({"_id": ObjectId(brand_id)})
                except:
                    pass
            
            if not brand:
                return None
            
            # Convert ObjectId to string if needed
            if not isinstance(brand["_id"], str):
                brand["_id"] = str(brand["_id"])
            
            # Get company name
            company = await self.companies_collection.find_one({"_id": brand["company_id"]})
            brand["company_name"] = company["name"] if company else None
            
            # Get statistics
            brand["total_agents"] = await self.agents_collection.count_documents(
                {"brand_ids": brand_id}
            )
            brand["total_knowledge_items"] = await self.knowledge_collection.count_documents(
                {"brand_ids": brand_id}
            )
            brand["total_conversations"] = await self.conversations_collection.count_documents(
                {"brand_ids": brand_id}
            )
            
            return BrandResponse(**brand)
            
        except InvalidId:
            logger.error(f"Invalid brand ID: {brand_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting brand: {e}")
            raise
    
    async def update_brand(
        self,
        brand_id: str,
        brand_data: BrandUpdate,
        updated_by: str = "system"
    ) -> Optional[BrandResponse]:
        """Update a brand"""
        try:
            # Check if brand exists
            # Try with string ID first, then ObjectId if valid
            existing = await self.collection.find_one({"_id": brand_id})
            if not existing and ObjectId.is_valid(brand_id):
                try:
                    existing = await self.collection.find_one({"_id": ObjectId(brand_id)})
                except:
                    pass
            if not existing:
                return None
            
            # Check if new code conflicts with existing
            if brand_data.code:
                code_exists = await self.collection.find_one({
                    "_id": {"$ne": brand_id},
                    "company_id": existing["company_id"],
                    "code": brand_data.code
                })
                if code_exists:
                    raise ValueError(f"Brand code '{brand_data.code}' already exists")
            
            # Prepare update document
            update_doc = {
                k: v for k, v in brand_data.model_dump(exclude_unset=True).items()
                if v is not None
            }
            
            if update_doc:
                update_doc["updated_at"] = datetime.utcnow()
                update_doc["updated_by"] = updated_by
                
                # Update in MongoDB - handle both string and ObjectId
                if existing:
                    await self.collection.update_one(
                        {"_id": existing["_id"]},
                        {"$set": update_doc}
                    )
            
            # Return updated brand
            return await self.get_brand(brand_id)
            
        except Exception as e:
            logger.error(f"Error updating brand: {e}")
            raise
    
    async def delete_brand(self, brand_id: str) -> bool:
        """Delete a brand (soft delete by setting status to archived)"""
        try:
            # First get the brand to ensure it exists and get correct _id format
            brand = await self.get_brand(brand_id)
            if not brand:
                return False
            
            # Use the brand's actual _id for queries
            actual_id = brand.id
            
            # Check for existing relationships
            agents_count = await self.agents_collection.count_documents({"brand_ids": actual_id})
            knowledge_count = await self.knowledge_collection.count_documents({"brand_ids": actual_id})
            
            if agents_count > 0 or knowledge_count > 0:
                # Soft delete - just mark as archived
                result = await self.collection.update_one(
                    {"_id": actual_id},
                    {
                        "$set": {
                            "status": BrandStatus.ARCHIVED,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            else:
                # Hard delete if no relationships
                result = await self.collection.delete_one({"_id": actual_id})
            
            return result.modified_count > 0 or result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting brand: {e}")
            raise
    
    async def list_brands(
        self,
        company_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        status: Optional[BrandStatus] = None,
        search: Optional[str] = None
    ) -> BrandListResponse:
        """List brands with pagination and filtering"""
        try:
            # Build query
            query = {}
            
            if company_id:
                query["company_id"] = company_id
            
            if status:
                query["status"] = status
            
            if search:
                query["$or"] = [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"code": {"$regex": search, "$options": "i"}},
                    {"description": {"$regex": search, "$options": "i"}}
                ]
            
            # Get total count
            total = await self.collection.count_documents(query)
            
            # Calculate pagination
            skip = (page - 1) * page_size
            total_pages = (total + page_size - 1) // page_size
            
            # Get brands with company info
            pipeline = [
                {"$match": query},
                {"$sort": {"created_at": -1}},
                {"$skip": skip},
                {"$limit": page_size},
                {
                    "$addFields": {
                        "company_id_obj": {
                            "$cond": {
                                "if": {"$eq": [{"$type": "$company_id"}, "string"]},
                                "then": {"$toObjectId": "$company_id"},
                                "else": "$company_id"
                            }
                        }
                    }
                },
                {
                    "$lookup": {
                        "from": "companies",
                        "localField": "company_id_obj",
                        "foreignField": "_id",
                        "as": "company"
                    }
                },
                {
                    "$addFields": {
                        "company_name": {"$arrayElemAt": ["$company.name", 0]}
                    }
                },
                {"$project": {"company": 0, "company_id_obj": 0}}
            ]
            
            cursor = self.collection.aggregate(pipeline)
            
            brands = []
            async for doc in cursor:
                # Convert ObjectId to string
                brand_id = str(doc["_id"])
                doc["_id"] = brand_id
                
                # Convert company_id to string if it's an ObjectId
                if "company_id" in doc and not isinstance(doc["company_id"], str):
                    doc["company_id"] = str(doc["company_id"])
                
                # Get statistics for each brand
                doc["total_agents"] = await self.agents_collection.count_documents(
                    {"brand_ids": brand_id}
                )
                doc["total_knowledge_items"] = await self.knowledge_collection.count_documents(
                    {"brand_ids": brand_id}
                )
                doc["total_conversations"] = await self.conversations_collection.count_documents(
                    {"brand_ids": brand_id}
                )
                
                brands.append(BrandResponse(**doc))
            
            return BrandListResponse(
                brands=brands,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Error listing brands: {e}")
            raise
    
    async def get_brands_by_company(
        self,
        company_id: str,
        include_inactive: bool = False
    ) -> List[BrandResponse]:
        """Get all brands for a company"""
        try:
            query = {"company_id": company_id}
            
            if not include_inactive:
                query["status"] = BrandStatus.ACTIVE
            
            cursor = self.collection.find(query).sort("name", 1)
            
            brands = []
            async for doc in cursor:
                # Convert ObjectId to string if needed
                if not isinstance(doc["_id"], str):
                    doc["_id"] = str(doc["_id"])
                    
                # Get company name
                company = await self.companies_collection.find_one({"_id": doc["company_id"]})
                doc["company_name"] = company["name"] if company else None
                
                brands.append(BrandResponse(**doc))
            
            return brands
            
        except Exception as e:
            logger.error(f"Error getting brands by company: {e}")
            raise
    
    async def get_brand_stats(
        self,
        brand_id: str,
        period: str = "monthly"
    ) -> Optional[BrandStats]:
        """Get brand performance statistics"""
        try:
            brand = await self.get_brand(brand_id)
            if not brand:
                return None
            
            stats = BrandStats(
                brand_id=brand_id,
                brand_name=brand.name,
                period=period,
                active_agents=brand.total_agents,
                knowledge_base_hits=brand.total_knowledge_items,
                calculated_at=datetime.utcnow()
            )
            
            # Additional statistics would be calculated from message/conversation collections
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting brand stats: {e}")
            raise
    
    async def assign_ai_agent(self, brand_id: str, ai_agent_id: str, updated_by: str = "system") -> bool:
        """
        Assign an AI agent to a brand (1:1 relationship)
        Updates both brand and AI agent to maintain the relationship
        """
        try:
            # Get brand to ensure it exists and get correct _id format
            brand = await self.get_brand(brand_id)
            if not brand:
                return False
            
            # Update brand with AI agent reference
            brand_result = await self.collection.update_one(
                {"_id": brand.id},
                {
                    "$set": {
                        "ai_agent_id": ai_agent_id,
                        "updated_at": datetime.utcnow(),
                        "updated_by": updated_by
                    }
                }
            )
            
            if brand_result.modified_count == 0:
                return False
            
            # Update AI agent with brand reference (1:1 relationship)
            agent_result = await self.agents_collection.update_one(
                {"_id": ai_agent_id},
                {
                    "$set": {
                        "brand_ids": [brand.id],  # Use the actual brand ID format as a list
                        "updated_at": datetime.utcnow(),
                        "updated_by": updated_by
                    }
                }
            )
            
            if agent_result.modified_count == 0:
                # Rollback brand update if agent update fails
                await self.collection.update_one(
                    {"_id": brand.id},
                    {
                        "$unset": {"ai_agent_id": ""},
                        "$set": {
                            "updated_at": datetime.utcnow(),
                            "updated_by": updated_by
                        }
                    }
                )
                return False
            
            logger.info(f"Successfully assigned AI agent {ai_agent_id} to brand {brand_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error assigning AI agent to brand: {e}")
            raise
    
    async def unassign_ai_agent(self, brand_id: str, updated_by: str = "system") -> bool:
        """
        Unassign AI agent from a brand
        Removes the 1:1 relationship between brand and AI agent
        """
        try:
            # Get current brand to find AI agent and get correct _id format
            brand = await self.get_brand(brand_id)
            if not brand or not brand.ai_agent_id:
                return False
            
            ai_agent_id = brand.ai_agent_id
            
            # Remove AI agent reference from brand
            brand_result = await self.collection.update_one(
                {"_id": brand.id},
                {
                    "$unset": {"ai_agent_id": ""},
                    "$set": {
                        "updated_at": datetime.utcnow(),
                        "updated_by": updated_by
                    }
                }
            )
            
            # Remove brand reference from AI agent
            agent_result = await self.agents_collection.update_one(
                {"_id": ai_agent_id},
                {
                    "$unset": {"brand_ids": ""},
                    "$set": {
                        "updated_at": datetime.utcnow(),
                        "updated_by": updated_by
                    }
                }
            )
            
            logger.info(f"Successfully unassigned AI agent {ai_agent_id} from brand {brand_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error unassigning AI agent from brand: {e}")
            raise
    
    async def migrate_existing_brands(self):
        """Migrate existing brand references to actual brand documents"""
        try:
            # Get unique brand IDs from various collections
            agent_brands = await self.agents_collection.distinct("brand_ids")
            knowledge_brands = await self.knowledge_collection.distinct("brand_ids")
            
            all_brand_ids = set(agent_brands + knowledge_brands)
            
            # Create default brands for unmigrated IDs
            default_company_id = "default_company"  # You'd create this first
            
            for brand_id in all_brand_ids:
                # Try with string ID first, then ObjectId if valid
                existing = await self.collection.find_one({"_id": brand_id})
                if not existing and ObjectId.is_valid(brand_id):
                    try:
                        existing = await self.collection.find_one({"_id": ObjectId(brand_id)})
                    except:
                        pass
                if not existing:
                    # Create a default brand entry
                    doc = {
                        "_id": brand_id,
                        "company_id": default_company_id,
                        "name": f"Brand {brand_id}",
                        "code": f"BRAND_{brand_id[:8]}",
                        "status": BrandStatus.ACTIVE,
                        "voice_settings": {},
                        "ai_settings": {},
                        "social_settings": {},
                        "timezone": "UTC",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "created_by": "migration",
                        "updated_by": "migration"
                    }
                    await self.collection.insert_one(doc)
                    logger.info(f"Migrated brand ID: {brand_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error migrating brands: {e}")
            raise


# Create singleton instance
brand_service = BrandService()