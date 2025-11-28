from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import List, Optional, Dict, Any
from app.models.template import (
    ReportTemplate,
    TemplateCreate,
    TemplateUpdate,
    TemplateUpload,
    TemplateResponse,
    TemplateListResponse,
)
from app.services.template_service import TemplateService
from app.utils import get_database
from app.api.routes.auth import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/templates", tags=["templates"])

def get_template_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> TemplateService:
    """Get template service instance"""
    return TemplateService(db)

@router.get("", response_model=TemplateListResponse)
async def list_templates(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    service: TemplateService = Depends(get_template_service)
):
    """List all templates with filtering and pagination"""
    return await service.list_templates(
        page=page,
        limit=limit,
        category=category,
        is_active=is_active,
        search=search,
        tags=tags
    )

@router.post("", response_model=ReportTemplate)
async def create_template(
    template: TemplateCreate,
    current_user: dict = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """Create a new template"""
    user_id = str(current_user.get("_id", ""))
    return await service.create_template(template, user_id=user_id)

@router.get("/categories", response_model=List[str])
async def get_categories(
    service: TemplateService = Depends(get_template_service)
):
    """Get all unique template categories"""
    return await service.get_categories()

@router.get("/tags", response_model=List[str])
async def get_tags(
    service: TemplateService = Depends(get_template_service)
):
    """Get all unique template tags"""
    return await service.get_tags()

@router.get("/{template_id}", response_model=ReportTemplate)
async def get_template(
    template_id: str,
    service: TemplateService = Depends(get_template_service)
):
    """Get a specific template by ID"""
    template = await service.get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return template

@router.put("/{template_id}", response_model=ReportTemplate)
async def update_template(
    template_id: str,
    update: TemplateUpdate,
    current_user: dict = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """Update a template"""
    template = await service.update_template(template_id, update)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return template

@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: dict = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """Delete a template"""
    deleted = await service.delete_template(template_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return {"message": "Template deleted successfully"}

@router.post("/upload", response_model=Dict[str, Any])
async def upload_template(
    upload: TemplateUpload,
    current_user: dict = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """Upload a template file to S3"""
    result = await service.upload_template(upload)
    return result

@router.post("/{template_id}/increment-usage")
async def increment_usage(
    template_id: str,
    service: TemplateService = Depends(get_template_service)
):
    """Increment template usage count"""
    await service.increment_usage(template_id)
    return {"message": "Usage count incremented"}

@router.get("/{template_id}/content", response_model=Dict[str, str])
async def get_template_content(
    template_id: str,
    service: TemplateService = Depends(get_template_service)
):
    """Get template content from S3"""
    template = await service.get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    if not template.template_url:
        return {"content": template.template_content or ""}
    
    try:
        content = await service.fetch_from_s3(template.template_url)
        return {"content": content}
    except Exception as e:
        logger.error(f"Failed to fetch template content: {str(e)}")
        return {"content": template.template_content or ""}

@router.post("/duplicate/{template_id}", response_model=ReportTemplate)
async def duplicate_template(
    template_id: str,
    new_name: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """Duplicate an existing template"""
    # Get original template
    original = await service.get_template(template_id)
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Create a copy
    template_copy = TemplateCreate(
        name=new_name,
        description=original.description,
        template_content=original.template_content,
        template_url=None,  # Will create new S3 object
        category=original.category,
        tags=original.tags,
        is_active=original.is_active
    )
    
    # If original has S3 content, fetch it
    if original.template_url:
        try:
            content = await service.fetch_from_s3(original.template_url)
            template_copy.template_content = content
        except:
            pass
    
    user_id = str(current_user.get("_id", ""))
    return await service.create_template(template_copy, user_id=user_id)

@router.get("/search/placeholders", response_model=List[str])
async def search_placeholders(
    content: str = Query(..., description="Template content to search for placeholders"),
    service: TemplateService = Depends(get_template_service)
):
    """Extract placeholders from template content"""
    return service.extract_placeholders(content)