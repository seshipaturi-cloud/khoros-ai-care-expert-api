from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional
import logging
import boto3
from io import BytesIO
from app.models.knowledge_base import (
    KnowledgeBaseItem,
    KnowledgeBaseItemSummary,
    KnowledgeBaseItemCreate,
    KnowledgeBaseItemUpdate,
    FileUploadResponse,
    SearchQuery,
    SearchResult,
    BulkAssignAgents,
    KnowledgeBaseStats,
    ContentType,
    FileInfo
)
from app.models.chat import (
    ChatRequest,
    ChatResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatHistoryResponse,
    ChatSource
)
from app.services.knowledge_base_service import knowledge_base_service
from app.services.s3_service import s3_service
from app.services.vector_service import vector_service
from app.services.langchain_ingestion_service import langchain_ingestion_service
from app.services.website_ingestion_service import website_ingestion_service
from app.services.rag_service import get_rag_service
from app.services.youtube_service import youtube_service
from app.utils.cache import get_cache_stats, clear_all_caches, cleanup_all_caches
from config.settings import settings
from datetime import datetime
from fastapi import BackgroundTasks
import uuid
import json

logger = logging.getLogger(__name__)

from app.api.middleware.auth import get_current_user

router = APIRouter(tags=["knowledge-base"])


@router.post("/items", response_model=KnowledgeBaseItem)
async def create_knowledge_base_item(
    item: KnowledgeBaseItemCreate,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Create a new knowledge base item and trigger ingestion if file is present"""
    try:
        created_item = await knowledge_base_service.create_item(
            item_data=item,
            user_id=current_user.id,
            company_id=current_user.company_id
        )
        
        # If item has an S3 file, trigger ingestion in background
        if item.s3_key and item.mime_type:
            background_tasks.add_task(
                langchain_ingestion_service.process_document,
                item_id=str(created_item.id),
                s3_key=item.s3_key,
                mime_type=item.mime_type
            )
            logger.info(f"Triggered background ingestion for item {created_item.id}")
        
        return created_item
    except Exception as e:
        logger.error(f"Error creating knowledge base item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/items", response_model=List[KnowledgeBaseItemSummary])
async def list_knowledge_base_items(
    content_type: Optional[ContentType] = None,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user)
):
    """List knowledge base items with optional filtering (excludes large fields like embeddings)"""
    try:
        # Filter by company_id from the current user
        items = await knowledge_base_service.list_items(
            company_id=current_user.company_id,
            brand_id=None,  # Will list all items accessible to user
            content_type=content_type,
            skip=skip,
            limit=limit
        )
        # The service already excludes embeddings, chunks, and indexed_content
        # We return the items using the Summary model which doesn't include these fields
        return items
    except Exception as e:
        logger.error(f"Error listing knowledge base items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/items/{item_id}", response_model=KnowledgeBaseItem)
async def get_knowledge_base_item(
    item_id: str,
    current_user = Depends(get_current_user)
):
    """Get a specific knowledge base item"""
    try:
        item = await knowledge_base_service.get_item(item_id)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base item {item_id} not found"
            )
        
        # Check if user has access to this item
        if item.company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this item"
            )
        
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge base item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/items/{item_id}", response_model=KnowledgeBaseItem)
async def update_knowledge_base_item(
    item_id: str,
    update_data: KnowledgeBaseItemUpdate,
    current_user = Depends(get_current_user)
):
    """Update a knowledge base item"""
    try:
        # Check if item exists and user has access
        existing_item = await knowledge_base_service.get_item(item_id)
        
        if not existing_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base item {item_id} not found"
            )
        
        if existing_item.company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this item"
            )
        
        updated_item = await knowledge_base_service.update_item(item_id, update_data)
        return updated_item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating knowledge base item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/items/{item_id}")
async def delete_knowledge_base_item(
    item_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a knowledge base item and all associated data (S3, MongoDB, Vector Store)"""
    try:
        # Check if item exists and user has access
        existing_item = await knowledge_base_service.get_item(item_id)
        
        if not existing_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base item {item_id} not found"
            )
        
        if existing_item.company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this item"
            )
        
        # Log deletion request
        logger.info(f"User {current_user.id} requesting deletion of item {item_id}")
        
        # Perform comprehensive deletion
        deleted = await knowledge_base_service.delete_item(item_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete item from database. Check logs for partial deletion status."
            )
        
        return {
            "message": f"Item {item_id} and all associated data deleted successfully",
            "deleted_item_id": item_id,
            "deleted_components": ["mongodb", "s3", "vector_store"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting knowledge base item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/upload/presigned-url", response_model=FileUploadResponse)
async def get_presigned_upload_url(
    filename: str = Form(...),
    content_type: str = Form(...),
    file_type: str = Form(...),  # document, media, or website
    current_user = Depends(get_current_user)
):
    """Get a presigned URL for direct S3 upload without creating an item first"""
    try:
        # Generate a unique item ID for the S3 key
        from bson import ObjectId
        temp_item_id = str(ObjectId())
        
        # Generate S3 key
        s3_key = s3_service.generate_s3_key(
            brand_id=current_user.company_id,  # Use company_id for organization
            content_type=file_type,  # This is already a string from Form
            filename=filename,
            item_id=temp_item_id
        )
        
        # Generate presigned URL
        upload_url = s3_service.generate_presigned_upload_url(
            s3_key=s3_key,
            content_type=content_type,
            expires_in=3600,
            metadata={
                'company_id': current_user.company_id,
                'uploaded_by': current_user.id,
                'temp_item_id': temp_item_id
            }
        )
        
        return FileUploadResponse(
            upload_url=upload_url,
            s3_key=s3_key,
            expires_in=3600
        )
    except Exception as e:
        logger.error(f"Error generating presigned URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/upload/server-proxy", response_model=FileUploadResponse)
async def upload_file_server_proxy(
    file: UploadFile = File(...),
    file_type: str = Form(...),  # document, media, or website
    current_user = Depends(get_current_user)
):
    """Upload file through server (avoids CORS issues)"""
    try:
        # Generate a unique item ID for the S3 key
        from bson import ObjectId
        temp_item_id = str(ObjectId())
        
        # Generate S3 key
        s3_key = s3_service.generate_s3_key(
            brand_id=current_user.company_id,  # Using company_id for S3 organization
            content_type=file_type,
            filename=file.filename,
            item_id=temp_item_id
        )
        
        # Read file content
        file_content = await file.read()
        
        # Upload to S3 through server
        success = s3_service.upload_file_from_bytes(
            file_bytes=file_content,
            s3_key=s3_key,
            content_type=file.content_type,
            metadata={
                'company_id': current_user.company_id,
                'uploaded_by': current_user.id,
                'temp_item_id': temp_item_id
            }
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to S3"
            )
        
        logger.info(f"File uploaded to S3 via server proxy: {s3_key}")
        
        return FileUploadResponse(
            upload_url="",  # Not needed for proxy upload
            s3_key=s3_key,
            expires_in=0
        )
    except Exception as e:
        logger.error(f"Error in server proxy upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/upload/request", response_model=FileUploadResponse)
async def request_file_upload(
    item_id: str = Form(...),
    filename: str = Form(...),
    content_type: str = Form(...),
    current_user = Depends(get_current_user)
):
    """Request a presigned URL for file upload"""
    try:
        # Check if item exists and user has access
        item = await knowledge_base_service.get_item(item_id)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base item {item_id} not found"
            )
        
        if item.company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this item"
            )
        
        # Generate S3 key
        s3_key = s3_service.generate_s3_key(
            brand_id=item.company_id,  # Using company_id for S3 organization
            content_type=item.content_type,
            filename=filename,
            item_id=item_id
        )
        
        # Generate presigned URL
        upload_url = s3_service.generate_presigned_upload_url(
            s3_key=s3_key,
            content_type=content_type,
            expires_in=3600,
            metadata={
                'item_id': item_id,
                'company_id': item.company_id,
                'uploaded_by': current_user.id
            }
        )
        
        return FileUploadResponse(
            upload_url=upload_url,
            s3_key=s3_key,
            expires_in=3600
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting file upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/upload/complete")
async def complete_file_upload(
    item_id: str = Form(...),
    s3_key: str = Form(...),
    file_size: int = Form(...),
    current_user = Depends(get_current_user)
):
    """Confirm file upload completion and update item"""
    try:
        # Verify file exists in S3
        file_metadata = s3_service.get_file_metadata(s3_key)
        
        if not file_metadata:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File not found in S3"
            )
        
        # Update item with file info
        file_info = FileInfo(
            name=s3_key.split('/')[-1],
            size=file_size,
            s3_key=s3_key,
            s3_bucket=s3_service.bucket_name,
            mime_type=file_metadata.get('content_type', 'application/octet-stream'),
            uploaded_at=datetime.utcnow()
        )
        
        updated = await knowledge_base_service.update_file_info(item_id, file_info)
        
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update file info"
            )
        
        return {"message": "File upload completed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing file upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/upload/direct", response_model=KnowledgeBaseItem)
