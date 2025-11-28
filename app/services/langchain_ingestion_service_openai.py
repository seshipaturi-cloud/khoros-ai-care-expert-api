"""
LangChain-based document ingestion service for processing and vectorizing documents
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import time
from bson import ObjectId

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
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
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_community.document_loaders import S3FileLoader

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
    """Service for document ingestion using LangChain"""
    
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
        
        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key,
            model="text-embedding-3-small"
        )
        
        # Text splitter configuration
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )
        
        # Vector store will be initialized per item
        self.vector_store = None
    
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
    
    async def process_document(
        self,
        item_id: str,
        s3_key: str,
        mime_type: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Dict[str, Any]:
        """Process document using LangChain pipeline"""
        
        start_time = time.time()
        temp_file_path = None
        
        stats = {
            'success': False,
            'chunks_created': 0,
            'total_tokens': 0,
            'embedding_tokens': 0,
            'processing_time': 0,
            'char_count': 0,
            'word_count': 0,
            'error': None
        }
        
        try:
            # Update status to processing
            await self.collection.update_one(
                {'_id': ObjectId(item_id)},
                {'$set': {'indexing_status': 'processing'}}
            )
            
            # Download file from S3
            temp_file_path = await self.download_from_s3(s3_key)
            
            # Load document using appropriate loader
            loader = self._get_loader_for_file(temp_file_path, mime_type)
            documents = loader.load()
            
            if not documents:
                raise ValueError("No content extracted from document")
            
            # Combine all document content
            full_text = "\n".join([doc.page_content for doc in documents])
            stats['char_count'] = len(full_text)
            stats['word_count'] = len(full_text.split())
            
            # Update text splitter if custom parameters provided
            if chunk_size != 1000 or chunk_overlap != 200:
                self.text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    length_function=len,
                    separators=["\n\n", "\n", ".", "!", "?", " ", ""]
                )
            
            # Split documents into chunks
            split_docs = self.text_splitter.split_documents(documents)
            stats['chunks_created'] = len(split_docs)
            
            # Add metadata to each chunk
            for i, doc in enumerate(split_docs):
                doc.metadata.update({
                    'item_id': item_id,
                    's3_key': s3_key,
                    'chunk_index': i,
                    'total_chunks': len(split_docs),
                    'mime_type': mime_type,
                    'processed_at': datetime.utcnow().isoformat()
                })
            
            # Generate embeddings and prepare for storage
            chunks_with_embeddings = []
            total_tokens = 0
            
            for i, doc in enumerate(split_docs):
                # Generate embedding for chunk
                embedding = self.embeddings.embed_query(doc.page_content)
                
                # Estimate tokens (rough approximation)
                chunk_tokens = len(doc.page_content) // 4
                total_tokens += chunk_tokens
                
                chunk_data = {
                    'chunk_id': i,
                    'text': doc.page_content,
                    'embedding': embedding,
                    'metadata': doc.metadata,
                    'tokens': chunk_tokens,
                    'embedding_model': 'text-embedding-3-small',
                    'created_at': datetime.utcnow()
                }
                
                chunks_with_embeddings.append(chunk_data)
            
            stats['total_tokens'] = total_tokens
            stats['embedding_tokens'] = total_tokens
            
            # Calculate processing time
            processing_time = time.time() - start_time
            stats['processing_time'] = round(processing_time, 2)
            
            # Store in MongoDB with embeddings and statistics
            update_result = await self.collection.update_one(
                {'_id': ObjectId(item_id)},
                {
                    '$set': {
                        'chunks': chunks_with_embeddings,
                        'indexed_content': full_text[:5000],  # Store first 5000 chars for preview
                        'embeddings_processed': True,
                        'embeddings_processed_at': datetime.utcnow(),
                        'indexing_status': 'completed',
                        'ingestion_stats': {
                            'chunks_count': stats['chunks_created'],
                            'total_tokens': stats['total_tokens'],
                            'embedding_tokens': stats['embedding_tokens'],
                            'char_count': stats['char_count'],
                            'word_count': stats['word_count'],
                            'processing_time_seconds': stats['processing_time'],
                            'embedding_model': 'text-embedding-3-small',
                            'ingested_at': datetime.utcnow(),
                            'langchain_version': '0.3.13'
                        }
                    }
                }
            )
            
            stats['success'] = update_result.modified_count > 0
            
            logger.info(
                f"Successfully processed document {item_id}: "
                f"{stats['chunks_created']} chunks, {stats['total_tokens']} tokens"
            )
            
        except Exception as e:
            logger.error(f"Error processing document {item_id}: {e}")
            stats['error'] = str(e)
            
            # Update status to failed
            await self.collection.update_one(
                {'_id': ObjectId(item_id)},
                {
                    '$set': {
                        'indexing_status': 'failed',
                        'indexing_error': str(e),
                        'ingestion_stats': {
                            'error': str(e),
                            'failed_at': datetime.utcnow()
                        }
                    }
                }
            )
        
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
        
        return stats
    
    async def search_similar_documents(
        self,
        query: str,
        brand_id: str,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity"""
        
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # MongoDB Atlas vector search pipeline
            pipeline = [
                {
                    '$search': {
                        'index': 'kb_index',  # Ensure this index exists in Atlas
                        'knnBeta': {
                            'vector': query_embedding,
                            'path': 'chunks.embedding',
                            'k': limit * 2,
                            'filter': {'brand_id': brand_id}
                        }
                    }
                },
                {
                    '$project': {
                        '_id': 1,
                        'title': 1,
                        'content_type': 1,
                        'chunks': 1,
                        'score': {'$meta': 'searchScore'}
                    }
                },
                {
                    '$match': {
                        'score': {'$gte': similarity_threshold}
                    }
                },
                {
                    '$limit': limit
                }
            ]
            
            results = []
            async for doc in self.collection.aggregate(pipeline):
                # Find the best matching chunk
                best_chunk = None
                if doc.get('chunks'):
                    # Get the first chunk as representative
                    best_chunk = doc['chunks'][0] if doc['chunks'] else None
                
                results.append({
                    'item_id': str(doc['_id']),
                    'title': doc.get('title', ''),
                    'content_type': doc.get('content_type', ''),
                    'chunk_text': best_chunk.get('text', '') if best_chunk else '',
                    'score': float(doc.get('score', 0))
                })
            
            logger.info(f"Vector search returned {len(results)} results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    async def reindex_item(self, item_id: str) -> Dict[str, Any]:
        """Reindex an existing item"""
        
        try:
            # Get item from database
            item = await self.collection.find_one({'_id': ObjectId(item_id)})
            
            if not item:
                raise ValueError(f"Item {item_id} not found")
            
            if not item.get('file') or not item['file'].get('s3_key'):
                raise ValueError(f"Item {item_id} has no associated file")
            
            # Process the document
            return await self.process_document(
                item_id=item_id,
                s3_key=item['file']['s3_key'],
                mime_type=item['file'].get('mime_type', 'text/plain')
            )
            
        except Exception as e:
            logger.error(f"Error reindexing item {item_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Create singleton instance
langchain_ingestion_service = LangChainIngestionService()