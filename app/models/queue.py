"""
Queue Management Models for Message Routing and Agent Assignment
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, time
from pydantic import BaseModel, Field
from enum import Enum


class QueueType(str, Enum):
    """Type of queue"""
    MANUAL = "manual"  # Manual assignment
    ROUND_ROBIN = "round_robin"  # Distribute evenly
    SKILL_BASED = "skill_based"  # Based on agent skills
    PRIORITY = "priority"  # Based on message priority
    LOAD_BALANCED = "load_balanced"  # Based on agent workload
    AI_ROUTED = "ai_routed"  # AI determines best agent


class QueueStatus(str, Enum):
    """Queue operational status"""
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    OVERFLOW = "overflow"  # Too many messages
    AFTER_HOURS = "after_hours"


class RoutingRule(BaseModel):
    """Rule for routing messages to queues"""
    name: str
    priority: int = Field(default=0, ge=0, le=100)
    
    # Conditions (all must match)
    source_platforms: Optional[List[str]] = None
    message_types: Optional[List[str]] = None
    customer_tiers: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    intents: Optional[List[str]] = None
    sentiment_range: Optional[Dict[str, float]] = None  # {"min": -1.0, "max": 0.0}
    keywords: Optional[List[str]] = None
    
    # Time-based conditions
    business_hours_only: bool = Field(default=False)
    specific_days: Optional[List[int]] = None  # 0=Monday, 6=Sunday
    specific_hours: Optional[Dict[str, str]] = None  # {"start": "09:00", "end": "17:00"}
    
    # Actions
    target_queue_id: Optional[str] = None
    target_team_id: Optional[str] = None
    target_agent_id: Optional[str] = None
    auto_respond: bool = Field(default=False)
    escalate: bool = Field(default=False)
    
    is_active: bool = Field(default=True)


class SLAConfiguration(BaseModel):
    """Service Level Agreement configuration"""
    first_response_time_seconds: int = Field(default=300, ge=60)  # 5 minutes default
    resolution_time_seconds: int = Field(default=3600, ge=300)  # 1 hour default
    
    # Escalation thresholds
    warning_threshold_percent: int = Field(default=80, ge=50, le=100)
    critical_threshold_percent: int = Field(default=90, ge=50, le=100)
    
    # Actions on breach
    auto_escalate_on_breach: bool = Field(default=True)
    notify_supervisor_on_warning: bool = Field(default=True)
    notify_manager_on_breach: bool = Field(default=True)


class QueueCapacity(BaseModel):
    """Queue capacity configuration"""
    max_queue_size: int = Field(default=100, ge=1, le=10000)
    max_wait_time_seconds: int = Field(default=1800, ge=60)  # 30 minutes
    
    # Per-agent limits
    max_concurrent_per_agent: int = Field(default=5, ge=1, le=50)
    max_daily_per_agent: int = Field(default=50, ge=1, le=500)
    
    # Overflow handling
    overflow_queue_id: Optional[str] = None
    overflow_action: str = Field(default="queue")  # queue, reject, auto_respond


class QueueCreate(BaseModel):
    """Schema for creating a queue"""
    company_id: str
    brand_id: str
    name: str
    description: Optional[str] = None
    
    # Queue configuration
    queue_type: QueueType
    priority: int = Field(default=50, ge=0, le=100)
    
    # Team/Agent assignment
    team_id: Optional[str] = None
    agent_ids: List[str] = Field(default_factory=list)
    
    # Routing rules
    routing_rules: List[RoutingRule] = Field(default_factory=list)
    
    # SLA and capacity
    sla_config: SLAConfiguration = Field(default_factory=SLAConfiguration)
    capacity_config: QueueCapacity = Field(default_factory=QueueCapacity)
    
    # Operating hours
    operating_hours: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    timezone: str = Field(default="UTC")
    
    # Auto-responses
    auto_acknowledge: bool = Field(default=False)
    acknowledgment_message: Optional[str] = None
    
    # Settings
    is_active: bool = Field(default=True)
    is_default: bool = Field(default=False)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QueueUpdate(BaseModel):
    """Schema for updating a queue"""
    name: Optional[str] = None
    description: Optional[str] = None
    
    # Queue configuration
    queue_type: Optional[QueueType] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[QueueStatus] = None
    
    # Team/Agent assignment
    team_id: Optional[str] = None
    agent_ids: Optional[List[str]] = None
    
    # Routing rules
    routing_rules: Optional[List[RoutingRule]] = None
    
    # SLA and capacity
    sla_config: Optional[SLAConfiguration] = None
    capacity_config: Optional[QueueCapacity] = None
    
    # Operating hours
    operating_hours: Optional[Dict[str, Dict[str, str]]] = None
    
    # Auto-responses
    auto_acknowledge: Optional[bool] = None
    acknowledgment_message: Optional[str] = None
    
    # Settings
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    
    metadata: Optional[Dict[str, Any]] = None


class QueueItem(BaseModel):
    """Item in a queue"""
    message_id: str
    conversation_id: Optional[str] = None
    
    # Priority and position
    priority: int
    position: int
    
    # Timing
    enqueued_at: datetime
    wait_time_seconds: int = Field(default=0)
    sla_deadline: datetime
    is_overdue: bool = Field(default=False)
    
    # Customer info
    customer_id: str
    customer_name: str
    customer_tier: Optional[str] = None
    
    # Message preview
    message_preview: str
    sentiment: Optional[str] = None
    intent: Optional[str] = None
    
    # Assignment
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    
    # Status
    status: str  # waiting, assigned, in_progress


class Queue(BaseModel):
    """Queue with current state"""
    id: str = Field(alias="_id")
    company_id: str
    brand_id: str
    brand_name: Optional[str] = None
    
    name: str
    description: Optional[str] = None
    
    # Configuration
    queue_type: QueueType
    priority: int
    status: QueueStatus
    
    # Team/Agent
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    agent_ids: List[str]
    agent_names: Optional[List[str]] = None
    
    # Current state
    current_size: int = Field(default=0)
    items: List[QueueItem] = Field(default_factory=list)
    
    # Metrics
    avg_wait_time: int = Field(default=0)
    longest_wait_time: int = Field(default=0)
    messages_today: int = Field(default=0)
    sla_breach_count: int = Field(default=0)
    sla_compliance_rate: float = Field(default=100.0)
    
    # Available agents
    available_agents: int = Field(default=0)
    busy_agents: int = Field(default=0)
    offline_agents: int = Field(default=0)
    
    # Settings
    is_active: bool
    is_default: bool
    
    # Configuration
    routing_rules: List[RoutingRule]
    sla_config: SLAConfiguration
    capacity_config: QueueCapacity
    operating_hours: Dict[str, Dict[str, str]]
    timezone: str
    
    # Auto-responses
    auto_acknowledge: bool
    acknowledgment_message: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QueueAssignment(BaseModel):
    """Assignment of message to agent from queue"""
    queue_id: str
    message_id: str
    conversation_id: Optional[str] = None
    
    # Assignment details
    assigned_to: str  # Agent user ID
    assigned_by: str  # System or supervisor ID
    assignment_method: str  # manual, auto, ai_suggested
    
    # Timing
    assigned_at: datetime
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # SLA tracking
    sla_deadline: datetime
    sla_status: str  # on_track, warning, breached
    response_time: Optional[int] = None
    resolution_time: Optional[int] = None
    
    # Status
    status: str  # assigned, accepted, in_progress, completed, reassigned


class QueueTransfer(BaseModel):
    """Transfer request between queues"""
    message_id: str
    from_queue_id: str
    to_queue_id: str
    reason: str
    transferred_by: str
    notes: Optional[str] = None
    maintain_priority: bool = Field(default=True)


class QueueStats(BaseModel):
    """Queue performance statistics"""
    queue_id: str
    queue_name: str
    period: str  # hourly, daily, weekly, monthly
    
    # Volume metrics
    total_messages: int = 0
    messages_assigned: int = 0
    messages_completed: int = 0
    messages_abandoned: int = 0
    messages_transferred: int = 0
    
    # Time metrics
    avg_wait_time_seconds: float = 0.0
    max_wait_time_seconds: int = 0
    avg_handle_time_seconds: float = 0.0
    avg_response_time_seconds: float = 0.0
    
    # SLA metrics
    sla_met_count: int = 0
    sla_breach_count: int = 0
    sla_compliance_rate: float = 0.0
    
    # Agent metrics
    unique_agents: int = 0
    avg_messages_per_agent: float = 0.0
    agent_utilization_rate: float = 0.0
    
    # Quality metrics
    customer_satisfaction: float = 0.0
    first_contact_resolution_rate: float = 0.0
    
    calculated_at: datetime


class QueueListResponse(BaseModel):
    """Queue list with pagination"""
    queues: List[Queue]
    total: int
    page: int
    page_size: int
    total_pages: int


class BulkAssignment(BaseModel):
    """Bulk assignment request"""
    queue_id: str
    message_ids: List[str]
    agent_id: str
    distribute_evenly: bool = Field(default=False)
    respect_capacity: bool = Field(default=True)