async def upload_file_directly(
    file: UploadFile = File(...),
    item_id: str = Form(...),
    current_user = Depends(get_current_user)
):
    """Upload a file directly through the API"""
    try:
        # Check if item exists and user has access
        item = await knowledge_base_service.get_item(item_id)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base item {item_id} not found"
            )
        
        if item.company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this item"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Generate S3 key
        s3_key = s3_service.generate_s3_key(
            brand_id=item.company_id,  # Using company_id for S3 organization
            content_type=item.content_type,
            filename=file.filename,
            item_id=item_id
        )
        
        # Upload to S3
        success = s3_service.upload_file_from_bytes(
            file_bytes=file_content,
            s3_key=s3_key,
            content_type=file.content_type,
            metadata={
                'item_id': item_id,
                'company_id': item.company_id,
                'uploaded_by': current_user.id
            }
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to S3"
            )
        
        # Update item with file info
        file_info = FileInfo(
            name=file.filename,
            size=len(file_content),
            s3_key=s3_key,
            s3_bucket=s3_service.bucket_name,
            mime_type=file.content_type or 'application/octet-stream',
            uploaded_at=datetime.utcnow()
        )
        
        await knowledge_base_service.update_file_info(item_id, file_info)
        
        # Return updated item
        updated_item = await knowledge_base_service.get_item(item_id)
        return updated_item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file directly: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/websites", response_model=KnowledgeBaseItem)
