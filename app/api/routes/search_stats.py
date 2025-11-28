"""
Search Statistics API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime

from app.models.search_stats import (
    SearchStatCreate,
    SearchStat,
    SearchTrend,
    SearchAnalytics,
    SearchContext
)
from app.services.search_stats_service import search_stats_service
from app.api.middleware.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search-stats", tags=["search-stats"])


@router.post("/record", response_model=SearchStat)
async def record_search(
    search_data: SearchStatCreate,
    current_user: dict = Depends(get_current_user)
):
    """Record a new search query"""
    try:
        # Add user info to search data
        search_data.user_id = current_user.get("id", "anonymous")
        search_data.brand_id = current_user.get("brand_id", "default-brand")
        
        result = await search_stats_service.record_search(search_data)
        return result
    except Exception as e:
        logger.error(f"Error recording search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/popular", response_model=List[SearchTrend])
async def get_popular_searches(
    context: Optional[SearchContext] = None,
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get popular search queries"""
    try:
        brand_id = current_user.get("brand_id", "default-brand")
        trends = await search_stats_service.get_popular_searches(
            brand_id=brand_id,
            context=context,
            days=days,
            limit=limit
        )
        return trends
    except Exception as e:
        logger.error(f"Error getting popular searches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/recent", response_model=List[SearchStat])
async def get_recent_searches(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get recent search queries"""
    try:
        brand_id = current_user.get("brand_id", "default-brand")
        user_id = current_user.get("id")
        
        searches = await search_stats_service.get_recent_searches(
            brand_id=brand_id,
            user_id=user_id,
            limit=limit
        )
        return searches
    except Exception as e:
        logger.error(f"Error getting recent searches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/no-results", response_model=List[str])
async def get_no_results_queries(
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get queries that returned no results"""
    try:
        brand_id = current_user.get("brand_id", "default-brand")
        queries = await search_stats_service.get_no_results_queries(
            brand_id=brand_id,
            days=days,
            limit=limit
        )
        return queries
    except Exception as e:
        logger.error(f"Error getting no results queries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/analytics", response_model=SearchAnalytics)
async def get_search_analytics(
    days: int = Query(default=30, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive search analytics"""
    try:
        brand_id = current_user.get("brand_id", "default-brand")
        analytics = await search_stats_service.get_search_analytics(
            brand_id=brand_id,
            days=days
        )
        return analytics
    except Exception as e:
        logger.error(f"Error getting search analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )