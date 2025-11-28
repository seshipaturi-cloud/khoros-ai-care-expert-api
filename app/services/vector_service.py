from typing import List, Dict, Any, Optional
import numpy as np
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from datetime import datetime
import time
from config.settings import settings
from app.utils.cache import (
    embedding_cache,
    search_cache,
    create_embedding_cache_key,
    create_search_cache_key
)

# Embedding provider imports
try:
    import openai
except ImportError:
    openai = None
    
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

logger = logging.getLogger(__name__)


class VectorService:
    def __init__(self):
        # MongoDB connection for vector operations
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.database_name]
        self.items_collection = self.db.knowledge_base_items  # Complete items
        self.vectors_collection = self.db.knowledge_base_vectors  # Vector chunks
        self.collection = self.db.knowledge_base_items  # Keep for compatibility
        
        # Initialize embedding provider based on configuration
        self.embedding_provider = settings.embedding_provider.lower()
        self.embedding_client = None
        self.embedding_model = None
        self._initialize_embedding_provider()
        
        # Ensure vector index exists
        self._ensure_vector_index()
    
    def _initialize_embedding_provider(self):
        """Initialize the embedding provider based on configuration"""
        logger.info(f"Initializing embedding provider: {self.embedding_provider}")

        if self.embedding_provider == "openai":
            if not openai:
                logger.error("OpenAI library not installed. Falling back to HuggingFace.")
                self.embedding_provider = "huggingface"
            elif not settings.openai_api_key:
                logger.error("OpenAI API key not configured. Falling back to HuggingFace.")
                self.embedding_provider = "huggingface"
            else:
                self.embedding_client = openai.OpenAI(api_key=settings.openai_api_key)
                self.embedding_model = settings.openai_embedding_model or "text-embedding-3-small"
                logger.info(f"Using OpenAI embeddings with model: {self.embedding_model}")
                return

        elif self.embedding_provider == "anthropic":
            # Anthropic doesn't provide embedding models, fallback to HuggingFace
            logger.warning("Anthropic doesn't provide embedding models. Falling back to HuggingFace.")
            self.embedding_provider = "huggingface"

        # Default to HuggingFace
        if self.embedding_provider == "huggingface" or not self.embedding_client:
            if not SentenceTransformer:
                logger.error("sentence-transformers library not installed. Installing default embeddings.")
                raise ImportError("No embedding provider available. Please install sentence-transformers or configure OpenAI.")

            model_name = settings.huggingface_embedding_model or "sentence-transformers/all-MiniLM-L6-v2"
            try:
                # Fix for macOS heap corruption: disable MPS and set single thread
                import torch
                import os
                os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
                os.environ['OMP_NUM_THREADS'] = '1'
                os.environ['MKL_NUM_THREADS'] = '1'
                torch.set_num_threads(1)

                self.embedding_client = SentenceTransformer(model_name, device='cpu')
                self.embedding_model = model_name
                logger.info(f"Using HuggingFace embeddings with model: {self.embedding_model} (CPU mode)")
            except Exception as e:
                logger.error(f"Failed to load HuggingFace model {model_name}: {e}")
                # Try with a simpler model
                self.embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
                self.embedding_client = SentenceTransformer(self.embedding_model, device='cpu')
                logger.info(f"Loaded fallback HuggingFace model: {self.embedding_model}")
    
    def _ensure_vector_index(self):
        """Ensure MongoDB Atlas vector search index exists"""
        try:
            # This would be done in MongoDB Atlas UI or via Atlas API
            # Creating a vector search index programmatically requires Atlas API
            expected_dimensions = self._get_embedding_dimension()
            logger.info(f"Vector search index 'kb_index' should be configured for {expected_dimensions} dimensions")
            logger.info(f"Current embedding provider: {self.embedding_provider} using {self.embedding_model}")
            
            # Log warning if using HuggingFace with potentially mismatched index
            if self.embedding_provider == "huggingface" and expected_dimensions == 384:
                logger.warning("Ensure MongoDB Atlas kb_index is configured for 384 dimensions (HuggingFace)")
            elif self.embedding_provider == "openai" and expected_dimensions == 1536:
                logger.warning("Ensure MongoDB Atlas kb_index is configured for 1536 dimensions (OpenAI)")
                
        except Exception as e:
            logger.error(f"Error ensuring vector index: {e}")
    
    async def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for a text using the configured provider (with caching)"""
        try:
            # Create cache key based on text, provider, and model
            cache_key = create_embedding_cache_key(text, self.embedding_provider, self.embedding_model)

            # Check cache first
            cached_embedding = embedding_cache.get(cache_key)
            if cached_embedding is not None:
                logger.info(f"✅ Embedding cache hit (provider: {self.embedding_provider})")
                return cached_embedding

            logger.info(f"❌ Embedding cache miss, generating... (provider: {self.embedding_provider})")

            if self.embedding_provider == "openai":
                # Use OpenAI API
                response = self.embedding_client.embeddings.create(
                    model=self.embedding_model,
                    input=text
                )
                embedding = response.data[0].embedding

            elif self.embedding_provider == "huggingface":
                # Use HuggingFace SentenceTransformer
                # Note: SentenceTransformer is synchronous, but we're in an async context
                import asyncio
                from concurrent.futures import ThreadPoolExecutor

                # Create a dedicated thread pool with single thread to avoid memory corruption
                loop = asyncio.get_event_loop()

                # Use partial to avoid passing the entire model through pickle
                from functools import partial
                encode_fn = partial(self.embedding_client.encode, show_progress_bar=False, batch_size=1)

                embedding = await loop.run_in_executor(
                    None,  # Use default executor
                    encode_fn,
                    text
                )
                embedding = embedding.tolist()  # Convert numpy array to list

            else:
                raise ValueError(f"Unsupported embedding provider: {self.embedding_provider}")

            # Store in cache (1 hour TTL for embeddings since they're deterministic)
            embedding_cache.set(cache_key, embedding, ttl=3600)

            logger.debug(f"Generated and cached embedding with dimension: {len(embedding)} using {self.embedding_provider}")
            return embedding

        except Exception as e:
            logger.error(f"Error generating embeddings with {self.embedding_provider}: {e}")
            raise
    
    async def chunk_text(
        self, 
        text: str, 
        chunk_size: int = 1000, 
        chunk_overlap: int = 200
    ) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks for better retrieval"""
        chunks = []
        
        if not text:
            return chunks
        
        # Simple character-based chunking
        # In production, use more sophisticated chunking (sentence boundaries, etc.)
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending
                for sep in ['. ', '! ', '? ', '\n\n', '\n']:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep != -1:
                        end = last_sep + len(sep)
                        break
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': chunk_text,
                    'start_char': start,
                    'end_char': end,
                    'chunk_size': len(chunk_text)
                })
                chunk_id += 1
            
            # Move start position with overlap
            start = end - chunk_overlap if end < len(text) else end
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks
    
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in text (rough estimation)"""
        # Rough estimation: 1 token ≈ 4 characters for English text
        # This is a simplified approach without tiktoken
        return len(text) // 4
    
    async def process_and_store_embeddings(
        self, 
        item_id: str,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Dict[str, Any]:
        """Process text into chunks and store with embeddings in separate collections"""
        start_time = time.time()
        stats = {
            'success': False,
            'chunks_created': 0,
            'total_tokens': 0,
            'embedding_tokens': 0,
            'processing_time': 0,
            'char_count': len(text),
            'word_count': len(text.split()),
            'error': None
        }
        
        try:
            # Get the knowledge base item metadata
            item = await self.items_collection.find_one({'_id': item_id})
            if not item:
                raise ValueError(f"Knowledge base item {item_id} not found")
            
            # Count total tokens in original text
            stats['total_tokens'] = self.count_tokens(text)
            
            # Create chunks
            chunks = await self.chunk_text(text, chunk_size, chunk_overlap)
            stats['chunks_created'] = len(chunks)
            
            # Delete existing vectors for this item if any
            await self.vectors_collection.delete_many({'knowledge_item_id': item_id})
            
            # Generate embeddings and store each chunk separately
            vector_docs = []
            embedding_tokens = 0
            
            for i, chunk in enumerate(chunks):
                chunk_tokens = self.count_tokens(chunk['text'])
                embedding_tokens += chunk_tokens
                
                # Generate embedding for this chunk
                embedding = await self.generate_embeddings(chunk['text'])
                
                # Create vector document
                vector_doc = {
                    'knowledge_item_id': item_id,
                    'chunk_index': i,
                    'chunk_text': chunk['text'],
                    'embeddings': embedding,
                    
                    # Metadata from parent item
                    'title': item.get('title', ''),
                    'content_type': item.get('content_type', ''),
                    'company_id': item.get('company_id', ''),
                    'ai_agent_ids': item.get('ai_agent_ids', []),
                    'brand_ids': item.get('brand_ids', []),
                    
                    # Chunk-specific metadata
                    'start_position': chunk['start_char'],
                    'end_position': chunk['end_char'],
                    'token_count': chunk_tokens,
                    
                    # Processing details
                    'embedding_provider': self.embedding_provider,
                    'embedding_model': self.embedding_model,
                    'created_at': datetime.utcnow(),
                    
                    # Additional metadata
                    'metadata': item.get('metadata', {})
                }
                
                vector_docs.append(vector_doc)
            
            stats['embedding_tokens'] = embedding_tokens
            
            # Bulk insert all vector documents into the vectors collection
            if vector_docs:
                result = await self.vectors_collection.insert_many(vector_docs)
                logger.info(f"Inserted {len(result.inserted_ids)} vector documents into knowledge_base_vectors collection")
            
            # Calculate processing time
            processing_time = time.time() - start_time
            stats['processing_time'] = round(processing_time, 2)
            
            # Update the knowledge base item with processing stats
            result = await self.items_collection.update_one(
                {'_id': item_id},
                {
                    '$set': {
                        'total_chunks': stats['chunks_created'],
                        'total_tokens': stats['total_tokens'],
                        'embedding_provider': self.embedding_provider,
                        'embedding_model': self.embedding_model,
                        'embeddings_processed': True,
                        'embeddings_processed_at': datetime.utcnow(),
                        'indexing_status': 'completed',
                        'ingestion_stats': {
                            'chunks_created': stats['chunks_created'],
                            'total_characters': stats['char_count'],
                            'estimated_tokens': stats['total_tokens'],
                            'processing_time_seconds': stats['processing_time'],
                            'embedding_provider': self.embedding_provider,
                            'embedding_model': self.embedding_model,
                            'chunk_size': chunk_size,
                            'chunk_overlap': chunk_overlap,
                            'processed_at': datetime.utcnow()
                        }
                    }
                }
            )
            
            stats['success'] = result.modified_count > 0
            logger.info(f"Stored {len(vector_docs)} vector chunks for item {item_id}. Tokens: {stats['total_tokens']}")
            
        except Exception as e:
            logger.error(f"Error processing embeddings: {e}")
            stats['error'] = str(e)
            
            # Update status to failed with error details
            await self.items_collection.update_one(
                {'_id': item_id},
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
        
        return stats
    
    async def vector_search(
        self,
        query: str,
        company_id: Optional[str] = None,
        brand_ids: Optional[List[str]] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        content_types: Optional[List[str]] = None,
        agent_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search using MongoDB Atlas Search (with caching)"""
        try:
            # Create cache key for this search
            cache_key = create_search_cache_key(
                query=query,
                company_id=company_id,
                brand_ids=brand_ids,
                agent_ids=agent_ids,
                content_types=content_types,
                limit=limit,
                similarity_threshold=similarity_threshold
            )

            # Check cache first
            cached_results = search_cache.get(cache_key)
            if cached_results is not None:
                logger.info(f"✅ Search cache hit! Returning {len(cached_results)} cached results")
                return cached_results

            logger.info(f"🔍 Vector search started (cache miss)")
            logger.info(f"   Query: {query[:100]}...")
            logger.info(f"   Filters - company_id: {company_id}, agent_ids: {agent_ids}, brand_ids: {brand_ids}")
            logger.info(f"   Limit: {limit}, Threshold: {similarity_threshold}")

            # Generate query embedding (this will use embedding cache)
            query_embedding = await self.generate_embeddings(query)
            logger.info(f"   Generated embedding with {len(query_embedding)} dimensions")
            
            # Build filter criteria for MongoDB Atlas Search
            # Atlas Search requires specific operator syntax for filters in knnBeta
            filter_conditions = []
            
            if company_id:
                filter_conditions.append({
                    'equals': {
                        'path': 'company_id',
                        'value': company_id
                    }
                })
            
            if brand_ids and len(brand_ids) > 0:
                filter_conditions.append({
                    'in': {
                        'path': 'brand_ids',
                        'value': brand_ids
                    }
                })
            
            if content_types and len(content_types) > 0:
                filter_conditions.append({
                    'in': {
                        'path': 'content_type',
                        'value': content_types
                    }
                })
            
            if agent_ids and len(agent_ids) > 0:
                filter_conditions.append({
                    'in': {
                        'path': 'ai_agent_ids',
                        'value': agent_ids
                    }
                })
            
            # Build the knnBeta query
            knn_query = {
                'vector': query_embedding,
                'path': 'embeddings',  # Using root-level embeddings field
                'k': limit * 3  # Get more results for filtering
            }
            
            # Add filter only if there are conditions
            if filter_conditions:
                if len(filter_conditions) == 1:
                    knn_query['filter'] = filter_conditions[0]
                else:
                    # Multiple conditions need to be wrapped in compound.must
                    knn_query['filter'] = {
                        'compound': {
                            'must': filter_conditions
                        }
                    }
            
            # MongoDB Atlas Vector Search using $vectorSearch
            # Your existing kb_index is a Lucene vector index on knowledge_base_vectors
            pipeline = [
                {
                    '$vectorSearch': {
                        'index': 'kb_index',  # Your existing index on knowledge_base_vectors
                        'path': 'embeddings',
                        'queryVector': query_embedding,
                        'numCandidates': limit * 10,  # Candidates to consider
                        'limit': limit * 3  # Results to return before filtering
                    }
                },
                {
                    '$project': {
                        'knowledge_item_id': 1,
                        'chunk_text': 1,
                        'chunk_index': 1,
                        'title': 1,
                        'content_type': 1,
                        'metadata': 1,
                        'company_id': 1,
                        'ai_agent_ids': 1,
                        'brand_ids': 1,
                        'score': {'$meta': 'vectorSearchScore'}  # Use vectorSearchScore for $vectorSearch
                    }
                }
            ]
            
            # Add post-processing filters if needed
            # Note: company_id='1' is treated as a default/search all
            if company_id or agent_ids or brand_ids or content_types:
                filter_conditions = {}
                
                # Only add company_id filter if it's not '1' (which is the default)
                if company_id and company_id != '1':
                    filter_conditions['company_id'] = company_id
                    logger.info(f"   Adding company_id filter: {company_id}")
                elif company_id == '1':
                    logger.info(f"   Company_id='1' detected - searching across all companies")
                    
                if agent_ids:
                    filter_conditions['ai_agent_ids'] = {'$in': agent_ids}
                    logger.info(f"   Adding agent_ids filter: {agent_ids}")
                if brand_ids:
                    filter_conditions['brand_ids'] = {'$in': brand_ids}
                    logger.info(f"   Adding brand_ids filter: {brand_ids}")
                if content_types:
                    filter_conditions['content_type'] = {'$in': content_types}
                    logger.info(f"   Adding content_types filter: {content_types}")
                
                if filter_conditions:  # Only add $match if there are actual filters
                    logger.info(f"   Post-processing filters: {filter_conditions}")
                    pipeline.append({'$match': filter_conditions})
                else:
                    logger.info(f"   No post-processing filters applied")
            
            # Add limit (score filtering is handled after projection)
            pipeline.append({'$limit': limit})
            
            # Execute search on vectors collection
            results = []
            logger.info(f"   Executing vector search pipeline on {self.vectors_collection.name}")
            
            # Count total documents before filtering
            total_docs = await self.vectors_collection.count_documents({})
            logger.info(f"   Total documents in collection: {total_docs}")
            
            # Log pipeline for debugging
            logger.debug(f"   Pipeline: {pipeline}")
            
            async for doc in self.vectors_collection.aggregate(pipeline):
                # Vector document already contains the chunk text and metadata
                score = float(doc.get('score', 0))
                
                # Filter by similarity threshold
                if score < similarity_threshold:
                    logger.debug(f"   Skipping result with low score: {score:.3f} < {similarity_threshold}")
                    continue
                    
                title = doc.get('title', '')
                
                result = {
                    'item_id': doc.get('knowledge_item_id'),
                    'title': title,
                    'content_type': doc.get('content_type', ''),
                    'chunk': doc.get('chunk_text', ''),
                    'chunk_index': doc.get('chunk_index', 0),
                    'score': score,
                    'metadata': doc.get('metadata', {})
                }
                results.append(result)
                logger.debug(f"   Found: {title} (score: {score:.3f})")
            
            logger.info(f"Vector search returned {len(results)} results")
            if results:
                logger.info(f"   Top result: {results[0]['title']} (score: {results[0]['score']:.3f})")
            else:
                logger.info(f"   No results found for query: {query[:50]}...")
                
                # Additional debugging for no results
                if company_id or agent_ids or brand_ids:
                    # Check what documents exist with these filters
                    filter_check = {}
                    if company_id:
                        filter_check['company_id'] = company_id
                    if agent_ids:
                        filter_check['ai_agent_ids'] = {'$in': agent_ids}
                    
                    sample_count = await self.vectors_collection.count_documents(filter_check)
                    logger.info(f"   Documents matching filters: {sample_count}")
                    
                    # Get a sample document to check structure
                    sample_doc = await self.vectors_collection.find_one({})
                    if sample_doc:
                        logger.info(f"   Sample doc company_id: {sample_doc.get('company_id')}")
                        logger.info(f"   Sample doc agent_ids: {sample_doc.get('ai_agent_ids', [])}")
                        logger.info(f"   Sample doc has embeddings: {'embeddings' in sample_doc}")

            # Cache the results (5 minutes TTL for search results)
            search_cache.set(cache_key, results, ttl=300)
            logger.info(f"💾 Cached search results ({len(results)} items) for 5 minutes")

            return results

        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    async def hybrid_search(
        self,
        query: str,
        company_id: str,
        brand_ids: Optional[List[str]] = None,
        limit: int = 10,
        text_weight: float = 0.3,
        vector_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining text and vector search"""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embeddings(query)
            
            # MongoDB Atlas Hybrid Search
            pipeline = [
                {
                    '$search': {
                        'index': 'kb_hybrid_index',
                        'compound': {
                            'should': [
                                {
                                    'text': {
                                        'query': query,
                                        'path': ['title', 'description', 'indexed_content'],
                                        'score': {'boost': {'value': text_weight}}
                                    }
                                },
                                {
                                    'knnBeta': {
                                        'vector': query_embedding,
                                        'path': 'embeddings',  # Using root-level embeddings field
                                        'k': limit * 2,
                                        'score': {'boost': {'value': vector_weight}}
                                    }
                                }
                            ],
                            'filter': [
                                {'equals': {'path': 'company_id', 'value': company_id}}
                            ] + ([{'in': {'path': 'brand_ids', 'value': brand_ids}}] if brand_ids else [])
                        }
                    }
                },
                {
                    '$project': {
                        '_id': 1,
                        'title': 1,
                        'content_type': 1,
                        'description': 1,
                        'score': {'$meta': 'searchScore'}
                    }
                },
                {
                    '$limit': limit
                }
            ]
            
            results = []
            async for doc in self.items_collection.aggregate(pipeline):
                results.append({
                    'item_id': str(doc['_id']),
                    'title': doc.get('title', ''),
                    'content_type': doc.get('content_type', ''),
                    'description': doc.get('description', ''),
                    'score': float(doc.get('score', 0))
                })
            
            logger.info(f"Hybrid search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (norm1 * norm2)
    
    async def delete_embeddings(self, item_id: str) -> bool:
        """Delete embeddings for an item from both collections"""
        try:
            # Delete from vectors collection
            delete_result = await self.vectors_collection.delete_many(
                {'knowledge_item_id': item_id}
            )
            
            # Update item status
            update_result = await self.items_collection.update_one(
                {'_id': item_id},
                {
                    '$unset': {
                        'total_chunks': '',
                        'embeddings_processed': '',
                        'embeddings_processed_at': '',
                        'ingestion_stats': ''
                    },
                    '$set': {
                        'indexing_status': 'pending'
                    }
                }
            )
            
            logger.info(f"Deleted {delete_result.deleted_count} vector chunks for item {item_id}")
            return update_result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting embeddings: {e}")
            return False
    
    def get_embedding_info(self) -> Dict[str, Any]:
        """Get information about the current embedding configuration"""
        dimension = self._get_embedding_dimension()
        return {
            'provider': self.embedding_provider,
            'model': self.embedding_model,
            'dimension': dimension,
            'status': 'active' if self.embedding_client else 'inactive',
            'index_configuration': {
                'expected_dimension': dimension,
                'index_name': 'kb_index',
                'path': 'embeddings',  # Root-level embeddings field
                'similarity': 'cosine'
            }
        }
    
    async def check_embedding_compatibility(self, item_id: str) -> Dict[str, Any]:
        """Check if an item's embeddings are compatible with current configuration"""
        try:
            # Check if item exists
            item = await self.items_collection.find_one({'_id': item_id})
            if not item:
                return {'compatible': False, 'reason': 'Item not found'}
            
            # Check for vectors in the vectors collection
            vector = await self.vectors_collection.find_one({'knowledge_item_id': item_id})
            if not vector:
                return {'compatible': False, 'reason': 'No embeddings found'}
            
            embeddings = vector.get('embeddings', [])
            actual_dimension = len(embeddings) if embeddings else 0
            expected_dimension = self._get_embedding_dimension()
            
            return {
                'compatible': actual_dimension == expected_dimension,
                'actual_dimension': actual_dimension,
                'expected_dimension': expected_dimension,
                'embedding_provider': item.get('embedding_provider', 'unknown'),
                'embedding_model': item.get('embedding_model', 'unknown'),
                'needs_reindexing': actual_dimension != expected_dimension
            }
            
        except Exception as e:
            logger.error(f"Error checking embedding compatibility: {e}")
            return {'compatible': False, 'reason': str(e)}
    
    def _get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings for the current model"""
        if self.embedding_provider == "openai":
            # OpenAI embedding dimensions
            if "text-embedding-3-large" in self.embedding_model:
                return 3072
            elif "text-embedding-3-small" in self.embedding_model:
                return 1536
            elif "text-embedding-ada-002" in self.embedding_model:
                return 1536
            else:
                return 1536  # Default for OpenAI
        
        elif self.embedding_provider == "huggingface":
            # HuggingFace model dimensions
            if "all-MiniLM-L6-v2" in self.embedding_model:
                return 384
            elif "all-mpnet-base-v2" in self.embedding_model:
                return 768
            elif "all-MiniLM-L12-v2" in self.embedding_model:
                return 384
            else:
                # Try to get dimension from model if loaded
                if self.embedding_client:
                    try:
                        test_embedding = self.embedding_client.encode("test")
                        return len(test_embedding)
                    except:
                        pass
                return 384  # Default for HuggingFace
        
        return 768  # Generic default


# Create a singleton instance
vector_service = VectorService()