async def create_website_knowledge_item(
    request: Request,
    urls: List[str] = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    crawl_depth: int = Form(1),
    refresh_frequency: str = Form("manual"),
    follow_redirects: bool = Form(True),
    respect_robots_txt: bool = Form(True),
    extract_metadata: bool = Form(True),
    crawler: Optional[str] = Form(None),  # 'firecrawl', 'custom', or None for auto
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user = Depends(get_current_user)
):
    """Create a website knowledge base item and trigger crawling"""
    try:
        # Parse agent_ids from form data
        form_data = await request.form()
        agent_ids = []
        
        # Extract agent_ids - handle ai_agent_ids, agent_ids, and agent_ids[] formats
        for key, value in form_data.multi_items():
            if key == "ai_agent_ids" or key == "agent_ids" or key == "agent_ids[]":
                agent_ids.append(value)
        
        logger.info(f"📌 Creating website with {len(agent_ids)} agent_ids")
        
        # Create the knowledge base item
        item_data = KnowledgeBaseItemCreate(
            title=title,
            description=description,
            content_type=ContentType.WEBSITE,
            company_id=current_user.company_id,
            ai_agent_ids=agent_ids,
            metadata={
                "urls": urls,
                "crawl_depth": crawl_depth,
                "refresh_frequency": refresh_frequency,
                "follow_redirects": follow_redirects,
                "respect_robots_txt": respect_robots_txt,
                "extract_metadata": extract_metadata,
                "crawler": crawler  # Save crawler preference
            },
            processing_options={
                "auto_index": True,
                "enable_ocr": False,
                "extract_metadata": extract_metadata,
                "generate_embeddings": True,
                "chunk_size": 1000,
                "chunk_overlap": 200
            }
        )
        
        # Store website URLs in metadata
        item_data.metadata["website_urls"] = urls
        
        created_item = await knowledge_base_service.create_item(
            item_data=item_data,
            user_id=current_user.id,
            company_id=current_user.company_id
        )
        
        logger.info(f"✅ Created website item {created_item.id} with {len(created_item.ai_agent_ids)} agent_ids")
        
        # Update with website_url field
        await knowledge_base_service.collection.update_one(
            {"_id": str(created_item.id)},
            {"$set": {"website_url": urls[0] if len(urls) == 1 else urls}}
        )
        
        # Trigger website crawling and ingestion in background
        background_tasks.add_task(
            website_ingestion_service.process_website,
            item_id=str(created_item.id),
            urls=urls,
            crawl_depth=crawl_depth,
            follow_redirects=follow_redirects,
            extract_metadata=extract_metadata,
            force_crawler=crawler  # Pass crawler choice
        )
        
        logger.info(f"Created website knowledge item {created_item.id} and triggered crawling")
        
        return created_item
        
    except Exception as e:
        logger.error(f"Error creating website knowledge item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/items/{item_id}/index")
async def index_knowledge_base_item(
    item_id: str,
    content: str = Form(...),
    current_user = Depends(get_current_user)
):
    """Index content for a knowledge base item"""
    try:
        # Process content and generate embeddings
        success = await knowledge_base_service.process_item_content(item_id, content)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to index content"
            )
        
        return {"message": f"Item {item_id} indexed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error indexing knowledge base item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/search", response_model=List[SearchResult])
async def search_knowledge_base(
    search_query: SearchQuery,
    current_user = Depends(get_current_user)
):
    """Search knowledge base using vector similarity"""
    try:
        # Set company_id from user
        search_query.company_id = current_user.company_id
        # Remove brand_id since we're using company-based access control
        search_query.brand_id = None
        
        results = await vector_service.vector_search(
            query=search_query.query,
            company_id=current_user.company_id,
            brand_ids=None,  # No longer using brand filtering in search
            limit=search_query.limit,
            similarity_threshold=search_query.similarity_threshold,
            content_types=search_query.content_types,
            agent_ids=search_query.agent_ids
        )
        
        return [SearchResult(**result) for result in results]
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/search/internal", response_model=List[SearchResult])
async def search_knowledge_base_internal(
    search_query: SearchQuery
):
    """
    Internal search endpoint for knowledge base without authentication.
    This endpoint is intended for internal service-to-service communication only.
    In production, this should be protected by network security or service mesh.
    """
    try:
        logger.info(f"📥 Internal search request received")
        logger.info(f"   Query: {search_query.query[:100]}...")
        logger.info(f"   Company ID: {search_query.company_id}")
        logger.info(f"   Agent IDs: {search_query.agent_ids}")
        logger.info(f"   Content types: {search_query.content_types}")
        logger.info(f"   Limit: {search_query.limit}, Threshold: {search_query.similarity_threshold}")
        
        # For internal search, allow searching across all documents if no company_id provided
        # This helps with finding brand guidelines across the knowledge base
        
        # First try vector search with company_id if provided
        results = await vector_service.vector_search(
            query=search_query.query,
            company_id=search_query.company_id,  # Can be None to search all
            brand_ids=None,  # No longer using brand filtering in search
            limit=search_query.limit,
            similarity_threshold=search_query.similarity_threshold,
            content_types=search_query.content_types,
            agent_ids=search_query.agent_ids
        )
        
        logger.info(f"   Vector search returned {len(results)} results")
        
        # If no results and no company_id, do a text search fallback
        if not results and not search_query.company_id:
            logger.info("   No results from vector search and no company_id - trying text search fallback")
            # Simple text search fallback for brand guidelines
            try:
                from app.services.knowledge_base_service import knowledge_base_service
                
                # Get all items and do simple text matching
                all_items = await knowledge_base_service.collection.find({
                    "$or": [
                        {"title": {"$regex": search_query.query, "$options": "i"}},
                        {"description": {"$regex": search_query.query, "$options": "i"}},
                        {"indexed_content": {"$regex": search_query.query, "$options": "i"}}
                    ]
                }).limit(search_query.limit).to_list(search_query.limit)
                
                # Convert to SearchResult format with all required fields
                results = []
                for item in all_items:
                    # Get first chunk text or create from content
                    chunks = item.get("chunks", [])
                    if chunks and len(chunks) > 0:
                        chunk_text = chunks[0].get("text", "") if isinstance(chunks[0], dict) else str(chunks[0])
                    else:
                        # Use indexed_content or description as fallback
                        chunk_text = item.get("indexed_content", item.get("description", ""))[:500]
                    
                    results.append({
                        "item_id": item.get("_id"),
                        "title": item.get("title", "Unknown"),
                        "content_type": item.get("content_type", "unknown"),
                        "chunk": chunk_text,  # String field
                        "score": 1.0,  # Default score for text search
                        "metadata": item.get("metadata", {})  # Required field
                    })
                
                logger.info(f"Text search fallback found {len(results)} results for query: {search_query.query}")
                if results:
                    logger.info(f"   First fallback result: {results[0].get('title', 'Unknown')}")
            except Exception as e:
                logger.error(f"Text search fallback failed: {e}")
        
        # Log final results before returning
        if results:
            logger.info(f"✅ Returning {len(results)} total results")
            logger.info(f"   Top result: {results[0].get('title', 'Unknown')} (score: {results[0].get('score', 0):.3f})")
        else:
            logger.info(f"⚠️ No results found for query: {search_query.query[:50]}...")
        
        return [SearchResult(**result) for result in results]
    except Exception as e:
        logger.error(f"Error in internal knowledge base search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/chat/internal", response_model=ChatResponse)
