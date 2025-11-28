"""
Website crawling and ingestion service
"""

import logging
import asyncio
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import hashlib
from firecrawl import FirecrawlApp

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

# Motor for async MongoDB operations
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings

logger = logging.getLogger(__name__)


class WebsiteIngestionService:
    """Service for crawling websites and ingesting content"""
    
    def __init__(self):
        # MongoDB connection
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.database_name]
        self.collection = self.db.knowledge_base_items
        
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
        
        # Initialize Firecrawl if API key is available
        self.firecrawl_app = None
        self.use_firecrawl = settings.use_firecrawl
        if settings.firecrawl_api_key:
            try:
                self.firecrawl_app = FirecrawlApp(api_key=settings.firecrawl_api_key)
                logger.info("Firecrawl API initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Firecrawl: {e}. Falling back to custom crawler.")
                self.use_firecrawl = False
        else:
            if self.use_firecrawl:
                logger.warning("Firecrawl API key not found. Using custom crawler instead.")
            self.use_firecrawl = False
    
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
    
    def fetch_webpage(self, url: str) -> Optional[str]:
        """Fetch webpage content"""
        try:
            # Add headers to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(url, timeout=30, allow_redirects=True, headers=headers)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 403:
                logger.warning(f"Access forbidden for {url}. The website may be blocking automated requests.")
                # Try without user agent as fallback
                response = requests.get(url, timeout=30, allow_redirects=True)
                if response.status_code == 200:
                    return response.text
                return None
            else:
                logger.warning(f"Failed to fetch {url}: Status {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_text_from_html(self, html_content: str) -> Dict[str, Any]:
        """Extract text and metadata from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract metadata
        metadata = {
            'title': '',
            'description': '',
            'keywords': '',
            'author': ''
        }
        
        # Get title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()
        
        # Get meta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            if tag.get('name') == 'description':
                metadata['description'] = tag.get('content', '')
            elif tag.get('name') == 'keywords':
                metadata['keywords'] = tag.get('content', '')
            elif tag.get('name') == 'author':
                metadata['author'] = tag.get('content', '')
        
        # Get text content
        text = soup.get_text()
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return {
            'text': text,
            'metadata': metadata
        }
    
    def extract_links(self, html_content: str, base_url: str, max_depth: int = 1) -> List[str]:
        """Extract links from HTML content"""
        if max_depth <= 0:
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all('a', href=True):
            url = urljoin(base_url, link['href'])
            parsed = urlparse(url)
            
            # Only include links from the same domain
            if parsed.netloc == base_domain:
                links.append(url)
        
        # Remove duplicates and return
        return list(set(links))
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Rough estimation: 1 token ≈ 4 characters for English text
        return len(text) // 4
    
    def crawl_website_firecrawl(
        self,
        urls: List[str],
        crawl_depth: int = 1,
        follow_redirects: bool = True,
        extract_metadata: bool = True
    ) -> Dict[str, Any]:
        """Crawl websites using Firecrawl API"""
        
        if not self.firecrawl_app:
            logger.warning("Firecrawl not available, falling back to custom crawler")
            return self.crawl_website_custom(urls, crawl_depth, follow_redirects, extract_metadata)
        
        all_content = []
        all_metadata = []
        visited_urls = set()
        
        try:
            for url in urls:
                logger.info(f"Crawling with Firecrawl: {url}")
                
                # Use Firecrawl's crawl method for deep crawling
                if crawl_depth > 1:
                    # Start crawl job - crawl method takes URL as parameter
                    try:
                        crawl_job = self.firecrawl_app.crawl(url)
                        
                        # Process crawl results
                        if crawl_job and hasattr(crawl_job, 'data') and crawl_job.data:
                            for page in crawl_job.data:
                                if hasattr(page, 'markdown') and page.markdown:
                                    all_content.append(page.markdown)
                                elif hasattr(page, 'html') and page.html:
                                    # Extract text from HTML if markdown not available
                                    extracted = self.extract_text_from_html(page.html)
                                    all_content.append(extracted['text'])
                                
                                if hasattr(page, 'url'):
                                    visited_urls.add(page.url)
                                
                                if extract_metadata and hasattr(page, 'metadata'):
                                    # Convert metadata to dict if it's a Pydantic model
                                    metadata_dict = page.metadata
                                    if hasattr(metadata_dict, 'model_dump'):
                                        metadata_dict = metadata_dict.model_dump()
                                    elif hasattr(metadata_dict, 'dict'):
                                        metadata_dict = metadata_dict.dict()
                                    
                                    all_metadata.append({
                                        'url': page.url if hasattr(page, 'url') else url,
                                        'metadata': metadata_dict
                                    })
                    except Exception as e:
                        logger.warning(f"Crawl failed for {url}, falling back to scrape: {e}")
                        # Fall back to single page scrape
                        crawl_depth = 1
                
                # Single page scrape (or fallback from crawl)
                if crawl_depth <= 1 or len(all_content) == 0:
                    scrape_result = self.firecrawl_app.scrape(url)
                    
                    if scrape_result:
                        # Process the Document object
                        if hasattr(scrape_result, 'markdown') and scrape_result.markdown:
                            all_content.append(scrape_result.markdown)
                        elif hasattr(scrape_result, 'html') and scrape_result.html:
                            # Extract text from HTML if markdown not available  
                            extracted = self.extract_text_from_html(scrape_result.html)
                            all_content.append(extracted['text'])
                        elif hasattr(scrape_result, 'raw_html') and scrape_result.raw_html:
                            # Try raw_html if html is not available
                            extracted = self.extract_text_from_html(scrape_result.raw_html)
                            all_content.append(extracted['text'])
                        
                        visited_urls.add(url)
                        
                        if extract_metadata and hasattr(scrape_result, 'metadata'):
                            # Convert metadata to dict if it's a Pydantic model
                            metadata_dict = scrape_result.metadata
                            if hasattr(metadata_dict, 'model_dump'):
                                metadata_dict = metadata_dict.model_dump()
                            elif hasattr(metadata_dict, 'dict'):
                                metadata_dict = metadata_dict.dict()
                            
                            all_metadata.append({
                                'url': url,
                                'metadata': metadata_dict
                            })
            
            # Combine all content
            combined_text = "\n\n".join(all_content)
            
            return {
                'text': combined_text,
                'metadata': all_metadata,
                'pages_crawled': len(visited_urls),
                'urls_visited': list(visited_urls),
                'crawler': 'firecrawl'
            }
            
        except Exception as e:
            logger.error(f"Firecrawl error: {e}. Falling back to custom crawler.")
            return self.crawl_website_custom(urls, crawl_depth, follow_redirects, extract_metadata)
    
    def crawl_website_custom(
        self,
        urls: List[str],
        crawl_depth: int = 1,
        follow_redirects: bool = True,
        extract_metadata: bool = True
    ) -> Dict[str, Any]:
        """Crawl websites using custom crawler (original implementation)"""
        
        all_content = []
        all_metadata = []
        visited_urls = set()
        urls_to_visit = urls.copy()
        current_depth = 0
        
        while urls_to_visit and current_depth < crawl_depth:
            next_batch = []
            
            for url in urls_to_visit:
                if url in visited_urls:
                    continue
                
                visited_urls.add(url)
                logger.info(f"Custom crawling: {url} (depth: {current_depth})")
                
                # Fetch webpage
                html_content = self.fetch_webpage(url)
                if not html_content:
                    continue
                
                # Extract text and metadata
                extracted = self.extract_text_from_html(html_content)
                all_content.append(extracted['text'])
                if extract_metadata:
                    all_metadata.append({
                        'url': url,
                        'metadata': extracted['metadata']
                    })
                
                # Extract links for next depth level
                if current_depth < crawl_depth - 1:
                    links = self.extract_links(html_content, url, 1)
                    next_batch.extend(links)
            
            urls_to_visit = list(set(next_batch) - visited_urls)
            current_depth += 1
        
        # Combine all content
        combined_text = "\n\n".join(all_content)
        
        return {
            'text': combined_text,
            'metadata': all_metadata,
            'pages_crawled': len(visited_urls),
            'urls_visited': list(visited_urls),
            'crawler': 'custom'
        }
    
    def crawl_website(
        self,
        urls: List[str],
        crawl_depth: int = 1,
        follow_redirects: bool = True,
        extract_metadata: bool = True,
        force_crawler: Optional[str] = None  # 'firecrawl', 'custom', or None for auto
    ) -> Dict[str, Any]:
        """Crawl websites and extract content (main entry point)"""
        
        # Determine which crawler to use
        use_firecrawl = force_crawler == 'firecrawl' or (
            force_crawler is None and self.use_firecrawl and self.firecrawl_app
        )
        
        if use_firecrawl:
            logger.info("Using Firecrawl for website crawling")
            return self.crawl_website_firecrawl(urls, crawl_depth, follow_redirects, extract_metadata)
        else:
            logger.info("Using custom crawler for website crawling")
            return self.crawl_website_custom(urls, crawl_depth, follow_redirects, extract_metadata)
    
    async def process_website(
        self,
        item_id: str,
        urls: List[str],
        crawl_depth: int = 1,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        follow_redirects: bool = True,
        extract_metadata: bool = True,
        force_crawler: Optional[str] = None  # 'firecrawl', 'custom', or None for auto
    ) -> Dict[str, Any]:
        """Process a website and generate embeddings"""
        
        start_time = time.time()
        
        try:
            logger.info(f"Starting website ingestion for item_id: {item_id}, urls: {urls}")
            
            # Update status to processing
            await self.collection.update_one(
                {"_id": item_id},
                {
                    "$set": {
                        "indexing_status": "processing",
                        "embeddings_processed_at": datetime.utcnow()
                    }
                }
            )
            
            # Crawl website(s) - using sync method
            crawl_result = self.crawl_website(
                urls=urls,
                crawl_depth=crawl_depth,
                follow_redirects=follow_redirects,
                extract_metadata=extract_metadata,
                force_crawler=force_crawler
            )
            
            full_text = crawl_result['text']
            crawler_used = crawl_result.get('crawler', 'unknown')
            
            if not full_text:
                # Provide more context about the failure
                error_msg = f"No content extracted from website(s). "
                if crawl_result.get('urls_visited'):
                    error_msg += f"Attempted to crawl: {', '.join(crawl_result['urls_visited'][:3])}. "
                error_msg += "The website may be blocking automated requests or may require authentication."
                raise ValueError(error_msg)
            
            # Create document
            doc = Document(
                page_content=full_text,
                metadata={
                    'source': urls[0] if len(urls) == 1 else 'multiple',
                    'pages_crawled': crawl_result['pages_crawled'],
                    'urls': crawl_result['urls_visited']
                }
            )
            
            # Update text splitter if custom parameters provided
            if chunk_size != 1000 or chunk_overlap != 200:
                self.text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    length_function=len,
                    separators=["\n\n", "\n", ".", "!", "?", " ", ""]
                )
            
            # Split text into chunks
            chunks = self.text_splitter.split_documents([doc])
            logger.info(f"Split website content into {len(chunks)} chunks")
            
            # Generate embeddings for each chunk
            chunk_texts = [chunk.page_content for chunk in chunks]
            embeddings_list = self.embeddings.embed_documents(chunk_texts)
            
            # Prepare chunks for storage (without embeddings in chunks)
            chunk_docs = []
            for i, chunk in enumerate(chunks):
                chunk_docs.append({
                    "chunk_id": f"{item_id}_chunk_{i}",
                    "content": chunk.page_content,
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
                "embedding_provider": self.embedding_provider,
                "embedding_model": self.embedding_model_name,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "processed_at": datetime.utcnow(),
                "pages_crawled": crawl_result['pages_crawled'],
                "urls_visited": crawl_result['urls_visited'],
                "crawler_used": crawler_used
            }
            
            # Store website metadata if extracted
            website_metadata = {}
            if extract_metadata and crawl_result['metadata']:
                # Ensure all metadata is serializable
                serializable_metadata = []
                for meta_item in crawl_result['metadata']:
                    if isinstance(meta_item, dict):
                        # Convert any remaining Pydantic models in the metadata
                        clean_meta = {}
                        for key, value in meta_item.items():
                            if hasattr(value, 'model_dump'):
                                clean_meta[key] = value.model_dump()
                            elif hasattr(value, 'dict'):
                                clean_meta[key] = value.dict()
                            else:
                                clean_meta[key] = value
                        serializable_metadata.append(clean_meta)
                    else:
                        serializable_metadata.append(meta_item)
                
                website_metadata = {
                    "extracted_metadata": serializable_metadata
                }
            
            # Update document in MongoDB with processed data
            logger.info(f"Updating MongoDB document with ingestion stats for item_id: {item_id}")
            
            update_data = {
                "indexing_status": "completed",
                "indexed_content": full_text[:5000],  # Store first 5000 chars for preview
                "chunks": chunk_docs,  # Chunks without embeddings
                "embeddings": embeddings_list,  # All embeddings in a single array field
                "embeddings_processed": True,
                "embeddings_processed_at": datetime.utcnow(),
                "ingestion_stats": ingestion_stats,
                "total_chunks": len(chunks),
                "total_tokens": total_tokens,
                "embedding_provider": self.embedding_provider,
                "embedding_model": self.embedding_model_name,
                **website_metadata
            }
            
            update_result = await self.collection.update_one(
                {"_id": item_id},
                {"$set": update_data}
            )
            
            if update_result.matched_count == 0:
                logger.error(f"No document found to update with _id: {item_id}")
                raise ValueError(f"Failed to update document with ID: {item_id}")
            
            logger.info(f"Successfully processed website {item_id} using {self.embedding_provider} in {processing_time:.2f} seconds")
            
            return {
                "success": True,
                "stats": ingestion_stats
            }
            
        except Exception as e:
            logger.error(f"Error processing website {item_id}: {e}")
            
            # Update status to failed
            try:
                await self.collection.update_one(
                    {"_id": item_id},
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


# Create singleton instance
website_ingestion_service = WebsiteIngestionService()