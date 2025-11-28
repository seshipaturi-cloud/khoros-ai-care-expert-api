"""
Tags API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.models.tag import (
    TagCreate,
    TagUpdate,
    TagResponse,
    TagListResponse,
    TagCategory
)
from app.services.tag_service import tag_service
from app.api.middleware.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    # current_user: dict = Depends(get_current_user)  # Auth disabled
):
    """Create a new tag"""
    try:
        tag = await tag_service.create_tag(
            tag_data,
            created_by="system"  # created_by=current_user.get("id", "system")
        )
        return tag

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating tag: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tag"
        )


@router.get("/", response_model=TagListResponse)
async def list_tags(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    category: Optional[TagCategory] = None,
    enabled: Optional[bool] = None,
    search: Optional[str] = None,
    # current_user: dict = Depends(get_current_user)  # Auth disabled
):
    """List tags with pagination"""
    try:
        result = await tag_service.list_tags(
            page=page,
            page_size=page_size,
            category=category,
            enabled=enabled,
            search=search
        )
        return result

    except Exception as e:
        logger.error(f"Error listing tags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tags"
        )


@router.get("/popular", response_model=List[TagResponse])
async def get_popular_tags(
    limit: int = Query(default=10, ge=1, le=50),
    # current_user: dict = Depends(get_current_user)  # Auth disabled
):
    """Get most popular tags by usage"""
    try:
        tags = await tag_service.get_popular_tags(limit=limit)
        return tags

    except Exception as e:
        logger.error(f"Error getting popular tags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get popular tags"
        )


@router.get("/category/{category}", response_model=List[TagResponse])
async def get_tags_by_category(
    category: TagCategory,
    # current_user: dict = Depends(get_current_user)  # Auth disabled
):
    """Get all tags in a specific category"""
    try:
        tags = await tag_service.get_tags_by_category(category)
        return tags

    except Exception as e:
        logger.error(f"Error getting tags by category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tags by category"
        )


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: str,
    # current_user: dict = Depends(get_current_user)  # Auth disabled
):
    """Get a tag by ID"""
    try:
        tag = await tag_service.get_tag(tag_id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag {tag_id} not found"
            )
        return tag

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tag {tag_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tag"
        )


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: str,
    tag_data: TagUpdate,
    # current_user: dict = Depends(get_current_user)  # Auth disabled
):
    """Update a tag"""
    try:
        tag = await tag_service.update_tag(
            tag_id,
            tag_data,
            updated_by="system"  # updated_by=current_user.get("id", "system")
        )
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag {tag_id} not found"
            )
        return tag

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tag {tag_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tag"
        )


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: str,
    # current_user: dict = Depends(get_current_user)  # Auth disabled
):
    """Delete a tag"""
    try:
        success = await tag_service.delete_tag(tag_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag {tag_id} not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tag {tag_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete tag"
        )


@router.post("/{tag_id}/toggle", response_model=TagResponse)
async def toggle_tag(
    tag_id: str,
    # current_user: dict = Depends(get_current_user)  # Auth disabled
):
    """Toggle tag enabled/disabled status"""
    try:
        tag = await tag_service.toggle_tag(tag_id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag {tag_id} not found"
            )
        return tag

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling tag {tag_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle tag"
        )


@router.post("/{tag_id}/increment-usage", status_code=status.HTTP_200_OK)
async def increment_tag_usage(
    tag_id: str,
    # current_user: dict = Depends(get_current_user)  # Auth disabled
):
    """Increment tag usage count"""
    try:
        success = await tag_service.increment_usage(tag_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag {tag_id} not found"
            )
        return {"message": "Tag usage incremented successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error incrementing tag usage {tag_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to increment tag usage"
        )
