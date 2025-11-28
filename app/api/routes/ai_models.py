"""
AI Models API Routes
Individual AI models that use LLM providers (separate from provider configurations)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import List, Optional
from app.models.ai_model import (
    AIModelCreate,
    AIModelUpdate,
    AIModelResponse,
    AIModelListResponse,
    AIModelStats,
    AIModelTestResult,
    ModelStatus,
    ModelType
)
from app.services.ai_model_service import ai_model_service
from app.api.middleware.auth import get_current_user
from app.utils.user_context_extractor import get_user_context
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-models", tags=["ai-models"])


@router.post("/", response_model=AIModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    request: Request,
    model_data: AIModelCreate
    # current_user: dict = Depends(get_current_user)  # Temporarily disabled for testing
):
    """Create a new AI model"""
    try:
        # Authentication temporarily disabled for testing
        # user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        # user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)

        # Check permissions - DISABLED
        # if user_role not in ["super_admin", "company_admin"]:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Insufficient permissions to create AI models"
        #     )

        # Extract user context from request
        user_context = get_user_context(request)

        model = await ai_model_service.create_model(
            model_data,
            created_by="system",  # Using default since auth is disabled
            user_context=user_context
        )
        return model

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating AI model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create AI model"
        )


@router.get("/", response_model=AIModelListResponse)
async def list_models(
    company_id: Optional[str] = None,
    provider_id: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    model_type: Optional[ModelType] = None,
    model_status: Optional[ModelStatus] = None,
    enabled: Optional[bool] = None
    # current_user: dict = Depends(get_current_user)  # Temporarily disabled
):
    """List AI models with pagination"""
    try:
        # Authentication temporarily disabled
        # user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        # user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)

        # If not super admin, filter by user's company
        # if user_role != "super_admin":
        #     company_id = user_company_id

        result = await ai_model_service.list_models(
            company_id=company_id,
            provider_id=provider_id,
            page=page,
            page_size=page_size,
            model_type=model_type,
            status=model_status,
            enabled=enabled
        )
        return result

    except Exception as e:
        logger.error(f"Error listing AI models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list AI models"
        )


@router.get("/provider/{provider_id}", response_model=List[AIModelResponse])
async def get_models_by_provider(
    provider_id: str,
    include_inactive: bool = Query(default=False),
    # current_user: dict = Depends(get_current_user)  # Temporarily disabled
):
    """Get all models for a specific LLM provider"""
    try:
        models = await ai_model_service.get_models_by_provider(
            provider_id,
            include_inactive=include_inactive
        )
        return models

    except Exception as e:
        logger.error(f"Error getting models by provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get models"
        )


@router.get("/{model_id}", response_model=AIModelResponse)
async def get_model(
    model_id: str,
    # current_user: dict = Depends(get_current_user)  # Temporarily disabled
):
    """Get an AI model by ID"""
    try:
        model = await ai_model_service.get_model(model_id)

        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )

        # Check permissions
        # user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        # user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)

        # if user_role != "super_admin" and model.company_id != user_company_id:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Access denied to this model"
        #     )

        return model

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get model"
        )


@router.put("/{model_id}", response_model=AIModelResponse)
async def update_model(
    request: Request,
    model_id: str,
    model_data: AIModelUpdate,
    # current_user: dict = Depends(get_current_user)  # Temporarily disabled
):
    """Update an AI model"""
    try:
        # Get existing model to check permissions
        existing = await ai_model_service.get_model(model_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )

        # user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        # user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)

        # Check permissions - DISABLED
        # if user_role not in ["super_admin", "company_admin"]:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Insufficient permissions to update models"
        #     )

        # if user_role != "super_admin" and existing.company_id != user_company_id:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Can only update models for your company"
        #     )

        # Extract user context from request
        user_context = get_user_context(request)

        model = await ai_model_service.update_model(
            model_id,
            model_data,
            updated_by="system",  # Using default since auth is disabled
            user_context=user_context
        )

        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )

        return model

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update model"
        )


@router.delete("/{model_id}")
async def delete_model(
    model_id: str,
    # current_user: dict = Depends(get_current_user)  # Temporarily disabled
):
    """Delete an AI model"""
    try:
        # Get existing model to check permissions
        existing = await ai_model_service.get_model(model_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )

        # user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        # user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)

        # # Check permissions
        # if user_role not in ["super_admin", "company_admin"]:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Insufficient permissions to delete models"
        #     )

        # if user_role != "super_admin" and existing.company_id != user_company_id:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Can only delete models for your company"
        #     )

        success = await ai_model_service.delete_model(model_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )

        return {"message": "Model deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete model"
        )


@router.post("/{model_id}/toggle", response_model=AIModelResponse)
async def toggle_model(
    model_id: str,
    # current_user: dict = Depends(get_current_user)  # Temporarily disabled
):
    """Toggle model enabled/disabled status"""
    try:
        existing = await ai_model_service.get_model(model_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )

        user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)

        if user_role not in ["super_admin", "company_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        if user_role != "super_admin" and existing.company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        model = await ai_model_service.toggle_model(model_id)

        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )

        return model

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle model"
        )


@router.post("/{model_id}/test", response_model=AIModelTestResult)
async def test_model(
    model_id: str,
    # current_user: dict = Depends(get_current_user)  # Temporarily disabled
):
    """Test model connectivity and functionality"""
    try:
        result = await ai_model_service.test_model(model_id)
        return result

    except Exception as e:
        logger.error(f"Error testing model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test model"
        )


@router.get("/{model_id}/stats", response_model=AIModelStats)
async def get_model_stats(
    model_id: str,
    period: str = Query(default="monthly", regex="^(hourly|daily|weekly|monthly)$"),
    # current_user: dict = Depends(get_current_user)  # Temporarily disabled
):
    """Get model statistics"""
    try:
        stats = await ai_model_service.get_model_stats(model_id, period)

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get model stats"
        )


@router.post("/{model_id}/log-usage")
async def log_model_usage(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    success: bool,
    feature_id: Optional[str] = None,
    # current_user: dict = Depends(get_current_user)  # Temporarily disabled
):
    """Log model usage for statistics tracking"""
    try:
        logged = await ai_model_service.log_model_usage(
            model_id,
            input_tokens,
            output_tokens,
            latency_ms,
            success,
            feature_id
        )

        if not logged:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to log usage"
            )

        return {"message": "Usage logged successfully"}

    except Exception as e:
        logger.error(f"Error logging model usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log usage"
        )
