"""
AI Feature Models for managing AI-powered features
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from app.models.user_context import UserContext


class FeatureType(str, Enum):
    """AI Feature types"""
    ANALYSIS = "Analysis"
    CLASSIFICATION = "Classification"
    GENERATION = "Generation"
    DETECTION = "Detection"
    PRIORITY = "Priority"
    NLP = "NLP"
    TRANSLATION = "Translation"


class FeatureStatus(str, Enum):
    """Feature status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"


class AIFeatureCreate(BaseModel):
    """Schema for creating a new AI feature"""
    company_id: str = Field(..., description="Parent company ID")
    name: str = Field(..., min_length=2, max_length=100, description="Feature name")
    feature_type: FeatureType
    description: str = Field(..., min_length=10, max_length=500)
    icon: str = Field(default="🧠", max_length=10)

    # Attached AI models (LLM provider IDs in priority order)
    attached_models: List[str] = Field(default_factory=list, description="LLM provider IDs in priority order")

    # Configuration
    enabled: bool = Field(default=True)
    config: Dict[str, Any] = Field(default_factory=dict, description="Feature-specific configuration")

    # Additional
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AIFeatureUpdate(BaseModel):
    """Schema for updating an AI feature"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, min_length=10, max_length=500)
    icon: Optional[str] = Field(None, max_length=10)

    # Attached AI models
    attached_models: Optional[List[str]] = None

    # Configuration
    enabled: Optional[bool] = None
    status: Optional[FeatureStatus] = None
    config: Optional[Dict[str, Any]] = None

    # Additional
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class AIFeatureResponse(BaseModel):
    """Schema for AI feature response"""
    id: str = Field(..., alias="_id")
    company_id: str
    company_name: Optional[str] = None  # Populated from lookup

    name: str
    feature_type: FeatureType
    description: str
    icon: str

    status: FeatureStatus
    enabled: bool

    # Attached models
    attached_models: List[str] = Field(default_factory=list)
    attached_model_names: Optional[List[str]] = Field(default_factory=list)  # Populated from lookup

    # Statistics
    total_conversations: int = Field(default=0)
    total_analyses: int = Field(default=0)
    accuracy_rate: float = Field(default=0.0, description="Percentage 0-100")
    success_rate: float = Field(default=100.0, description="Percentage 0-100")
    avg_processing_time_ms: float = Field(default=0.0)
    last_used: Optional[datetime] = None

    # Usage this month
    conversations_this_month: int = Field(default=0)
    analyses_this_month: int = Field(default=0)

    # Configuration
    config: Dict[str, Any] = Field(default_factory=dict)

    # Additional
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None  # Deprecated: Use created_by_context
    updated_by: Optional[str] = None  # Deprecated: Use updated_by_context

    # User context for audit trails
    created_by_context: Optional[UserContext] = None
    updated_by_context: Optional[UserContext] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AIFeatureStats(BaseModel):
    """AI Feature usage statistics"""
    feature_id: str
    feature_name: str
    period: str  # hourly, daily, weekly, monthly

    # Usage metrics
    total_conversations: int = 0
    total_analyses: int = 0
    successful_analyses: int = 0
    failed_analyses: int = 0

    # Performance metrics
    avg_processing_time_ms: float = 0.0
    p50_processing_time_ms: float = 0.0
    p95_processing_time_ms: float = 0.0
    p99_processing_time_ms: float = 0.0

    # Accuracy metrics
    accuracy_rate: float = 0.0
    confidence_scores: List[float] = Field(default_factory=list)

    # Model usage breakdown
    model_usage: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # Error tracking
    error_types: Dict[str, int] = Field(default_factory=dict)

    calculated_at: datetime


class AIFeatureListResponse(BaseModel):
    """Response for AI feature list with pagination"""
    features: List[AIFeatureResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
