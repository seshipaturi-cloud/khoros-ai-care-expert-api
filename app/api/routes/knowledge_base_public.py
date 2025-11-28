"""
Public Knowledge Base API routes for aicareexpert (NO AUTHENTICATION)
⚠️ WARNING: These endpoints are NOT protected by authentication.
Use only for development/testing purposes.
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional
import logging
from datetime import datetime

from app.models.knowledge_base import (
    KnowledgeBaseItem,
    KnowledgeBaseItemSummary,
    KnowledgeBaseItemCreate,
    KnowledgeBaseItemUpdate,
    FileUploadResponse,
    SearchQuery,
    SearchResult,
    KnowledgeBaseStats,
    ContentType
)
from app.models.chat import ChatRequest, ChatResponse
from app.services.knowledge_base_service import knowledge_base_service
from app.services.s3_service import s3_service
from app.services.langchain_ingestion_service import langchain_ingestion_service
from app.services.rag_service import get_rag_service
from config.settings import settings
import json

logger = logging.getLogger(__name__)

router = APIRouter(tags=["knowledge-base-public"])

# Mock user for public endpoints
MOCK_USER_ID = "public-user-id"
MOCK_COMPANY_ID = "public-company-id"


async def get_all_active_agent_ids():
    """Get all active AI agent IDs from database for auto-assignment"""
    try:
        from app.services.ai_agent_service import ai_agent_service
        agents = await ai_agent_service.list_agents()
        # Return list of agent IDs (convert ObjectId to string if needed)
        agent_ids = [str(agent.id) if hasattr(agent, 'id') else str(agent['_id']) for agent in agents]
        logger.info(f"Found {len(agent_ids)} active agents for auto-assignment")
        return agent_ids
    except Exception as e:
        logger.warning(f"Failed to get agents for auto-assignment: {e}")
        return []


@router.post("/items", response_model=KnowledgeBaseItem)
async def create_knowledge_base_item_public(
    item: KnowledgeBaseItemCreate,
    background_tasks: BackgroundTasks
):
    """Create a new knowledge base item (NO AUTH - PUBLIC ENDPOINT)"""
    try:
        # Auto-assign all active AI agents from database
        all_agent_ids = await get_all_active_agent_ids()
        if all_agent_ids:
            item.ai_agent_ids = all_agent_ids
            logger.info(f"Auto-assigned {len(all_agent_ids)} agents to knowledge base item")

        created_item = await knowledge_base_service.create_item(
            item_data=item,
            user_id=MOCK_USER_ID,
            company_id=MOCK_COMPANY_ID
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
async def list_knowledge_base_items_public(
    content_type: Optional[ContentType] = None,
    skip: int = 0,
    limit: int = 100
):
    """List knowledge base items (NO AUTH - PUBLIC ENDPOINT)"""
    try:
        items = await knowledge_base_service.list_items(
            company_id=None,  # List all items when no company filter
            brand_id=None,
            content_type=content_type,
            skip=skip,
            limit=limit
        )
        return items
    except Exception as e:
        logger.error(f"Error listing knowledge base items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/items/{item_id}", response_model=KnowledgeBaseItem)
async def get_knowledge_base_item_public(item_id: str):
    """Get a specific knowledge base item (NO AUTH - PUBLIC ENDPOINT)"""
    try:
        item = await knowledge_base_service.get_item(item_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base item {item_id} not found"
            )

        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving knowledge base item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/items/{item_id}", response_model=KnowledgeBaseItem)
async def update_knowledge_base_item_public(
    item_id: str,
    item_update: KnowledgeBaseItemUpdate,
    background_tasks: BackgroundTasks
):
    """Update a knowledge base item (NO AUTH - PUBLIC ENDPOINT)"""
    try:
        existing_item = await knowledge_base_service.get_item(item_id)

        if not existing_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base item {item_id} not found"
            )

        updated_item = await knowledge_base_service.update_item(item_id, item_update)

        # Check if file was updated and trigger re-ingestion
        if item_update.s3_key and item_update.s3_key != existing_item.s3_key:
            if item_update.mime_type or existing_item.mime_type:
                mime_type = item_update.mime_type or existing_item.mime_type
                background_tasks.add_task(
                    langchain_ingestion_service.process_document,
                    item_id=str(updated_item.id),
                    s3_key=item_update.s3_key,
                    mime_type=mime_type
                )
                logger.info(f"Triggered background re-ingestion for updated item {updated_item.id}")

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
async def delete_knowledge_base_item_public(item_id: str):
    """Delete a knowledge base item (NO AUTH - PUBLIC ENDPOINT)"""
    try:
        existing_item = await knowledge_base_service.get_item(item_id)

        if not existing_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base item {item_id} not found"
            )

        # Delete from vector store if indexed
        if existing_item.is_indexed and existing_item.vector_ids:
            try:
                await vector_service.delete_vectors(existing_item.vector_ids)
                logger.info(f"Deleted {len(existing_item.vector_ids)} vectors for item {item_id}")
            except Exception as e:
                logger.warning(f"Failed to delete vectors for item {item_id}: {e}")

        # Delete from S3 if file exists
        if existing_item.s3_key:
            try:
                await s3_service.delete_file(existing_item.s3_key)
                logger.info(f"Deleted S3 file for item {item_id}")
            except Exception as e:
                logger.warning(f"Failed to delete S3 file for item {item_id}: {e}")

        # Delete from database
        await knowledge_base_service.delete_item(item_id)

        return {"message": f"Knowledge base item {item_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting knowledge base item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/upload/presigned-url", response_model=FileUploadResponse)
async def get_presigned_upload_url_public(
    filename: str,
    content_type: str
):
    """Get a presigned URL for file upload (NO AUTH - PUBLIC ENDPOINT)"""
    try:
        presigned_data = await s3_service.generate_presigned_upload_url(
            filename=filename,
            content_type=content_type
        )

        return FileUploadResponse(**presigned_data)
    except Exception as e:
        logger.error(f"Error generating presigned URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/search", response_model=List[SearchResult])
async def search_knowledge_base_public(search_query: SearchQuery):
    """Search knowledge base (NO AUTH - PUBLIC ENDPOINT)"""
    try:
        results = await knowledge_base_service.search(
            query=search_query.query,
            company_id=None,  # Search all when no company filter
            brand_id=search_query.brand_id,
            top_k=search_query.top_k or 10,
            filters=search_query.filters
        )
        return results
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/chat", response_model=ChatResponse)
async def chat_with_knowledge_base_public(chat_request: ChatRequest):
    """Chat with knowledge base (NO AUTH - PUBLIC ENDPOINT)"""
    try:
        rag_service = get_rag_service()

        response = await rag_service.chat(
            message=chat_request.message,
            session_id=chat_request.session_id,
            company_id=MOCK_COMPANY_ID,
            brand_id=chat_request.brand_id,
            chat_history=chat_request.chat_history or [],
            system_prompt=chat_request.system_prompt
        )

        return response
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/stats", response_model=KnowledgeBaseStats)
async def get_knowledge_base_stats_public():
    """Get statistics for knowledge base (NO AUTH - PUBLIC ENDPOINT)"""
    try:
        stats = await knowledge_base_service.get_stats(
            company_id=None,  # Get stats for all when no company filter
            brand_id=None
        )
        return stats
    except Exception as e:
        logger.error(f"Error getting knowledge base stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/embedding-info")
async def get_embedding_configuration_public():
    """Get embedding model configuration (NO AUTH - PUBLIC ENDPOINT)"""
    try:
        return {
            "provider": settings.embedding_provider,
            "model": settings.embedding_model,
            "dimensions": settings.embedding_dimensions
        }
    except Exception as e:
        logger.error(f"Error getting embedding info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/items/{item_id}/ingest")
async def ingest_knowledge_base_item_public(
    item_id: str,
    background_tasks: BackgroundTasks
):
    """Manually trigger ingestion for a knowledge base item (NO AUTH - PUBLIC ENDPOINT)"""
    try:
        item = await knowledge_base_service.get_item(item_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base item {item_id} not found"
            )

        if not item.s3_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item has no file to ingest"
            )

        # Trigger ingestion in background
        background_tasks.add_task(
            langchain_ingestion_service.process_document,
            item_id=item_id,
            s3_key=item.s3_key,
            mime_type=item.mime_type
        )

        return {
            "message": f"Ingestion triggered for item {item_id}",
            "item_id": item_id,
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
async def get_ingestion_status_public(item_id: str):
    """Get ingestion status for a knowledge base item (NO AUTH - PUBLIC ENDPOINT)"""
    try:
        item = await knowledge_base_service.get_item(item_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base item {item_id} not found"
            )

        return {
            "item_id": item_id,
            "is_indexed": item.is_indexed,
            "ingestion_status": item.ingestion_status,
            "ingestion_error": item.ingestion_error,
            "indexed_at": item.indexed_at,
            "vector_count": len(item.vector_ids) if item.vector_ids else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ingestion status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/upload/file", response_model=FileUploadResponse)
async def upload_file_public(
    file: UploadFile,
    file_type: str = "document"
):
    """Upload file and return S3 key (NO AUTH - PUBLIC ENDPOINT)"""
    try:
        from bson import ObjectId
        temp_item_id = str(ObjectId())

        # Generate S3 key
        s3_key = s3_service.generate_s3_key(
            brand_id=MOCK_COMPANY_ID,
            content_type=file_type,
            filename=file.filename,
            item_id=temp_item_id
        )

        # Read file content
        file_content = await file.read()

        # Upload to S3
        success = s3_service.upload_file_from_bytes(
            file_bytes=file_content,
            s3_key=s3_key,
            content_type=file.content_type,
            metadata={
                'company_id': MOCK_COMPANY_ID,
                'temp_item_id': temp_item_id,
                'original_filename': file.filename
            }
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to S3"
            )

        return FileUploadResponse(
            s3_key=s3_key,
            file_size=len(file_content),
            content_type=file.content_type,
            success=True
        )
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/websites", response_model=KnowledgeBaseItem)
async def create_website_public(
    request: Request,
    urls: List[str] = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    crawl_depth: int = Form(1),
    refresh_frequency: str = Form("manual"),
    follow_redirects: bool = Form(True),
    respect_robots_txt: bool = Form(True),
    extract_metadata: bool = Form(True),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Create a website knowledge base item and trigger crawling (NO AUTH - PUBLIC ENDPOINT)"""
    try:
        # Parse agent_ids from form data
        form_data = await request.form()
        agent_ids = []
        metadata_json = {}

        # Extract agent_ids and metadata
        for key, value in form_data.multi_items():
            if key == "ai_agent_ids" or key == "agent_ids":
                agent_ids.append(value)
            elif key == "metadata":
                try:
                    metadata_json = json.loads(value)
                except:
                    pass

        logger.info(f"📌 Creating website (public) with {len(urls)} URLs")

        # Auto-assign all active AI agents from database
        all_agent_ids = await get_all_active_agent_ids()
        if all_agent_ids:
            agent_ids = all_agent_ids
            logger.info(f"Auto-assigned {len(all_agent_ids)} agents to website")

        # Create the knowledge base item
        item_data = KnowledgeBaseItemCreate(
            title=title,
            description=description,
            content_type=ContentType.WEBSITE,
            company_id=MOCK_COMPANY_ID,
            ai_agent_ids=agent_ids if agent_ids else [],
            metadata={
                **metadata_json,
                "urls": urls,
                "crawl_depth": crawl_depth,
                "refresh_frequency": refresh_frequency,
                "follow_redirects": follow_redirects,
                "respect_robots_txt": respect_robots_txt,
                "extract_metadata": extract_metadata
            },
            processing_options={
                "auto_index": True,
                "enable_ocr": False,
                "extract_metadata": extract_metadata,
                "generate_embeddings": True
            }
        )

        created_item = await knowledge_base_service.create_item(
            item_data=item_data,
            user_id=MOCK_USER_ID,
            company_id=MOCK_COMPANY_ID
        )

        # Update with website_url field
        from app.services.knowledge_base_service import knowledge_base_service
        await knowledge_base_service.collection.update_one(
            {"_id": str(created_item.id)},
            {"$set": {"website_url": urls[0] if len(urls) == 1 else urls}}
        )

        # Trigger website crawling in background
        from app.services.website_ingestion_service import website_ingestion_service
        background_tasks.add_task(
            website_ingestion_service.process_website,
            item_id=str(created_item.id),
            urls=urls,
            crawl_depth=crawl_depth,
            follow_redirects=follow_redirects,
            extract_metadata=extract_metadata,
            force_crawler=None
        )

        logger.info(f"✅ Created website item {created_item.id} (public)")

        return created_item
    except Exception as e:
        logger.error(f"Error creating website item (public): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/youtube/process")
