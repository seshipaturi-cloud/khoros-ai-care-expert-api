"""
Team/Group Models for organizing users within companies and brands
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, time
from pydantic import BaseModel, Field, validator
from enum import Enum


class TeamType(str, Enum):
    """Types of teams"""
    SUPPORT = "support"  # Customer support team
    SALES = "sales"  # Sales team
    TECHNICAL = "technical"  # Technical support team
    SOCIAL_MEDIA = "social_media"  # Social media management team
    ESCALATION = "escalation"  # Escalation team
    QUALITY = "quality"  # Quality assurance team
    TRAINING = "training"  # Training team
    CUSTOM = "custom"  # Custom team type


class TeamStatus(str, Enum):
    """Team status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class TeamShift(str, Enum):
    """Team shift timings"""
    MORNING = "morning"  # 6 AM - 2 PM
    AFTERNOON = "afternoon"  # 2 PM - 10 PM
    NIGHT = "night"  # 10 PM - 6 AM
    FLEXIBLE = "flexible"  # Flexible hours
    TWENTY_FOUR_SEVEN = "24x7"  # Round the clock


class TeamPriority(str, Enum):
    """Team priority for routing"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class WorkSchedule(BaseModel):
    """Team work schedule"""
    monday: bool = Field(default=True)
    tuesday: bool = Field(default=True)
    wednesday: bool = Field(default=True)
    thursday: bool = Field(default=True)
    friday: bool = Field(default=True)
    saturday: bool = Field(default=False)
    sunday: bool = Field(default=False)
    
    # Working hours
    start_time: str = Field(default="09:00", description="HH:MM format")
    end_time: str = Field(default="18:00", description="HH:MM format")
    break_duration_minutes: int = Field(default=60, ge=0, le=120)
    
    # Timezone
    timezone: str = Field(default="UTC")
    
    # Holidays
    observe_company_holidays: bool = Field(default=True)
    custom_holidays: List[datetime] = Field(default_factory=list)


class TeamSkills(BaseModel):
    """Team skills and capabilities"""
    languages: List[str] = Field(default_factory=list, description="Languages supported")
    product_expertise: List[str] = Field(default_factory=list, description="Product areas")
    technical_skills: List[str] = Field(default_factory=list, description="Technical capabilities")
    certifications: List[str] = Field(default_factory=list, description="Team certifications")
    specializations: List[str] = Field(default_factory=list, description="Special focus areas")


class TeamRoutingRules(BaseModel):
    """Routing rules for the team"""
    auto_assignment: bool = Field(default=True, description="Enable auto-assignment")
    round_robin: bool = Field(default=True, description="Use round-robin assignment")
    skill_based_routing: bool = Field(default=False, description="Route based on skills")
    load_balancing: bool = Field(default=True, description="Balance load among members")
    
    # Priority routing
    priority_keywords: List[str] = Field(default_factory=list, description="Keywords for priority routing")
    priority_customers: List[str] = Field(default_factory=list, description="VIP customer IDs")
    
    # Capacity settings
    max_concurrent_conversations: int = Field(default=5, ge=1, le=50)
    max_daily_conversations: int = Field(default=50, ge=1, le=500)
    
    # Escalation rules
    escalation_threshold_minutes: int = Field(default=30, ge=5, le=120)
    escalation_team_id: Optional[str] = None
    auto_escalate: bool = Field(default=False)


class TeamMember(BaseModel):
    """Team member information"""
    user_id: str
    user_name: Optional[str] = None  # Populated from lookup
    role_in_team: str = Field(default="member", description="member, lead, supervisor")
    
    # Assignment
    is_active: bool = Field(default=True)
    max_concurrent_conversations: Optional[int] = None  # Override team default
    current_load: int = Field(default=0)
    
    # Performance
    messages_handled_today: int = Field(default=0)
    avg_response_time_today: float = Field(default=0.0)
    satisfaction_score: float = Field(default=0.0)
    
    # Availability
    is_available: bool = Field(default=True)
    availability_status: Optional[str] = None  # available, busy, away, offline
    last_activity: Optional[datetime] = None
    
    # Assignment details
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: str
    removed_at: Optional[datetime] = None
    removed_by: Optional[str] = None


class TeamCreate(BaseModel):
    """Schema for creating a new team"""
    # Required fields
    company_id: str = Field(..., description="Parent company ID")
    name: str = Field(..., min_length=2, max_length=100, description="Team name")
    code: str = Field(..., min_length=2, max_length=20, description="Unique team code")
    
    # Team configuration
    team_type: TeamType = Field(default=TeamType.SUPPORT)
    brand_ids: List[str] = Field(default_factory=list, description="Brands this team serves")
    
    # Leadership
    manager_id: Optional[str] = Field(None, description="Team manager user ID")
    lead_ids: List[str] = Field(default_factory=list, description="Team lead user IDs")
    
    # Members
    member_ids: List[str] = Field(default_factory=list, description="Initial team member IDs")
    
    # Configuration
    skills: Optional[TeamSkills] = Field(default_factory=TeamSkills)
    schedule: Optional[WorkSchedule] = Field(default_factory=WorkSchedule)
    routing_rules: Optional[TeamRoutingRules] = Field(default_factory=TeamRoutingRules)
    
    # Settings
    shift: TeamShift = Field(default=TeamShift.FLEXIBLE)
    priority: TeamPriority = Field(default=TeamPriority.MEDIUM)
    max_members: int = Field(default=50, ge=1, le=500)
    min_members: int = Field(default=1, ge=1, le=50)
    
    # Contact
    email: Optional[str] = None
    phone: Optional[str] = None
    slack_channel: Optional[str] = None
    ms_teams_channel: Optional[str] = None
    
    # Additional
    description: Optional[str] = Field(None, max_length=500)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TeamUpdate(BaseModel):
    """Schema for updating a team"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    code: Optional[str] = Field(None, min_length=2, max_length=20)
    
    # Team configuration
    team_type: Optional[TeamType] = None
    brand_ids: Optional[List[str]] = None
    
    # Leadership
    manager_id: Optional[str] = None
    lead_ids: Optional[List[str]] = None
    
    # Configuration
    skills: Optional[TeamSkills] = None
    schedule: Optional[WorkSchedule] = None
    routing_rules: Optional[TeamRoutingRules] = None
    
    # Settings
    shift: Optional[TeamShift] = None
    priority: Optional[TeamPriority] = None
    status: Optional[TeamStatus] = None
    max_members: Optional[int] = Field(None, ge=1, le=500)
    min_members: Optional[int] = Field(None, ge=1, le=50)
    
    # Contact
    email: Optional[str] = None
    phone: Optional[str] = None
    slack_channel: Optional[str] = None
    ms_teams_channel: Optional[str] = None
    
    # Additional
    description: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class TeamResponse(BaseModel):
    """Schema for team response"""
    id: str = Field(..., alias="_id")
    company_id: str
    company_name: Optional[str] = None  # Populated from lookup
    
    name: str
    code: str
    status: TeamStatus
    
    # Team configuration
    team_type: TeamType
    brand_ids: List[str]
    brand_names: Optional[List[str]] = None  # Populated from lookup
    
    # Leadership
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None  # Populated from lookup
    lead_ids: List[str]
    lead_names: Optional[List[str]] = None  # Populated from lookup
    
    # Members
    members: List[TeamMember] = Field(default_factory=list)
    member_count: int = Field(default=0)
    active_member_count: int = Field(default=0)
    
    # Configuration
    skills: TeamSkills
    schedule: WorkSchedule
    routing_rules: TeamRoutingRules
    
    # Settings
    shift: TeamShift
    priority: TeamPriority
    max_members: int
    min_members: int
    
    # Contact
    email: Optional[str] = None
    phone: Optional[str] = None
    slack_channel: Optional[str] = None
    ms_teams_channel: Optional[str] = None
    
    # Statistics
    total_conversations_today: int = Field(default=0)
    total_conversations_month: int = Field(default=0)
    avg_response_time: float = Field(default=0.0)
    avg_resolution_time: float = Field(default=0.0)
    satisfaction_score: float = Field(default=0.0)
    escalation_rate: float = Field(default=0.0)
    
    # Availability
    is_available: bool = Field(default=True)
    available_members: int = Field(default=0)
    current_load_percentage: float = Field(default=0.0)
    
    # Additional
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
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


