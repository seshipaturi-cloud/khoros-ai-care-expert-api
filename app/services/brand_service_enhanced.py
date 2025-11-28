"""
Enhanced Brand Service with 1:1 AI Agent Relationship
According to architecture: One AI Agent per Brand
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
    BrandListResponse,
    BrandVoiceSettings,
    BrandAISettings,
    BrandSocialSettings
)
from app.models.ai_agent import AIAgentCreate
from app.services.company_service import company_service
from config.settings import settings

logger = logging.getLogger(__name__)


class EnhancedBrandService:
    """Enhanced service for managing brands with automatic AI agent creation"""
    
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.database_name]
        self.collection = self.db.brands
        
        # Related collections
        self.companies_collection = self.db.companies
        self.agents_collection = self.db.ai_agents
        self.knowledge_collection = self.db.knowledge_base_items
        self.messages_collection = self.db.messages
        self.queues_collection = self.db.queues
        self.llm_providers_collection = self.db.llm_providers
    
    async def create_brand(
        self,
        brand_data: BrandCreate,
        created_by: str = "system"
    ) -> BrandResponse:
        """
        Create a new brand with automatic AI agent creation
        Maintains 1:1 relationship between brand and AI agent
        """
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
            
            # Get company for additional info
            company = await self.companies_collection.find_one({"_id": brand_data.company_id})
            if not company:
                raise ValueError(f"Company {brand_data.company_id} not found")
            
            # Generate brand ID
            brand_id = str(ObjectId())
            
            # Prepare brand document
            brand_doc = {
                "_id": brand_id,
                "company_id": brand_data.company_id,
                "name": brand_data.name,
                "code": brand_data.code,
                "description": brand_data.description or f"Brand for {brand_data.name}",
                "industry": brand_data.industry or company.get("industry", "General"),
                "website": brand_data.website,
                "logo_url": brand_data.logo_url,
                
                # Voice settings with defaults
                "voice_settings": brand_data.voice_settings.model_dump() if brand_data.voice_settings else {
                    "tone": "professional",
                    "personality_traits": ["helpful", "knowledgeable", "patient"],
                    "language": {
                        "primary": "en",
                        "supported": ["en"]
                    },
                    "guidelines": {
                        "greeting": "Hello! How can I assist you today?",
                        "closing": "Thank you for contacting us!",
                        "do_not_use": [],
                        "preferred_phrases": ["I'd be happy to help", "Let me assist you"]
                    }
                },
                
                # AI settings with defaults
                "ai_settings": brand_data.ai_settings.model_dump() if brand_data.ai_settings else {
                    "enabled": True,
                    "llm_provider": "openai",
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7,
                    "max_tokens": 500,
                    "knowledge_base_enabled": True,
                    "auto_suggest": True,
                    "sentiment_analysis": True
                },
                
                # Social settings
                "social_settings": brand_data.social_settings.model_dump() if brand_data.social_settings else {
                    "platforms_enabled": [],
                    "auto_publish": False,
                    "moderation_enabled": True,
                    "response_time_sla_minutes": 15
                },
                
                # Queue configuration
                "queue_config": {
                    "auto_assignment": True,
                    "priority_rules": {
                        "vip_customers": "high",
                        "complaints": "urgent",
                        "general": "normal"
                    },
                    "sla_settings": {
                        "first_response_minutes": 5,
                        "resolution_hours": 24
                    }
                },
                
                # Statistics
                "stats": {
                    "total_conversations": 0,
                    "avg_response_time_minutes": 0,
                    "satisfaction_score": 0,
                    "resolution_rate": 0,
                    "active_conversations": 0
                },
                
                "status": BrandStatus.ACTIVE,
                "ai_agent_id": None,  # Will be set after agent creation
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": created_by,
                "updated_by": created_by
            }
            
            # Insert brand into MongoDB
            await self.collection.insert_one(brand_doc)
            logger.info(f"Created brand: {brand_data.name} with ID: {brand_id}")
            
            # Create AI Agent for the brand (1:1 relationship)
            agent_id = await self._create_ai_agent_for_brand(
                brand_id=brand_id,
                brand_name=brand_data.name,
                company_id=brand_data.company_id,
                ai_settings=brand_doc["ai_settings"],
                voice_settings=brand_doc["voice_settings"],
                created_by=created_by
            )
            
            # Update brand with AI agent reference
            await self.collection.update_one(
                {"_id": brand_id},
                {"$set": {"ai_agent_id": agent_id}}
            )
            brand_doc["ai_agent_id"] = agent_id
            
            # Create default queue for the brand
            await self._create_default_queue_for_brand(
                brand_id=brand_id,
                brand_name=brand_data.name,
                queue_config=brand_doc["queue_config"],
                created_by=created_by
            )
            
            # Add company name for response
            brand_doc["company_name"] = company["name"]
            
            return BrandResponse(**brand_doc)
            
        except Exception as e:
            logger.error(f"Error creating brand: {e}")
            # Cleanup if brand was created but agent creation failed
            if 'brand_id' in locals():
                await self.collection.delete_one({"_id": brand_id})
            raise
    
    async def _create_ai_agent_for_brand(
        self,
        brand_id: str,
        brand_name: str,
        company_id: str,
        ai_settings: dict,
        voice_settings: dict,
        created_by: str
    ) -> str:
        """
        Create AI agent for brand (1:1 relationship)
        Each brand gets exactly one AI agent
        """
        try:
            # Get default LLM provider for company
            default_provider = await self.llm_providers_collection.find_one({
                "company_id": company_id,
                "is_default": True,
                "status": "active"
            })
            
            if not default_provider:
                # Get any active provider
                default_provider = await self.llm_providers_collection.find_one({
                    "company_id": company_id,
                    "status": "active"
                })
            
            # Generate system message based on brand voice
            system_message = self._generate_system_message(brand_name, voice_settings)
            
            # Create AI agent document
            agent_doc = {
                "_id": str(ObjectId()),
                "company_id": company_id,
                "brand_id": brand_id,  # 1:1 relationship
                "name": f"{brand_name} AI Assistant",
                "description": f"AI-powered assistant for {brand_name}",
                
                # LLM Configuration
                "llm_provider_id": default_provider["_id"] if default_provider else None,
                "llm_model": ai_settings.get("model", "gpt-3.5-turbo"),
                "llm_config": {
                    "temperature": ai_settings.get("temperature", 0.7),
                    "max_tokens": ai_settings.get("max_tokens", 500),
                    "top_p": 0.9,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0
                },
                
                # Prompting
                "system_message": system_message,
                "prompt_template": """Customer: {customer_name}
