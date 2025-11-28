"""
Company Models for multi-tenant architecture
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, HttpUrl
from enum import Enum


class CompanyStatus(str, Enum):
    """Company account status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    EXPIRED = "expired"


class CompanyPlan(str, Enum):
    """Company subscription plans"""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class CompanySettings(BaseModel):
    """Company-specific settings and configurations"""
    max_brands: int = Field(default=5, ge=1, le=100)
    max_agents: int = Field(default=10, ge=1, le=1000)
    max_users: int = Field(default=20, ge=1, le=10000)
    max_knowledge_base_items: int = Field(default=1000, ge=1, le=100000)
    enable_custom_llm: bool = Field(default=False)
    enable_multi_language: bool = Field(default=True)
    enable_api_access: bool = Field(default=False)
    allowed_llm_providers: List[str] = Field(default_factory=lambda: ["openai", "anthropic"])
    storage_quota_gb: int = Field(default=10, ge=1, le=10000)
    api_rate_limit: int = Field(default=1000, ge=100, le=100000)
    custom_features: Dict[str, Any] = Field(default_factory=dict)


class SetupConfiguration(BaseModel):
    """Setup wizard configuration"""
    selected_ai_features: List[str] = Field(default_factory=list)
    brand_guidelines: Optional[str] = None
    brand_tone: Optional[str] = None
    brand_colors: Dict[str, str] = Field(default_factory=dict)
    subscription_plan: Optional[str] = None
    terms_accepted: bool = False
    terms_accepted_at: Optional[datetime] = None
    terms_accepted_by: Optional[str] = None


class SetupStatus(BaseModel):
    """Company setup status tracking"""
    is_setup_complete: bool = False
    setup_started_at: Optional[datetime] = None
    setup_completed_at: Optional[datetime] = None
    setup_step: int = Field(default=0, ge=0, le=7)
    configuration: Optional[SetupConfiguration] = Field(default_factory=SetupConfiguration)


class CompanyAddress(BaseModel):
    """Company address information"""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str


class CompanyContact(BaseModel):
    """Company contact information"""
    primary_email: EmailStr
    primary_phone: Optional[str] = None
    support_email: Optional[EmailStr] = None
    billing_email: Optional[EmailStr] = None
    technical_contact_name: Optional[str] = None
    technical_contact_email: Optional[EmailStr] = None


class CompanyBilling(BaseModel):
    """Company billing information"""
    plan: CompanyPlan = Field(default=CompanyPlan.STARTER)
    billing_cycle: str = Field(default="monthly")  # monthly, yearly
    next_billing_date: Optional[datetime] = None
    payment_method: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    credits_remaining: int = Field(default=0, ge=0)
    credits_used: int = Field(default=0, ge=0)


class CompanyCreate(BaseModel):
    """Schema for creating a new company"""
    name: str = Field(..., min_length=2, max_length=100, description="Company name")
    domain: Optional[str] = Field(None, description="Company primary domain")
    industry: Optional[str] = Field(None, description="Industry sector")
    size: Optional[str] = Field(None, description="Company size: small, medium, large, enterprise")

    # Contact information
    contact: CompanyContact
    address: Optional[CompanyAddress] = None

    # Settings and configuration
    settings: Optional[CompanySettings] = Field(default_factory=CompanySettings)
    plan: CompanyPlan = Field(default=CompanyPlan.STARTER)

    # Setup tracking
    setup_status: Optional[SetupStatus] = Field(default_factory=SetupStatus)

    # Additional information
    website: Optional[HttpUrl] = None
    logo_url: Optional[HttpUrl] = None
    description: Optional[str] = Field(None, max_length=500)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CompanyUpdate(BaseModel):
    """Schema for updating a company"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    
    # Contact information
    contact: Optional[CompanyContact] = None
    address: Optional[CompanyAddress] = None
    
    # Settings and configuration
    settings: Optional[CompanySettings] = None
    status: Optional[CompanyStatus] = None
    
    # Additional information
    website: Optional[HttpUrl] = None
    logo_url: Optional[HttpUrl] = None
    description: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = None


class CompanyResponse(BaseModel):
    """Schema for company response"""
    id: str = Field(..., alias="_id")
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None

    # Contact and address
    contact: CompanyContact
    address: Optional[CompanyAddress] = None

    # Settings and status
    settings: CompanySettings
    status: CompanyStatus
    plan: CompanyPlan
    billing: Optional[CompanyBilling] = None

    # Setup tracking
    setup_status: SetupStatus = Field(default_factory=SetupStatus)

    # Additional information
    website: Optional[HttpUrl] = None
    logo_url: Optional[HttpUrl] = None
    description: Optional[str] = None

    # Statistics
    total_brands: int = Field(default=0)
    total_agents: int = Field(default=0)
    total_users: int = Field(default=0)
    total_knowledge_items: int = Field(default=0)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CompanyStats(BaseModel):
    """Company usage statistics"""
    company_id: str
    period: str  # daily, weekly, monthly
    
    # Usage metrics
    total_messages_processed: int = 0
    total_ai_responses: int = 0
    total_api_calls: int = 0
    storage_used_gb: float = 0.0
    
    # Resource utilization
    brands_count: int = 0
    agents_count: int = 0
    users_count: int = 0
    knowledge_items_count: int = 0
    
    # Performance metrics
    avg_response_time_ms: float = 0.0
    success_rate: float = 0.0
    
    # Billing metrics
    credits_consumed: int = 0
    estimated_cost: float = 0.0
    
    calculated_at: datetime


class CompanyListResponse(BaseModel):
    """Response for company list with pagination"""
    companies: List[CompanyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SetupInitRequest(BaseModel):
    """Request to initialize setup for a company"""
    company_name: str = Field(..., min_length=2, max_length=100)
    company_domain: Optional[str] = None
    user_email: EmailStr
    user_name: str = Field(..., min_length=2, max_length=100)
    user_id: Optional[str] = None
    khoros_tenant_id: Optional[str] = None


class SetupInitResponse(BaseModel):
    """Response for setup initialization"""
    company_id: str
    company_name: str
    user_name: str
    user_email: str
    is_setup_complete: bool
    setup_step: int
    should_show_setup: bool


class SetupUpdateRequest(BaseModel):
    """Request to update setup configuration"""
    company_id: str
    setup_step: int = Field(..., ge=0, le=7)
    configuration: SetupConfiguration


class SetupCompleteRequest(BaseModel):
    """Request to complete the setup"""
    company_id: str
    configuration: SetupConfiguration