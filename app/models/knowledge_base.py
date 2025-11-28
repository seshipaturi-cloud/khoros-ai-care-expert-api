from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class ContentType(str, Enum):
    DOCUMENT = "document"
    MEDIA = "media"
    WEBSITE = "website"


class UploadStatus(str, Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"


class IndexingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingOptions(BaseModel):
    auto_index: bool = True
    enable_ocr: bool = False
    extract_metadata: bool = True
    generate_embeddings: bool = True
    chunk_size: int = 1000
    chunk_overlap: int = 200


class FileInfo(BaseModel):
    name: str
    size: int
    s3_key: str
    s3_bucket: str
    mime_type: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class WebsiteConfig(BaseModel):
    url: HttpUrl
    crawl_depth: int = Field(default=1, ge=1, le=5)
    refresh_frequency: str = "manual"  # manual, daily, weekly, monthly
    follow_redirects: bool = True
    respect_robots_txt: bool = True
    extract_metadata: bool = True


class KnowledgeBaseItemCreate(BaseModel):
    title: str
    description: Optional[str] = None
    content_type: ContentType
    company_id: str = Field(..., description="Company ID - content is at company level")
    ai_agent_ids: List[str] = Field(default_factory=list, description="AI agents that can access this content")
    brand_ids: List[str] = Field(default_factory=list, description="Brand IDs that can access this content")
    metadata: Dict[str, Any] = {}
    processing_options: ProcessingOptions = ProcessingOptions()
    website_config: Optional[WebsiteConfig] = None
    # S3 file info if already uploaded
    s3_key: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class KnowledgeBaseItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    ai_agent_ids: Optional[List[str]] = None
    brand_ids: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    indexing_status: Optional[IndexingStatus] = None


class IngestionStats(BaseModel):
    """Statistics from document ingestion/processing"""
    chunks_created: int
    total_characters: int
    estimated_tokens: int
    processing_time_seconds: float
    embedding_provider: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    processed_at: datetime


class KnowledgeBaseItem(BaseModel):
    """Complete knowledge base item stored in knowledge_base_items collection"""
    id: str = Field(alias="_id")
    title: str
    description: Optional[str] = None
    content_type: ContentType
    file: Optional[FileInfo] = None
    website_url: Optional[str] = None
    upload_status: UploadStatus
    indexing_status: IndexingStatus
    indexed_content: Optional[str] = None  # Full content stored here
    metadata: Dict[str, Any]
    company_id: str
    created_by: str
    ai_agent_ids: List[str]
    brand_ids: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    processing_options: ProcessingOptions
    website_config: Optional[WebsiteConfig] = None
    
    # Ingestion/processing statistics
    ingestion_stats: Optional[IngestionStats] = None
    embeddings_processed: Optional[bool] = None
    embeddings_processed_at: Optional[datetime] = None
    total_chunks: Optional[int] = None
    total_tokens: Optional[int] = None
    embedding_provider: Optional[str] = None
    embedding_model: Optional[str] = None
    indexing_error: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class KnowledgeBaseVector(BaseModel):
    """Vector chunk stored in knowledge_base_vectors collection"""
    id: str = Field(alias="_id")
    knowledge_item_id: str  # Reference to parent item in knowledge_base_items
    chunk_index: int  # Index of this chunk in the document
    chunk_text: str  # The actual text chunk
    embeddings: List[float]  # Vector embeddings for this chunk
    
    # Metadata from parent item
    title: str
    content_type: ContentType
    company_id: str
    ai_agent_ids: List[str]
    brand_ids: List[str]
    
    # Chunk-specific metadata
    start_position: int  # Character position in original document
    end_position: int  # Character position in original document
    token_count: int  # Number of tokens in this chunk
    
    # Processing details
    embedding_provider: str
    embedding_model: str
    created_at: datetime
    
    # Additional searchable metadata
    metadata: Dict[str, Any] = {}  # Can include section titles, page numbers, etc.
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class KnowledgeBaseItemSummary(BaseModel):
    """Lightweight version of KnowledgeBaseItem for list responses, excluding large fields"""
    id: str = Field(alias="_id")
    title: str
    description: Optional[str] = None
    content_type: ContentType
    file: Optional[FileInfo] = None
    website_url: Optional[str] = None
    upload_status: UploadStatus
    indexing_status: IndexingStatus
    metadata: Dict[str, Any]
    company_id: str
    created_by: str
    ai_agent_ids: List[str]
    brand_ids: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    processing_options: ProcessingOptions
    website_config: Optional[WebsiteConfig] = None
    
    # Ingestion/processing statistics (without large data)
    ingestion_stats: Optional[IngestionStats] = None
    embeddings_processed: Optional[bool] = None
    embeddings_processed_at: Optional[datetime] = None
    total_chunks: Optional[int] = None
    total_tokens: Optional[int] = None
    embedding_provider: Optional[str] = None
    embedding_model: Optional[str] = None
    indexing_error: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FileUploadResponse(BaseModel):
    upload_url: str
    s3_key: str
    expires_in: int = 3600


class SearchQuery(BaseModel):
    query: str
    company_id: Optional[str] = None
    brand_id: Optional[str] = None  # Keep for backward compatibility
    content_types: Optional[List[ContentType]] = None
    agent_ids: Optional[List[str]] = None
    limit: int = Field(default=10, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class SearchResult(BaseModel):
    item_id: str
    title: str
    content_type: ContentType
    chunk: str
    score: float
    metadata: Dict[str, Any]


class BulkAssignAgents(BaseModel):
    item_ids: List[str]
    agent_ids: Optional[List[str]] = None  # Support both field names
    ai_agent_ids: Optional[List[str]] = None  # Frontend sends this
    operation: str = "add"  # add or replace
    
    def get_agent_ids(self) -> List[str]:
        """Get agent IDs from either field"""
        return self.ai_agent_ids or self.agent_ids or []


class KnowledgeBaseStats(BaseModel):
    total_items: int
    documents: int
    media_files: int
    websites: int
    total_size: int
    indexed_items: int
    processing_items: int
    failed_items: int


# Chat-related models

class ChatSource(BaseModel):
    """Source citation for chat responses"""
    item_id: str
    title: str
    content_type: str
    score: float
    search_type: str
    snippet: str


class ChatRequest(BaseModel):
    """Chat request model"""
    question: str
    session_id: Optional[str] = None
    search_type: str = Field(default="hybrid", description="vector, text, or hybrid")
    content_types: Optional[List[ContentType]] = None
    agent_ids: Optional[List[str]] = None
    search_limit: int = Field(default=5, ge=1, le=20)
    stream: bool = Field(default=False, description="Whether to stream the response")


class ChatMessage(BaseModel):
    """Individual chat message"""
    role: str = Field(description="user or assistant")
    content: str
    timestamp: datetime
    sources: Optional[List[ChatSource]] = None


class ChatResponse(BaseModel):
    """Non-streaming chat response"""
    answer: str
    sources: List[ChatSource]
    session_id: str
    search_type: str
    search_results_count: int
    timestamp: str


class ChatHistoryResponse(BaseModel):
    """Chat history response"""
    session_id: str
    messages: List[ChatMessage]
    total_messages: int


class StreamChunk(BaseModel):
    """Streaming response chunk"""
    type: str = Field(description="sources, content, done, or error")
    content: Optional[str] = None
    sources: Optional[List[ChatSource]] = None
    search_results_count: Optional[int] = None
    session_id: Optional[str] = None
    timestamp: str
    error: Optional[str] = None