"""
Tag Models for managing master tags/labels
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class TagCategory(str, Enum):
    """Tag categories"""
    GENERAL = "General"
    SENTIMENT = "Sentiment"
    PRIORITY = "Priority"
    TOPIC = "Topic"
    PRODUCT = "Product"
    ISSUE = "Issue"
    CUSTOM = "Custom"


class TagCreate(BaseModel):
    """Schema for creating a new tag"""
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    description: Optional[str] = Field(None, max_length=200, description="Tag description")
    category: TagCategory = Field(default=TagCategory.GENERAL)
    color: str = Field(default="#22d3ee", description="Hex color code")
    enabled: bool = Field(default=True)

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TagUpdate(BaseModel):
    """Schema for updating a tag"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    category: Optional[TagCategory] = None
    color: Optional[str] = None
    enabled: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class TagResponse(BaseModel):
    """Schema for tag response"""
    id: str = Field(..., alias="_id")
    name: str
    description: Optional[str] = None
    category: TagCategory
    color: str
    enabled: bool

    # Usage statistics
    usage_count: int = Field(default=0, description="Number of times tag has been used")
    last_used: Optional[datetime] = None

    # Metadata
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


class TagListResponse(BaseModel):
    """Response for tag list with pagination"""
    tags: List[TagResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
