"""
AI Agent Service for MongoDB operations
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.models.ai_agent import (
    AIAgentCreate,
    AIAgentUpdate,
    AIAgentResponse,
    AIAgentStats,
    LLMProvider
)
from config.settings import settings

logger = logging.getLogger(__name__)


class AIAgentService:
    """Service for managing AI agents in MongoDB"""
    
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.database_name]
        self.collection = self.db.ai_agents
        self.brands_collection = self.db.brands
        
    async def create_agent(
        self,
        agent_data: AIAgentCreate,
        user_id: str
    ) -> AIAgentResponse:
        """Create a new AI agent"""
        try:
            # Prepare document for insertion
            document = {
                **agent_data.dict(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": user_id,
                "updated_by": user_id,
                "last_used": None,
                "total_responses": 0,
                "success_rate": 0.0,
                "avg_response_time": None
            }
            
            # Insert into MongoDB
            result = await self.collection.insert_one(document)
            
            # Fetch the created document
            created_agent = await self.collection.find_one({"_id": result.inserted_id})
            
            # Get brand names - handle both brand_id (singular) and brand_ids (plural)
            if "brand_id" in created_agent and created_agent["brand_id"]:
                brand_names = await self._get_brand_names([created_agent["brand_id"]])
                created_agent["brand_name"] = brand_names[0] if brand_names else None
            elif "brand_ids" in created_agent:
                brand_names = await self._get_brand_names(created_agent.get("brand_ids", []))
                created_agent["brand_names"] = brand_names
            
            # Convert _id to string for response
            created_agent["_id"] = str(created_agent["_id"])
            
            logger.info(f"Created AI agent: {created_agent['name']} with ID: {created_agent['_id']}")
            
            return AIAgentResponse(**created_agent)
            
        except Exception as e:
            logger.error(f"Error creating AI agent: {e}")
            raise
    
    async def get_agent(self, agent_id: str) -> Optional[AIAgentResponse]:
        """Get an AI agent by ID"""
        try:
            # Validate ObjectId
            if not ObjectId.is_valid(agent_id):
                return None
            
            agent = await self.collection.find_one({"_id": ObjectId(agent_id)})
            
            if not agent:
                return None
            
            # Get brand names - handle both brand_id (singular) and brand_ids (plural)
            if "brand_id" in agent and agent["brand_id"]:
                brand_names = await self._get_brand_names([agent["brand_id"]])
                agent["brand_name"] = brand_names[0] if brand_names else None
            elif "brand_ids" in agent:
                brand_names = await self._get_brand_names(agent.get("brand_ids", []))
                agent["brand_names"] = brand_names
            
            # Convert _id to string
            agent["_id"] = str(agent["_id"])
            
            return AIAgentResponse(**agent)
            
        except Exception as e:
            logger.error(f"Error getting AI agent {agent_id}: {e}")
            raise
    
    async def list_agents(
        self,
        company_id: Optional[str] = None,
        brand_id: Optional[str] = None,
        active_only: bool = False,
        skip: int = 0,
        limit: int = 10
    ) -> Dict[str, Any]:
        """List AI agents with optional filtering"""
        try:
            # Build query
            query = {}
            if company_id:
                query["company_id"] = company_id
            if brand_id:
                query["brand_id"] = brand_id
            if active_only:
                query["active"] = True
            
            # Get total count
            total = await self.collection.count_documents(query)
            
            # Fetch agents with pagination
            cursor = self.collection.find(query).skip(skip).limit(limit)
            agents = []
            
            async for agent in cursor:
                # Get brand names - handle both brand_id (singular) and brand_ids (plural)
                if "brand_id" in agent and agent["brand_id"]:
                    brand_names = await self._get_brand_names([agent["brand_id"]])
                    agent["brand_name"] = brand_names[0] if brand_names else None
                elif "brand_ids" in agent:
                    brand_names = await self._get_brand_names(agent.get("brand_ids", []))
                    agent["brand_names"] = brand_names
                
                # Convert _id to string
                agent["_id"] = str(agent["_id"])
                agents.append(AIAgentResponse(**agent))
            
            return {
                "agents": agents,
                "total": total,
                "page": (skip // limit) + 1,
                "page_size": limit
            }
            
        except Exception as e:
            logger.error(f"Error listing AI agents: {e}")
            raise
    
    async def update_agent(
        self,
        agent_id: str,
        agent_data: AIAgentUpdate,
        user_id: str
    ) -> Optional[AIAgentResponse]:
        """Update an AI agent"""
        try:
            # Validate ObjectId
            if not ObjectId.is_valid(agent_id):
                return None
            
            # Prepare update data
            update_data = {
                k: v for k, v in agent_data.dict().items() 
                if v is not None
            }
            
            if not update_data:
                # No updates provided
                return await self.get_agent(agent_id)
            
            update_data["updated_at"] = datetime.utcnow()
            update_data["updated_by"] = user_id
            
            # Update the document
            result = await self.collection.update_one(
                {"_id": ObjectId(agent_id)},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                return None
            
            # Fetch updated agent
            return await self.get_agent(agent_id)
            
        except Exception as e:
            logger.error(f"Error updating AI agent {agent_id}: {e}")
            raise
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an AI agent"""
        try:
            # Validate ObjectId
            if not ObjectId.is_valid(agent_id):
                return False
            
            result = await self.collection.delete_one({"_id": ObjectId(agent_id)})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted AI agent: {agent_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting AI agent {agent_id}: {e}")
            raise
    
    async def toggle_agent_status(self, agent_id: str, active: bool) -> Optional[AIAgentResponse]:
        """Toggle the active status of an AI agent"""
        try:
            # Validate ObjectId
            if not ObjectId.is_valid(agent_id):
                return None
            
            result = await self.collection.update_one(
                {"_id": ObjectId(agent_id)},
                {
                    "$set": {
                        "active": active,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.matched_count == 0:
                return None
            
            return await self.get_agent(agent_id)
            
        except Exception as e:
            logger.error(f"Error toggling AI agent status {agent_id}: {e}")
            raise
    
    async def update_agent_stats(
        self,
        agent_id: str,
        response_time: float,
        success: bool
    ):
        """Update agent statistics after a response"""
        try:
            # Validate ObjectId
            if not ObjectId.is_valid(agent_id):
                return
            
            # Get current stats
            agent = await self.collection.find_one(
                {"_id": ObjectId(agent_id)},
                {"total_responses": 1, "success_rate": 1, "avg_response_time": 1}
            )
            
            if not agent:
                return
            
            # Calculate new stats
            total_responses = agent.get("total_responses", 0) + 1
            current_success_rate = agent.get("success_rate", 0.0)
            current_avg_time = agent.get("avg_response_time", response_time)
            
            # Update success rate
            if success:
                new_success_rate = ((current_success_rate * (total_responses - 1)) + 100) / total_responses
            else:
                new_success_rate = (current_success_rate * (total_responses - 1)) / total_responses
            
            # Update average response time
            new_avg_time = ((current_avg_time * (total_responses - 1)) + response_time) / total_responses
            
            # Update in database
            await self.collection.update_one(
                {"_id": ObjectId(agent_id)},
                {
                    "$set": {
                        "total_responses": total_responses,
                        "success_rate": new_success_rate,
                        "avg_response_time": new_avg_time,
                        "last_used": datetime.utcnow()
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating AI agent stats {agent_id}: {e}")
    
    async def get_agent_stats(self, agent_id: str) -> Optional[AIAgentStats]:
        """Get detailed statistics for an AI agent"""
        try:
            # Validate ObjectId
            if not ObjectId.is_valid(agent_id):
                return None
            
            agent = await self.collection.find_one({"_id": ObjectId(agent_id)})
            
            if not agent:
                return None
            
            # TODO: Implement detailed stats from conversation/message collections
            # For now, return basic stats
            stats = AIAgentStats(
                agent_id=str(agent["_id"]),
                total_conversations=0,  # TODO: Query from conversations collection
                total_messages=agent.get("total_responses", 0),
                avg_conversation_length=0.0,  # TODO: Calculate from conversations
                avg_response_time=agent.get("avg_response_time", 0.0),
                success_rate=agent.get("success_rate", 0.0),
                user_satisfaction=None,  # TODO: Implement satisfaction tracking
                last_7_days_usage=[],  # TODO: Aggregate from logs
                top_intents=[],  # TODO: Analyze from conversations
                error_rate=100.0 - agent.get("success_rate", 0.0)
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting AI agent stats {agent_id}: {e}")
            raise
    
    async def _get_brand_names(self, brand_ids: List[str]) -> List[str]:
        """Get brand names from brand IDs"""
        try:
            if not brand_ids:
                return []
            
            # Convert to ObjectIds
            object_ids = [ObjectId(bid) for bid in brand_ids if ObjectId.is_valid(bid)]
            
            if not object_ids:
                return []
            
            # Fetch brand names
            cursor = self.brands_collection.find(
                {"_id": {"$in": object_ids}},
                {"name": 1}
            )
            
            brand_names = []
            async for brand in cursor:
                brand_names.append(brand.get("name", "Unknown"))
            
            return brand_names
            
        except Exception as e:
            logger.error(f"Error getting brand names: {e}")
            return []


# Create singleton instance
ai_agent_service = AIAgentService()