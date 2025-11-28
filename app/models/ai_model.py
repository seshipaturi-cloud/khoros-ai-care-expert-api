"""
AI Model Models - Individual AI models that use LLM providers
Separate from LLM Provider configurations
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from app.models.user_context import UserContext


class ModelType(str, Enum):
    """AI Model types"""
    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    EMBEDDINGS = "embeddings"
    CODE_GENERATION = "code_generation"
    VISION = "vision"
    AUDIO = "audio"
    MULTIMODAL = "multimodal"


class ModelStatus(str, Enum):
    """Model status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    BETA = "beta"
    ERROR = "error"


class ModelCapability(str, Enum):
    """Model capabilities"""
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    VISION = "vision"
    AUDIO = "audio"
    CODE = "code"
    JSON_MODE = "json_mode"
    TOOL_USE = "tool_use"


class AIModelCreate(BaseModel):
    """Schema for creating a new AI model"""
    company_id: str = Field(..., description="Parent company ID")
    provider_id: str = Field(..., description="LLM Provider ID this model uses")

    # Model identification
    name: str = Field(..., min_length=2, max_length=100, description="Model display name")
    model_identifier: str = Field(..., description="Technical model ID (e.g., gpt-4, claude-3-opus)")
    version: Optional[str] = Field(None, description="Model version if applicable")

    # Model details
    model_type: ModelType = Field(default=ModelType.CHAT)
    capabilities: List[ModelCapability] = Field(default_factory=list)
    description: Optional[str] = Field(None, max_length=500)

    # Context and limits
    context_window: int = Field(..., ge=1, description="Maximum context window in tokens")
    max_output_tokens: int = Field(..., ge=1, description="Maximum output tokens")

    # Default parameters
    default_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    default_top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    default_top_k: Optional[int] = Field(None, ge=1)
    default_frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    default_presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)

    # Cost configuration
    input_cost_per_1k_tokens: float = Field(default=0.0, ge=0, description="Cost per 1K input tokens in USD")
    output_cost_per_1k_tokens: float = Field(default=0.0, ge=0, description="Cost per 1K output tokens in USD")

    # Performance settings
    supports_streaming: bool = Field(default=True)
    supports_function_calling: bool = Field(default=False)
    supports_vision: bool = Field(default=False)
    supports_audio: bool = Field(default=False)

    # Quotas and limits
    monthly_request_quota: Optional[int] = Field(None, ge=0)
    monthly_token_quota: Optional[int] = Field(None, ge=0)
    max_cost_per_month: Optional[float] = Field(None, ge=0)

    # Priority and usage
    priority: int = Field(default=1, ge=1, le=100, description="Priority for model selection (1 = highest)")
    enabled: bool = Field(default=True)

    # Additional
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AIModelUpdate(BaseModel):
    """Schema for updating an AI model"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    # Context and limits
    context_window: Optional[int] = Field(None, ge=1)
    max_output_tokens: Optional[int] = Field(None, ge=1)

    # Default parameters
    default_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    default_top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    default_top_k: Optional[int] = Field(None, ge=1)

    # Cost configuration
    input_cost_per_1k_tokens: Optional[float] = Field(None, ge=0)
    output_cost_per_1k_tokens: Optional[float] = Field(None, ge=0)

    # Settings
    priority: Optional[int] = Field(None, ge=1, le=100)
    enabled: Optional[bool] = None
    status: Optional[ModelStatus] = None

    # Quotas
    monthly_request_quota: Optional[int] = Field(None, ge=0)
    monthly_token_quota: Optional[int] = Field(None, ge=0)
    max_cost_per_month: Optional[float] = Field(None, ge=0)

    # Additional
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class AIModelResponse(BaseModel):
    """Schema for AI model response"""
    id: str = Field(..., alias="_id")
    company_id: str
    company_name: Optional[str] = None
    provider_id: str
    provider_name: Optional[str] = None  # Populated from LLM provider lookup

    # Model identification
    name: str
    model_identifier: str
    version: Optional[str] = None

    # Model details
    model_type: ModelType
    capabilities: List[ModelCapability] = Field(default_factory=list)
    description: Optional[str] = None

    # Context and limits
    context_window: int
    max_output_tokens: int

    # Default parameters
    default_temperature: float
    default_top_p: float
    default_top_k: Optional[int] = None
    default_frequency_penalty: float
    default_presence_penalty: float

    # Cost configuration
    input_cost_per_1k_tokens: float
    output_cost_per_1k_tokens: float

    # Performance settings
    supports_streaming: bool
    supports_function_calling: bool
    supports_vision: bool
    supports_audio: bool

    # Status and priority
    status: ModelStatus
    priority: int
    enabled: bool

    # Usage statistics
    total_requests: int = Field(default=0)
    successful_requests: int = Field(default=0)
    failed_requests: int = Field(default=0)
    total_input_tokens: int = Field(default=0)
    total_output_tokens: int = Field(default=0)
    total_cost: float = Field(default=0.0)
    avg_latency_ms: float = Field(default=0.0)
    success_rate: float = Field(default=100.0)
    last_used: Optional[datetime] = None

    # This month usage
    requests_this_month: int = Field(default=0)
    tokens_this_month: int = Field(default=0)
    cost_this_month: float = Field(default=0.0)

    # Quotas status
    monthly_request_quota: Optional[int] = None
    monthly_token_quota: Optional[int] = None
    max_cost_per_month: Optional[float] = None
    quota_exceeded: bool = Field(default=False)

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


class AIModelStats(BaseModel):
    """AI Model usage statistics"""
    model_id: str
    model_name: str
    period: str  # hourly, daily, weekly, monthly

    # Request metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    success_rate: float = 100.0

    # Token metrics
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0

    # Cost metrics
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0

    # Performance metrics
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0

    # Usage by feature
    feature_usage: Dict[str, int] = Field(default_factory=dict, description="Usage count by feature ID")

    # Error tracking
    error_types: Dict[str, int] = Field(default_factory=dict)
    error_messages: List[str] = Field(default_factory=list)

    calculated_at: datetime


class AIModelListResponse(BaseModel):
    """Response for AI model list with pagination"""
    models: List[AIModelResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AIModelTestResult(BaseModel):
    """Result of testing a model"""
    success: bool
    message: str
    response_time_ms: float
    model_info: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None
