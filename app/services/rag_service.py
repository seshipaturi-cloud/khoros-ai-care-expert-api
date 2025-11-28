"""
RAG (Retrieval Augmented Generation) Service for Knowledge Base Chat
"""

import os
# Set tokenizers parallelism to avoid warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
import anthropic

# LangChain imports - only for embeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG-based question answering on knowledge base"""
    
    def __init__(self):
        # MongoDB connection
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.database_name]
        self.kb_collection = self.db.knowledge_base_items
        self.chat_collection = self.db.chat_sessions
        
        # Initialize embeddings
        self.embeddings = self._initialize_embeddings()
        
        # Initialize Claude LLM
        self.llm = self._initialize_llm()
    
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
        else:
            return self._get_huggingface_embeddings()
    
    def _get_huggingface_embeddings(self):
        """Get HuggingFace embeddings"""
        logger.info(f"Using HuggingFace embeddings with model: {settings.huggingface_embedding_model}")
        return HuggingFaceEmbeddings(
            model_name=settings.huggingface_embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    
    def _initialize_llm(self):
        """Initialize LLM - use simple Anthropic client directly"""
        logger.info("Initializing LLM for RAG service")
        
        # Use direct Anthropic client - simple and reliable
        if settings.anthropic_api_key:
            try:
                logger.info("Using Anthropic Claude for RAG")
                self.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
                return self.anthropic_client
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic: {e}")
        
        # Try OpenAI as fallback
        if settings.openai_api_key:
            try:
                import openai
                logger.info("Using OpenAI GPT-4 as fallback for RAG")
                openai.api_key = settings.openai_api_key
                self.openai_client = openai
                return self.openai_client
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {e}")
        
        # If nothing works, raise error
        raise ValueError(
            "Failed to initialize any LLM. Please ensure either Anthropic or OpenAI API keys are configured."
        )

    async def _translate_query_if_needed(self, query: str) -> str:
        """Detect non-English queries and translate them to English for embedding"""
        try:
            # Quick check: if the query is mostly ASCII, it's likely English
            ascii_ratio = sum(ord(c) < 128 for c in query) / len(query) if query else 1
            if ascii_ratio > 0.9:
                return query  # Probably English, no translation needed

            # Use Claude to translate
            logger.info(f"🌐 Detected non-English query, translating...")

            if hasattr(self, 'anthropic_client'):
                message = self.anthropic_client.messages.create(
                    model=settings.anthropic_model or "claude-sonnet-4-5-20250929",
                    max_tokens=200,
                    messages=[{
                        "role": "user",
                        "content": f"Translate the following text to English. Return ONLY the English translation, nothing else:\n\n{query}"
                    }]
                )
                translated = message.content[0].text.strip()
                logger.info(f"✅ Translated: '{query[:50]}...' -> '{translated[:50]}...'")
                return translated
            elif hasattr(self, 'openai_client'):
                response = await asyncio.to_thread(
                    self.openai_client.ChatCompletion.create,
                    model="gpt-4o-mini",
                    messages=[{
                        "role": "user",
                        "content": f"Translate the following text to English. Return ONLY the English translation:\n\n{query}"
                    }],
                    max_tokens=200
                )
                translated = response.choices[0].message.content.strip()
                logger.info(f"✅ Translated: '{query[:50]}...' -> '{translated[:50]}...'")
                return translated
            else:
                logger.warning("No LLM available for translation, using original query")
                return query

        except Exception as e:
            logger.error(f"Translation failed: {e}, using original query")
            return query

    async def vector_search(
        self,
        query: str,
        brand_id: str = None,
        company_id: Optional[str] = None,  # Accept company_id too
        agent_id: Optional[str] = None,
        limit: int = 5,
        similarity_threshold: float = 0.3  # Lowered threshold for better recall
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search on knowledge base"""
        try:
            # Import vector_service to use the updated vector search
            from app.services.vector_service import vector_service
            
            # Use the vector_service which searches knowledge_base_vectors collection
            results = await vector_service.vector_search(
                query=query,
                company_id=company_id or brand_id,  # Use either company_id or brand_id
                agent_ids=[agent_id] if agent_id else None,
                limit=limit,
                similarity_threshold=similarity_threshold
            )
            
            # Format results for consistency with generate_answer expectations
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "item_id": result.get("item_id", ""),  # Add item_id for hybrid search
                    "chunk_content": result.get("chunk", ""),  # Changed from "content" to "chunk_content"
                    "title": result.get("title", "Unknown"),
                    "score": result.get("score", 0),
                    "similarity": result.get("score", 0),  # Add similarity field for hybrid search
                    "metadata": result.get("metadata", {})
                })
            
            logger.info(f"Vector search via vector_service returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    async def text_search_TEMP_DISABLED(
        self,
        query: str,
        brand_id: str = None,
        company_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """OLD METHOD - Perform text search on knowledge base"""
        # OLD CODE - keeping for reference
        try:
            # If agent_id is provided, use it directly
            if agent_id:
                match_conditions.append({
                    "$or": [
                        {"ai_agent_ids": agent_id},  # Check in agent_ids array
                        {"agent_id": agent_id},      # Check single agent_id field
                        {"agent_ids": agent_id}      # Alternative field name
                    ]
                })
            else:
                # Fall back to company_id/brand_id matching
                if company_id:
                    match_conditions.append({"company_id": company_id})
                
                if brand_id:
                    match_conditions.append({
                        "$or": [
                            {"brand_id": brand_id},
                            {"brand_ids": brand_id}
                        ]
                    })
                
                # If no filters at all, try to match any documents
                if not match_conditions:
                    search_id = brand_id or company_id
                    if search_id:
                        match_conditions.append({
                            "$or": [
                                {"company_id": search_id},
                                {"brand_id": search_id},
                                {"brand_ids": search_id}
                            ]
                        })
            
            # Build final match criteria
            if match_conditions:
                match_criteria = {
                    "$and": match_conditions,
                    "indexing_status": "completed"
                }
            else:
                # If no conditions, just match completed documents
                match_criteria = {"indexing_status": "completed"}
            
            # Don't filter by agent_id for now since the documents have different agent_ids
            # if agent_id and agent_id != 'default':
            #     match_criteria["agent_ids"] = agent_id
            
            logger.info(f"Vector search match criteria: {match_criteria}")
            
            # First check if we have any documents with chunks matching our criteria
            docs_with_chunks = await self.kb_collection.count_documents({
                **match_criteria,
                "chunks": {"$exists": True, "$ne": []}
            })
            logger.info(f"Documents with chunks matching criteria: {docs_with_chunks}")
            
            # Also check total docs with chunks (regardless of criteria)
            total_with_chunks = await self.kb_collection.count_documents({
                "chunks": {"$exists": True, "$ne": []},
                "indexing_status": "completed"
            })
            logger.info(f"Total documents with chunks in DB: {total_with_chunks}")
            
            # Debug: Check a sample document's chunks
            sample_doc = await self.kb_collection.find_one({
                "chunks": {"$exists": True, "$ne": []},
                "indexing_status": "completed"
            })
            if sample_doc:
                chunks = sample_doc.get('chunks', [])
                if chunks and len(chunks) > 0:
                    has_embeddings = 'embedding' in chunks[0]
                    embedding_size = len(chunks[0].get('embedding', [])) if has_embeddings else 0
                    logger.debug(f"Sample doc '{sample_doc.get('title')}' has {len(chunks)} chunks, embeddings: {has_embeddings}, embedding size: {embedding_size}")
            
            # If no documents have chunks matching criteria, return empty results
            if docs_with_chunks == 0:
                logger.warning("No documents with chunks found matching search criteria.")
                return []
            
            # MongoDB vector search pipeline
            # New pipeline that works with embeddings array and chunks array
            pipeline = [
                {
                    "$match": match_criteria
                },
                {
                    "$match": {
                        "embeddings": {"$exists": True, "$ne": []},
                        "chunks": {"$exists": True, "$ne": []}
                    }
                },
                {
                    "$addFields": {
                        "chunk_with_similarity": {
                            "$map": {
                                "input": {"$range": [0, {"$size": "$chunks"}]},
                                "as": "idx",
                                "in": {
                                    "$mergeObjects": [
                                        {"$arrayElemAt": ["$chunks", "$$idx"]},
                                        {
                                            "similarity": {
                                                "$let": {
                                                    "vars": {
                                                        "embedding": {"$arrayElemAt": ["$embeddings", "$$idx"]},
                                                        "dotProduct": {
                                                            "$reduce": {
                                                                "input": {"$zip": {"inputs": [{"$arrayElemAt": ["$embeddings", "$$idx"]}, query_embedding]}},
                                                                "initialValue": 0,
                                                                "in": {"$add": ["$$value", {"$multiply": [{"$arrayElemAt": ["$$this", 0]}, {"$arrayElemAt": ["$$this", 1]}]}]}
                                                            }
                                                        }
                                                    },
                                                    "in": "$$dotProduct"
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    }
                },
                {
                    "$unwind": "$chunk_with_similarity"
                },
                {
                    "$match": {
                        "chunk_with_similarity.similarity": {"$gte": similarity_threshold}
                    }
                },
                {
                    "$sort": {"chunk_with_similarity.similarity": -1}
                },
                {
                    "$limit": limit
                },
                {
                    "$project": {
                        "chunk_content": "$chunk_with_similarity.content",
                        "chunk_metadata": "$chunk_with_similarity.metadata",
                        "similarity": "$chunk_with_similarity.similarity",
                        "title": 1,
                        "content_type": 1,
                        "item_id": "$_id",
                        "website_url": 1,
                        "file": 1
                    }
                }
            ]
            
            results = []
            async for doc in self.kb_collection.aggregate(pipeline):
                results.append(doc)
            
            logger.info(f"Vector search found {len(results)} relevant chunks")
            return results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    async def text_search(
        self,
        query: str,
        brand_id: str = None,
        company_id: Optional[str] = None,  # Accept company_id too
        agent_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Perform text search on knowledge base - using vector search as fallback for now"""
        # For now, just use vector search with lower threshold
        # TODO: Implement proper text search if needed
        return await self.vector_search(
            query=query,
            brand_id=brand_id,
            company_id=company_id,
            agent_id=agent_id,
            limit=limit,
            similarity_threshold=0.2  # Lower threshold for text-like search
        )
    
    # Removed old text_search implementation that was here
    
    async def _old_text_search_removed(self):
        # This method was removed - old implementation cleaned up
        pass
    
    async def hybrid_search(
        self,
        query: str,
        brand_id: str = None,
        company_id: Optional[str] = None,  # Accept company_id too
        agent_id: Optional[str] = None,
        limit: int = 5,
        vector_weight: float = 0.7,
        text_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining vector and text search"""
        try:
            # Perform both searches in parallel, passing company_id
            vector_task = self.vector_search(query, brand_id, company_id, agent_id, limit * 2)
            text_task = self.text_search(query, brand_id, company_id, agent_id, limit * 2)
            
            vector_results, text_results = await asyncio.gather(vector_task, text_task)
            
            # Combine and re-rank results
            combined_scores = {}
            all_results = {}
            
            # Process vector results
            for result in vector_results:
                item_id = result["item_id"]
                combined_scores[item_id] = result["similarity"] * vector_weight
                all_results[item_id] = result
            
            # Process text results - prefer text results for better content
            for result in text_results:
                item_id = result["item_id"]
                if item_id in combined_scores:
                    combined_scores[item_id] += result["similarity"] * text_weight
                    # If text result has more content, use it instead of vector result
                    if len(result.get("chunk_content", "")) > len(all_results[item_id].get("chunk_content", "")):
                        all_results[item_id] = result
                else:
                    combined_scores[item_id] = result["similarity"] * text_weight
                    all_results[item_id] = result
            
            # Sort by combined score and return top results
            sorted_items = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
            
            results = []
            for item_id, score in sorted_items:
                result = all_results[item_id]
                result["combined_score"] = score
                results.append(result)
            
            
            logger.info(f"Hybrid search found {len(results)} results")
            
            # Debug: Log what we're returning
            if not results:
                logger.warning(f"⚠️ Hybrid search returning empty results")
                logger.info(f"   Vector results: {len(vector_results)}, Text results: {len(text_results)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []
    
    async def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Generate answer using LLM with retrieved context"""
        try:
            # Prepare context from retrieved chunks
            context_texts = []
            sources = []
            
            for chunk in context_chunks:
                context_texts.append(chunk["chunk_content"])
                
                # Prepare source information
                source = {
                    "title": chunk.get("title", "Unknown"),
                    "type": chunk.get("content_type", "unknown"),
                    "item_id": chunk.get("item_id")
                }
                
                if chunk.get("website_url"):
                    source["url"] = chunk["website_url"]
                elif chunk.get("file"):
                    source["file"] = chunk["file"].get("name", "Unknown file")
                
                if source not in sources:
                    sources.append(source)
            
            context = "\n\n---\n\n".join(context_texts)
            
            # Log the context being sent to LLM for debugging
            logger.info(f"📝 Context being sent to LLM ({len(context)} chars):")
            for i, text in enumerate(context_texts[:3]):  # Log first 3 chunks
                preview = text[:200] + "..." if len(text) > 200 else text
                logger.info(f"  Chunk {i+1}: {preview}")
            
            # Prepare chat history context if available
            history_context = ""
            if chat_history and len(chat_history) > 0:
                history_lines = []
                for msg in chat_history[-5:]:  # Last 5 messages for context
                    role = "Human" if msg["role"] == "user" else "Assistant"
                    history_lines.append(f"{role}: {msg['content']}")
                history_context = "Previous conversation:\n" + "\n".join(history_lines) + "\n\n"
            
            # Create prompt
            system_prompt = """You are a helpful AI assistant that answers questions based on the provided knowledge base context. 
                    
When answering:
1. Use ONLY the information provided in the context to answer the question
2. If the context doesn't contain enough information to answer the question, say so clearly
3. Be accurate and cite specific information from the context when possible
4. Keep your answers concise but comprehensive
5. If multiple sources provide information, synthesize them appropriately"""
            
            user_prompt = f"""Context: {context}

{history_context}Question: {query}

Answer:"""
            
            # Use direct Anthropic API
            if isinstance(self.llm, anthropic.Anthropic):
                # Using Anthropic
                message = self.llm.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=1000,
                    temperature=0.3,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                response = message.content[0].text
            else:
                # Using OpenAI as fallback
                import openai
                completion = await openai.ChatCompletion.acreate(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                response = completion.choices[0].message.content
            
            return {
                "answer": response,
                "sources": sources,
                "context_used": len(context_texts)
            }
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return {
                "answer": f"I apologize, but I encountered an error while generating the answer: {str(e)}",
                "sources": [],
                "context_used": 0
            }
    
    async def chat(
        self,
        question: str = None,
        query: str = None,  # Support both question and query
        company_id: str = None,
        brand_id: str = None,  # Support both company_id and brand_id
        session_id: Optional[str] = None,
        agent_ids: Optional[List[str]] = None,  # Accept multiple agent IDs
        agent_id: Optional[str] = None,  # Also support single agent ID
        search_type: str = "hybrid",  # "vector", "text", or "hybrid"
        search_limit: int = 5,
        limit: int = None,  # Support both search_limit and limit
        content_types: Optional[List[str]] = None,
        **kwargs  # Accept any other parameters
    ) -> Dict[str, Any]:
        """Main chat interface for RAG-based Q&A"""
        try:
            # Handle parameter variations
            query = question or query
            if not query:
                raise ValueError("Either 'question' or 'query' parameter is required")
            
            # Keep both company_id and brand_id separate - don't merge them
            # Allow search by agent_id alone
            if not company_id and not brand_id and not agent_id:
                raise ValueError("Either 'company_id', 'brand_id', or 'agent_id' parameter is required")
            limit = search_limit or limit or 5
            
            # Handle agent IDs - could be a list or single ID
            if agent_ids and len(agent_ids) > 0:
                agent_id = agent_ids[0]  # Use first agent ID for now
            elif not agent_id:
                agent_id = None
            
            # If no company_id but we have agent_id, fetch company_id from agent
            if not company_id and agent_id:
                try:
                    from bson import ObjectId
                    agent_doc = await self.db.ai_agents.find_one({'_id': ObjectId(agent_id)})
                    if agent_doc:
                        company_id = agent_doc.get('company_id')
                        logger.info(f"📋 Retrieved company_id from agent: {company_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to fetch company_id from agent {agent_id}: {e}")
            
            logger.info(f"Processing chat query: {query[:100] if len(query) > 100 else query}... with {search_type} search")
            logger.info(f"Search parameters - brand_id: {brand_id}, company_id: {company_id}, agent_id: {agent_id}, agent_ids: {agent_ids}, limit: {limit}")

            # Translate non-English queries to English for better embedding matching
            original_query = query
            query = await self._translate_query_if_needed(query)
            if query != original_query:
                logger.info(f"🌐 Translated query from: '{original_query[:50]}...' to: '{query[:50]}...'")

            # Get chat history if session exists
            chat_history = []
            if session_id:
                session = await self.chat_collection.find_one({"_id": session_id})
                if session:
                    chat_history = session.get("messages", [])
            
            # Perform search based on type - pass both company_id and brand_id
            # Use company_id as brand_id if brand_id is not provided
            search_brand_id = brand_id or company_id
            
            if search_type == "vector":
                search_results = await self.vector_search(query, search_brand_id, company_id, agent_id, limit)
            elif search_type == "text":
                search_results = await self.text_search(query, search_brand_id, company_id, agent_id, limit)
            else:  # hybrid
                search_results = await self.hybrid_search(query, search_brand_id, company_id, agent_id, limit)
            
            # Generate answer if we have context
            logger.info(f"🔍 Search returned {len(search_results) if search_results else 0} results")
            if search_results:
                logger.info(f"✅ Found results, generating answer...")
                response = await self.generate_answer(query, search_results, chat_history)
            else:
                logger.warning(f"❌ No search results found for query: {query}")
                logger.info(f"🔍 Debug: Checking if any documents exist in DB...")
                
                # Debug: Check if there are ANY documents
                total_docs = await self.kb_collection.count_documents({"indexing_status": "completed"})
                logger.info(f"📚 Total completed documents in DB: {total_docs}")
                
                # Check documents for this brand/company
                search_id = brand_id or company_id
                if search_id:
                    brand_docs = await self.kb_collection.count_documents({
                        "$or": [
                            {"company_id": search_id},
                            {"brand_ids": search_id},
                            {"brand_id": search_id}
                        ],
                        "indexing_status": "completed"
                    })
                    logger.info(f"📚 Documents for ID {search_id}: {brand_docs}")
                
                response = {
                    "answer": "I couldn't find any relevant information in the knowledge base to answer your question. Please try rephrasing your question or ask about topics that have been added to the knowledge base.",
                    "sources": [],
                    "context_used": 0
                }
            
            # Save to chat history
            if session_id:
                await self.chat_collection.update_one(
                    {"_id": session_id},
                    {
                        "$push": {
                            "messages": {
                                "$each": [
                                    {"role": "user", "content": query, "timestamp": datetime.utcnow()},
                                    {"role": "assistant", "content": response["answer"], "timestamp": datetime.utcnow()}
                                ]
                            }
                        },
                        "$set": {"last_updated": datetime.utcnow()}
                    }
                )
            
            # Format sources to match expected structure
            formatted_sources = []
            for source in response.get("sources", []):
                formatted_sources.append({
                    "item_id": source.get("item_id", ""),
                    "title": source.get("title", "Unknown"),
                    "content_type": source.get("type", source.get("content_type", "unknown")),
                    "score": 0.95,  # Default score
                    "search_type": search_type,
                    "snippet": source.get("snippet", "")
                })
            
            return {
                "success": True,
                "answer": response["answer"],
                "sources": formatted_sources,
                "context_used": response["context_used"],
                "search_type": search_type,
                "search_results_count": len(formatted_sources),
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                "success": False,
                "answer": f"I apologize, but I encountered an error: {str(e)}",
                "sources": [],
                "context_used": 0,
                "search_type": search_type,
                "search_results_count": 0,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def create_chat_session(self, company_id: str = None, brand_id: str = None, user_id: str = None) -> str:
        """Create a new chat session"""
        from bson import ObjectId
        
        # Support both company_id and brand_id
        brand_id = company_id or brand_id
        if not brand_id:
            brand_id = "unknown"  # Use a neutral default for session creation
        
        session_id = str(ObjectId())
        await self.chat_collection.insert_one({
            "_id": session_id,
            "brand_id": brand_id,
            "company_id": company_id,  # Store both for compatibility
            "user_id": user_id or "anonymous",
            "messages": [],
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        })
        
        return session_id
    
    async def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a session"""
        session = await self.chat_collection.find_one({"_id": session_id})
        if session:
            return session.get("messages", [])
        return []
    
    async def clear_chat_session(self, session_id: str) -> bool:
        """Clear chat history for a session"""
        result = await self.chat_collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "messages": [],
                    "last_updated": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0


# Create singleton instance with lazy loading
_rag_service = None

def get_rag_service():
    """Get or create RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service

# For backward compatibility
rag_service = None  # Will be initialized on first use