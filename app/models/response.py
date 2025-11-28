"""
Response Models for AI-Generated and Human Responses
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ResponseType(str, Enum):
    """Type of response"""
    AI_GENERATED = "ai_generated"
    AI_SUGGESTED = "ai_suggested"
    HUMAN = "human"
    TEMPLATE = "template"
    HYBRID = "hybrid"  # AI-generated but human-edited
    AUTO = "auto"  # Fully automated


class ResponseStatus(str, Enum):
    """Response status"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class ResponseChannel(str, Enum):
    """Channel for sending response"""
    SAME_AS_SOURCE = "same_as_source"
    PUBLIC_REPLY = "public_reply"
    PRIVATE_MESSAGE = "private_message"
    EMAIL = "email"
    SMS = "sms"
    PHONE_CALL = "phone_call"


class ApprovalStatus(str, Enum):
    """Approval status for responses"""
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


class ResponseQuality(BaseModel):
    """Quality metrics for a response"""
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    tone_appropriateness: float = Field(..., ge=0.0, le=1.0)
    grammar_score: float = Field(..., ge=0.0, le=1.0)
    brand_alignment: float = Field(..., ge=0.0, le=1.0)
    completeness: float = Field(..., ge=0.0, le=1.0)
    overall_score: float = Field(..., ge=0.0, le=1.0)
    issues_found: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class ResponseGeneration(BaseModel):
    """AI response generation details"""
    ai_agent_id: str
    llm_provider_id: str
    llm_model: str
    
    # Generation parameters
    prompt_template: str
    system_prompt: str
    temperature: float
    max_tokens: int
    
    # Context used
    knowledge_items_used: List[str] = Field(default_factory=list)
    similar_responses_referenced: List[str] = Field(default_factory=list)
    
    # Generation metrics
    generation_time_ms: int
    tokens_used: int
    cost: float
    attempts: int = Field(default=1)
    
    # Quality check
    quality_metrics: Optional[ResponseQuality] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class ResponseTemplate(BaseModel):
    """Predefined response template"""
    id: str = Field(alias="_id")
    company_id: str
    brand_id: Optional[str] = None  # None means company-wide
    
    name: str
    category: str  # greeting, apology, escalation, etc.
    
    # Template content
    content: str
    variables: List[str] = Field(default_factory=list)  # {{customer_name}}, {{issue}}, etc.
    
    # Usage conditions
    intents: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    sentiment_triggers: List[str] = Field(default_factory=list)
    
    # Settings
    is_active: bool = Field(default=True)
    auto_approve: bool = Field(default=False)
    priority: int = Field(default=0)
    
    # Statistics
    usage_count: int = Field(default=0)
    success_rate: float = Field(default=0.0)
    avg_satisfaction: float = Field(default=0.0)
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: Optional[str] = None


class ResponseCreate(BaseModel):
    """Schema for creating a response"""
    # References
    message_id: str = Field(..., description="Original message being responded to")
    conversation_id: Optional[str] = None
    company_id: str
    brand_id: str
    
    # Response content
    content: str
    response_type: ResponseType
    channel: ResponseChannel = Field(default=ResponseChannel.SAME_AS_SOURCE)
    
    # AI Generation (if applicable)
    generation_details: Optional[ResponseGeneration] = None
    template_id: Optional[str] = None
    
    # Approval
    requires_approval: bool = Field(default=True)
    approved_by: Optional[str] = None
    
    # Scheduling
    send_immediately: bool = Field(default=False)
    scheduled_for: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResponseUpdate(BaseModel):
    """Schema for updating a response"""
    content: Optional[str] = None
    status: Optional[ResponseStatus] = None
    channel: Optional[ResponseChannel] = None
    
    # Approval
    approval_status: Optional[ApprovalStatus] = None
    approved_by: Optional[str] = None
    approval_notes: Optional[str] = None
    
    # Scheduling
    scheduled_for: Optional[datetime] = None
    
    # After sending
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    platform_response_id: Optional[str] = None
    delivery_error: Optional[str] = None
    
    metadata: Optional[Dict[str, Any]] = None


class ResponseMessage(BaseModel):
    """Complete response message"""
    id: str = Field(alias="_id")
    
    # References
    message_id: str
    conversation_id: Optional[str] = None
    company_id: str
    brand_id: str
    brand_name: Optional[str] = None
    
    # Response details
    content: str
    response_type: ResponseType
    channel: ResponseChannel
    status: ResponseStatus
    
    # AI Generation
    generation_details: Optional[ResponseGeneration] = None
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    
    # Approval
    requires_approval: bool
    approval_status: ApprovalStatus
    approved_by: Optional[str] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    
    # Authorship
    created_by: str  # User or AI agent ID
    created_by_name: Optional[str] = None
    edited_by: Optional[str] = None
    edited_by_name: Optional[str] = None
    
    # Delivery
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    platform_response_id: Optional[str] = None
    delivery_error: Optional[str] = None
    
    # Scheduling
    scheduled_for: Optional[datetime] = None
    
    # Customer feedback
    customer_rating: Optional[int] = Field(None, ge=1, le=5)
    customer_feedback: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ResponseSuggestion(BaseModel):
    """AI-suggested responses for human review"""
    message_id: str
    suggestions: List[Dict[str, Any]]  # Multiple response options
    
    # Best suggestion
    recommended_index: int = Field(default=0)
    recommendation_reason: str
    
    # Context
    customer_context: Dict[str, Any]
    conversation_context: Dict[str, Any]
    
    # Metadata
    generated_at: datetime
    expires_at: datetime  # Suggestions expire after some time


class ResponseMetrics(BaseModel):
    """Response performance metrics"""
    response_id: str
    
    # Time metrics
    time_to_first_response: Optional[int] = None  # seconds
    total_response_time: Optional[int] = None
    
    # Quality metrics
    quality_score: Optional[float] = None
    sentiment_impact: Optional[float] = None  # How response affected sentiment
    
    # Customer metrics
    customer_satisfaction: Optional[float] = None
    resolved_in_first_contact: bool = Field(default=False)
    
    # Engagement metrics
    customer_read: bool = Field(default=False)
    customer_replied: bool = Field(default=False)
    conversation_continued: bool = Field(default=False)
    
    calculated_at: datetime


class ResponseListResponse(BaseModel):
    """Response list with pagination"""
    responses: List[ResponseMessage]
    total: int
    page: int
    page_size: int
    total_pages: int


class BulkResponseRequest(BaseModel):
    """Bulk response generation request"""
    message_ids: List[str]
    use_ai: bool = Field(default=True)
    auto_approve: bool = Field(default=False)
    auto_send: bool = Field(default=False)
    template_id: Optional[str] = None
    custom_prompt: Optional[str] = None