async def chat_with_knowledge_base_internal(
    chat_request: ChatRequest
):
    """
    Internal chat endpoint for knowledge base without authentication.
    This endpoint is intended for internal service-to-service communication and frontend use.
    """
    try:
        logger.info("📥 Internal chat request received")
        logger.info(f"   Query: {chat_request.query[:100] if chat_request.query else 'None'}...")
        logger.info(f"   Agent ID: {chat_request.agent_id}")
        logger.info(f"   Session ID: {chat_request.session_id}")
        logger.info(f"   Search type: {chat_request.search_type}")
        
        # Use the RAG service to process the chat
        result = await get_rag_service().chat(
            query=chat_request.query,
            company_id=None,  # Will be fetched from agent_id if needed
            session_id=chat_request.session_id,
            agent_id=chat_request.agent_id,
            search_type=chat_request.search_type,
            limit=chat_request.limit
        )
        
        # Convert sources to ChatSource models
        sources = [
            ChatSource(
                title=source.get("title", "Unknown"),
                type=source.get("type", source.get("content_type", "unknown")),
                item_id=source.get("item_id", ""),
                url=source.get("url"),
                file=source.get("file")
            )
            for source in result.get("sources", [])
        ]
        
        return ChatResponse(
            success=result.get("success", False),
            answer=result.get("answer", ""),
            sources=sources,
            session_id=result.get("session_id"),
            search_type=result.get("search_type", "hybrid"),
            context_used=result.get("context_used", 0),
            timestamp=result.get("timestamp")
        )
        
    except Exception as e:
        logger.error(f"Error in internal chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/answer/internal")
async def generate_knowledge_base_answer_internal(
    query: SearchQuery
):
    """
    Internal RAG answer generation endpoint without authentication.
    Returns a synthesized answer from knowledge base documents instead of raw documents.
    This endpoint is intended for internal service-to-service communication only.
    """
    try:
        logger.info(f"📝 Internal RAG answer request received")
        logger.info(f"   Query: {query.query[:100]}...")
        logger.info(f"   Company ID: {query.company_id}")
        logger.info(f"   Agent IDs: {query.agent_ids}")
        
        # Initialize RAG service
        rag = get_rag_service()
        
        # Use the chat method which performs search and generates answer
        result = await rag.chat(
            query=query.query,
            company_id=query.company_id,
            agent_ids=query.agent_ids if query.agent_ids else None,
            search_limit=query.limit or 5,
            search_type="vector"  # Use vector search
        )
        
        logger.info(f"✅ RAG answer generated successfully")
        logger.info(f"   Answer length: {len(result.get('answer', ''))} chars")
        logger.info(f"   Sources used: {len(result.get('sources', []))}")
        
        # Return in a format compatible with the AI service expectations
        return {
            "answer": result.get("answer", "No answer could be generated from the knowledge base."),
            "sources": result.get("sources", []),
            "success": result.get("success", False),
            "search_type": "rag_answer"
        }
        
    except Exception as e:
        logger.error(f"Error in RAG answer generation: {e}")
        # Return a structured response even on error
        return {
            "answer": "I couldn't find relevant information in the knowledge base to answer your question.",
            "sources": [],
            "success": False,
            "search_type": "rag_answer",
            "error": str(e)
        }


