"""
Company Service for managing multi-tenant companies
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from bson.errors import InvalidId

from app.models.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyStatus,
    CompanyStats,
    CompanyListResponse,
    CompanySettings,
    CompanyBilling,
    SetupStatus,
    SetupConfiguration,
    SetupInitRequest,
    SetupInitResponse,
    CompanyContact
)
from config.settings import settings

logger = logging.getLogger(__name__)


class CompanyService:
    """Service for managing company operations"""
    
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.database_name]
        self.collection = self.db.companies
        
        # Related collections
        self.brands_collection = self.db.brands
        self.agents_collection = self.db.ai_agents
        self.users_collection = self.db.users
        self.knowledge_collection = self.db.knowledge_base_items
        
    async def create_company(
        self,
        company_data: CompanyCreate,
        created_by: str = "system"
    ) -> CompanyResponse:
        """Create a new company"""
        try:
            # Check if company with same name or domain exists
            existing = await self.collection.find_one({
                "$or": [
                    {"name": company_data.name},
                    {"domain": company_data.domain} if company_data.domain else {"_id": None}
                ]
            })
            
            if existing:
                raise ValueError(f"Company with name '{company_data.name}' or domain already exists")
            
            # Prepare document for MongoDB
            # Convert Pydantic model to dict, ensuring HttpUrl becomes string
            company_dict = company_data.model_dump(exclude_unset=True, mode='json')
            
            doc = {
                "_id": str(ObjectId()),
                **company_dict,
                "status": CompanyStatus.ACTIVE,
                "billing": CompanyBilling().model_dump() if not hasattr(company_data, 'billing') else company_data.billing,
                "total_brands": 0,
                "total_agents": 0,
                "total_users": 0,
                "total_knowledge_items": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": created_by,
                "updated_by": created_by
            }
            
            # Insert into MongoDB
            await self.collection.insert_one(doc)
            
            logger.info(f"Created company: {company_data.name} with ID: {doc['_id']}")
            
            return CompanyResponse(**doc)
            
        except Exception as e:
            logger.error(f"Error creating company: {e}")
            raise
    
    async def get_company(self, company_id: str) -> Optional[CompanyResponse]:
        """Get a company by ID"""
        try:
            # Try with string ID first (for backward compatibility)
            company = await self.collection.find_one({"_id": company_id})
            
            # If not found and company_id is a valid ObjectId string, try with ObjectId
            if not company and ObjectId.is_valid(company_id):
                try:
                    company = await self.collection.find_one({"_id": ObjectId(company_id)})
                except:
                    pass
            
            if not company:
                return None
            
            # Get the company ID as string for consistency in related collections
            company_id_str = str(company["_id"]) if isinstance(company["_id"], ObjectId) else company["_id"]
            
            # Get statistics
            company["total_brands"] = await self.brands_collection.count_documents(
                {"company_id": company_id_str}
            )
            company["total_agents"] = await self.agents_collection.count_documents(
                {"company_id": company_id_str}
            )
            company["total_users"] = await self.users_collection.count_documents(
                {"company_id": company_id_str}
            )
            company["total_knowledge_items"] = await self.knowledge_collection.count_documents(
                {"company_id": company_id_str}
            )
            
            # Set default values for missing fields
            if "settings" not in company:
                company["settings"] = {
                    "ai_enabled": True,
                    "default_language": "en",
                    "timezone": "UTC",
                    "allowed_llm_providers": ["openai", "anthropic", "azure_openai", "aws_bedrock", "google"]
                }
            
            if "plan" not in company:
                company["plan"] = "STARTER"
            
            # Convert ObjectId to string for response
            if isinstance(company.get("_id"), ObjectId):
                company["_id"] = str(company["_id"])
            
            return CompanyResponse(**company)
            
        except InvalidId:
            logger.error(f"Invalid company ID: {company_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting company: {e}")
            raise
    
    async def update_company(
        self,
        company_id: str,
        company_data: CompanyUpdate,
        updated_by: str = "system"
    ) -> Optional[CompanyResponse]:
        """Update a company"""
        try:
            # Check if company exists (try both string and ObjectId)
            existing = await self.collection.find_one({"_id": company_id})
            if not existing and ObjectId.is_valid(company_id):
                try:
                    existing = await self.collection.find_one({"_id": ObjectId(company_id)})
                except:
                    pass
            
            if not existing:
                return None
            
            # Prepare update document
            update_doc = {
                k: v for k, v in company_data.model_dump(exclude_unset=True).items()
                if v is not None
            }
            
            if update_doc:
                update_doc["updated_at"] = datetime.utcnow()
                update_doc["updated_by"] = updated_by
                
                # Update in MongoDB (use the same ID type as existing)
                await self.collection.update_one(
                    {"_id": existing["_id"]},
                    {"$set": update_doc}
                )
            
            # Return updated company
            return await self.get_company(company_id)
            
        except Exception as e:
            logger.error(f"Error updating company: {e}")
            raise
    
    async def delete_company(self, company_id: str) -> bool:
        """Delete a company (soft delete by setting status to archived)"""
        try:
            # Find the company first to get the actual ID type
            company = await self.collection.find_one({"_id": company_id})
            if not company and ObjectId.is_valid(company_id):
                try:
                    company = await self.collection.find_one({"_id": ObjectId(company_id)})
                except:
                    pass
            
            if not company:
                logger.warning(f"Company not found for deletion: {company_id}")
                return False
            
            actual_id = company["_id"]
            
            # Check for existing relationships
            brands_count = await self.brands_collection.count_documents({"company_id": str(actual_id) if isinstance(actual_id, ObjectId) else actual_id})
            
            if brands_count > 0:
                # Soft delete - just mark as archived
                result = await self.collection.update_one(
                    {"_id": actual_id},
                    {
                        "$set": {
                            "status": CompanyStatus.EXPIRED,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                return result.modified_count > 0
            else:
                # Hard delete if no relationships
                result = await self.collection.delete_one({"_id": actual_id})
                return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting company: {e}")
            raise
    
    async def list_companies(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[CompanyStatus] = None,
        search: Optional[str] = None
    ) -> CompanyListResponse:
        """List companies with pagination and filtering"""
        try:
            # Build query
            query = {}
            
            if status:
                query["status"] = status
            
            if search:
                query["$or"] = [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"domain": {"$regex": search, "$options": "i"}},
                    {"description": {"$regex": search, "$options": "i"}}
                ]
            
            # Get total count
            total = await self.collection.count_documents(query)
            
            # Calculate pagination
            skip = (page - 1) * page_size
            total_pages = (total + page_size - 1) // page_size
            
            # Get companies
            cursor = self.collection.find(query).skip(skip).limit(page_size).sort("created_at", -1)
            
            companies = []
            async for doc in cursor:
                # Get the company ID as string for consistency in related collections
                company_id_str = str(doc["_id"]) if isinstance(doc["_id"], ObjectId) else doc["_id"]
                
                # Get statistics for each company
                doc["total_brands"] = await self.brands_collection.count_documents(
                    {"company_id": company_id_str}
                )
                doc["total_agents"] = await self.agents_collection.count_documents(
                    {"company_id": company_id_str}
                )
                doc["total_users"] = await self.users_collection.count_documents(
                    {"company_id": company_id_str}
                )
                doc["total_knowledge_items"] = await self.knowledge_collection.count_documents(
                    {"company_id": company_id_str}
                )
                
                # Set default values for missing fields
                if "settings" not in doc:
                    doc["settings"] = {
                        "ai_enabled": True,
                        "default_language": "en",
                        "timezone": "UTC",
                        "allowed_llm_providers": ["openai", "anthropic", "azure_openai", "aws_bedrock", "google"]
                    }
                
                if "plan" not in doc:
                    doc["plan"] = "STARTER"
                
                # Convert ObjectId to string for response
                if isinstance(doc.get("_id"), ObjectId):
                    doc["_id"] = str(doc["_id"])
                
                companies.append(CompanyResponse(**doc))
            
            return CompanyListResponse(
                companies=companies,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Error listing companies: {e}")
            raise
    
    async def get_company_stats(
        self,
        company_id: str,
        period: str = "monthly"
    ) -> Optional[CompanyStats]:
        """Get company usage statistics"""
        try:
            company = await self.get_company(company_id)
            if not company:
                return None
            
            # Aggregate statistics from various collections
            # This is a simplified version - you'd want more complex aggregation in production
            
            stats = CompanyStats(
                company_id=company_id,
                period=period,
                brands_count=company.total_brands,
                agents_count=company.total_agents,
                users_count=company.total_users,
                knowledge_items_count=company.total_knowledge_items,
                calculated_at=datetime.utcnow()
            )
            
            # Get message statistics (would need message collection)
            # stats.total_messages_processed = await self.get_message_count(company_id, period)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting company stats: {e}")
            raise
    
    async def check_company_limits(
        self,
        company_id: str,
        resource_type: str
    ) -> Dict[str, Any]:
        """Check if company has reached resource limits"""
        try:
            company = await self.get_company(company_id)
            if not company:
                return {"allowed": False, "reason": "Company not found"}
            
            if company.status != CompanyStatus.ACTIVE:
                return {"allowed": False, "reason": f"Company status is {company.status}"}
            
            # Check specific resource limits
            if resource_type == "brands":
                if company.total_brands >= company.settings.max_brands:
                    return {
                        "allowed": False,
                        "reason": f"Brand limit reached ({company.settings.max_brands})"
                    }
            
            elif resource_type == "agents":
                if company.total_agents >= company.settings.max_agents:
                    return {
                        "allowed": False,
                        "reason": f"Agent limit reached ({company.settings.max_agents})"
                    }
            
            elif resource_type == "users":
                if company.total_users >= company.settings.max_users:
                    return {
                        "allowed": False,
                        "reason": f"User limit reached ({company.settings.max_users})"
                    }
            
            elif resource_type == "knowledge_items":
                if company.total_knowledge_items >= company.settings.max_knowledge_base_items:
                    return {
                        "allowed": False,
                        "reason": f"Knowledge base limit reached ({company.settings.max_knowledge_base_items})"
                    }
            
            return {"allowed": True, "reason": "Within limits"}
            
        except Exception as e:
            logger.error(f"Error checking company limits: {e}")
            return {"allowed": False, "reason": str(e)}
    
    async def get_companies_by_status(
        self,
        status: CompanyStatus
    ) -> List[CompanyResponse]:
        """Get all companies with a specific status"""
        try:
            cursor = self.collection.find({"status": status})
            companies = []

            async for doc in cursor:
                # Convert ObjectId to string for response
                if isinstance(doc.get("_id"), ObjectId):
                    doc["_id"] = str(doc["_id"])
                companies.append(CompanyResponse(**doc))

            return companies

        except Exception as e:
            logger.error(f"Error getting companies by status: {e}")
            raise

    async def initialize_setup(
        self,
        request: SetupInitRequest
    ) -> SetupInitResponse:
        """Initialize or check setup status for a company"""
        try:
            # Check if company already exists by name or domain
            query = {"name": request.company_name}
            if request.company_domain:
                query = {
                    "$or": [
                        {"name": request.company_name},
                        {"domain": request.company_domain}
                    ]
                }

            existing_company = await self.collection.find_one(query)

            if existing_company:
                # Company exists - return setup status
                company_id_str = str(existing_company["_id"]) if isinstance(existing_company["_id"], ObjectId) else existing_company["_id"]

                # Get setup status
                setup_status = existing_company.get("setup_status", {})
                is_complete = setup_status.get("is_setup_complete", False)
                setup_step = setup_status.get("setup_step", 0)

                return SetupInitResponse(
                    company_id=company_id_str,
                    company_name=existing_company["name"],
                    user_name=request.user_name,
                    user_email=request.user_email,
                    is_setup_complete=is_complete,
                    setup_step=setup_step,
                    should_show_setup=not is_complete
                )

            else:
                # Create new company record
                company_id = str(ObjectId())

                doc = {
                    "_id": company_id,
                    "name": request.company_name,
                    "domain": request.company_domain,
                    "contact": {
                        "primary_email": request.user_email,
                        "technical_contact_name": request.user_name,
                        "technical_contact_email": request.user_email
                    },
                    "settings": CompanySettings().model_dump(),
                    "status": CompanyStatus.TRIAL,
                    "plan": "STARTER",
                    "setup_status": {
                        "is_setup_complete": False,
                        "setup_started_at": datetime.utcnow(),
                        "setup_completed_at": None,
                        "setup_step": 0,
                        "configuration": SetupConfiguration().model_dump()
                    },
                    "total_brands": 0,
                    "total_agents": 0,
                    "total_users": 0,
                    "total_knowledge_items": 0,
                    "metadata": {
                        "user_id": request.user_id,
                        "khoros_tenant_id": request.khoros_tenant_id
                    },
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "created_by": request.user_id or "system"
                }

                await self.collection.insert_one(doc)

                logger.info(f"Created new company for setup: {request.company_name} with ID: {company_id}")

                return SetupInitResponse(
                    company_id=company_id,
                    company_name=request.company_name,
                    user_name=request.user_name,
                    user_email=request.user_email,
                    is_setup_complete=False,
                    setup_step=0,
                    should_show_setup=True
                )

        except Exception as e:
            logger.error(f"Error initializing setup: {e}")
            raise

    async def update_setup(
        self,
        company_id: str,
        setup_step: int,
        configuration: SetupConfiguration
    ) -> bool:
        """Update setup configuration and progress"""
        try:
            # Find company
            company = await self.collection.find_one({"_id": company_id})
            if not company and ObjectId.is_valid(company_id):
                company = await self.collection.find_one({"_id": ObjectId(company_id)})

            if not company:
                logger.warning(f"Company not found for setup update: {company_id}")
                return False

            actual_id = company["_id"]

            # Update setup status
            update_doc = {
                "setup_status.setup_step": setup_step,
                "setup_status.configuration": configuration.model_dump(),
                "updated_at": datetime.utcnow()
            }

            result = await self.collection.update_one(
                {"_id": actual_id},
                {"$set": update_doc}
            )

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Error updating setup: {e}")
            raise

    async def complete_setup(
        self,
        company_id: str,
        configuration: SetupConfiguration
    ) -> Optional[CompanyResponse]:
        """Mark setup as complete and apply final configuration"""
        try:
            # Find company
            company = await self.collection.find_one({"_id": company_id})
            if not company and ObjectId.is_valid(company_id):
                company = await self.collection.find_one({"_id": ObjectId(company_id)})

            if not company:
                logger.warning(f"Company not found for setup completion: {company_id}")
                return None

            actual_id = company["_id"]

            # Mark setup as complete
            update_doc = {
                "setup_status.is_setup_complete": True,
                "setup_status.setup_completed_at": datetime.utcnow(),
                "setup_status.setup_step": 7,
                "setup_status.configuration": configuration.model_dump(),
                "status": CompanyStatus.ACTIVE,  # Activate company
                "updated_at": datetime.utcnow()
            }

            # Update subscription plan if provided
            if configuration.subscription_plan:
                update_doc["plan"] = configuration.subscription_plan

            await self.collection.update_one(
                {"_id": actual_id},
                {"$set": update_doc}
            )

            logger.info(f"Completed setup for company: {company_id}")

            # Return updated company
            return await self.get_company(company_id)

        except Exception as e:
            logger.error(f"Error completing setup: {e}")
            raise


# Create singleton instance
company_service = CompanyService()