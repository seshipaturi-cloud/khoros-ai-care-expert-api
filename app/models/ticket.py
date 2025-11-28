from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in-progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TicketCategory(str, Enum):
    TECHNICAL = "Technical"
    BILLING = "Billing"
    AI_FEATURES = "AI Features"
    KNOWLEDGE_BASE = "Knowledge Base"
    GENERAL = "General"


class TicketNote(BaseModel):
    id: int
    text: str
    author: str
    timestamp: str


class TicketHistoryEntry(BaseModel):
    action: str
    timestamp: str
    user: str


class TicketCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    priority: TicketPriority = TicketPriority.MEDIUM
    category: TicketCategory = TicketCategory.TECHNICAL


class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assignedTo: Optional[str] = None


class NoteCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


class Ticket(BaseModel):
    id: str
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    category: TicketCategory
    createdAt: str
    updatedAt: str
    assignedTo: str
    notes: List[TicketNote] = []
    history: List[TicketHistoryEntry] = []

    class Config:
        json_schema_extra = {
            "example": {
                "id": "TKT-001",
                "subject": "API Integration Issue",
                "description": "Unable to connect to OpenAI API",
                "status": "open",
                "priority": "high",
                "category": "Technical",
                "createdAt": "2025-10-18 09:30 AM",
                "updatedAt": "2025-10-20 11:45 AM",
                "assignedTo": "Support Team",
                "notes": [],
                "history": []
            }
        }


class TicketListResponse(BaseModel):
    tickets: List[Ticket]
    total: int
    filtered: int
