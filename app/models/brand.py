"""
Brand Models for multi-brand management within companies
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class BrandStatus(str, Enum):
    """Brand status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class BrandVoiceSettings(BaseModel):
    """Brand voice and tone settings for AI interactions"""
    tone: str = Field(default="professional", description="Brand tone: professional, casual, friendly, formal")
    personality_traits: List[str] = Field(default_factory=list, description="Brand personality traits")
    language_style: str = Field(default="neutral", description="Language style: neutral, technical, simple, conversational")
    response_style: str = Field(default="helpful", description="Response style: helpful, concise, detailed, empathetic")
    greeting_template: Optional[str] = None
    closing_template: Optional[str] = None
    forbidden_phrases: List[str] = Field(default_factory=list)
    preferred_phrases: List[str] = Field(default_factory=list)
    custom_instructions: Optional[str] = None


class BrandAISettings(BaseModel):
    """Brand-specific AI configuration"""
    default_llm_provider: str = Field(default="openai")
    default_llm_model: str = Field(default="gpt-3.5-turbo")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_response_length: int = Field(default=500, ge=50, le=2000)
    enable_knowledge_base: bool = Field(default=True)
    enable_auto_response: bool = Field(default=False)
    response_time_sla_seconds: int = Field(default=60, ge=1, le=3600)
    escalation_threshold: int = Field(default=3, ge=1, le=10)
    sentiment_analysis_enabled: bool = Field(default=True)
    language_detection_enabled: bool = Field(default=True)


class BrandSocialSettings(BaseModel):
    """Brand social media settings"""
    platforms_enabled: List[str] = Field(default_factory=list)
    auto_publish: bool = Field(default=False)
    moderation_enabled: bool = Field(default=True)
    response_templates: Dict[str, str] = Field(default_factory=dict)
    hashtags: List[str] = Field(default_factory=list)
    mentions_monitoring: bool = Field(default=True)


class BrandCreate(BaseModel):
    """Schema for creating a new brand"""
    company_id: str = Field(..., description="Parent company ID")
    name: str = Field(..., min_length=2, max_length=100, description="Brand name")
    code: str = Field(..., min_length=2, max_length=20, description="Unique brand code")
    
    # Brand information
    industry: Optional[str] = None
    website: Optional[HttpUrl] = None
    logo_url: Optional[HttpUrl] = None
    primary_color: Optional[str] = Field(None, description="Primary brand color in hex")
    secondary_color: Optional[str] = Field(None, description="Secondary brand color in hex")
    
    # Settings
    voice_settings: Optional[BrandVoiceSettings] = Field(default_factory=BrandVoiceSettings)
    ai_settings: Optional[BrandAISettings] = Field(default_factory=BrandAISettings)
    social_settings: Optional[BrandSocialSettings] = Field(default_factory=BrandSocialSettings)
    
    # Contact information
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    timezone: str = Field(default="UTC")
    business_hours: Optional[Dict[str, str]] = None
    
    # Additional
    description: Optional[str] = Field(None, max_length=500)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BrandUpdate(BaseModel):
    """Schema for updating a brand"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    code: Optional[str] = Field(None, min_length=2, max_length=20)
    
    # Brand information
    industry: Optional[str] = None
    website: Optional[HttpUrl] = None
    logo_url: Optional[HttpUrl] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    
    # Settings
    voice_settings: Optional[BrandVoiceSettings] = None
    ai_settings: Optional[BrandAISettings] = None
    social_settings: Optional[BrandSocialSettings] = None
    status: Optional[BrandStatus] = None
    
    # Contact information
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    timezone: Optional[str] = None
    business_hours: Optional[Dict[str, str]] = None
    
    # Additional
    description: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = None


class BrandResponse(BaseModel):
    """Schema for brand response"""
    id: str = Field(..., alias="_id")
    company_id: str
    company_name: Optional[str] = None  # Populated from lookup
    
    name: str
    code: str
    status: BrandStatus
    
    # Brand information
    industry: Optional[str] = None
    website: Optional[HttpUrl] = None
    logo_url: Optional[HttpUrl] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    
    # Settings
    voice_settings: BrandVoiceSettings
    ai_settings: BrandAISettings
    social_settings: BrandSocialSettings
    
    # Contact information
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    timezone: str
    business_hours: Optional[Dict[str, str]] = None
    
    # AI Agent (one-to-one relationship)
    ai_agent_id: Optional[str] = Field(None, description="Associated AI agent ID (one-to-one)")
    
    # Statistics
    total_knowledge_items: int = Field(default=0)
    total_conversations: int = Field(default=0)
    
    # Additional
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
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


class BrandStats(BaseModel):
    """Brand performance statistics"""
    brand_id: str
    brand_name: str
    period: str  # daily, weekly, monthly
    
    # Message metrics
    total_messages: int = 0
    messages_resolved: int = 0
    messages_escalated: int = 0
    avg_resolution_time_seconds: float = 0.0
    
    # AI metrics
    ai_responses_generated: int = 0
    ai_accuracy_score: float = 0.0
    knowledge_base_hits: int = 0
    
    # Customer metrics
    unique_customers: int = 0
    satisfaction_score: float = 0.0
    sentiment_positive: int = 0
    sentiment_negative: int = 0
    sentiment_neutral: int = 0
    
    # Agent metrics
    active_agents: int = 0
    agent_utilization_rate: float = 0.0
    
    calculated_at: datetime


class BrandListResponse(BaseModel):
    """Response for brand list with pagination"""
    brands: List[BrandResponse]
    total: int
    page: int
    page_size: int
    total_pages: int