"""
Brand API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.models.brand import (
    BrandCreate,
    BrandUpdate,
    BrandResponse,
    BrandListResponse,
    BrandStats,
    BrandStatus
)
from app.services.brand_service import brand_service
from app.api.middleware.auth import get_current_user
from app.models.auth import UserInDB
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/brands", tags=["brands"])


@router.post("/", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    brand_data: BrandCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new brand"""
    try:
        # Check permissions
        user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)
        
        if user_role not in ["super_admin", "company_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create brands"
            )
        
        # If company_admin, automatically set company_id to their company
        if user_role == "company_admin" and user_company_id:
            brand_data.company_id = user_company_id
        
        # If not super admin, can only create brands for their company
        if user_role != "super_admin" and brand_data.company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only create brands for your company"
            )
        
        brand = await brand_service.create_brand(
            brand_data,
            created_by=current_user.get("id", "system") if isinstance(current_user, dict) else getattr(current_user, 'id', 'system')
        )
        return brand
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating brand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create brand"
        )


@router.get("/", response_model=BrandListResponse)
async def list_brands(
    company_id: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    brand_status: Optional[BrandStatus] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List brands with pagination"""
    try:
        user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)
        
        # If not super admin, filter by user's company
        if user_role != "super_admin":
            company_id = user_company_id
        
        result = await brand_service.list_brands(
            company_id=company_id,
            page=page,
            page_size=page_size,
            status=brand_status,
            search=search
        )
        return result
    except Exception as e:
        logger.error(f"Error listing brands: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list brands"
        )


@router.get("/company/{company_id}", response_model=List[BrandResponse])
async def get_brands_by_company(
    company_id: str,
    include_inactive: bool = Query(default=False),
    current_user: dict = Depends(get_current_user)
):
    """Get all brands for a company"""
    try:
        user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)
        
        # Check permissions
        if user_role != "super_admin" and company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this company's brands"
            )
        
        brands = await brand_service.get_brands_by_company(
            company_id,
            include_inactive=include_inactive
        )
        return brands
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting brands by company: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get brands"
        )


@router.get("/company/{company_id}/internal", response_model=List[BrandResponse])
async def get_brands_by_company_internal(
    company_id: str,
    include_inactive: bool = Query(default=False)
):
    """
    Internal endpoint to get brands by company without authentication.
    This endpoint is intended for internal service-to-service communication only.
    In production, this should be protected by network security or service mesh.
    """
    try:
        brands = await brand_service.get_brands_by_company(
            company_id,
            include_inactive=include_inactive
        )
        return brands
    except Exception as e:
        logger.error(f"Error getting brands by company (internal): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get brands"
        )


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a brand by ID"""
    try:
        brand = await brand_service.get_brand(brand_id)
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand not found"
            )
        
        # Check permissions
        user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)
        
        if user_role != "super_admin" and brand.company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this brand"
            )
        
        return brand
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting brand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get brand"
        )


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: str,
    brand_data: BrandUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a brand"""
    try:
        # Get existing brand to check permissions
        existing = await brand_service.get_brand(brand_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand not found"
            )
        
        user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)
        
        # Check permissions
        if user_role not in ["super_admin", "company_admin", "brand_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update brand"
            )
        
        if user_role != "super_admin" and existing.company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only update brands in your company"
            )
        
        # For brand_admin, check if they have access to this specific brand
        if user_role == "brand_admin":
            user_brand_ids = current_user.get("brand_ids", []) if isinstance(current_user, dict) else getattr(current_user, 'brand_ids', [])
            if brand_id not in user_brand_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No access to this brand"
                )
        
        brand = await brand_service.update_brand(
            brand_id,
            brand_data,
            updated_by=current_user.get("id", "system") if isinstance(current_user, dict) else getattr(current_user, 'id', 'system')
        )
        
        return brand
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating brand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update brand"
        )


@router.delete("/{brand_id}")
async def delete_brand(
    brand_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a brand"""
    try:
        # Get existing brand to check permissions
        existing = await brand_service.get_brand(brand_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand not found"
            )
        
        user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)
        
        # Only company and super admins can delete brands
        if user_role not in ["super_admin", "company_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only company admins can delete brands"
            )
        
        if user_role != "super_admin" and existing.company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only delete brands in your company"
            )
        
        success = await brand_service.delete_brand(brand_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete brand"
            )
        
        return {"message": "Brand deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting brand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete brand"
        )


