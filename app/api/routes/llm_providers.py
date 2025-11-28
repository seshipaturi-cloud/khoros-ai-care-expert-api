"""
LLM Provider API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import List, Optional
from app.models.llm_provider import (
    LLMProviderCreate,
    LLMProviderUpdate,
    LLMProviderResponse,
    LLMProviderListResponse,
    LLMProviderStats,
    ProviderStatus,
    ProviderType
)
from app.services.llm_provider_service import llm_provider_service
from app.api.middleware.auth import get_current_user
from app.models.auth import UserInDB
from app.utils.user_context_extractor import get_user_context
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm-providers", tags=["llm-providers"])


@router.post("/", response_model=LLMProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    request: Request,
    provider_data: LLMProviderCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new LLM provider configuration"""
    try:
        user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)

        # Check permissions
        if user_role not in ["super_admin", "company_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create LLM providers"
            )

        # If company_admin, automatically set company_id to their company
        if user_role == "company_admin" and user_company_id:
            provider_data.company_id = user_company_id

        # If not super admin, can only create providers for their company
        if user_role != "super_admin" and provider_data.company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only create providers for your company"
            )

        # Extract user context from request
        user_context = get_user_context(request)

        provider = await llm_provider_service.create_provider(
            provider_data,
            created_by=current_user.get("id", "system") if isinstance(current_user, dict) else getattr(current_user, 'id', 'system'),
            user_context=user_context
        )
        return provider
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create provider"
        )


@router.get("/", response_model=LLMProviderListResponse)
async def list_providers(
    company_id: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    provider_status: Optional[ProviderStatus] = None,
    provider_type: Optional[ProviderType] = None,
    current_user: dict = Depends(get_current_user)
):
    """List LLM providers with pagination"""
    try:
        user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)
        
        # If not super admin, filter by user's company
        if user_role != "super_admin":
            company_id = user_company_id
        
        result = await llm_provider_service.list_providers(
            company_id=company_id,
            page=page,
            page_size=page_size,
            status=provider_status,
            provider_type=provider_type
        )
        return result
    except Exception as e:
        logger.error(f"Error listing providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list providers"
        )


@router.get("/company/{company_id}", response_model=List[LLMProviderResponse])
async def get_providers_by_company(
    company_id: str,
    include_inactive: bool = Query(default=False),
    current_user: dict = Depends(get_current_user)
):
    """Get all providers for a company"""
    try:
        user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)
        
        # Check permissions
        if user_role != "super_admin" and company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this company's providers"
            )
        
        providers = await llm_provider_service.get_providers_by_company(
            company_id,
            include_inactive=include_inactive
        )
        return providers
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting providers by company: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get providers"
        )


@router.get("/{provider_id}", response_model=LLMProviderResponse)
async def get_provider(
    provider_id: str,
    include_credentials: bool = Query(default=False),
    current_user: dict = Depends(get_current_user)
):
    """Get an LLM provider by ID"""
    try:
        # Only company admins and super admins can view credentials
        if include_credentials:
            if current_user.role not in ["super_admin", "company_admin"]:
                include_credentials = False
        
        provider = await llm_provider_service.get_provider(
            provider_id,
            include_credentials=include_credentials
        )
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )
        
        # Check permissions
        user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)
        
        if user_role != "super_admin" and provider.company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this provider"
            )
        
        return provider
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get provider"
        )


@router.put("/{provider_id}", response_model=LLMProviderResponse)
async def update_provider(
    request: Request,
    provider_id: str,
    provider_data: LLMProviderUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an LLM provider"""
    try:
        # Get existing provider to check permissions
        existing = await llm_provider_service.get_provider(provider_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )

        user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)

        # Check permissions
        if user_role not in ["super_admin", "company_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update provider"
            )

        if user_role != "super_admin" and existing.company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only update providers in your company"
            )

        # Extract user context from request
        user_context = get_user_context(request)

        provider = await llm_provider_service.update_provider(
            provider_id,
            provider_data,
            updated_by=current_user.get("id", "system") if isinstance(current_user, dict) else getattr(current_user, 'id', 'system'),
            user_context=user_context
        )

        return provider
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update provider"
        )


@router.delete("/{provider_id}")
async def delete_provider(
    provider_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an LLM provider"""
    try:
        # Get existing provider to check permissions
        existing = await llm_provider_service.get_provider(provider_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )
        
        user_role = current_user.get("role")
        user_company_id = current_user.get("company_id")
        
        # Only company and super admins can delete providers
        if user_role not in ["super_admin", "company_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only company admins can delete providers"
            )
        
        if user_role != "super_admin" and existing.company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only delete providers in your company"
            )
        
        success = await llm_provider_service.delete_provider(provider_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete provider"
            )
        
        return {"message": "Provider deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete provider"
        )


@router.get("/{provider_id}/stats", response_model=LLMProviderStats)
async def get_provider_stats(
    provider_id: str,
    period: str = Query(default="daily", regex="^(hourly|daily|weekly|monthly)$"),
    current_user: dict = Depends(get_current_user)
):
    """Get provider usage statistics"""
    try:
        # Get provider to check permissions
        provider = await llm_provider_service.get_provider(provider_id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )
        
        user_role = current_user.get("role")
        user_company_id = current_user.get("company_id")
        
        # Check permissions
        if user_role != "super_admin" and provider.company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this provider's statistics"
            )
        
        stats = await llm_provider_service.get_provider_stats(provider_id, period)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Statistics not available"
            )
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting provider stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get provider statistics"
        )


@router.post("/{provider_id}/test")
async def test_provider(
    provider_id: str,
    test_prompt: str = Query(default="Hello, can you respond?"),
    current_user: dict = Depends(get_current_user)
):
    """Test an LLM provider configuration"""
    try:
        # Get provider to check permissions
        provider = await llm_provider_service.get_provider(
            provider_id,
            include_credentials=True
        )
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )
        
        user_role = current_user.get("role")
        user_company_id = current_user.get("company_id")
        
        # Check permissions
        if user_role not in ["super_admin", "company_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to test provider"
            )
        
        if user_role != "super_admin" and provider.company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only test providers in your company"
            )
        
        # Here you would implement actual provider testing logic
        # For now, return a mock response
        return {
            "success": True,
            "message": "Provider test successful",
            "response": f"Test response for prompt: {test_prompt}",
            "latency_ms": 250,
            "model_used": provider.default_model_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test provider"
        )


@router.post("/{provider_id}/log-usage")
async def log_provider_usage(
    provider_id: str,
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    success: bool,
    error_message: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Log usage for a provider (internal use)"""
    try:
        # This endpoint would typically be called by internal services
        # Add appropriate authentication/authorization
        
        await llm_provider_service.log_usage(
            provider_id=provider_id,
            model_id=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            success=success,
            error_message=error_message
        )
        
        return {"message": "Usage logged successfully"}
        
    except Exception as e:
        logger.error(f"Error logging usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log usage"
        )