Issue: {issue}
Context: {knowledge}
Brand Voice: {voice_guidelines}

Please provide a helpful response following the brand guidelines.""",
                
                # Knowledge access
                "knowledge_access": {
                    "enabled": ai_settings.get("knowledge_base_enabled", True),
                    "accessible_kb_ids": [],  # Will be populated as KB items are added
                    "retrieval_limit": 5,
                    "min_similarity_score": 0.7
                },
                
                # Capabilities
                "capabilities": {
                    "auto_respond": ai_settings.get("auto_suggest", True),
                    "sentiment_analysis": ai_settings.get("sentiment_analysis", True),
                    "intent_classification": True,
                    "language_detection": True,
                    "pii_detection": True,
                    "profanity_filter": True
                },
                
                # Skills
                "skills": [
                    "answer_questions",
                    "provide_information",
                    "troubleshooting",
                    "escalation_handling"
                ],
                
                # Performance metrics
                "performance": {
                    "total_messages_processed": 0,
                    "avg_response_time_ms": 0,
                    "avg_confidence_score": 0,
                    "escalation_rate": 0,
                    "satisfaction_score": 0
                },
                
                "status": "active",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": created_by,
                "updated_by": created_by
            }
            
            # Insert AI agent
            await self.agents_collection.insert_one(agent_doc)
            logger.info(f"Created AI agent for brand {brand_name} with ID: {agent_doc['_id']}")
            
            return agent_doc["_id"]
            
        except Exception as e:
            logger.error(f"Error creating AI agent for brand: {e}")
            raise
    
    async def _create_default_queue_for_brand(
        self,
        brand_id: str,
        brand_name: str,
        queue_config: dict,
        created_by: str
    ) -> str:
        """Create default queue for brand"""
        try:
            queue_doc = {
                "_id": str(ObjectId()),
                "brand_id": brand_id,
                "name": f"{brand_name} Support Queue",
                "queue_type": "skill_based",
                "routing_rules": [
                    {
                        "condition": "sentiment.score < -0.5",
                        "action": "assign",
                        "priority": "high"
                    },
                    {
                        "condition": "customer.is_vip == true",
                        "action": "assign",
                        "priority": "urgent"
                    },
                    {
                        "condition": "default",
                        "action": "assign",
                        "priority": "normal"
                    }
                ],
                "sla_config": queue_config.get("sla_settings", {
                    "first_response_minutes": 5,
                    "resolution_hours": 24
                }),
                "capacity": {
                    "max_queue_size": 100,
                    "current_size": 0,
                    "avg_wait_time_seconds": 0
                },
                "status": "active",
                "created_at": datetime.utcnow(),
                "created_by": created_by
            }
            
            await self.queues_collection.insert_one(queue_doc)
            logger.info(f"Created default queue for brand {brand_name}")
            
            # Update brand with default queue
            await self.collection.update_one(
                {"_id": brand_id},
                {"$set": {"queue_config.default_queue_id": queue_doc["_id"]}}
            )
            
            return queue_doc["_id"]
            
        except Exception as e:
            logger.error(f"Error creating default queue: {e}")
            raise
    
    def _generate_system_message(self, brand_name: str, voice_settings: dict) -> str:
        """Generate system message for AI agent based on brand voice"""
        tone = voice_settings.get("tone", "professional")
        traits = voice_settings.get("personality_traits", ["helpful"])
        guidelines = voice_settings.get("guidelines", {})
        
        traits_text = ", ".join(traits)
        
        system_message = f"""You are a customer service representative for {brand_name}.