class TeamStats(BaseModel):
    """Team performance statistics"""
    team_id: str
    team_name: str
    period: str  # hourly, daily, weekly, monthly
    
    # Volume metrics
    total_conversations: int = 0
    conversations_resolved: int = 0
    conversations_escalated: int = 0
    conversations_pending: int = 0
    
    # Performance metrics
    avg_response_time_seconds: float = 0.0
    avg_resolution_time_seconds: float = 0.0
    first_response_sla_met: float = 0.0  # Percentage
    resolution_sla_met: float = 0.0  # Percentage
    
    # Quality metrics
    customer_satisfaction: float = 0.0
    quality_score: float = 0.0
    escalation_rate: float = 0.0
    
    # Efficiency metrics
    messages_per_conversation: float = 0.0
    agent_utilization: float = 0.0  # Percentage
    concurrent_conversation_avg: float = 0.0
    
    # Member metrics
    active_members: int = 0
    total_member_hours: float = 0.0
    conversations_per_member: float = 0.0
    
    # By member breakdown
    member_stats: List[Dict[str, Any]] = Field(default_factory=list)
    
    calculated_at: datetime


class TeamListResponse(BaseModel):
    """Response for team list with pagination"""
    teams: List[TeamResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TeamAssignment(BaseModel):
    """Team assignment request"""
    team_id: str
    user_ids: List[str]
    role_in_team: str = Field(default="member", description="member, lead, supervisor")
    assigned_by: str


class TeamTransfer(BaseModel):
    """Transfer user between teams"""
    user_id: str
    from_team_id: str
    to_team_id: str
    reason: Optional[str] = None
    effective_date: Optional[datetime] = None
    transferred_by: str