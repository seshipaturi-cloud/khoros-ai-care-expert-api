"""
AI Agent models for MongoDB
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


class AIAgentCreate(BaseModel):
    """Model for creating a new AI agent"""
    company_id: Optional[str] = Field(None, description="Parent company ID - will be set from user if not provided")
    brand_id: str = Field(..., description="Single brand ID (one-to-one relationship)")
    name: str
    description: str
    llm_provider_id: str = Field(..., description="LLM provider configuration ID (required)")
    llm_model: str  # e.g., "gpt-4", "claude-3-5-sonnet-20241022"
    system_message: str
    user_message_template: Optional[str] = None
    response_length: int = Field(default=200, ge=50, le=2000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1000, ge=100, le=4000)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    active: bool = True
    skills: Optional[List[str]] = []
    knowledge_base_access: bool = True
    team_ids: Optional[List[str]] = Field(default_factory=list, description="Assigned team IDs")
    metadata: Optional[Dict[str, Any]] = {}


class AIAgentUpdate(BaseModel):
    """Model for updating an AI agent"""
    name: Optional[str] = None
    description: Optional[str] = None
    llm_provider_id: Optional[str] = None
    llm_model: Optional[str] = None
    system_message: Optional[str] = None
    user_message_template: Optional[str] = None
    response_length: Optional[int] = Field(None, ge=50, le=2000)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(None, ge=100, le=4000)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    active: Optional[bool] = None
    skills: Optional[List[str]] = None
    knowledge_base_access: Optional[bool] = None
    team_ids: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class AIAgentResponse(BaseModel):
    """Response model for AI agent"""
    id: str = Field(alias="_id")
    company_id: Optional[str] = None  # Optional for backward compatibility
    company_name: Optional[str] = None  # Populated from lookup
    brand_id: Optional[str] = None  # Optional for backward compatibility
    brand_ids: Optional[List[str]] = []  # Legacy field for backward compatibility
    brand_name: Optional[str] = None  # Populated from brand lookup (singular)
    brand_names: Optional[List[str]] = []  # Legacy field for backward compatibility (plural)
    name: str
    description: str
    llm_provider_id: Optional[str] = None  # Optional for backward compatibility
    llm_provider_name: Optional[str] = None  # Populated from provider lookup
    llm_model: Optional[str] = None
    system_message: Optional[str] = None
    user_message_template: Optional[str] = None
    response_length: Optional[int] = 200
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    max_tokens: Optional[int] = 1000
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    active: bool
    skills: List[str] = []
    knowledge_base_access: bool = True
    team_ids: List[str] = []
    team_names: Optional[List[str]] = []  # Populated from team lookup
    metadata: Dict[str, Any] = {}
    
    # Statistics
    last_used: Optional[datetime] = None
    total_responses: int = 0
    success_rate: float = 0.0
    avg_response_time: Optional[float] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AIAgentListResponse(BaseModel):
    """Response model for listing AI agents"""
    agents: List[AIAgentResponse]
    total: int
    page: int = 1
    page_size: int = 10


class AIAgentStats(BaseModel):
    """Statistics for an AI agent"""
    agent_id: str
    total_conversations: int
    total_messages: int
    avg_conversation_length: float
    avg_response_time: float
    success_rate: float
    user_satisfaction: Optional[float] = None
    last_7_days_usage: List[Dict[str, Any]] = []
    top_intents: List[Dict[str, Any]] = []
    error_rate: float = 0.0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }