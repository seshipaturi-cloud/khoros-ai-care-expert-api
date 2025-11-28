"""
Cache utility for embedding and vector search results
Implements TTL-based in-memory caching to reduce redundant computations
"""
import hashlib
import json
import time
from typing import Any, Dict, Optional, List
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class TTLCache:
    """Thread-safe Time-To-Live cache implementation"""

    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        """
        Initialize TTL cache

        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
            max_size: Maximum number of items to store (default: 1000)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._hits = 0
        self._misses = 0

    def _create_key(self, *args, **kwargs) -> str:
        """Create a cache key from arguments"""
        # Convert args and kwargs to a stable string representation
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())  # Sort for consistency
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]

        # Check if expired
        if time.time() > entry['expires_at']:
            del self._cache[key]
            self._misses += 1
            logger.debug(f"Cache expired for key: {key[:8]}...")
            return None

        self._hits += 1
        logger.debug(f"Cache hit for key: {key[:8]}...")
        return entry['value']

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with TTL"""
        # Implement simple LRU eviction if cache is full
        if len(self._cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]['created_at'])
            del self._cache[oldest_key]
            logger.debug(f"Cache full, evicted oldest entry: {oldest_key[:8]}...")

        ttl = ttl or self.default_ttl
        self._cache[key] = {
            'value': value,
            'created_at': time.time(),
            'expires_at': time.time() + ttl
        }
        logger.debug(f"Cache set for key: {key[:8]}... (TTL: {ttl}s)")

    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("Cache cleared")

    def cleanup_expired(self):
        """Remove expired entries from cache"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time > entry['expires_at']
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests
        }


# Global cache instances
embedding_cache = TTLCache(default_ttl=3600, max_size=1000)  # 1 hour TTL for embeddings
search_cache = TTLCache(default_ttl=300, max_size=500)  # 5 minutes TTL for search results


def create_search_cache_key(
    query: str,
    company_id: Optional[str] = None,
    brand_ids: Optional[List[str]] = None,
    agent_ids: Optional[List[str]] = None,
    content_types: Optional[List[str]] = None,
    limit: int = 10,
    similarity_threshold: float = 0.7
) -> str:
    """
    Create a unique cache key for vector search results

    Args:
        query: Search query text
        company_id: Company ID filter
        brand_ids: Brand IDs filter
        agent_ids: Agent IDs filter
        content_types: Content types filter
        limit: Result limit
        similarity_threshold: Similarity threshold

    Returns:
        MD5 hash of the search parameters
    """
    cache_data = {
        'query': query.strip().lower(),  # Normalize query
        'company_id': company_id,
        'brand_ids': sorted(brand_ids) if brand_ids else None,
        'agent_ids': sorted(agent_ids) if agent_ids else None,
        'content_types': sorted(content_types) if content_types else None,
        'limit': limit,
        'threshold': similarity_threshold
    }

    key_string = json.dumps(cache_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()


def create_embedding_cache_key(text: str, provider: str, model: str) -> str:
    """
    Create a unique cache key for embeddings

    Args:
        text: Text to embed
        provider: Embedding provider (openai, huggingface)
        model: Model name

    Returns:
        MD5 hash of text + provider + model
    """
    # Normalize text (strip whitespace, lowercase)
    normalized_text = text.strip().lower()

    cache_data = {
        'text': normalized_text,
        'provider': provider,
        'model': model
    }

    key_string = json.dumps(cache_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()


def cache_async(cache: TTLCache, ttl: Optional[int] = None):
    """
    Decorator for caching async function results

    Args:
        cache: TTLCache instance to use
        ttl: Optional TTL override
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from arguments
            cache_key = cache._create_key(*args, **kwargs)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"✅ Cache hit for {func.__name__}")
                return cached_result

            # Execute function
            logger.info(f"❌ Cache miss for {func.__name__}, executing...")
            result = await func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics for all caches"""
    return {
        'embedding_cache': embedding_cache.get_stats(),
        'search_cache': search_cache.get_stats()
    }


def clear_all_caches():
    """Clear all caches"""
    embedding_cache.clear()
    search_cache.clear()
    logger.info("All caches cleared")


def cleanup_all_caches():
    """Clean up expired entries from all caches"""
    embedding_cache.cleanup_expired()
    search_cache.cleanup_expired()
