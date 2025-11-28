"""
Enhanced User Models with Company and Role relationships
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum
from app.models.role import RoleAssignment, PermissionType


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"  # Awaiting email verification
    LOCKED = "locked"  # Too many failed login attempts


class UserType(str, Enum):
    """Type of user account"""
    INTERNAL = "internal"  # Company employee
    EXTERNAL = "external"  # External contractor
    SYSTEM = "system"  # System/service account
    API = "api"  # API-only account


class NotificationPreference(BaseModel):
    """User notification preferences"""
    email_enabled: bool = Field(default=True)
    sms_enabled: bool = Field(default=False)
    push_enabled: bool = Field(default=True)
    
    # Notification types
    message_assigned: bool = Field(default=True)
    message_escalated: bool = Field(default=True)
    daily_summary: bool = Field(default=True)
    weekly_report: bool = Field(default=False)
    system_alerts: bool = Field(default=True)
    
    # Quiet hours
    quiet_hours_enabled: bool = Field(default=False)
    quiet_hours_start: Optional[str] = Field(None, description="HH:MM format")
    quiet_hours_end: Optional[str] = Field(None, description="HH:MM format")
    quiet_hours_timezone: str = Field(default="UTC")


class UserProfile(BaseModel):
    """User profile information"""
    avatar_url: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = None
    mobile: Optional[str] = None
    
    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    
    # Professional info
    job_title: Optional[str] = None
    department: Optional[str] = None
    manager_id: Optional[str] = None
    employee_id: Optional[str] = None
    hire_date: Optional[date] = None
    
    # Preferences
    timezone: str = Field(default="UTC")
    language: str = Field(default="en")
    date_format: str = Field(default="MM/DD/YYYY")
    time_format: str = Field(default="12h")  # 12h or 24h


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    # Required fields
    company_id: str = Field(..., description="Parent company ID")
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    password: str = Field(..., min_length=8, description="User password")
    
    # Basic information
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    display_name: Optional[str] = Field(None, max_length=100)
    
    # User type and status
    user_type: UserType = Field(default=UserType.INTERNAL)
    status: Optional[UserStatus] = Field(default=UserStatus.PENDING)
    
    # Role assignments
    role_ids: List[str] = Field(default_factory=list, description="Initial role IDs")
    primary_role_id: Optional[str] = None
    
    # Brand and team assignments
    brand_ids: Optional[List[str]] = Field(default_factory=list, description="Assigned brand IDs")
    team_ids: Optional[List[str]] = Field(default_factory=list, description="Assigned team IDs")
    
    # Profile and preferences
    profile: Optional[UserProfile] = Field(default_factory=UserProfile)
    notification_preferences: Optional[NotificationPreference] = Field(default_factory=NotificationPreference)
    
    # Additional
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    # Basic information
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    display_name: Optional[str] = Field(None, max_length=100)
    
    # User type and status
    user_type: Optional[UserType] = None
    status: Optional[UserStatus] = None
    
    # Role assignments (requires special permissions)
    role_ids: Optional[List[str]] = None
    primary_role_id: Optional[str] = None
    
    # Brand and team assignments
    brand_ids: Optional[List[str]] = None
    team_ids: Optional[List[str]] = None
    
    # Profile and preferences
    profile: Optional[UserProfile] = None
    notification_preferences: Optional[NotificationPreference] = None
    
    # Password change
    password: Optional[str] = Field(None, min_length=8)
    
    # Additional
    metadata: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    """Schema for user response"""
    id: str = Field(..., alias="_id")
    company_id: str
    company_name: Optional[str] = None  # Populated from lookup
    
    # Authentication info
    email: EmailStr
    username: str
    email_verified: bool = Field(default=False)
    
    # Basic information
    first_name: str
    last_name: str
    full_name: str  # Computed: first_name + last_name
    display_name: Optional[str] = None
    
    # User type and status
    user_type: UserType
    status: UserStatus
    
    # Role information
    roles: List[RoleAssignment] = Field(default_factory=list)
    primary_role: Optional[RoleAssignment] = None
    effective_permissions: List[PermissionType] = Field(default_factory=list)  # Computed from all roles
    
    # Brand and team assignments
    brand_ids: List[str] = Field(default_factory=list)
    brand_names: Optional[List[str]] = None  # Populated from lookup
    team_ids: List[str] = Field(default_factory=list)
    team_names: Optional[List[str]] = None  # Populated from lookup
    
    # Profile and preferences
    profile: UserProfile
    notification_preferences: NotificationPreference
    
    # Activity tracking
    last_login: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    login_count: int = Field(default=0)
    failed_login_attempts: int = Field(default=0)
    last_password_change: Optional[datetime] = None
    
    # Statistics
    total_messages_handled: int = Field(default=0)
    avg_response_time: float = Field(default=0.0)
    satisfaction_score: float = Field(default=0.0)
    
    # Additional
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class UserSession(BaseModel):
    """User session information"""
    user_id: str
    session_id: str
    
    # Session details
    ip_address: str
    user_agent: str
    device_type: Optional[str] = None  # desktop, mobile, tablet
    browser: Optional[str] = None
    os: Optional[str] = None
    
    # Location
    country: Optional[str] = None
    city: Optional[str] = None
    
    # Session timing
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    
    # Session state
    is_active: bool = Field(default=True)
    terminated_reason: Optional[str] = None


class UserActivity(BaseModel):
    """User activity log"""
    user_id: str
    activity_type: str  # login, logout, password_change, role_change, etc.
    activity_details: Dict[str, Any] = Field(default_factory=dict)
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    # Result
    success: bool = Field(default=True)
    error_message: Optional[str] = None
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserListResponse(BaseModel):
    """Response for user list with pagination"""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserStats(BaseModel):
    """User performance statistics"""
    user_id: str
    period: str  # daily, weekly, monthly
    
    # Message handling
    messages_handled: int = 0
    messages_resolved: int = 0
    messages_escalated: int = 0
    avg_response_time_seconds: float = 0.0
    avg_resolution_time_seconds: float = 0.0
    
    # Quality metrics
    customer_satisfaction: float = 0.0
    first_contact_resolution_rate: float = 0.0
    escalation_rate: float = 0.0
    
    # Activity metrics
    active_hours: float = 0.0
    idle_time_percentage: float = 0.0
    availability_percentage: float = 0.0
    
    # AI assistance metrics
    ai_suggestions_used: int = 0
    ai_accuracy_rating: float = 0.0
    
    calculated_at: datetime


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr
    reset_token: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=8)


class EmailVerification(BaseModel):
    """Email verification request"""
    email: EmailStr
    verification_token: str