@router.post("/agents/assign")
async def assign_agents_to_items(
    assignment: BulkAssignAgents,
    current_user = Depends(get_current_user)
):
    """Assign agents to multiple knowledge base items"""
    try:
        # Get agent IDs from either field (ai_agent_ids or agent_ids)
        agent_ids = assignment.get_agent_ids()
        
        modified_count = await knowledge_base_service.assign_agents(
            item_ids=assignment.item_ids,
            agent_ids=agent_ids,
            operation=assignment.operation
        )
        
        return {
            "message": f"Updated {modified_count} items",
            "modified_count": modified_count
        }
    except Exception as e:
        logger.error(f"Error assigning agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/stats", response_model=KnowledgeBaseStats)
async def get_knowledge_base_stats(
    current_user = Depends(get_current_user)
):
    """Get statistics for knowledge base"""
    try:
        stats = await knowledge_base_service.get_stats(
            company_id=current_user.company_id,
            brand_id=None  # No longer using brand_id for filtering
        )
        return stats
    except Exception as e:
        logger.error(f"Error getting knowledge base stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/embedding-info")
async def get_embedding_configuration(
    current_user = Depends(get_current_user)
):
    """Get current embedding provider configuration and status"""
    try:
        info = vector_service.get_embedding_info()
        return {
            "provider": info["provider"],
            "model": info["model"],
            "dimension": info["dimension"],
            "status": info["status"],
            "index_configuration": info.get("index_configuration"),
            "supported_providers": ["openai", "huggingface", "anthropic"],
            "note": "Anthropic doesn't provide embedding models and will fallback to HuggingFace"
        }
    except Exception as e:
        logger.error(f"Error getting embedding configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/items/{item_id}/embedding-compatibility")
async def check_item_embedding_compatibility(
    item_id: str,
    current_user = Depends(get_current_user)
):
    """Check if an item's embeddings are compatible with current configuration"""
    try:
        result = await vector_service.check_embedding_compatibility(item_id)
        return result
    except Exception as e:
        logger.error(f"Error checking embedding compatibility: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )



@router.get("/items/{item_id}/download")
async def get_download_url(
    item_id: str,
    current_user = Depends(get_current_user)
):
    """Get a presigned download URL for a file"""
    try:
        # Get item
        item = await knowledge_base_service.get_item(item_id)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base item {item_id} not found"
            )
        
        if item.company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this item"
            )
        
        if not item.file or not item.file.s3_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file associated with this item"
            )
        
        # Clean filename to remove Unicode characters that cause issues with S3
        import re
        # Remove non-ASCII characters and replace with underscore
        safe_filename = re.sub(r'[^\x00-\x7F]+', '_', item.file.name)
        # Also replace any special space characters
        safe_filename = safe_filename.replace('\u202f', '_').replace('\xa0', '_')
        
        # Generate download URL (with attachment disposition)
        download_url = s3_service.generate_presigned_download_url(
            s3_key=item.file.s3_key,
            expires_in=3600,
            filename=safe_filename,  # Use safe filename
            inline=False  # Force download
        )
        
        return {
            "download_url": download_url,
            "expires_in": 3600,
            "filename": safe_filename
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting download URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/items/{item_id}/preview")
async def get_preview_url(
    item_id: str,
    current_user = Depends(get_current_user)
):
    """Get a presigned preview URL for a file (inline display)"""
    try:
        # Get item
        item = await knowledge_base_service.get_item(item_id)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base item {item_id} not found"
            )
        
        if item.company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this item"
            )
        
        if not item.file or not item.file.s3_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file associated with this item"
            )
        
        # Clean filename to remove Unicode characters that cause issues with S3
        import re
        # Remove non-ASCII characters and replace with underscore
        safe_filename = re.sub(r'[^\x00-\x7F]+', '_', item.file.name)
        # Also replace any special space characters
        safe_filename = safe_filename.replace('\u202f', '_').replace('\xa0', '_')
        
        # Generate preview URL with inline disposition for all files
        preview_url = s3_service.generate_presigned_download_url(
            s3_key=item.file.s3_key,
            expires_in=3600,
            filename=safe_filename,  # Use safe filename
            inline=True,  # Display inline for preview
            content_type=item.file.mime_type  # Add content type for proper browser handling
        )
        
        return {
            "preview_url": preview_url,
            "expires_in": 3600,
            "filename": item.file.name,
            "mime_type": item.file.mime_type,
            "use_proxy": False
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preview URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/items/{item_id}/file")
async def get_file_content(
    item_id: str,
    current_user = Depends(get_current_user)
):
    """Proxy endpoint to serve file content directly from S3 (avoids CORS issues)"""
    try:
        # Get item
        item = await knowledge_base_service.get_item(item_id)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base item {item_id} not found"
            )
        
        if item.company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this item"
            )
        
        if not item.file or not item.file.s3_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file associated with this item"
            )
        
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            aws_session_token=getattr(settings, 'aws_session_token', None),
            region_name=settings.aws_region
        )
        
        try:
            # Get the file from S3
            s3_response = s3_client.get_object(
                Bucket=settings.s3_bucket_name,
                Key=item.file.s3_key
            )
            
            # Read the file content
            file_content = s3_response['Body'].read()
            
            # Return as streaming response with appropriate content type
            # Handle unicode in filename
            import urllib.parse
            safe_filename = urllib.parse.quote(item.file.name.encode('utf-8'))
            
            return StreamingResponse(
                BytesIO(file_content),
                media_type=item.file.mime_type or 'application/octet-stream',
                headers={
                    "Content-Disposition": f"inline; filename*=UTF-8''{safe_filename}",
                    "Cache-Control": "public, max-age=3600",
                    "Access-Control-Allow-Origin": "*"
                }
            )
            
        except Exception as s3_error:
            logger.error(f"Error fetching file from S3: {s3_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve file from storage: {str(s3_error)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving file content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/youtube/process")