Your communication style should be {tone} and you should embody these traits: {traits_text}.

Guidelines:
- Greeting: {guidelines.get('greeting', 'Hello! How can I help you today?')}
- Closing: {guidelines.get('closing', 'Thank you for contacting us!')}
- Preferred phrases: {', '.join(guidelines.get('preferred_phrases', []))}
- Avoid using: {', '.join(guidelines.get('do_not_use', []))}

Always:
1. Be helpful and empathetic
2. Provide accurate information
3. Follow brand voice guidelines
4. Escalate when uncertain
5. Protect customer privacy"""
        
        return system_message
    
    async def get_brand(self, brand_id: str) -> Optional[BrandResponse]:
        """Get a brand by ID with all related information"""
        try:
            brand = await self.collection.find_one({"_id": brand_id})
            
            if not brand:
                return None
            
            # Get company name
            company = await self.companies_collection.find_one({"_id": brand["company_id"]})
            brand["company_name"] = company["name"] if company else None
            
            # Get AI agent info (1:1 relationship)
            if brand.get("ai_agent_id"):
                agent = await self.agents_collection.find_one({"_id": brand["ai_agent_id"]})
                brand["ai_agent_name"] = agent["name"] if agent else None
                brand["ai_agent_status"] = agent["status"] if agent else None
            
            # Get statistics
            brand["total_messages"] = await self.messages_collection.count_documents(
                {"brand_id": brand_id}
            )
            brand["total_knowledge_items"] = await self.knowledge_collection.count_documents({
                "company_id": brand["company_id"],
                "ai_agent_ids": brand.get("ai_agent_id")
            })
            brand["active_queues"] = await self.queues_collection.count_documents({
                "brand_id": brand_id,
                "status": "active"
            })
            
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
        """Update a brand and its associated AI agent"""
        try:
            # Check if brand exists
            existing = await self.collection.find_one({"_id": brand_id})
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
            update_doc = {}
            
            # Update basic fields
            for field in ["name", "code", "description", "industry", "website", "logo_url", "status"]:
                if hasattr(brand_data, field) and getattr(brand_data, field) is not None:
                    update_doc[field] = getattr(brand_data, field)
            
            # Update nested objects
            if brand_data.voice_settings:
                update_doc["voice_settings"] = brand_data.voice_settings.model_dump()
                # Update AI agent system message if voice changed
                await self._update_agent_system_message(
                    existing.get("ai_agent_id"),
                    brand_data.name or existing["name"],
                    update_doc["voice_settings"]
                )
            
            if brand_data.ai_settings:
                update_doc["ai_settings"] = brand_data.ai_settings.model_dump()
                # Update AI agent configuration
                await self._update_agent_configuration(
                    existing.get("ai_agent_id"),
                    update_doc["ai_settings"]
                )
            
            if brand_data.social_settings:
                update_doc["social_settings"] = brand_data.social_settings.model_dump()
            
            if update_doc:
                update_doc["updated_at"] = datetime.utcnow()
                update_doc["updated_by"] = updated_by
                
                # Update in MongoDB
                await self.collection.update_one(
                    {"_id": brand_id},
                    {"$set": update_doc}
                )
            
            # Return updated brand
            return await self.get_brand(brand_id)
            
        except Exception as e:
            logger.error(f"Error updating brand: {e}")
            raise
    
    async def _update_agent_system_message(
        self,
        agent_id: str,
        brand_name: str,
        voice_settings: dict
    ):
        """Update AI agent system message when brand voice changes"""
        if not agent_id:
            return
        
        try:
            system_message = self._generate_system_message(brand_name, voice_settings)
            await self.agents_collection.update_one(
                {"_id": agent_id},
                {
                    "$set": {
                        "system_message": system_message,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error updating agent system message: {e}")
    
    async def _update_agent_configuration(
        self,
        agent_id: str,
        ai_settings: dict
    ):
        """Update AI agent configuration when AI settings change"""
        if not agent_id:
            return
        
        try:
            update_fields = {
                "llm_model": ai_settings.get("model"),
                "llm_config.temperature": ai_settings.get("temperature"),
                "llm_config.max_tokens": ai_settings.get("max_tokens"),
                "capabilities.auto_respond": ai_settings.get("auto_suggest"),
                "capabilities.sentiment_analysis": ai_settings.get("sentiment_analysis"),
                "knowledge_access.enabled": ai_settings.get("knowledge_base_enabled"),
                "updated_at": datetime.utcnow()
            }
            
            # Remove None values
            update_fields = {k: v for k, v in update_fields.items() if v is not None}
            
            if update_fields:
                await self.agents_collection.update_one(
                    {"_id": agent_id},
                    {"$set": update_fields}
                )
        except Exception as e:
            logger.error(f"Error updating agent configuration: {e}")
    
    async def delete_brand(self, brand_id: str) -> bool:
        """
        Delete a brand (soft delete)
        Note: AI agent is kept but marked as inactive (1:1 relationship)
        """
        try:
            brand = await self.collection.find_one({"_id": brand_id})
            if not brand:
                return False
            
            # Soft delete - mark as archived
            await self.collection.update_one(
                {"_id": brand_id},
                {
                    "$set": {
                        "status": BrandStatus.ARCHIVED,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Mark AI agent as inactive
            if brand.get("ai_agent_id"):
                await self.agents_collection.update_one(
                    {"_id": brand["ai_agent_id"]},
                    {
                        "$set": {
                            "status": "inactive",
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            
            # Mark queues as inactive
            await self.queues_collection.update_many(
                {"brand_id": brand_id},
                {
                    "$set": {
                        "status": "inactive",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Archived brand {brand_id} and related entities")
            return True
            
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
            
            # Get brands with related info
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
                    "$lookup": {
                        "from": "ai_agents",
                        "localField": "ai_agent_id",
                        "foreignField": "_id",
                        "as": "agent"
                    }
                },
                {
                    "$addFields": {
                        "company_name": {"$arrayElemAt": ["$company.name", 0]},
                        "ai_agent_name": {"$arrayElemAt": ["$agent.name", 0]},
                        "ai_agent_status": {"$arrayElemAt": ["$agent.status", 0]}
                    }
                },
                {"$project": {"company": 0, "agent": 0}}
            ]
            
            cursor = self.collection.aggregate(pipeline)
            
            brands = []
            async for doc in cursor:
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
            
            # Get message statistics
            total_messages = await self.messages_collection.count_documents({"brand_id": brand_id})
            
            # Get AI agent performance if exists
            agent_performance = {}
            if brand.ai_agent_id:
                agent = await self.agents_collection.find_one({"_id": brand.ai_agent_id})
                if agent:
                    agent_performance = agent.get("performance", {})
            
            stats = BrandStats(
                brand_id=brand_id,
                brand_name=brand.name,
                period=period,
                total_messages=total_messages,
                ai_agent_performance=agent_performance,
                active_queues=brand.active_queues or 0,
                total_knowledge_items=brand.total_knowledge_items or 0,
                calculated_at=datetime.utcnow()
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting brand stats: {e}")
            raise


# Create singleton instance
enhanced_brand_service = EnhancedBrandService()