@router.post("/{brand_id}/assign-ai-agent")
async def assign_ai_agent_to_brand(
    brand_id: str,
    ai_agent_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Assign an AI agent to a brand (1:1 relationship)"""
    try:
        # Get brand to check permissions
        brand = await brand_service.get_brand(brand_id)
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand not found"
            )
        
        user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)
        
        # Check permissions
        if user_role not in ["super_admin", "company_admin", "brand_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to assign AI agent"
            )
        
        if user_role != "super_admin" and brand.company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only manage brands in your company"
            )
        
        # Check if brand already has an AI agent
        if brand.ai_agent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Brand already has an AI agent assigned. Each brand can have only one AI agent."
            )
        
        # Verify AI agent exists and belongs to same company
        from app.services.ai_agent_service import ai_agent_service
        agent = await ai_agent_service.get_agent(ai_agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI agent not found"
            )
        
        if agent.company_id != brand.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="AI agent must belong to the same company as the brand"
            )
        
        # Check if AI agent is already assigned to another brand
        if agent.brand_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="AI agent is already assigned to another brand. Each AI agent can only be assigned to one brand."
            )
        
        # Assign AI agent to brand
        await brand_service.assign_ai_agent(brand_id, ai_agent_id, current_user.get("id", "system") if isinstance(current_user, dict) else getattr(current_user, 'id', 'system'))
        
        return {"message": f"AI agent {ai_agent_id} successfully assigned to brand {brand_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning AI agent to brand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign AI agent"
        )


@router.get("/{brand_id}/ai-agent")
async def get_brand_ai_agent(
    brand_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the AI agent for a brand (1:1 relationship)"""
    try:
        # Get brand to check permissions and get agent ID
        brand = await brand_service.get_brand(brand_id)
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand not found"
            )
        
        user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)
        
        # Check permissions
        if user_role != "super_admin" and brand.company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this brand's AI agent"
            )
        
        if not brand.ai_agent_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No AI agent configured for this brand"
            )
        
        # Get AI agent details
        from app.services.ai_agent_service import ai_agent_service
        agent = await ai_agent_service.get_agent(brand.ai_agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI agent not found"
            )
        
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting brand AI agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get brand AI agent"
        )


@router.get("/{brand_id}/stats", response_model=BrandStats)
async def get_brand_stats(
    brand_id: str,
    period: str = Query(default="monthly", regex="^(daily|weekly|monthly)$"),
    current_user: dict = Depends(get_current_user)
):
    """Get brand performance statistics"""
    try:
        # Get brand to check permissions
        brand = await brand_service.get_brand(brand_id)
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand not found"
            )
        
        user_role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)
        user_company_id = current_user.get("company_id") if isinstance(current_user, dict) else getattr(current_user, 'company_id', None)
        
        # Check permissions
        if user_role != "super_admin" and brand.company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this brand's statistics"
            )
        
        stats = await brand_service.get_brand_stats(brand_id, period)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Statistics not available"
            )
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting brand stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get brand statistics"
        )


@router.post("/migrate")
async def migrate_brands(
    current_user: dict = Depends(get_current_user)
):
    """Migrate existing brand references to actual brand documents"""
    try:
        # Only super admins can run migration
        if (current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, 'role', None)) != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admins can run migrations"
            )
        
        success = await brand_service.migrate_existing_brands()
        
        if success:
            return {"message": "Brands migrated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Migration failed"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error migrating brands: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to migrate brands"
        )