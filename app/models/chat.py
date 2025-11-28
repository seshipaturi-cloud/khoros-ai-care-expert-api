"""
Chat models for Knowledge Base RAG
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SearchType(str, Enum):
    VECTOR = "vector"
    TEXT = "text"
    HYBRID = "hybrid"


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    query: str
    session_id: Optional[str] = None
    search_type: SearchType = SearchType.HYBRID
    agent_id: Optional[str] = None
    limit: int = 5


class ChatSource(BaseModel):
    """Source information for chat response"""
    title: str
    type: str
    item_id: str
    url: Optional[str] = None
    file: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    success: bool
    answer: str
    sources: List[ChatSource]
    context_used: int
    search_type: str
    session_id: Optional[str] = None


class ChatMessage(BaseModel):
    """Individual chat message"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime


class ChatSessionCreate(BaseModel):
    """Request to create a new chat session"""
    pass  # No additional fields needed, brand_id and user_id come from auth


class ChatSessionResponse(BaseModel):
    """Response with chat session info"""
    session_id: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    """Response with chat history"""
    session_id: str
    messages: List[ChatMessage]


class StreamChunk(BaseModel):
    """Streaming response chunk"""
    type: str  # "content", "source", "done"
    data: Optional[str] = None
    source: Optional[ChatSource] = None