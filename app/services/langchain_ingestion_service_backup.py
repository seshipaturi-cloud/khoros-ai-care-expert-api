"""
LangChain-based document ingestion service using HuggingFace embeddings
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import time
from bson import ObjectId

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
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
    """Service for document ingestion using LangChain with HuggingFace embeddings"""
    
    def __init__(self):
        # MongoDB connection
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.database_name]
        self.collection = self.db.knowledge_base_items
        
        # S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            aws_session_token=getattr(settings, 'aws_session_token', None),
            region_name=settings.aws_region
        )
        self.bucket_name = settings.s3_bucket_name
        
        # Initialize HuggingFace embeddings (free, local)
        # Using sentence-transformers/all-MiniLM-L6-v2 - a popular, efficient model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},  # Use 'cuda' if you have GPU
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Text splitter configuration
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )
    
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
        
        temp_path = None
        start_time = time.time()
        
        try:
            # Update status to processing
            await self.collection.update_one(
                {"_id": ObjectId(item_id)},
                {
                    "$set": {
                        "indexing_status": "processing",
                        "embeddings_processed_at": datetime.utcnow()
                    }
                }
            )
            
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
            logger.info(f"Split document into {len(chunks)} chunks")
            
            # Generate embeddings for each chunk
            chunk_texts = [chunk.page_content for chunk in chunks]
            embeddings = self.embeddings.embed_documents(chunk_texts)
            
            # Prepare chunks with embeddings for storage
            embedded_chunks = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                embedded_chunks.append({
                    "chunk_id": f"{item_id}_chunk_{i}",
                    "content": chunk.page_content,
                    "embedding": embedding,
                    "metadata": {
                        **chunk.metadata,
                        "chunk_index": i,
                        "item_id": item_id
                    }
                })
            
            # Calculate statistics
            processing_time = time.time() - start_time
            total_tokens = self.estimate_tokens(full_text)
            
            ingestion_stats = {
                "chunks_created": len(chunks),
                "total_characters": len(full_text),
                "estimated_tokens": total_tokens,
                "processing_time_seconds": processing_time,
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "processed_at": datetime.utcnow()
            }
            
            # Update document in MongoDB with processed data
            update_result = await self.collection.update_one(
                {"_id": ObjectId(item_id)},
                {
                    "$set": {
                        "indexing_status": "completed",
                        "indexed_content": full_text[:5000],  # Store first 5000 chars for preview
                        "chunks": embedded_chunks,
                        "embeddings_processed": True,
                        "embeddings_processed_at": datetime.utcnow(),
                        "ingestion_stats": ingestion_stats
                    }
                }
            )
            
            if update_result.modified_count == 0:
                logger.warning(f"No document updated for item_id: {item_id}")
            
            logger.info(f"Successfully processed document {item_id} in {processing_time:.2f} seconds")
            
            return {
                "success": True,
                "stats": ingestion_stats
            }
            
        except Exception as e:
            logger.error(f"Error processing document {item_id}: {e}")
            
            # Update status to failed
            await self.collection.update_one(
                {"_id": ObjectId(item_id)},
                {
                    "$set": {
                        "indexing_status": "failed",
                        "indexing_error": str(e),
                        "embeddings_processed_at": datetime.utcnow()
                    }
                }
            )
            
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
        """Search for similar documents using embeddings"""
        
        try:
            # Generate embedding for query
            query_embedding = self.embeddings.embed_query(query)
            
            # Create aggregation pipeline for vector search
            pipeline = [
                {
                    "$match": {
                        "brand_id": brand_id,
                        "indexing_status": "completed",
                        "chunks": {"$exists": True}
                    }
                },
                {
                    "$unwind": "$chunks"
                },
                {
                    "$project": {
                        "title": 1,
                        "description": 1,
                        "content_type": 1,
                        "chunk_content": "$chunks.content",
                        "chunk_id": "$chunks.chunk_id",
                        "chunk_index": "$chunks.metadata.chunk_index",
                        "embedding": "$chunks.embedding"
                    }
                }
            ]
            
            # Execute pipeline
            cursor = self.collection.aggregate(pipeline)
            
            # Calculate similarities and sort
            results = []
            async for doc in cursor:
                # Calculate cosine similarity
                doc_embedding = doc.get("embedding", [])
                if doc_embedding:
                    # Simple dot product for normalized vectors (cosine similarity)
                    similarity = sum(a * b for a, b in zip(query_embedding, doc_embedding))
                    
                    if similarity >= similarity_threshold:
                        results.append({
                            "item_id": str(doc["_id"]),
                            "title": doc.get("title"),
                            "description": doc.get("description"),
                            "content_type": doc.get("content_type"),
                            "chunk_content": doc.get("chunk_content"),
                            "chunk_id": doc.get("chunk_id"),
                            "chunk_index": doc.get("chunk_index"),
                            "similarity_score": similarity
                        })
            
            # Sort by similarity and limit
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            results = results[:limit]
            
            logger.info(f"Found {len(results)} similar documents for query")
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {e}")
            return []


# Create singleton instance
langchain_ingestion_service = LangChainIngestionService()