async def process_youtube_url(
    youtube_url: str = Form(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    agent_ids: Optional[List[str]] = Form([]),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user = Depends(get_current_user)
):
    """Process a YouTube video URL - download, transcribe, and ingest"""
    try:
        # Create the knowledge base item first
        item_data = KnowledgeBaseItemCreate(
            title=title or f"YouTube Video - {youtube_url}",
            description=description or f"YouTube video from: {youtube_url}",
            content_type=ContentType.MEDIA,
            company_id=current_user.company_id,
            ai_agent_ids=agent_ids or [],
            metadata={
                "youtube_url": youtube_url,
                "media_type": "youtube_video",
                "source": "youtube"
            },
            processing_options={
                "auto_index": True,
                "extract_transcript": True,
                "generate_embeddings": True
            }
        )
        
        # Create the item in database
        created_item = await knowledge_base_service.create_item(
            item_data=item_data,
            user_id=current_user.id,
            company_id=current_user.company_id
        )
        
        item_id = str(created_item.id)
        
        # Process YouTube video in background
        background_tasks.add_task(
            youtube_service.process_youtube_video,
            item_id=item_id,
            youtube_url=youtube_url,
            title=title,
            description=description
        )
        
        logger.info(f"Started YouTube processing for item {item_id}")
        
        return {
            "message": "YouTube video processing started",
            "item_id": item_id,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error processing YouTube URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/items/{item_id}/re-crawl")
async def re_crawl_website(
    item_id: str,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Re-crawl and re-index a website"""
    try:
        # Get the item from MongoDB
        item = await knowledge_base_service.get_item(item_id)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base item {item_id} not found"
            )
        
        # Check if user has access to this item
        if item.company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this item"
            )
        
        # Check if it's a website
        if item.content_type != ContentType.WEBSITE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This endpoint is only for re-crawling websites"
            )
        
        # Extract URLs from metadata
        urls = []
        if item.website_url:
            urls = [item.website_url] if isinstance(item.website_url, str) else item.website_url
        elif item.metadata.get("urls"):
            urls = item.metadata["urls"]
        elif item.metadata.get("website_urls"):
            urls = item.metadata["website_urls"]
        
        if not urls:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No URLs found for this website item"
            )
        
        # Get crawl settings from metadata
        crawl_depth = item.metadata.get("crawl_depth", 1)
        follow_redirects = item.metadata.get("follow_redirects", True)
        extract_metadata = item.metadata.get("extract_metadata", True)
        
        # Trigger website re-crawling in background
        background_tasks.add_task(
            website_ingestion_service.process_website,
            item_id=item_id,
            urls=urls,
            crawl_depth=crawl_depth,
            follow_redirects=follow_redirects,
            extract_metadata=extract_metadata,
            force_crawler=item.metadata.get("crawler", None)  # Use saved crawler preference
        )
        
        logger.info(f"Triggered re-crawl for website {item_id}")
        
        return {"message": f"Website re-crawl started for item {item_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error re-crawling website: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/items/{item_id}/ingest")
async def ingest_knowledge_base_item(
    item_id: str,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Manually trigger ingestion for a knowledge base item"""
    try:
        # Get item
        item = await knowledge_base_service.get_item(item_id)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base item {item_id} not found"
            )
        
        if item.company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this item"
            )
        
        if not item.file or not item.file.s3_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file associated with this item"
            )
        
        # Trigger ingestion in background
        background_tasks.add_task(
            langchain_ingestion_service.process_document,
            item_id=item_id,
            s3_key=item.file.s3_key,
            mime_type=item.file.mime_type or 'text/plain'
        )
        
        return {
            "message": f"Ingestion triggered for item {item_id}",
            "status": "processing"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering ingestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/items/{item_id}/ingestion-status")
async def get_ingestion_status(
    item_id: str,
    current_user = Depends(get_current_user)
):
    """Get the ingestion status and statistics for an item"""
    try:
        # Get item
        item = await knowledge_base_service.get_item(item_id)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base item {item_id} not found"
            )
        
        if item.company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this item"
            )
        
        return {
            "item_id": item_id,
            "indexing_status": item.indexing_status,
            "ingestion_stats": getattr(item, 'ingestion_stats', None),
            "embeddings_processed": getattr(item, 'embeddings_processed', False),
            "embeddings_processed_at": getattr(item, 'embeddings_processed_at', None),
            "chunks_count": len(getattr(item, 'chunks', [])) if hasattr(item, 'chunks') else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ingestion status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/debug/items")
async def debug_list_items(
    current_user = Depends(get_current_user)
):
    """Debug endpoint to list all items with their IDs"""
    try:
        items = await knowledge_base_service.list_items(
            company_id=current_user.company_id,
            brand_id=None,  # No longer using brand_id for filtering
            limit=10
        )
        
        debug_info = []
        for item in items:
            debug_info.append({
                "_id": str(item.id),
                "title": item.title,
                "content_type": item.content_type,
                "indexing_status": item.indexing_status,
                "has_file": bool(item.file),
                "s3_key": item.file.s3_key if item.file else None
            })
        
        return {
            "total_items": len(items),
            "items": debug_info
        }
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============= Chat/RAG Endpoints =============

@router.post("/chat", response_model=ChatResponse)
async def chat_with_knowledge_base(
    chat_request: ChatRequest,
    current_user = Depends(get_current_user)
):
    """Chat with the knowledge base using RAG"""
    try:
        # Use the RAG service to process the chat
        result = await get_rag_service().chat(
            query=chat_request.query,
            company_id=current_user.company_id,
            session_id=chat_request.session_id,
            agent_id=chat_request.agent_id,
            search_type=chat_request.search_type.value,
            limit=chat_request.limit
        )
        
        # Convert sources to ChatSource models
        sources = [
            ChatSource(
                title=source.get("title", "Unknown"),
                type=source.get("type", "unknown"),
                item_id=source.get("item_id", ""),
                url=source.get("url"),
                file=source.get("file")
            )
            for source in result.get("sources", [])
        ]
        
        return ChatResponse(
            success=result.get("success", False),
            answer=result.get("answer", ""),
            sources=sources,
            context_used=result.get("context_used", 0),
            search_type=result.get("search_type", "hybrid"),
            session_id=result.get("session_id")
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/chat/session", response_model=ChatSessionResponse)
async def create_chat_session(
    current_user = Depends(get_current_user)
):
    """Create a new chat session"""
    try:
        session_id = await get_rag_service().create_chat_session(
            company_id=current_user.company_id,
            user_id=current_user.id
        )
        
        return ChatSessionResponse(
            session_id=session_id,
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/chat/session/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Get chat history for a session"""
    try:
        messages = await get_rag_service().get_chat_history(session_id)
        
        return ChatHistoryResponse(
            session_id=session_id,
            messages=messages
        )
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/chat/session/{session_id}/clear")
async def clear_chat_session(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Clear chat history for a session"""
    try:
        success = await get_rag_service().clear_chat_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        return {"message": "Chat session cleared successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing chat session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Chat endpoints

@router.post("/chat", response_model=ChatResponse)
async def chat_with_knowledge_base(
    chat_request: ChatRequest,
    current_user = Depends(get_current_user)
):
    """Chat with the knowledge base using RAG"""
    try:
        # Generate session ID if not provided
        if not chat_request.session_id:
            chat_request.session_id = str(uuid.uuid4())
        
        # Use the RAG service to process the chat
        response = await get_rag_service().chat(
            question=chat_request.question,
            session_id=chat_request.session_id,
            company_id=current_user.company_id,
            search_type=chat_request.search_type,
            content_types=[ct.value for ct in chat_request.content_types] if chat_request.content_types else None,
            agent_ids=chat_request.agent_ids,
            search_limit=chat_request.search_limit
        )
        
        # Convert sources to ChatSource models
        sources = [
            ChatSource(
                item_id=source["item_id"],
                title=source["title"],
                content_type=source["content_type"],
                score=source["score"],
                search_type=source["search_type"],
                snippet=source["snippet"]
            ) for source in response["sources"]
        ]
        
        return ChatResponse(
            answer=response["answer"],
            sources=sources,
            session_id=response["session_id"],
            search_type=response["search_type"],
            search_results_count=response["search_results_count"],
            timestamp=response["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/chat/stream")
async def stream_chat_with_knowledge_base(
    chat_request: ChatRequest,
    current_user = Depends(get_current_user)
):
    """Stream chat with the knowledge base using RAG"""
    try:
        # Generate session ID if not provided
        if not chat_request.session_id:
            chat_request.session_id = str(uuid.uuid4())
        
        async def generate_stream():
            try:
                async for chunk in get_rag_service().stream_chat(
                    question=chat_request.question,
                    session_id=chat_request.session_id,
                    company_id=current_user.company_id,
                    search_type=chat_request.search_type,
                    content_types=[ct.value for ct in chat_request.content_types] if chat_request.content_types else None,
                    agent_ids=chat_request.agent_ids,
                    search_limit=chat_request.search_limit
                ):
                    # Convert sources to ChatSource models if present
                    if chunk.get("type") == "sources" and chunk.get("sources"):
                        sources = [
                            ChatSource(
                                item_id=source["item_id"],
                                title=source["title"],
                                content_type=source["content_type"],
                                score=source["score"],
                                search_type=source["search_type"],
                                snippet=source["snippet"]
                            ).dict() for source in chunk["sources"]
                        ]
                        chunk["sources"] = sources
                    
                    # Yield as Server-Sent Events format
                    yield f"data: {json.dumps(chunk)}\n\n"
                    
            except Exception as e:
                error_chunk = {
                    "type": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        logger.error(f"Error in stream chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/chat/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    limit: int = 20,
    current_user = Depends(get_current_user)
):
    """Get chat history for a session"""
    try:
        messages = await get_rag_service().get_chat_history(
            session_id=session_id,
            company_id=current_user.company_id,
            limit=limit
        )
        
        # Convert to ChatMessage models
        chat_messages = []
        for msg in messages:
            sources = None
            if msg.sources:
                sources = [
                    ChatSource(
                        item_id=source["item_id"],
                        title=source["title"],
                        content_type=source["content_type"],
                        score=source["score"],
                        search_type=source["search_type"],
                        snippet=source["snippet"]
                    ) for source in msg.sources
                ]
            
            chat_messages.append({
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "sources": sources
            })
        
        return ChatHistoryResponse(
            session_id=session_id,
            messages=chat_messages,
            total_messages=len(chat_messages)
        )
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/chat/{session_id}/history")
async def clear_chat_history(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Clear chat history for a session"""
    try:
        success = await get_rag_service().clear_chat_history(
            session_id=session_id,
            brand_id=getattr(current_user, "brand_id", None)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clear chat history"
            )
        
        return {"message": f"Chat history cleared for session {session_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/analyze-file")
async def analyze_file_with_ai(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Analyze a file using AI to extract metadata"""
    try:
        # Read file content (limit to first 10KB for analysis)
        content = await file.read(10240)  # Read first 10KB
        await file.seek(0)  # Reset file pointer
        
        # Convert content to text based on file type
        file_text = ""
        file_type = file.content_type or "text/plain"
        
        if file_type.startswith("text/") or file_type == "application/json":
            try:
                file_text = content.decode('utf-8')
            except:
                file_text = content.decode('latin-1')
        else:
            # For binary files, just use filename and type
            file_text = f"Filename: {file.filename}\nType: {file_type}\n"
            # Try to extract some text if it's a document
            if file_type == "application/pdf":
                file_text += "[PDF document content]"
            elif file_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                               "application/msword"]:
                file_text += "[Word document content]"
        
        # Use Anthropic for analysis
        from anthropic import Anthropic
        anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
        
        # Create prompt for AI analysis
        prompt = f"""Analyze the following file and extract metadata. 
        
File name: {file.filename}
File type: {file_type}
Content preview:
{file_text[:2000]}

Based on this file, provide the following information in JSON format:
1. title: A descriptive title for this content
2. description: A brief description (2-3 sentences) of what this content is about
3. summary: A comprehensive summary (3-5 sentences) covering the main points, key topics, and important information in the content
4. tags: An array of 3-5 relevant tags
5. language: The primary language code (e.g., "en", "es", "fr")
6. category: Choose the most appropriate category from: brand guidelines, tutorial, documentation, faq, guide, policy, marketing, technical, report, presentation, whitepaper, blog, news, support, training, demo

Respond ONLY with valid JSON, no additional text."""

        # Get AI analysis
        response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse the response
        import json
        try:
            analysis = json.loads(response.content[0].text)
            print(analysis)
        except:
            # Fallback if parsing fails
            analysis = {
                "title": file.filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title(),
                "description": f"Content from {file.filename}",
                "summary": f"This document contains content from {file.filename}. Please review the file for detailed information.",
                "tags": ["uploaded", "document"],
                "language": "en",
                "category": "documentation"
            }
        
        # Ensure all required fields are present
        analysis.setdefault("title", file.filename)
        analysis.setdefault("description", "")
        analysis.setdefault("summary", "")
        analysis.setdefault("tags", [])
        analysis.setdefault("language", "en")
        analysis.setdefault("category", "documentation")
        
        return {
            "success": True,
            "analysis": analysis,
            "filename": file.filename,
            "file_type": file_type
        }
        
    except Exception as e:
        logger.error(f"Error analyzing file with AI: {e}")
        # Return default values on error
        return {
            "success": False,
            "error": str(e),
            "analysis": {
                "title": file.filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title(),
                "description": "",
                "summary": "",
                "tags": [],
                "language": "en",
                "category": "documentation"
            },
            "filename": file.filename,
            "file_type": file.content_type or "unknown"
        }


# ============================================================================
# Cache Management Endpoints
# ============================================================================

@router.get("/cache/stats")
async def get_cache_statistics():
    """
    Get statistics for all caches (embedding and search caches)

    Returns cache hit rates, sizes, and performance metrics.
    """
    try:
        stats = get_cache_stats()
        logger.info(f"📊 Cache statistics requested")

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "caches": stats
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache statistics: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_caches():
    """
    Clear all caches (embedding and search caches)

    Use this endpoint when you need to force refresh of all cached data.
    """
    try:
        # Get stats before clearing
        stats_before = get_cache_stats()

        # Clear all caches
        clear_all_caches()
        logger.info(f"🗑️  All caches cleared manually")

        return {
            "success": True,
            "message": "All caches cleared successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "stats_before_clear": stats_before
        }
    except Exception as e:
        logger.error(f"Error clearing caches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear caches: {str(e)}"
        )


@router.post("/cache/cleanup")
async def cleanup_expired_caches():
    """
    Clean up expired entries from all caches

    This removes only expired entries, keeping valid cached data.
    """
    try:
        stats_before = get_cache_stats()

        # Cleanup expired entries
        cleanup_all_caches()
        logger.info(f"🧹 Cleaned up expired cache entries")

        stats_after = get_cache_stats()

        return {
            "success": True,
            "message": "Expired cache entries cleaned up",
            "timestamp": datetime.utcnow().isoformat(),
            "stats_before": stats_before,
            "stats_after": stats_after
        }
    except Exception as e:
        logger.error(f"Error cleaning up caches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup caches: {str(e)}"
        )