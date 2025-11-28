"""
LLM Provider Models for managing AI model configurations
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum
from app.models.user_context import UserContext


class ProviderType(str, Enum):
    """LLM Provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE_OPENAI = "azure_openai"
    AWS_BEDROCK = "aws_bedrock"
    HUGGINGFACE = "huggingface"
    CUSTOM = "custom"


class ProviderStatus(str, Enum):
    """Provider configuration status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    QUOTA_EXCEEDED = "quota_exceeded"


class ModelCapability(str, Enum):
    """Model capabilities"""
    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    EMBEDDINGS = "embeddings"
    CODE_GENERATION = "code_generation"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    AUDIO = "audio"


class ModelConfig(BaseModel):
    """Configuration for a specific model"""
    model_id: str = Field(..., description="Model identifier (e.g., gpt-4, claude-3)")
    display_name: str = Field(..., description="User-friendly model name")
    capabilities: List[ModelCapability] = Field(default_factory=list)
    
    # Model limits
    max_tokens: int = Field(default=4096, ge=1)
    max_input_tokens: int = Field(default=4096, ge=1)
    max_output_tokens: int = Field(default=4096, ge=1)
    
    # Cost configuration
    input_cost_per_1k_tokens: float = Field(default=0.0, ge=0)
    output_cost_per_1k_tokens: float = Field(default=0.0, ge=0)
    
    # Performance settings
    default_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    default_top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    supports_streaming: bool = Field(default=True)
    supports_functions: bool = Field(default=False)
    
    # Additional settings
    is_deprecated: bool = Field(default=False)
    deprecation_date: Optional[datetime] = None
    recommended_alternative: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProviderCredentials(BaseModel):
    """Secure credentials for provider access"""
    api_key: Optional[str] = Field(None, description="API key (encrypted in storage)")
    api_secret: Optional[str] = Field(None, description="API secret (encrypted in storage)")
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    
    # Azure specific
    azure_endpoint: Optional[str] = None
    azure_deployment_name: Optional[str] = None
    azure_api_version: Optional[str] = None
    
    # AWS specific
    aws_region: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # Custom endpoint
    custom_endpoint_url: Optional[HttpUrl] = None
    custom_headers: Optional[Dict[str, str]] = None


class RateLimitConfig(BaseModel):
    """Rate limiting configuration"""
    requests_per_minute: int = Field(default=60, ge=1)
    requests_per_hour: int = Field(default=3600, ge=1)
    requests_per_day: int = Field(default=86400, ge=1)
    tokens_per_minute: int = Field(default=90000, ge=1)
    tokens_per_hour: int = Field(default=5400000, ge=1)
    concurrent_requests: int = Field(default=10, ge=1)


class LLMProviderCreate(BaseModel):
    """Schema for creating a new LLM provider configuration"""
    company_id: str = Field(..., description="Parent company ID")
    name: str = Field(..., min_length=2, max_length=100, description="Provider configuration name")
    provider_type: ProviderType
    
    # Credentials (will be encrypted)
    credentials: ProviderCredentials
    
    # Models configuration
    models: List[ModelConfig] = Field(default_factory=list)
    default_model_id: Optional[str] = None
    
    # Rate limiting
    rate_limits: Optional[RateLimitConfig] = Field(default_factory=RateLimitConfig)
    
    # Quotas and limits
    monthly_token_quota: Optional[int] = Field(None, ge=0)
    monthly_request_quota: Optional[int] = Field(None, ge=0)
    max_cost_per_month: Optional[float] = Field(None, ge=0)
    
    # Settings
    auto_fallback_enabled: bool = Field(default=False)
    fallback_provider_id: Optional[str] = None
    retry_attempts: int = Field(default=3, ge=0, le=10)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    
    # Additional
    description: Optional[str] = Field(None, max_length=500)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMProviderUpdate(BaseModel):
    """Schema for updating an LLM provider configuration"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    
    # Credentials (will be encrypted)
    credentials: Optional[ProviderCredentials] = None
    
    # Models configuration
    models: Optional[List[ModelConfig]] = None
    default_model_id: Optional[str] = None
    
    # Rate limiting
    rate_limits: Optional[RateLimitConfig] = None
    
    # Quotas and limits
    monthly_token_quota: Optional[int] = Field(None, ge=0)
    monthly_request_quota: Optional[int] = Field(None, ge=0)
    max_cost_per_month: Optional[float] = Field(None, ge=0)
    
    # Settings
    auto_fallback_enabled: Optional[bool] = None
    fallback_provider_id: Optional[str] = None
    retry_attempts: Optional[int] = Field(None, ge=0, le=10)
    timeout_seconds: Optional[int] = Field(None, ge=1, le=300)
    status: Optional[ProviderStatus] = None
    
    # Additional
    description: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMProviderResponse(BaseModel):
    """Schema for LLM provider response (credentials excluded)"""
    id: str = Field(..., alias="_id")
    company_id: str
    company_name: Optional[str] = None  # Populated from lookup
    
    name: str
    provider_type: ProviderType
    status: ProviderStatus
    
    # Models configuration
    models: List[ModelConfig]
    default_model_id: Optional[str] = None
    
    # Rate limiting
    rate_limits: RateLimitConfig
    
    # Quotas and limits
    monthly_token_quota: Optional[int] = None
    monthly_request_quota: Optional[int] = None
    max_cost_per_month: Optional[float] = None
    
    # Current usage
    tokens_used_this_month: int = Field(default=0)
    requests_this_month: int = Field(default=0)
    cost_this_month: float = Field(default=0.0)
    
    # Settings
    auto_fallback_enabled: bool
    fallback_provider_id: Optional[str] = None
    retry_attempts: int
    timeout_seconds: int
    
    # Statistics
    total_requests: int = Field(default=0)
    total_tokens: int = Field(default=0)
    total_errors: int = Field(default=0)
    avg_latency_ms: float = Field(default=0.0)
    success_rate: float = Field(default=100.0)
    last_used: Optional[datetime] = None
    last_error: Optional[str] = None
    
    # Additional
    description: Optional[str] = None
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


class LLMProviderStats(BaseModel):
    """LLM Provider usage statistics"""
    provider_id: str
    provider_name: str
    period: str  # hourly, daily, weekly, monthly
    
    # Usage metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Token metrics
    input_tokens: int = 0
    output_tokens: int = 0
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
    
    # Model breakdown
    model_usage: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Error tracking
    error_types: Dict[str, int] = Field(default_factory=dict)
    
    calculated_at: datetime


class LLMProviderListResponse(BaseModel):
    """Response for LLM provider list with pagination"""
    providers: List[LLMProviderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int