async def process_youtube_public(
    youtube_url: str = Form(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    extract_captions: bool = Form(True),
    extract_transcript: bool = Form(True),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Process a YouTube video URL (NO AUTH - PUBLIC ENDPOINT)"""
    try:
        from app.services.youtube_service import youtube_service

        # Auto-assign all active AI agents from database
        all_agent_ids = await get_all_active_agent_ids()
        logger.info(f"Auto-assigned {len(all_agent_ids)} agents to YouTube video")

        # Parse metadata from form if sent
        metadata_json = {}

        # Create the knowledge base item first
        item_data = KnowledgeBaseItemCreate(
            title=title or f"YouTube Video - {youtube_url}",
            description=description or f"YouTube video from: {youtube_url}",
            content_type=ContentType.MEDIA,
            company_id=MOCK_COMPANY_ID,
            ai_agent_ids=all_agent_ids,
            metadata={
                **metadata_json,
                "youtube_url": youtube_url,
                "media_type": "youtube_video",
                "extract_captions": extract_captions,
                "extract_transcript": extract_transcript
            },
            processing_options={
                "auto_index": True,
                "generate_embeddings": True
            }
        )

        created_item = await knowledge_base_service.create_item(
            item_data=item_data,
            user_id=MOCK_USER_ID,
            company_id=MOCK_COMPANY_ID
        )

        # Trigger YouTube processing in background
        background_tasks.add_task(
            youtube_service.process_youtube_video,
            item_id=str(created_item.id),
            youtube_url=youtube_url,
            extract_captions=extract_captions,
            extract_transcript=extract_transcript
        )

        logger.info(f"✅ Created YouTube item {created_item.id} and triggered processing")

        return created_item
    except Exception as e:
        logger.error(f"Error processing YouTube video (public): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/items/{item_id}/download")
async def get_download_url_public(item_id: str):
    """Get a presigned download URL for a file (NO AUTH - PUBLIC ENDPOINT)"""
    try:
        # Get item
        item = await knowledge_base_service.get_item(item_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base item {item_id} not found"
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
            filename=safe_filename,
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
async def get_preview_url_public(item_id: str):
    """Get a presigned preview URL for a file (NO AUTH - PUBLIC ENDPOINT)"""
    try:
        # Get item
        item = await knowledge_base_service.get_item(item_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base item {item_id} not found"
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
            filename=safe_filename,
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


@router.post("/analyze-file")
async def analyze_file_public(file: UploadFile = File(...)):
    """Analyze a file using AI to extract metadata (NO AUTH - PUBLIC ENDPOINT)"""
    try:
        # Read file content (limit to first 10KB for analysis)
        content = await file.read(10240)
        await file.seek(0)

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
3. summary: A comprehensive summary (3-5 sentences) covering the main points, key topics, and important information
4. tags: An array of 3-5 relevant tags
5. language: The primary language code (e.g., "en", "es", "fr")
6. category: Choose from: brand-guidelines, tutorial, documentation, faq, guide, policy, marketing, technical, report, presentation, whitepaper, blog, news, support, training, demo

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
        try:
            analysis = json.loads(response.content[0].text)
        except:
            # Fallback if parsing fails
            analysis = {
                "title": file.filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title(),
                "description": f"Content from {file.filename}",
                "summary": f"This document contains content from {file.filename}.",
                "tags": ["uploaded", "document"],
                "language": "en",
                "category": "documentation"
            }

        # Ensure all fields are present
        analysis.setdefault("title", file.filename)
        analysis.setdefault("description", "")
        analysis.setdefault("summary", "")
        analysis.setdefault("tags", [])
        analysis.setdefault("language", "en")
        analysis.setdefault("category", "documentation")

        return {
            "success": True,
            "analysis": analysis,
            "filename": file.filename
        }
    except Exception as e:
        logger.error(f"Error analyzing file: {e}")
        return {
            "success": False,
            "error": str(e),
            "filename": file.filename
        }
