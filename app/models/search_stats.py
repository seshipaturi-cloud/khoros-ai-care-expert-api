"""
Search Statistics Models
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class SearchContext(str, Enum):
    KNOWLEDGE_BASE = "knowledge_base"
    CHATBOT = "chatbot"
    AI_AGENTS = "ai_agents"
    DOCUMENTS = "documents"
    MEDIA = "media"
    WEBSITES = "websites"


class SearchStatCreate(BaseModel):
    """Model for creating a new search stat entry"""
    query: str
    context: SearchContext
    results_count: int = 0
    brand_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchStat(BaseModel):
    """Model for search statistics"""
    id: str = Field(alias="_id")
    query: str
    context: SearchContext
    results_count: int
    brand_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any]
    created_at: datetime
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SearchTrend(BaseModel):
    """Model for search trends"""
    query: str
    count: int
    last_searched: datetime
    avg_results: float
    contexts: List[str]


class SearchAnalytics(BaseModel):
    """Model for search analytics response"""
    total_searches: int
    unique_queries: int
    popular_searches: List[SearchTrend]
    recent_searches: List[SearchStat]
    no_results_queries: List[str]
    search_by_context: Dict[str, int]
    search_by_day: List[Dict[str, Any]]