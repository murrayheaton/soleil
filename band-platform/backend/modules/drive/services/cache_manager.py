"""
Cache manager for Google Drive operations.

Implements caching strategies to reduce API calls and improve performance.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)


class CacheEntry:
    """Single cache entry with TTL and metadata."""

    def __init__(self, value: Any, ttl_seconds: int = 300):
        """
        Initialize cache entry.

        Args:
            value: The cached value.
            ttl_seconds: Time to live in seconds.
        """
        self.value = value
        self.created_at = datetime.utcnow()
        self.ttl_seconds = ttl_seconds
        self.access_count = 0
        self.last_accessed = self.created_at

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > self.ttl_seconds

    def access(self) -> Any:
        """Access the cached value and update statistics."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
        return self.value


class CacheManager:
    """
    Cache manager for Google Drive operations.

    Provides in-memory caching with TTL, size limits, and eviction policies.
    """

    def __init__(
        self, max_size: int = 1000, default_ttl: int = 300, cleanup_interval: int = 60
    ):
        """
        Initialize the cache manager.

        Args:
            max_size: Maximum number of entries to cache.
            default_ttl: Default TTL in seconds.
            cleanup_interval: Interval for cleanup task in seconds.
        """
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        self.lock = asyncio.Lock()

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

        # Start cleanup task
        self._cleanup_task = None

    async def start(self) -> None:
        """Start the cache cleanup task."""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop the cache cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found or expired.
        """
        async with self.lock:
            entry = self.cache.get(key)

            if entry is None:
                self.misses += 1
                return None

            if entry.is_expired():
                del self.cache[key]
                self.misses += 1
                return None

            self.hits += 1
            return entry.access()

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Optional TTL override in seconds.
        """
        async with self.lock:
            # Check if we need to evict entries
            if len(self.cache) >= self.max_size and key not in self.cache:
                await self._evict_lru()

            ttl = ttl or self.default_ttl
            self.cache[key] = CacheEntry(value, ttl)

    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key.

        Returns:
            True if the key was found and deleted.
        """
        async with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    async def clear(self) -> None:
        """Clear all cached entries."""
        async with self.lock:
            self.cache.clear()

    async def invalidate_prefix(self, prefix: str) -> int:
        """
        Invalidate all cache entries with keys starting with prefix.

        Args:
            prefix: Key prefix to match.

        Returns:
            Number of entries invalidated.
        """
        async with self.lock:
            keys_to_delete = [k for k in self.cache.keys() if k.startswith(prefix)]
            for key in keys_to_delete:
                del self.cache[key]
            return len(keys_to_delete)

    async def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self.cache:
            return

        lru_key = min(self.cache.keys(), key=lambda k: self.cache[k].last_accessed)
        del self.cache[lru_key]
        self.evictions += 1

    async def _cleanup_loop(self) -> None:
        """Background task to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")

    async def _cleanup_expired(self) -> None:
        """Remove expired entries from cache."""
        async with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items() if entry.is_expired()
            ]
            for key in expired_keys:
                del self.cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": f"{hit_rate:.1f}%",
            "total_requests": total_requests,
        }

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0


def cached(key_func: Callable, ttl: Optional[int] = None):
    """
    Decorator for caching async function results.

    Args:
        key_func: Function to generate cache key from arguments.
        ttl: Optional TTL override.

    Example:
        @cached(lambda file_id: f"file:{file_id}")
        async def get_file_metadata(file_id: str):
            # expensive operation
            return metadata
    """

    def decorator(func):
        # Cache manager will be injected by the service
        cache_manager = None

        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal cache_manager

            # Get cache manager from self if this is a method
            if args and hasattr(args[0], "_cache_manager"):
                cache_manager = args[0]._cache_manager

            if not cache_manager:
                # No cache available, call function directly
                return await func(*args, **kwargs)

            # Generate cache key
            cache_key = key_func(*args, **kwargs)

            # Try to get from cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)

            return result

        wrapper._cached = True
        return wrapper

    return decorator
