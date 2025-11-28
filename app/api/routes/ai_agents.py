"""
AI Agents API routes
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status

from app.models.ai_agent import (
    AIAgentCreate,
    AIAgentUpdate,
    AIAgentResponse,
    AIAgentListResponse,
    AIAgentStats
)
from app.services.ai_agent_service import ai_agent_service
from app.api.middleware.auth import get_current_user
from app.models.auth import UserInDB

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/ai-agents",
    tags=["ai-agents"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=AIAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_agent(
    agent_data: AIAgentCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Create a new AI agent"""
    try:
        user_role = current_user.role if hasattr(current_user, 'role') else None
        user_company_id = current_user.company_id if hasattr(current_user, 'company_id') else None
        
        # Check permissions
        if user_role not in ["super_admin", "company_admin", "brand_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create AI agents"
            )
        
        # Always use the user's company_id
        if user_company_id:
            agent_data.company_id = user_company_id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to a company to create AI agents"
            )
        
        agent = await ai_agent_service.create_agent(
            agent_data=agent_data,
            user_id=current_user.id
        )
        return agent
    except Exception as e:
        logger.error(f"Error creating AI agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/", response_model=AIAgentListResponse)
async def list_ai_agents(
    brand_id: Optional[str] = Query(None, description="Filter by brand ID"),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    active_only: bool = Query(False, description="Only return active agents"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: UserInDB = Depends(get_current_user)
):
    """List all AI agents with optional filtering"""
    try:
        user_role = current_user.role if hasattr(current_user, 'role') else None
        user_company_id = current_user.company_id if hasattr(current_user, 'company_id') else None
        
        # If not super admin, filter by user's company
        if user_role != "super_admin":
            company_id = user_company_id
        
        skip = (page - 1) * page_size
        result = await ai_agent_service.list_agents(
            company_id=company_id,
            brand_id=brand_id,
            active_only=active_only,
            skip=skip,
            limit=page_size
        )
        
        return AIAgentListResponse(**result)
    except Exception as e:
        logger.error(f"Error listing AI agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{agent_id}", response_model=AIAgentResponse)
async def get_ai_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific AI agent by ID"""
    try:
        agent = await ai_agent_service.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI agent with ID {agent_id} not found"
            )
        
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{agent_id}", response_model=AIAgentResponse)
async def update_ai_agent(
    agent_id: str,
    agent_data: AIAgentUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an AI agent"""
    try:
        agent = await ai_agent_service.update_agent(
            agent_id=agent_id,
            agent_data=agent_data,
            user_id=current_user["id"]
        )
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI agent with ID {agent_id} not found"
            )
        
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating AI agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an AI agent"""
    try:
        success = await ai_agent_service.delete_agent(agent_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI agent with ID {agent_id} not found"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting AI agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("/{agent_id}/toggle-status", response_model=AIAgentResponse)
async def toggle_agent_status(
    agent_id: str,
    active: bool,
    current_user: dict = Depends(get_current_user)
):
    """Toggle the active status of an AI agent"""
    try:
        agent = await ai_agent_service.toggle_agent_status(agent_id, active)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI agent with ID {agent_id} not found"
            )
        
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling AI agent status {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{agent_id}/stats", response_model=AIAgentStats)
async def get_agent_stats(
    agent_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get statistics for an AI agent"""
    try:
        stats = await ai_agent_service.get_agent_stats(agent_id)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI agent with ID {agent_id} not found"
            )
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI agent stats {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Additional endpoints for brands (mock for now)
@router.get("/brands/list")
async def list_brands(
    current_user: dict = Depends(get_current_user)
):
    """List available brands"""
    # TODO: Implement actual brand listing from MongoDB
    return {
        "brands": [
            {"id": "1", "name": "GreenLife"},
            {"id": "2", "name": "TechCorp"},
            {"id": "3", "name": "BeautyCo"},
            {"id": "4", "name": "CulinaryCo"},
            {"id": "5", "name": "EduCorp"}
        ]
    }


@router.get("/llm-providers/list")
async def list_llm_providers(
    current_user: dict = Depends(get_current_user)
):
    """List available LLM providers"""
    return {
        "providers": [
            {"id": "openai_gpt4", "name": "OpenAI GPT-4", "provider": "openai", "model": "gpt-4"},
            {"id": "openai_gpt35", "name": "OpenAI GPT-3.5", "provider": "openai", "model": "gpt-3.5-turbo"},
            {"id": "anthropic_claude", "name": "Anthropic Claude 3.5", "provider": "anthropic", "model": "claude-3-5-sonnet-20241022"},
            {"id": "anthropic_claude_instant", "name": "Anthropic Claude Instant", "provider": "anthropic", "model": "claude-instant-1.2"},
            {"id": "custom", "name": "Custom LLM", "provider": "custom", "model": "custom"}
        ]
    }


@router.get("/public", response_model=AIAgentListResponse)
async def list_ai_agents_public(
    brand_id: Optional[str] = Query(None, description="Filter by brand ID"),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    active_only: bool = Query(False, description="Only return active agents"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page")
):
    """List all AI agents publicly without authentication"""
    try:
        skip = (page - 1) * page_size
        result = await ai_agent_service.list_agents(
            company_id=company_id,
            brand_id=brand_id,
            active_only=active_only,
            skip=skip,
            limit=page_size
        )

        return AIAgentListResponse(**result)
    except Exception as e:
        logger.error(f"Error listing AI agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )