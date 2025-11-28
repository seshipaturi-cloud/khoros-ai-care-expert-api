"""
Role and Permission Models for RBAC (Role-Based Access Control)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class PermissionType(str, Enum):
    """Types of permissions"""
    # Company permissions
    COMPANY_VIEW = "company:view"
    COMPANY_CREATE = "company:create"
    COMPANY_UPDATE = "company:update"
    COMPANY_DELETE = "company:delete"
    
    # Brand permissions
    BRAND_VIEW = "brand:view"
    BRAND_CREATE = "brand:create"
    BRAND_UPDATE = "brand:update"
    BRAND_DELETE = "brand:delete"
    
    # User permissions
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_ASSIGN_ROLE = "user:assign_role"
    
    # Agent permissions
    AGENT_VIEW = "agent:view"
    AGENT_CREATE = "agent:create"
    AGENT_UPDATE = "agent:update"
    AGENT_DELETE = "agent:delete"
    AGENT_EXECUTE = "agent:execute"
    
    # Knowledge Base permissions
    KNOWLEDGE_VIEW = "knowledge:view"
    KNOWLEDGE_CREATE = "knowledge:create"
    KNOWLEDGE_UPDATE = "knowledge:update"
    KNOWLEDGE_DELETE = "knowledge:delete"
    
    # LLM Provider permissions
    LLM_VIEW = "llm:view"
    LLM_CREATE = "llm:create"
    LLM_UPDATE = "llm:update"
    LLM_DELETE = "llm:delete"
    LLM_TEST = "llm:test"
    
    # Message/Conversation permissions
    MESSAGE_VIEW = "message:view"
    MESSAGE_CREATE = "message:create"
    MESSAGE_UPDATE = "message:update"
    MESSAGE_DELETE = "message:delete"
    MESSAGE_ASSIGN = "message:assign"
    
    # Analytics permissions
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"
    
    # System permissions
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_AUDIT = "system:audit"


class RoleType(str, Enum):
    """Predefined role types"""
    SUPER_ADMIN = "super_admin"  # System-wide admin
    COMPANY_ADMIN = "company_admin"  # Company-level admin
    BRAND_ADMIN = "brand_admin"  # Brand-level admin
    TEAM_LEAD = "team_lead"  # Team supervisor
    AGENT = "agent"  # Customer service agent
    ANALYST = "analyst"  # Data analyst
    VIEWER = "viewer"  # Read-only access
    CUSTOM = "custom"  # Custom role


class RoleScope(str, Enum):
    """Scope of role application"""
    SYSTEM = "system"  # System-wide
    COMPANY = "company"  # Company-wide
    BRAND = "brand"  # Brand-specific
    TEAM = "team"  # Team-specific


class Permission(BaseModel):
    """Individual permission"""
    type: PermissionType
    resource_id: Optional[str] = Field(None, description="Specific resource ID if permission is resource-specific")
    conditions: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional conditions for permission")
    granted_at: datetime = Field(default_factory=datetime.utcnow)
    granted_by: Optional[str] = None


class RoleCreate(BaseModel):
    """Schema for creating a new role"""
    company_id: Optional[str] = Field(None, description="Company ID (null for system roles)")
    name: str = Field(..., min_length=2, max_length=50, description="Role name")
    display_name: str = Field(..., min_length=2, max_length=100, description="User-friendly role name")
    role_type: RoleType = Field(default=RoleType.CUSTOM)
    scope: RoleScope
    
    # Permissions
    permissions: List[PermissionType] = Field(default_factory=list)
    
    # Scope restrictions
    brand_ids: Optional[List[str]] = Field(None, description="Specific brands this role applies to")
    team_ids: Optional[List[str]] = Field(None, description="Specific teams this role applies to")
    
    # Settings
    is_system_role: bool = Field(default=False, description="System-defined role that cannot be deleted")
    is_active: bool = Field(default=True)
    can_be_delegated: bool = Field(default=False, description="Can users with this role assign it to others")
    max_users: Optional[int] = Field(None, ge=1, description="Maximum users that can have this role")
    
    # Additional
    description: Optional[str] = Field(None, max_length=500)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RoleUpdate(BaseModel):
    """Schema for updating a role"""
    display_name: Optional[str] = Field(None, min_length=2, max_length=100)
    
    # Permissions
    permissions: Optional[List[PermissionType]] = None
    
    # Scope restrictions
    brand_ids: Optional[List[str]] = None
    team_ids: Optional[List[str]] = None
    
    # Settings
    is_active: Optional[bool] = None
    can_be_delegated: Optional[bool] = None
    max_users: Optional[int] = Field(None, ge=1)
    
    # Additional
    description: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = None


class RoleResponse(BaseModel):
    """Schema for role response"""
    id: str = Field(..., alias="_id")
    company_id: Optional[str] = None
    company_name: Optional[str] = None  # Populated from lookup
    
    name: str
    display_name: str
    role_type: RoleType
    scope: RoleScope
    
    # Permissions
    permissions: List[PermissionType]
    effective_permissions: Optional[List[PermissionType]] = None  # Including inherited
    
    # Scope restrictions
    brand_ids: Optional[List[str]] = None
    brand_names: Optional[List[str]] = None  # Populated from lookup
    team_ids: Optional[List[str]] = None
    team_names: Optional[List[str]] = None  # Populated from lookup
    
    # Settings
    is_system_role: bool = False
    is_active: bool = True
    can_be_delegated: bool = False
    max_users: Optional[int] = None
    current_users: int = Field(default=0, description="Current number of users with this role")
    
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


class RoleAssignment(BaseModel):
    """Role assignment to a user"""
    role_id: str
    role_name: str
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: str
    expires_at: Optional[datetime] = None
    is_primary: bool = Field(default=False, description="Primary role for the user")
    conditions: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Conditions for role assignment")


class RoleListResponse(BaseModel):
    """Response for role list with pagination"""
    roles: List[RoleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Predefined role templates with default permissions
ROLE_TEMPLATES = {
    RoleType.SUPER_ADMIN: {
        "display_name": "Super Administrator",
        "scope": RoleScope.SYSTEM,
        "permissions": [p for p in PermissionType],  # All permissions
        "is_system_role": True,
        "description": "Full system access with all permissions"
    },
    RoleType.COMPANY_ADMIN: {
        "display_name": "Company Administrator",
        "scope": RoleScope.COMPANY,
        "permissions": [
            PermissionType.COMPANY_VIEW,
            PermissionType.COMPANY_UPDATE,
            PermissionType.BRAND_VIEW,
            PermissionType.BRAND_CREATE,
            PermissionType.BRAND_UPDATE,
            PermissionType.BRAND_DELETE,
            PermissionType.USER_VIEW,
            PermissionType.USER_CREATE,
            PermissionType.USER_UPDATE,
            PermissionType.USER_DELETE,
            PermissionType.USER_ASSIGN_ROLE,
            PermissionType.AGENT_VIEW,
            PermissionType.AGENT_CREATE,
            PermissionType.AGENT_UPDATE,
            PermissionType.AGENT_DELETE,
            PermissionType.KNOWLEDGE_VIEW,
            PermissionType.KNOWLEDGE_CREATE,
            PermissionType.KNOWLEDGE_UPDATE,
            PermissionType.KNOWLEDGE_DELETE,
            PermissionType.LLM_VIEW,
            PermissionType.LLM_CREATE,
            PermissionType.LLM_UPDATE,
            PermissionType.LLM_DELETE,
            PermissionType.ANALYTICS_VIEW,
            PermissionType.ANALYTICS_EXPORT
        ],
        "is_system_role": True,
        "description": "Full company access with administrative permissions"
    },
    RoleType.BRAND_ADMIN: {
        "display_name": "Brand Administrator",
        "scope": RoleScope.BRAND,
        "permissions": [
            PermissionType.BRAND_VIEW,
            PermissionType.BRAND_UPDATE,
            PermissionType.USER_VIEW,
            PermissionType.USER_CREATE,
            PermissionType.USER_UPDATE,
            PermissionType.AGENT_VIEW,
            PermissionType.AGENT_CREATE,
            PermissionType.AGENT_UPDATE,
            PermissionType.KNOWLEDGE_VIEW,
            PermissionType.KNOWLEDGE_CREATE,
            PermissionType.KNOWLEDGE_UPDATE,
            PermissionType.MESSAGE_VIEW,
            PermissionType.MESSAGE_ASSIGN,
            PermissionType.ANALYTICS_VIEW
        ],
        "is_system_role": True,
        "description": "Brand-level administrative access"
    },
    RoleType.TEAM_LEAD: {
        "display_name": "Team Lead",
        "scope": RoleScope.TEAM,
        "permissions": [
            PermissionType.USER_VIEW,
            PermissionType.AGENT_VIEW,
            PermissionType.AGENT_EXECUTE,
            PermissionType.MESSAGE_VIEW,
            PermissionType.MESSAGE_UPDATE,
            PermissionType.MESSAGE_ASSIGN,
            PermissionType.KNOWLEDGE_VIEW,
            PermissionType.ANALYTICS_VIEW
        ],
        "is_system_role": True,
        "description": "Team supervision and management"
    },
    RoleType.AGENT: {
        "display_name": "Customer Service Agent",
        "scope": RoleScope.BRAND,
        "permissions": [
            PermissionType.AGENT_VIEW,
            PermissionType.AGENT_EXECUTE,
            PermissionType.MESSAGE_VIEW,
            PermissionType.MESSAGE_CREATE,
            PermissionType.MESSAGE_UPDATE,
            PermissionType.KNOWLEDGE_VIEW
        ],
        "is_system_role": True,
        "description": "Customer service operations"
    },
    RoleType.ANALYST: {
        "display_name": "Data Analyst",
        "scope": RoleScope.COMPANY,
        "permissions": [
            PermissionType.BRAND_VIEW,
            PermissionType.AGENT_VIEW,
            PermissionType.MESSAGE_VIEW,
            PermissionType.KNOWLEDGE_VIEW,
            PermissionType.ANALYTICS_VIEW,
            PermissionType.ANALYTICS_EXPORT
        ],
        "is_system_role": True,
        "description": "Analytics and reporting access"
    },
    RoleType.VIEWER: {
        "display_name": "Viewer",
        "scope": RoleScope.COMPANY,
        "permissions": [
            PermissionType.BRAND_VIEW,
            PermissionType.USER_VIEW,
            PermissionType.AGENT_VIEW,
            PermissionType.MESSAGE_VIEW,
            PermissionType.KNOWLEDGE_VIEW
        ],
        "is_system_role": True,
        "description": "Read-only access"
    }
}