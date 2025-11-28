"""
Flexible LangChain-based document ingestion service with multiple provider support
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import time
from bson import ObjectId

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
    TextLoader,
    CSVLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader
)
from langchain.schema import Document

# Motor for async MongoDB operations
from motor.motor_asyncio import AsyncIOMotorClient
import boto3
from botocore.exceptions import ClientError
import tempfile
import os
from pathlib import Path

from config.settings import settings

logger = logging.getLogger(__name__)


class LangChainIngestionService:
    """Flexible document ingestion service with multiple embedding provider support"""
    
    def __init__(self):
        # MongoDB connection
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.database_name]
        self.collection = self.db.knowledge_base_items  # Main items collection
        self.vectors_collection = self.db.knowledge_base_vectors  # Vectors collection for chunks
        
        # S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            aws_session_token=getattr(settings, 'aws_session_token', None),
            region_name=settings.aws_region
        )
        self.bucket_name = settings.s3_bucket_name
        
        # Initialize embeddings based on provider configuration
        self.embeddings = self._initialize_embeddings()
        self.embedding_provider = settings.embedding_provider
        self.embedding_model_name = self._get_embedding_model_name()
        
        # Text splitter configuration
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )
    
    def _initialize_embeddings(self):
        """Initialize embeddings based on configured provider"""
        provider = settings.embedding_provider.lower()
        
        if provider == "openai":
            if not settings.openai_api_key:
                logger.warning("OpenAI API key not found, falling back to HuggingFace")
                return self._get_huggingface_embeddings()
            
            logger.info(f"Using OpenAI embeddings with model: {settings.openai_embedding_model}")
            return OpenAIEmbeddings(
                openai_api_key=settings.openai_api_key,
                model=settings.openai_embedding_model
            )
        
        elif provider == "anthropic":
            # Note: Anthropic doesn't provide embedding models
            logger.warning("Anthropic doesn't provide embedding models, falling back to HuggingFace")
            return self._get_huggingface_embeddings()
        
        else:  # Default to HuggingFace (free, local)
            return self._get_huggingface_embeddings()
    
    def _get_huggingface_embeddings(self):
        """Get HuggingFace embeddings"""
        logger.info(f"Using HuggingFace embeddings with model: {settings.huggingface_embedding_model}")
        return HuggingFaceEmbeddings(
            model_name=settings.huggingface_embedding_model,
            model_kwargs={'device': 'cpu'},  # Use 'cuda' if you have GPU
            encode_kwargs={'normalize_embeddings': True}
        )
    
    def _get_embedding_model_name(self) -> str:
        """Get the name of the embedding model being used"""
        provider = settings.embedding_provider.lower()
        
        if provider == "openai":
            return settings.openai_embedding_model
        elif provider == "huggingface":
            return settings.huggingface_embedding_model
        else:
            return settings.huggingface_embedding_model  # Default
    
    def _get_loader_for_file(self, file_path: str, mime_type: str):
        """Get appropriate LangChain loader based on file type"""
        
        file_ext = Path(file_path).suffix.lower()
        
        # PDF files
        if mime_type == 'application/pdf' or file_ext == '.pdf':
            return PyPDFLoader(file_path)
        
        # Word documents
        elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                          'application/msword'] or file_ext in ['.docx', '.doc']:
            return Docx2txtLoader(file_path)
        
        # Excel files
        elif mime_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                          'application/vnd.ms-excel'] or file_ext in ['.xlsx', '.xls']:
            return UnstructuredExcelLoader(file_path)
        
        # PowerPoint files
        elif mime_type in ['application/vnd.openxmlformats-officedocument.presentationml.presentation',
                          'application/vnd.ms-powerpoint'] or file_ext in ['.pptx', '.ppt']:
            return UnstructuredPowerPointLoader(file_path)
        
        # CSV files
        elif mime_type == 'text/csv' or file_ext == '.csv':
            return CSVLoader(file_path)
        
        # HTML files
        elif mime_type == 'text/html' or file_ext in ['.html', '.htm']:
            return UnstructuredHTMLLoader(file_path)
        
        # Markdown files
        elif file_ext in ['.md', '.markdown']:
            return UnstructuredMarkdownLoader(file_path)
        
        # Default to text loader
        else:
            return TextLoader(file_path, encoding='utf-8')
    
    async def download_from_s3(self, s3_key: str) -> str:
        """Download file from S3 to temporary location"""
        try:
            # Create temporary file
            suffix = Path(s3_key).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                temp_path = tmp_file.name
                
                # Download from S3
                self.s3_client.download_file(
                    self.bucket_name,
                    s3_key,
                    temp_path
                )
                
                logger.info(f"Downloaded S3 file {s3_key} to {temp_path}")
                return temp_path
                
        except ClientError as e:
            logger.error(f"Error downloading from S3: {e}")
            raise
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Rough estimation: 1 token ≈ 4 characters for English text
        return len(text) // 4
    
    async def process_document(
        self,
        item_id: str,
        s3_key: str,
        mime_type: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Dict[str, Any]:
        """Process a document and generate embeddings"""
        
        logger.info(f"[INGESTION START] Processing document - Item ID: {item_id}")
        logger.info(f"[INGESTION] Collection: {self.collection.name}, Database: {self.db.name}")
        logger.info(f"[INGESTION] S3 Key: {s3_key}, MIME Type: {mime_type}")
        logger.info(f"[INGESTION] Chunk Size: {chunk_size}, Overlap: {chunk_overlap}")
        logger.info(f"[INGESTION] Embedding Provider: {self.embedding_provider}, Model: {self.embedding_model_name}")
        
        # Check if this is a media file that should be handled by media_ingestion_service
        media_types = [
            'image/', 'audio/', 'video/'
        ]
        
        # Check if mime_type indicates a media file
        is_media = any(mime_type.startswith(media_type) for media_type in media_types)
        
        # Also check file extension for media files
        file_ext = Path(s3_key).suffix.lower()
        media_extensions = [
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg',
            # Audio
            '.mp3', '.wav', '.m4a', '.ogg', '.aac', '.flac', '.wma',
            # Video
            '.mp4', '.avi', '.mov', '.wmv', '.webm', '.mkv', '.flv', '.mpg', '.mpeg'
        ]
        is_media = is_media or file_ext in media_extensions
        
        if is_media:
            # Route to media ingestion service
            logger.info(f"Routing media file {s3_key} to media_ingestion_service")
            from app.services.media_ingestion_service import media_ingestion_service
            
            # Download file first
            temp_path = await self.download_from_s3(s3_key)
            try:
                # Determine media type
                if mime_type.startswith('image/'):
                    media_type = 'image'
                elif mime_type.startswith('audio/'):
                    media_type = 'audio'
                elif mime_type.startswith('video/'):
                    media_type = 'video'
                else:
                    # Determine by extension
                    if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg']:
                        media_type = 'image'
                    elif file_ext in ['.mp3', '.wav', '.m4a', '.ogg', '.aac', '.flac', '.wma']:
                        media_type = 'audio'
                    else:
                        media_type = 'video'
                
                # Process with media ingestion service
                result = await media_ingestion_service.process_media(
                    item_id=item_id,
                    file_path=temp_path,
                    media_type=media_type,
                    mime_type=mime_type,
                    metadata={'s3_key': s3_key}
                )
                return result
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        
        # Continue with document processing for non-media files
        temp_path = None
        start_time = time.time()
        
        try:
            # Log the item_id being processed
            logger.info(f"Starting document ingestion for item_id: {item_id}, s3_key: {s3_key}")
            
            # MongoDB is using string IDs, not ObjectIds
            # Update status to processing
            update_result = await self.collection.update_one(
                {"_id": item_id},  # Use string ID directly
                {
                    "$set": {
                        "indexing_status": "processing",
                        "embeddings_processed_at": datetime.utcnow()
                    }
                }
            )
            
            if update_result.matched_count == 0:
                logger.error(f"No document found with _id: {item_id}")
                # Try to check if document exists in different format
                doc_check = await self.collection.find_one({"_id": {"$in": [item_id, ObjectId(item_id) if ObjectId.is_valid(item_id) else None]}})
                if doc_check:
                    logger.error(f"Document exists with different ID format: {doc_check.get('_id')}")
                raise ValueError(f"Document not found with ID: {item_id}")
            
            # Download file from S3
            temp_path = await self.download_from_s3(s3_key)
            
            # Load document using appropriate loader
            loader = self._get_loader_for_file(temp_path, mime_type)
            documents = loader.load()
            
            if not documents:
                raise ValueError("No content extracted from document")
            
            # Extract full text
            full_text = "\n".join([doc.page_content for doc in documents])
            
            # Update text splitter if custom parameters provided
            if chunk_size != 1000 or chunk_overlap != 200:
                self.text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    length_function=len,
                    separators=["\n\n", "\n", ".", "!", "?", " ", ""]
                )
            
            # Split text into chunks
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"[CHUNKING] Split document into {len(chunks)} chunks")
            logger.info(f"[CHUNKING] Full text length: {len(full_text)} characters")
            
            # Generate embeddings for each chunk
            chunk_texts = [chunk.page_content for chunk in chunks]
            logger.info(f"[EMBEDDINGS] Generating embeddings for {len(chunk_texts)} chunks")
            logger.info(f"[EMBEDDINGS] First chunk preview (50 chars): {chunk_texts[0][:50] if chunk_texts else 'No chunks'}...")
            
            embeddings_list = self.embeddings.embed_documents(chunk_texts)
            logger.info(f"[EMBEDDINGS] Generated {len(embeddings_list)} embeddings")
            if embeddings_list:
                logger.info(f"[EMBEDDINGS] Embedding dimension: {len(embeddings_list[0])}")
                logger.info(f"[EMBEDDINGS] First embedding sample (first 5 values): {embeddings_list[0][:5]}")
            
            # Get item metadata for vector documents
            item_doc = await self.collection.find_one({"_id": item_id})
            if not item_doc:
                logger.error(f"Item {item_id} not found in database")
                raise ValueError(f"Item {item_id} not found")
            
            # Delete existing vectors for this item if any
            delete_result = await self.vectors_collection.delete_many({"knowledge_item_id": item_id})
            logger.info(f"Deleted {delete_result.deleted_count} existing vector documents for item {item_id}")
            
            # Prepare vector documents for the vectors collection
            vector_docs = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings_list)):
                vector_doc = {
                    "knowledge_item_id": item_id,
                    "chunk_index": i,
                    "chunk_text": chunk.page_content,
                    "embeddings": embedding,
                    
                    # Metadata from parent item
                    "title": item_doc.get("title", ""),
                    "content_type": item_doc.get("content_type", ""),
                    "company_id": item_doc.get("company_id", ""),
                    "ai_agent_ids": item_doc.get("ai_agent_ids", []),
                    "brand_ids": item_doc.get("brand_ids", []),
                    
                    # Chunk-specific metadata
                    "start_position": chunk.metadata.get("start_position", i * chunk_size),
                    "end_position": chunk.metadata.get("end_position", (i + 1) * chunk_size),
                    "token_count": self.estimate_tokens(chunk.page_content),
                    
                    # Processing details
                    "embedding_provider": self.embedding_provider,
                    "embedding_model": self.embedding_model_name,
                    "created_at": datetime.utcnow(),
                    
                    # Additional metadata from chunk
                    "metadata": chunk.metadata
                }
                vector_docs.append(vector_doc)
            
            # Insert vectors into the vectors collection
            if vector_docs:
                insert_result = await self.vectors_collection.insert_many(vector_docs)
                logger.info(f"Inserted {len(insert_result.inserted_ids)} vector documents into knowledge_base_vectors collection")
            
            # Calculate statistics
            processing_time = time.time() - start_time
            total_tokens = self.estimate_tokens(full_text)
            
            ingestion_stats = {
                "chunks_created": len(chunks),
                "total_characters": len(full_text),
                "estimated_tokens": total_tokens,
                "processing_time_seconds": processing_time,
                "embedding_provider": self.embedding_provider,
                "embedding_model": self.embedding_model_name,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "processed_at": datetime.utcnow()
            }
            
            # Update main document in knowledge_base_items (without chunks and embeddings)
            logger.info(f"[MONGODB UPDATE] Starting update for item_id: {item_id}")
            logger.info(f"[MONGODB UPDATE] Main collection: {self.collection.name}")
            logger.info(f"[MONGODB UPDATE] Vectors stored in: {self.vectors_collection.name}")
            
            update_data = {
                "indexing_status": "completed",
                "indexed_content": full_text,  # Store full content
                "embeddings_processed": True,
                "embeddings_processed_at": datetime.utcnow(),
                "ingestion_stats": ingestion_stats,
                "total_chunks": len(chunks),
                "total_tokens": total_tokens,
                "embedding_provider": self.embedding_provider,
                "embedding_model": self.embedding_model_name
            }
            
            logger.info(f"[MONGODB UPDATE] Update data keys: {list(update_data.keys())}")
            logger.info(f"[MONGODB UPDATE] Embedding provider stored: {self.embedding_provider}")
            logger.info(f"[MONGODB UPDATE] Embedding model stored: {self.embedding_model_name}")
            
            update_result = await self.collection.update_one(
                {"_id": item_id},  # Use string ID directly
                {"$set": update_data}
            )
            
            logger.info(f"[MONGODB UPDATE] Update result - Matched: {update_result.matched_count}, Modified: {update_result.modified_count}")
            
            if update_result.matched_count == 0:
                logger.error(f"No document found to update with _id: {item_id}")
                # Try to find the document for debugging
                existing_doc = await self.collection.find_one({"_id": item_id})
                if existing_doc:
                    logger.error(f"Document exists but update failed: {existing_doc.get('title', 'Unknown')}")
                else:
                    logger.error(f"Document does not exist with _id: {item_id}")
                raise ValueError(f"Failed to update document with ID: {item_id}")
            
            if update_result.modified_count == 0:
                logger.warning(f"Document matched but not modified for item_id: {item_id}")
                logger.warning("This might occur if the document already has the same values")
            else:
                logger.info(f"Successfully updated document {item_id} with {len(chunks)} chunks and {total_tokens} estimated tokens")
            
            logger.info(f"[INGESTION SUCCESS] Successfully processed document {item_id}")
            logger.info(f"[INGESTION SUCCESS] Provider: {self.embedding_provider}, Time: {processing_time:.2f}s")
            logger.info(f"[INGESTION SUCCESS] Chunks: {len(chunks)}, Embeddings: {len(embeddings_list)}, Tokens: {total_tokens}")
            logger.info(f"[INGESTION COMPLETE] ========================================")
            
            return {
                "success": True,
                "stats": ingestion_stats
            }
            
        except Exception as e:
            logger.error(f"Error processing document {item_id}: {e}")
            
            # Update status to failed
            try:
                await self.collection.update_one(
                    {"_id": item_id},  # Use string ID directly
                    {
                        "$set": {
                            "indexing_status": "failed",
                            "indexing_error": str(e),
                            "embeddings_processed_at": datetime.utcnow(),
                            "embeddings_processed": False
                        }
                    }
                )
            except Exception as update_error:
                logger.error(f"Failed to update error status: {update_error}")
            
            return {
                "success": False,
                "error": str(e)
            }
        
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                    logger.info(f"Cleaned up temporary file: {temp_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_path}: {e}")
    
    async def search_similar(
        self,
        query: str,
        brand_id: str,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using embeddings from vectors collection"""
        
        try:
            # Generate embedding for query
            query_embedding = self.embeddings.embed_query(query)
            
            # Search in vectors collection directly
            cursor = self.vectors_collection.find({
                "brand_ids": brand_id  # Note: using brand_ids array field
            })
            
            # Calculate similarities and sort
            results = []
            async for doc in cursor:
                # Calculate cosine similarity
                doc_embedding = doc.get("embeddings", [])
                if doc_embedding:
                    # Simple dot product for normalized vectors (cosine similarity)
                    similarity = sum(a * b for a, b in zip(query_embedding, doc_embedding))
                    
                    if similarity >= similarity_threshold:
                        results.append({
                            "item_id": doc.get("knowledge_item_id"),
                            "title": doc.get("title"),
                            "content_type": doc.get("content_type"),
                            "chunk_content": doc.get("chunk_text"),
                            "chunk_index": doc.get("chunk_index"),
                            "similarity_score": similarity,
                            "metadata": doc.get("metadata", {})
                        })
            
            # Sort by similarity and limit
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            results = results[:limit]
            
            logger.info(f"Found {len(results)} similar chunks for query using {self.embedding_provider}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {e}")
            return []


# Create singleton instance
langchain_ingestion_service = LangChainIngestionService()