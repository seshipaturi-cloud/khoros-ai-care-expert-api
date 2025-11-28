from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class FeedbackCategory(str, Enum):
    """Feedback categories matching ic-backend-ui categories"""
    AI_ANALYSIS = "ai_analysis"
    AI_DRAFT_RESPONSE = "ai_draft_response"
    GENERAL = "general"
    OTHER = "other"


class FeedbackStatus(str, Enum):
    """Feedback status"""
    OPEN = "open"
    RESOLVED = "resolved"


class FeedbackBase(BaseModel):
    """Base feedback model"""
    case_id: str = Field(..., description="Case/ticket ID related to the feedback")
    category: FeedbackCategory = Field(..., description="Feedback category")
    description: str = Field(..., description="Feedback description/content")
    agent: Optional[str] = Field(None, description="Agent who submitted the feedback")
    module_id: Optional[str] = Field(None, description="Module ID if applicable")
    widget_uuid: Optional[str] = Field(None, description="Widget UUID if applicable")


class FeedbackCreate(FeedbackBase):
    """Model for creating new feedback"""
    pass


class FeedbackUpdate(BaseModel):
    """Model for updating feedback"""
    category: Optional[FeedbackCategory] = None
    description: Optional[str] = None
    resolved: Optional[bool] = None


class Feedback(FeedbackBase):
    """Complete feedback model with metadata"""
    id: str = Field(..., alias="_id", description="Unique feedback identifier")
    uuid: str = Field(..., description="UUID for feedback")
    timestamp: datetime = Field(..., description="Creation timestamp")
    resolved: bool = Field(default=False, description="Whether feedback is resolved")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "case_id": "CASE-12345",
                "category": "ai_analysis",
                "description": "AI analysis did not capture the customer's frustration level correctly",
                "agent": "john.doe@example.com",
                "module_id": "mod_001",
                "widget_uuid": "widget_123",
                "timestamp": "2025-10-21T10:30:00Z",
                "resolved": False,
                "updated_at": "2025-10-21T10:30:00Z"
            }
        }


class FeedbackListResponse(BaseModel):
    """Response model for feedback list"""
    feedbacks: List[Feedback]
    total: int
    filtered: int


class FeedbackStats(BaseModel):
    """Feedback statistics model"""
    total_feedback: int
    open_feedback: int
    resolved_feedback: int
    by_category: dict
    recent_feedback: List[Feedback]
    resolution_rate: float
    avg_resolution_time: Optional[float] = Field(None, description="Average resolution time in hours")

    class Config:
        json_schema_extra = {
            "example": {
                "total_feedback": 150,
                "open_feedback": 45,
                "resolved_feedback": 105,
                "by_category": {
                    "ai_analysis": 60,
                    "ai_draft_response": 50,
                    "general": 30,
                    "other": 10
                },
                "recent_feedback": [],
                "resolution_rate": 0.70,
                "avg_resolution_time": 24.5
            }
        }
