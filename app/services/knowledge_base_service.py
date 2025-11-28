from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from app.models.knowledge_base import (
    KnowledgeBaseItem,
    KnowledgeBaseItemSummary,
    KnowledgeBaseItemCreate,
    KnowledgeBaseItemUpdate,
    FileInfo,
    UploadStatus,
    IndexingStatus,
    ContentType,
    KnowledgeBaseStats
)
from app.services.s3_service import s3_service
from app.services.vector_service import vector_service
from config.settings import settings

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.database_name]
        self.collection = self.db.knowledge_base_items
        
    async def create_item(
        self,
        item_data: KnowledgeBaseItemCreate,
        user_id: str,
        company_id: Optional[str] = None
    ) -> KnowledgeBaseItem:
        """Create a new knowledge base item"""
        try:
            # Log agent_ids count
            logger.info(f"📝 Creating item with {len(item_data.ai_agent_ids) if item_data.ai_agent_ids else 0} agent_ids")
            
            # Prepare document for MongoDB
            doc = {
                '_id': str(ObjectId()),
                'title': item_data.title,
                'description': item_data.description,
                'content_type': item_data.content_type,
                'company_id': company_id or item_data.company_id,  # Use provided company_id or from item_data
                'ai_agent_ids': item_data.ai_agent_ids if item_data.ai_agent_ids else [],  # Ensure it's at least empty list
                'brand_ids': item_data.brand_ids if item_data.brand_ids else [],  # Brand IDs as a list
                'metadata': item_data.metadata,
                'upload_status': UploadStatus.COMPLETED if item_data.s3_key else UploadStatus.PENDING,
                'indexing_status': IndexingStatus.PENDING,
                'created_by': user_id,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'processing_options': item_data.processing_options.dict(),
                'website_config': item_data.website_config.dict() if item_data.website_config else None
            }
            
            # If S3 file info is provided, add it
            if item_data.s3_key:
                doc['file'] = {
                    'name': item_data.file_name,
                    'size': item_data.file_size,
                    's3_key': item_data.s3_key,
                    's3_bucket': settings.s3_bucket_name,
                    'mime_type': item_data.mime_type,
                    'uploaded_at': datetime.utcnow()
                }
            
            # Insert into MongoDB
            result = await self.collection.insert_one(doc)
            
            # Return the created item
            created_item = await self.get_item(doc['_id'])
            
            logger.info(f"Created knowledge base item: {doc['_id']}")
            return created_item
            
        except Exception as e:
            logger.error(f"Error creating knowledge base item: {e}")
            raise
    
    async def get_item(self, item_id: str) -> Optional[KnowledgeBaseItem]:
        """Get a single knowledge base item by ID"""
        try:
            doc = await self.collection.find_one({'_id': item_id})
            
            if not doc:
                return None
            
            return KnowledgeBaseItem(**doc)
            
        except Exception as e:
            logger.error(f"Error getting knowledge base item: {e}")
            raise
    
    async def list_items(
        self,
        company_id: Optional[str] = None,
        brand_id: Optional[str] = None,
        content_type: Optional[ContentType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[KnowledgeBaseItemSummary]:
        """List knowledge base items with filters, excluding large fields for performance"""
        try:
            # Build filter
            filter_query = {}
            
            # Filter by company_id if provided
            if company_id:
                filter_query['company_id'] = company_id
            
            # Note: brand_id filtering removed - now using company_id based filtering only
            # Knowledge base items are organized by company_id, not brand_id
            
            if content_type:
                filter_query['content_type'] = content_type
            
            # Exclude large fields from the query to improve performance
            projection = {
                'embeddings': 0,  # Exclude embeddings field
                'chunks': 0,      # Exclude chunks field
                'indexed_content': 0  # Exclude indexed content (can be large)
            }
            
            # Query MongoDB with projection and sort by creation date (newest first)
            cursor = self.collection.find(filter_query, projection).sort('created_at', -1).skip(skip).limit(limit)
            
            items = []
            async for doc in cursor:
                # Use the Summary model which doesn't expect the large fields
                items.append(KnowledgeBaseItemSummary(**doc))
            
            return items
            
        except Exception as e:
            logger.error(f"Error listing knowledge base items: {e}")
            raise
    
    async def update_item(
        self,
        item_id: str,
        update_data: KnowledgeBaseItemUpdate
    ) -> Optional[KnowledgeBaseItem]:
        """Update a knowledge base item"""
        try:
            # Build update document
            update_doc = {'$set': {'updated_at': datetime.utcnow()}}
            
            if update_data.title is not None:
                update_doc['$set']['title'] = update_data.title
            
            if update_data.description is not None:
                update_doc['$set']['description'] = update_data.description
            
            if update_data.ai_agent_ids is not None:
                update_doc['$set']['ai_agent_ids'] = update_data.ai_agent_ids
                
            if update_data.brand_ids is not None:
                update_doc['$set']['brand_ids'] = update_data.brand_ids
            
            if update_data.metadata is not None:
                update_doc['$set']['metadata'] = update_data.metadata
            
            if update_data.indexing_status is not None:
                update_doc['$set']['indexing_status'] = update_data.indexing_status
            
            # Update in MongoDB
            result = await self.collection.update_one(
                {'_id': item_id},
                update_doc
            )
            
            if result.modified_count == 0:
                return None
            
            # Return updated item
            return await self.get_item(item_id)
            
        except Exception as e:
            logger.error(f"Error updating knowledge base item: {e}")
            raise
    
    async def delete_item(self, item_id: str) -> bool:
        """Delete a knowledge base item and all its associated data from S3, MongoDB, and vector store"""
        try:
            # Get item to find S3 key and other details
            item = await self.get_item(item_id)
            
            if not item:
                logger.warning(f"Item {item_id} not found for deletion")
                return False
            
            # Track deletion status for each component
            deletion_status = {
                's3': False,
                'vector_store': False,
                'mongodb': False
            }
            
            # 1. Delete from S3 if file exists
            if item.file and item.file.s3_key:
                try:
                    s3_deleted = s3_service.delete_file(item.file.s3_key)
                    deletion_status['s3'] = s3_deleted
                    if s3_deleted:
                        logger.info(f"Deleted S3 file: {item.file.s3_key}")
                    else:
                        logger.warning(f"Failed to delete S3 file: {item.file.s3_key}")
                except Exception as s3_error:
                    logger.error(f"Error deleting from S3: {s3_error}")
                    deletion_status['s3'] = False
            else:
                deletion_status['s3'] = True  # No file to delete
            
            # 2. Delete embeddings and chunks from vector store
            try:
                vector_deleted = await vector_service.delete_embeddings(item_id)
                deletion_status['vector_store'] = vector_deleted
                if vector_deleted:
                    logger.info(f"Deleted embeddings for item: {item_id}")
                else:
                    logger.warning(f"No embeddings found to delete for item: {item_id}")
            except Exception as vector_error:
                logger.error(f"Error deleting from vector store: {vector_error}")
                deletion_status['vector_store'] = False
            
            # 3. Delete from MongoDB (main collection)
            try:
                result = await self.collection.delete_one({'_id': item_id})
                deletion_status['mongodb'] = result.deleted_count > 0
                
                if deletion_status['mongodb']:
                    logger.info(f"Deleted MongoDB document: {item_id}")
                else:
                    logger.warning(f"MongoDB document not found: {item_id}")
            except Exception as mongo_error:
                logger.error(f"Error deleting from MongoDB: {mongo_error}")
                deletion_status['mongodb'] = False
            
            # Log overall deletion status
            all_deleted = all(deletion_status.values())
            partial_deleted = any(deletion_status.values())
            
            if all_deleted:
                logger.info(f"Successfully deleted all data for item {item_id}")
            elif partial_deleted:
                failed_components = [k for k, v in deletion_status.items() if not v]
                logger.warning(f"Partial deletion for item {item_id}. Failed: {failed_components}")
            else:
                logger.error(f"Failed to delete any data for item {item_id}")
            
            # Return true if at least MongoDB document was deleted (primary deletion)
            return deletion_status['mongodb']
            
        except Exception as e:
            logger.error(f"Error deleting knowledge base item: {e}")
            raise
    
    async def update_file_info(
        self,
        item_id: str,
        file_info: FileInfo
    ) -> bool:
        """Update file information after successful upload"""
        try:
            result = await self.collection.update_one(
                {'_id': item_id},
                {
                    '$set': {
                        'file': file_info.dict(),
                        'upload_status': UploadStatus.COMPLETED,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Updated file info for item: {item_id}")
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating file info: {e}")
            raise
    
    async def process_item_content(
        self,
        item_id: str,
        content: str
    ) -> bool:
        """Process item content for indexing and embeddings"""
        try:
            # Get item
            item = await self.get_item(item_id)
            
            if not item:
                return False
            
            # Update indexing status and store full content
            await self.collection.update_one(
                {'_id': item_id},
                {
                    '$set': {
                        'indexing_status': IndexingStatus.PROCESSING,
                        'indexed_content': content,  # Store full content in items collection
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            # Process embeddings if enabled
            if item.processing_options.generate_embeddings:
                # Process and store chunks with embeddings in vectors collection
                stats = await vector_service.process_and_store_embeddings(
                    item_id,
                    content,
                    item.processing_options.chunk_size,
                    item.processing_options.chunk_overlap
                )
                
                if not stats.get('success'):
                    await self.collection.update_one(
                        {'_id': item_id},
                        {'$set': {
                            'indexing_status': IndexingStatus.FAILED,
                            'indexing_error': stats.get('error', 'Unknown error')
                        }}
                    )
                    return False
            else:
                # Just mark as completed if no embeddings needed
                await self.collection.update_one(
                    {'_id': item_id},
                    {'$set': {'indexing_status': IndexingStatus.COMPLETED}}
                )
            
            logger.info(f"Processed content for item: {item_id} - Full content stored, chunks created in vectors collection")
            return True
            
        except Exception as e:
            logger.error(f"Error processing item content: {e}")
            
            # Update status to failed
            await self.collection.update_one(
                {'_id': item_id},
                {'$set': {'indexing_status': IndexingStatus.FAILED}}
            )
            
            return False
    
    async def assign_agents(
        self,
        item_ids: List[str],
        agent_ids: List[str],
        operation: str = "add"
    ) -> int:
        """Assign or replace agents for multiple items"""
        try:
            if operation == "replace":
                # Replace existing agents
                result = await self.collection.update_many(
                    {'_id': {'$in': item_ids}},
                    {
                        '$set': {
                            'ai_agent_ids': agent_ids,
                            'updated_at': datetime.utcnow()
                        }
                    }
                )
            else:
                # Add to existing agents
                result = await self.collection.update_many(
                    {'_id': {'$in': item_ids}},
                    {
                        '$addToSet': {'ai_agent_ids': {'$each': agent_ids}},
                        '$set': {'updated_at': datetime.utcnow()}
                    }
                )
            
            logger.info(f"Updated agents for {result.modified_count} items")
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Error assigning agents: {e}")
            raise
    
    async def get_stats(self, company_id: Optional[str] = None, brand_id: Optional[str] = None) -> KnowledgeBaseStats:
        """Get statistics for knowledge base items"""
        try:
            # Build match criteria
            match_criteria = {}
            if company_id:
                match_criteria['company_id'] = company_id
            # Note: brand_id filtering removed - now using company_id based filtering only
            # if brand_id:
            #     match_criteria['brand_id'] = brand_id
                
            pipeline = [
                {'$match': match_criteria},
                {
                    '$group': {
                        '_id': None,
                        'total_items': {'$sum': 1},
                        'documents': {
                            '$sum': {
                                '$cond': [
                                    {'$eq': ['$content_type', ContentType.DOCUMENT]},
                                    1,
                                    0
                                ]
                            }
                        },
                        'media_files': {
                            '$sum': {
                                '$cond': [
                                    {'$eq': ['$content_type', ContentType.MEDIA]},
                                    1,
                                    0
                                ]
                            }
                        },
                        'websites': {
                            '$sum': {
                                '$cond': [
                                    {'$eq': ['$content_type', ContentType.WEBSITE]},
                                    1,
                                    0
                                ]
                            }
                        },
                        'total_size': {'$sum': '$file.size'},
                        'indexed_items': {
                            '$sum': {
                                '$cond': [
                                    {'$eq': ['$indexing_status', IndexingStatus.COMPLETED]},
                                    1,
                                    0
                                ]
                            }
                        },
                        'processing_items': {
                            '$sum': {
                                '$cond': [
                                    {'$eq': ['$indexing_status', IndexingStatus.PROCESSING]},
                                    1,
                                    0
                                ]
                            }
                        },
                        'failed_items': {
                            '$sum': {
                                '$cond': [
                                    {'$eq': ['$indexing_status', IndexingStatus.FAILED]},
                                    1,
                                    0
                                ]
                            }
                        }
                    }
                }
            ]
            
            async for doc in self.collection.aggregate(pipeline):
                return KnowledgeBaseStats(
                    total_items=doc.get('total_items', 0),
                    documents=doc.get('documents', 0),
                    media_files=doc.get('media_files', 0),
                    websites=doc.get('websites', 0),
                    total_size=doc.get('total_size', 0) or 0,
                    indexed_items=doc.get('indexed_items', 0),
                    processing_items=doc.get('processing_items', 0),
                    failed_items=doc.get('failed_items', 0)
                )
            
            # Return empty stats if no items
            return KnowledgeBaseStats(
                total_items=0,
                documents=0,
                media_files=0,
                websites=0,
                total_size=0,
                indexed_items=0,
                processing_items=0,
                failed_items=0
            )
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            raise


# Create a singleton instance
knowledge_base_service = KnowledgeBaseService()