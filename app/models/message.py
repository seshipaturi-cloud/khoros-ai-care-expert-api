"""
Message Models for Social Media Customer Care
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class MessageSource(str, Enum):
    """Source platform for messages"""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    WEB_CHAT = "web_chat"
    SMS = "sms"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    CUSTOM = "custom"


class MessageType(str, Enum):
    """Type of message"""
    PUBLIC_POST = "public_post"
    PRIVATE_MESSAGE = "private_message"
    COMMENT = "comment"
    MENTION = "mention"
    REVIEW = "review"
    STORY_MENTION = "story_mention"
    DIRECT_MESSAGE = "direct_message"


class MessageStatus(str, Enum):
    """Message processing status"""
    NEW = "new"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESPONDED = "responded"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    ARCHIVED = "archived"
    FAILED = "failed"


class MessagePriority(str, Enum):
    """Message priority level"""
    CRITICAL = "critical"  # Urgent issues, VIP customers
    HIGH = "high"  # Complaints, negative sentiment
    MEDIUM = "medium"  # General inquiries
    LOW = "low"  # Information requests, positive feedback


class SentimentScore(BaseModel):
    """Sentiment analysis results"""
    sentiment: str = Field(..., description="positive, negative, neutral, mixed")
    score: float = Field(..., ge=-1.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    emotions: Dict[str, float] = Field(default_factory=dict)  # joy, anger, fear, etc.


class IntentClassification(BaseModel):
    """Intent classification results"""
    primary_intent: str  # complaint, inquiry, feedback, support, sales
    confidence: float = Field(..., ge=0.0, le=1.0)
    secondary_intents: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    entities: Dict[str, List[str]] = Field(default_factory=dict)  # product, issue, etc.


class CustomerProfile(BaseModel):
    """Customer information"""
    platform_user_id: str
    username: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None
    is_verified: bool = Field(default=False)
    is_vip: bool = Field(default=False)
    follower_count: Optional[int] = None
    customer_tier: Optional[str] = None  # gold, silver, bronze
    previous_interactions: int = Field(default=0)
    lifetime_value: Optional[float] = None
    tags: List[str] = Field(default_factory=list)


class AIAnalysis(BaseModel):
    """AI analysis results for a message"""
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    ai_agent_id: str
    llm_provider_id: str
    llm_model: str
    
    # Analysis results
    sentiment: SentimentScore
    intent: IntentClassification
    urgency_score: float = Field(..., ge=0.0, le=1.0)
    
    # Language detection
    detected_language: str
    language_confidence: float
    needs_translation: bool = Field(default=False)
    translated_text: Optional[str] = None
    
    # Content analysis
    contains_pii: bool = Field(default=False)
    contains_profanity: bool = Field(default=False)
    spam_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Suggested actions
    suggested_response: Optional[str] = None
    suggested_response_confidence: float = Field(default=0.0)
    suggested_knowledge_items: List[str] = Field(default_factory=list)
    suggested_agent_skills: List[str] = Field(default_factory=list)
    auto_response_eligible: bool = Field(default=False)
    requires_human_review: bool = Field(default=True)
    
    # Processing metrics
    processing_time_ms: int
    tokens_used: int
    cost: float = Field(default=0.0)


class MessageAttachment(BaseModel):
    """Message attachment information"""
    type: str  # image, video, audio, document
    url: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    thumbnail_url: Optional[str] = None
    transcription: Optional[str] = None  # For audio/video
    ocr_text: Optional[str] = None  # For images


class MessageCreate(BaseModel):
    """Schema for creating a new message"""
    # Core fields
    company_id: str
    brand_id: str
    source: MessageSource
    message_type: MessageType
    
    # Message content
    external_id: str = Field(..., description="Platform-specific message ID")
    content: str
    raw_content: Optional[Dict[str, Any]] = Field(default_factory=dict)
    attachments: List[MessageAttachment] = Field(default_factory=list)
    
    # Customer info
    customer: CustomerProfile
    
    # Context
    conversation_id: Optional[str] = None
    parent_message_id: Optional[str] = None
    thread_id: Optional[str] = None
    platform_url: Optional[str] = None
    
    # Metadata
    received_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MessageUpdate(BaseModel):
    """Schema for updating a message"""
    status: Optional[MessageStatus] = None
    priority: Optional[MessagePriority] = None
    assigned_to: Optional[str] = None  # User ID
    assigned_team_id: Optional[str] = None
    
    # Processing updates
    ai_analysis: Optional[AIAnalysis] = None
    response_id: Optional[str] = None
    resolution_time_seconds: Optional[int] = None
    
    # Tags and notes
    tags: Optional[List[str]] = None
    internal_notes: Optional[str] = None
    
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Schema for message response"""
    id: str = Field(alias="_id")
    company_id: str
    brand_id: str
    brand_name: Optional[str] = None
    
    # Message details
    source: MessageSource
    message_type: MessageType
    status: MessageStatus
    priority: MessagePriority
    
    # Content
    external_id: str
    content: str
    attachments: List[MessageAttachment]
    
    # Customer
    customer: CustomerProfile
    
    # Context
    conversation_id: Optional[str] = None
    parent_message_id: Optional[str] = None
    thread_id: Optional[str] = None
    platform_url: Optional[str] = None
    
    # AI Analysis
    ai_analysis: Optional[AIAnalysis] = None
    
    # Assignment
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    assigned_team_id: Optional[str] = None
    assigned_team_name: Optional[str] = None
    assigned_at: Optional[datetime] = None
    
    # Response tracking
    response_id: Optional[str] = None
    responded_at: Optional[datetime] = None
    response_time_seconds: Optional[int] = None
    resolution_time_seconds: Optional[int] = None
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    internal_notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    received_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConversationThread(BaseModel):
    """Conversation thread grouping related messages"""
    id: str = Field(alias="_id")
    company_id: str
    brand_id: str
    
    # Thread info
    source: MessageSource
    title: Optional[str] = None
    
    # Customer
    customer: CustomerProfile
    
    # Messages
    message_ids: List[str] = Field(default_factory=list)
    message_count: int = Field(default=0)
    
    # Status
    status: MessageStatus
    priority: MessagePriority
    
    # AI Summary
    ai_summary: Optional[str] = None
    key_topics: List[str] = Field(default_factory=list)
    overall_sentiment: Optional[str] = None
    
    # Assignment
    assigned_to: Optional[str] = None
    assigned_team_id: Optional[str] = None
    
    # Metrics
    first_response_time: Optional[int] = None
    resolution_time: Optional[int] = None
    messages_exchanged: int = Field(default=0)
    
    # Timestamps
    started_at: datetime
    last_activity_at: datetime
    closed_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MessageBatch(BaseModel):
    """Batch of messages for bulk processing"""
    messages: List[MessageCreate]
    process_async: bool = Field(default=True)
    auto_assign: bool = Field(default=True)
    auto_respond: bool = Field(default=False)


class MessageListResponse(BaseModel):
    """Response for message list with pagination"""
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int