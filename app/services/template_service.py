from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
import re
import boto3
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status
from app.models.template import (
    ReportTemplate,
    TemplateCreate,
    TemplateUpdate,
    TemplateUpload,
    TemplateResponse,
    TemplateListResponse,
)
import logging
import os
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class TemplateService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.templates
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'khoros-reports')
        
    def extract_placeholders(self, content: str) -> List[str]:
        """Extract placeholders from template content"""
        pattern = r'\{\{\s*([^}]+)\s*\}\}'
        matches = re.findall(pattern, content)
        return list(set(matches))
    
    def parse_s3_url(self, url: str) -> tuple[str, str]:
        """Parse S3 URL to get bucket and key"""
        parsed = urlparse(url)
        if parsed.scheme == 's3':
            bucket = parsed.netloc
            key = parsed.path.lstrip('/')
        elif parsed.netloc.endswith('.amazonaws.com'):
            # Handle https://bucket.s3.amazonaws.com/key format
            bucket = parsed.netloc.split('.')[0]
            key = parsed.path.lstrip('/')
        elif 's3.amazonaws.com' in parsed.netloc:
            # Handle https://s3.amazonaws.com/bucket/key format
            path_parts = parsed.path.lstrip('/').split('/', 1)
            bucket = path_parts[0]
            key = path_parts[1] if len(path_parts) > 1 else ''
        else:
            raise ValueError(f"Invalid S3 URL: {url}")
        return bucket, key
    
    async def upload_to_s3(self, content: str, filename: str, file_type: str = 'html') -> str:
        """Upload template content to S3"""
        try:
            key = f"templates/{datetime.utcnow().strftime('%Y%m%d')}/{filename}"
            if not key.endswith(f'.{file_type}'):
                key = f"{key}.{file_type}"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType='text/html' if file_type == 'html' else 'text/plain'
            )
            
            # Generate S3 URL
            url = f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
            return url
        except Exception as e:
            logger.error(f"Failed to upload to S3: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload template to S3: {str(e)}"
            )
    
    async def fetch_from_s3(self, url: str) -> str:
        """Fetch template content from S3"""
        try:
            bucket, key = self.parse_s3_url(url)
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            return content
        except Exception as e:
            logger.error(f"Failed to fetch from S3: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch template from S3: {str(e)}"
            )
    
    async def create_template(self, template: TemplateCreate, user_id: Optional[str] = None) -> ReportTemplate:
        """Create a new template"""
        try:
            # Upload content to S3 if provided
            template_url = template.template_url
            if template.template_content and not template_url:
                filename = template.name.lower().replace(' ', '_')
                template_url = await self.upload_to_s3(
                    template.template_content,
                    filename,
                    'html'
                )
            
            # Extract placeholders from content
            placeholders = []
            if template.template_content:
                placeholders = self.extract_placeholders(template.template_content)
            
            # Parse S3 details from URL
            s3_bucket = None
            s3_key = None
            if template_url:
                try:
                    s3_bucket, s3_key = self.parse_s3_url(template_url)
                except:
                    pass
            
            # Create template document
            template_doc = {
                "name": template.name,
                "description": template.description,
                "template_url": template_url,
                "template_content": template.template_content,
                "placeholders": placeholders,
                "category": template.category,
                "tags": template.tags or [],
                "is_active": template.is_active,
                "created_by": user_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "s3_bucket": s3_bucket,
                "s3_key": s3_key,
                "usage_count": 0,
                "last_used_at": None
            }
            
            result = await self.collection.insert_one(template_doc)
            template_doc["_id"] = result.inserted_id
            
            return ReportTemplate(**template_doc)
        except Exception as e:
            logger.error(f"Failed to create template: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create template: {str(e)}"
            )
    
    async def get_template(self, template_id: str) -> Optional[ReportTemplate]:
        """Get a template by ID"""
        try:
            if not ObjectId.is_valid(template_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid template ID"
                )
            
            template = await self.collection.find_one({"_id": ObjectId(template_id)})
            if not template:
                return None
            
            return ReportTemplate(**template)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get template: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get template: {str(e)}"
            )
    
    async def update_template(self, template_id: str, update: TemplateUpdate) -> Optional[ReportTemplate]:
        """Update a template"""
        try:
            if not ObjectId.is_valid(template_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid template ID"
                )
            
            # Build update document
            update_doc = {}
            if update.name is not None:
                update_doc["name"] = update.name
            if update.description is not None:
                update_doc["description"] = update.description
            if update.category is not None:
                update_doc["category"] = update.category
            if update.tags is not None:
                update_doc["tags"] = update.tags
            if update.is_active is not None:
                update_doc["is_active"] = update.is_active
            
            # Handle template content update
            if update.template_content is not None:
                update_doc["template_content"] = update.template_content
                update_doc["placeholders"] = self.extract_placeholders(update.template_content)
                
                # Upload to S3 if no URL provided
                if not update.template_url:
                    existing = await self.collection.find_one({"_id": ObjectId(template_id)})
                    if existing:
                        filename = existing.get('name', 'template').lower().replace(' ', '_')
                        template_url = await self.upload_to_s3(
                            update.template_content,
                            filename,
                            'html'
                        )
                        update_doc["template_url"] = template_url
                        
                        # Parse S3 details
                        try:
                            s3_bucket, s3_key = self.parse_s3_url(template_url)
                            update_doc["s3_bucket"] = s3_bucket
                            update_doc["s3_key"] = s3_key
                        except:
                            pass
            
            if update.template_url is not None:
                update_doc["template_url"] = update.template_url
                # Parse S3 details
                try:
                    s3_bucket, s3_key = self.parse_s3_url(update.template_url)
                    update_doc["s3_bucket"] = s3_bucket
                    update_doc["s3_key"] = s3_key
                except:
                    pass
            
            if update_doc:
                update_doc["updated_at"] = datetime.utcnow()
                
                result = await self.collection.find_one_and_update(
                    {"_id": ObjectId(template_id)},
                    {"$set": update_doc},
                    return_document=True
                )
                
                if result:
                    return ReportTemplate(**result)
            
            return None
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update template: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update template: {str(e)}"
            )
    
    async def delete_template(self, template_id: str) -> bool:
        """Delete a template"""
        try:
            if not ObjectId.is_valid(template_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid template ID"
                )
            
            result = await self.collection.delete_one({"_id": ObjectId(template_id)})
            return result.deleted_count > 0
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete template: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete template: {str(e)}"
            )
    
    async def list_templates(
        self,
        page: int = 1,
        limit: int = 10,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> TemplateListResponse:
        """List templates with filtering and pagination"""
        try:
            # Build filter
            filter_doc = {}
            if category:
                filter_doc["category"] = category
            if is_active is not None:
                filter_doc["is_active"] = is_active
            if search:
                filter_doc["$or"] = [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"description": {"$regex": search, "$options": "i"}}
                ]
            if tags:
                filter_doc["tags"] = {"$in": tags}
            
            # Get total count
            total = await self.collection.count_documents(filter_doc)
            
            # Get paginated results
            skip = (page - 1) * limit
            cursor = self.collection.find(filter_doc).skip(skip).limit(limit).sort("created_at", -1)
            templates = []
            async for doc in cursor:
                templates.append(ReportTemplate(**doc))
            
            return TemplateListResponse(
                success=True,
                data=templates,
                total=total,
                page=page,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to list templates: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list templates: {str(e)}"
            )
    
    async def upload_template(self, upload: TemplateUpload) -> Dict[str, Any]:
        """Upload a template file to S3"""
        try:
            url = await self.upload_to_s3(
                upload.template_content,
                upload.template_name,
                upload.file_type
            )
            
            placeholders = self.extract_placeholders(upload.template_content)
            
            return {
                "template_url": url,
                "placeholders": placeholders,
                "s3_bucket": self.bucket_name,
                "s3_key": url.split('/')[-1]
            }
        except Exception as e:
            logger.error(f"Failed to upload template: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload template: {str(e)}"
            )
    
    async def increment_usage(self, template_id: str) -> None:
        """Increment template usage count"""
        try:
            if not ObjectId.is_valid(template_id):
                return
            
            await self.collection.update_one(
                {"_id": ObjectId(template_id)},
                {
                    "$inc": {"usage_count": 1},
                    "$set": {"last_used_at": datetime.utcnow()}
                }
            )
        except Exception as e:
            logger.error(f"Failed to increment usage: {str(e)}")
    
    async def get_categories(self) -> List[str]:
        """Get all unique template categories"""
        try:
            categories = await self.collection.distinct("category")
            return [c for c in categories if c]
        except Exception as e:
            logger.error(f"Failed to get categories: {str(e)}")
            return []
    
    async def get_tags(self) -> List[str]:
        """Get all unique template tags"""
        try:
            pipeline = [
                {"$unwind": "$tags"},
                {"$group": {"_id": "$tags"}},
                {"$sort": {"_id": 1}}
            ]
            cursor = self.collection.aggregate(pipeline)
            tags = []
            async for doc in cursor:
                if doc["_id"]:
                    tags.append(doc["_id"])
            return tags
        except Exception as e:
            logger.error(f"Failed to get tags: {str(e)}")
            return []