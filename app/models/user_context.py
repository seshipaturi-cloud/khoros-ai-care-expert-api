"""
User Context Model - Stores user and company information for audit trails
This model is embedded in all other models that need to track user actions
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    """User information captured from requests"""
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    title: Optional[str] = None
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    role_types: Optional[List[str]] = Field(default_factory=list)
    department: Optional[str] = None
    locale: Optional[str] = None


class CompanyInfo(BaseModel):
    """Company information captured from requests"""
    id: Optional[str] = None
    key: Optional[str] = None
    name: Optional[str] = None


class UserContext(BaseModel):
    """Complete user context for audit trails"""
    user: Optional[UserInfo] = None
    company: Optional[CompanyInfo] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
