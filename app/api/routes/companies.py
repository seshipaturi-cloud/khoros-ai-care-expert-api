"""
Company API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from app.models.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyListResponse,
    CompanyStats,
    CompanyStatus
)
from app.services.company_service import company_service
from app.api.middleware.auth import get_current_user, require_admin, require_permission
from app.models.auth import UserInDB
from app.services.auth_service import auth_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    current_user: UserInDB = Depends(require_admin)
):
    """Create a new company - Only super_admin can create companies"""
    try:
        # Additional check for super_admin
        if not current_user.is_superuser:
            roles = await auth_service.get_user_roles(current_user.id)
            is_super_admin = any(role.get("role_type") == "super_admin" for role in roles)
            if not is_super_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only super admins can create companies"
                )
        
        company = await company_service.create_company(
            company_data,
            created_by=current_user.id
        )
        return company
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating company: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create company"
        )


@router.get("/", response_model=CompanyListResponse)
async def list_companies(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[CompanyStatus] = None,
    search: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_user)
):
    """List all companies with pagination"""
    try:
        # Check if user is super admin
        is_super_admin = current_user.is_superuser
        if not is_super_admin:
            roles = await auth_service.get_user_roles(current_user.id)
            is_super_admin = any(role.get("role_type") == "super_admin" for role in roles)
        
        # Only super admins can list all companies
        if not is_super_admin:
            # Regular users can only see their own company
            company_id = getattr(current_user, 'company_id', None)
            if not company_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User not associated with any company"
                )
            company = await company_service.get_company(company_id)
            if company:
                return CompanyListResponse(
                    companies=[company],
                    total=1,
                    page=1,
                    page_size=1,
                    total_pages=1
                )
            else:
                return CompanyListResponse(
                    companies=[],
                    total=0,
                    page=1,
                    page_size=1,
                    total_pages=0
                )
        
        result = await company_service.list_companies(
            page=page,
            page_size=page_size,
            status=status,
            search=search
        )
        return result
    except Exception as e:
        logger.error(f"Error listing companies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list companies"
        )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get a company by ID"""
    try:
        # Check permissions
        is_super_admin = current_user.is_superuser
        if not is_super_admin:
            roles = await auth_service.get_user_roles(current_user.id)
            is_super_admin = any(role.get("role_type") == "super_admin" for role in roles)
        
        if not is_super_admin:
            user_company_id = getattr(current_user, 'company_id', None)
            if user_company_id != company_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this company"
                )
        
        company = await company_service.get_company(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        return company
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get company"
        )


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    company_data: CompanyUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Update a company"""
    try:
        # Check permissions
        is_super_admin = current_user.is_superuser
        if not is_super_admin:
            roles = await auth_service.get_user_roles(current_user.id)
            is_super_admin = any(role.get("role_type") == "super_admin" for role in roles)
            is_company_admin = any(role.get("role_type") == "company_admin" for role in roles)
            
            if not is_super_admin and not is_company_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to update company"
                )
            
            if is_company_admin and not is_super_admin:
                user_company_id = getattr(current_user, 'company_id', None)
                if user_company_id != company_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Can only update your own company"
                    )
        
        company = await company_service.update_company(
            company_id,
            company_data,
            updated_by=current_user.id
        )
        
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        return company
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating company: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update company"
        )


@router.delete("/{company_id}")
async def delete_company(
    company_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Delete a company"""
    try:
        # Only super admins can delete companies
        is_super_admin = current_user.is_superuser
        if not is_super_admin:
            roles = await auth_service.get_user_roles(current_user.id)
            is_super_admin = any(role.get("role_type") == "super_admin" for role in roles)
        
        if not is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admins can delete companies"
            )
        
        success = await company_service.delete_company(company_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        return {"message": "Company deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting company: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete company"
        )


@router.get("/{company_id}/stats", response_model=CompanyStats)
async def get_company_stats(
    company_id: str,
    period: str = Query(default="monthly", regex="^(daily|weekly|monthly)$"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get company usage statistics"""
    try:
        # Check permissions
        is_super_admin = current_user.is_superuser
        if not is_super_admin:
            roles = await auth_service.get_user_roles(current_user.id)
            is_super_admin = any(role.get("role_type") == "super_admin" for role in roles)
        
        if not is_super_admin:
            user_company_id = getattr(current_user, 'company_id', None)
            if user_company_id != company_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this company's statistics"
                )
        
        stats = await company_service.get_company_stats(company_id, period)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get company statistics"
        )


@router.post("/{company_id}/check-limits")
async def check_company_limits(
    company_id: str,
    resource_type: str = Query(..., regex="^(brands|agents|users|knowledge_items)$"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Check if company has reached resource limits"""
    try:
        # Check permissions
        is_super_admin = current_user.is_superuser
        if not is_super_admin:
            roles = await auth_service.get_user_roles(current_user.id)
            is_super_admin = any(role.get("role_type") == "super_admin" for role in roles)
        
        if not is_super_admin:
            user_company_id = getattr(current_user, 'company_id', None)
            if user_company_id != company_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        result = await company_service.check_company_limits(company_id, resource_type)
        return result
    except Exception as e:
        logger.error(f"Error checking company limits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check company limits"
        )