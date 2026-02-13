"""
Cachetools-based in-memory cache implementation for AutoHeal selectors.

This module provides an enterprise-grade in-memory cache using the cachetools library,
equivalent to the Java Caffeine-based implementation.
"""

import logging
import threading
import time
from typing import Optional

from cachetools import TTLCache

from autoheal.config.cache_config import CacheConfig
from autoheal.core.selector_cache import SelectorCache
from autoheal.metrics.cache_metrics import CacheMetrics
from autoheal.models.cached_selector import CachedSelector
from autoheal.models.element_context import ElementContext
from autoheal.models.position import Position

logger = logging.getLogger(__name__)


class CachetoolsSelectorCache(SelectorCache):
    """
    Enterprise-grade cache implementation using cachetools.

    This cache provides in-memory caching with TTL (time-to-live) support,
    automatic eviction, and comprehensive metrics tracking.

    Attributes:
        cache: The underlying TTLCache instance.
        metrics: Cache performance metrics.
        config: Cache configuration.

    Examples:
        >>> from autoheal.config import CacheConfig
        >>> from datetime import timedelta
        >>>
        >>> config = CacheConfig(
        ...     maximum_size=10000,
        ...     expire_after_write=timedelta(hours=24)
        ... )
        >>> cache = CachetoolsSelectorCache(config)
        >>>
        >>> # Store a selector
        >>> selector = CachedSelector(...)
        >>> cache.put("my-key", selector)
        >>>
        >>> # Retrieve selector
        >>> cached = cache.get("my-key")
        >>> if cached:
        ...     print(f"Found selector: {cached.selector}")
    """

    def __init__(self, config: CacheConfig) -> None:
        """
        Create a new cachetools-based selector cache.

        Args:
            config: Cache configuration settings.
        """
        self._config = config
        self._metrics = CacheMetrics()
        self._lock = threading.RLock()

        # Create TTLCache with max size and TTL from config
        # Use the minimum of expire_after_write and expire_after_access as TTL
        ttl_seconds = min(
            config.expire_after_write.total_seconds(),
            config.expire_after_access.total_seconds()
        )

        self._cache: TTLCache[str, CachedSelector] = TTLCache(
            maxsize=config.maximum_size,
            ttl=ttl_seconds
        )

        # Track access times for expire_after_access support
        self._access_times: dict[str, float] = {}

        logger.info(
            "CachetoolsSelectorCache initialized with max size: %d, TTL: %d seconds",
            config.maximum_size,
            ttl_seconds
        )

    def __init_with_cache__(
        self,
        config: CacheConfig,
        cache: TTLCache[str, CachedSelector],
        metrics: CacheMetrics
    ) -> None:
        """
        Alternative constructor for testing (dependency injection).

        Args:
            config: Cache configuration.
            cache: Pre-configured TTLCache instance.
            metrics: Pre-configured metrics instance.
        """
        self._config = config
        self._cache = cache
        self._metrics = metrics
        self._lock = threading.RLock()
        self._access_times = {}

    def get(self, key: str) -> Optional[CachedSelector]:
        """
        Retrieve a cached selector by key.

        Args:
            key: Cache key.

        Returns:
            CachedSelector if found, None otherwise.
        """
        start_time = time.time()

        with self._lock:
            # Check if entry is expired based on access time
            if key in self._access_times:
                time_since_access = time.time() - self._access_times[key]
                if time_since_access > self._config.expire_after_access.total_seconds():
                    # Entry expired based on access time
                    self._evict_entry(key)
                    self._metrics.record_miss()
                    logger.debug("Cache miss (expired by access) for key: %s", key)
                    return None

            # Try to get from cache
            result = self._cache.get(key)

            if result is not None:
                # Update access time
                self._access_times[key] = time.time()
                self._metrics.record_hit()
                logger.debug("Cache hit for key: %s", key)
                return result
            else:
                self._metrics.record_miss()
                logger.debug("Cache miss for key: %s", key)
                return None

    def put(self, key: str, selector: CachedSelector) -> None:
        """
        Store a selector in the cache.

        Args:
            key: Cache key.
            selector: Selector to cache.
        """
        start_time = time.time()

        with self._lock:
            # Check if we're evicting an entry
            if len(self._cache) >= self._cache.maxsize and key not in self._cache:
                self._metrics.record_eviction()
                logger.debug("Cache entry will be evicted due to max size")

            self._cache[key] = selector
            self._access_times[key] = time.time()

            elapsed_ms = (time.time() - start_time) * 1000
            self._metrics.record_load(int(elapsed_ms))
            logger.debug("Cached selector for key: %s", key)

    def update_success(self, key: str, success: bool) -> None:
        """
        Update success rate for a cached selector.

        Args:
            key: Cache key.
            success: Whether the selector usage was successful.
        """
        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                cached.record_usage(success)
                logger.debug("Updated success rate for key: %s (success: %s)", key, success)

    def get_metrics(self) -> CacheMetrics:
        """
        Get cache performance metrics.

        Returns:
            Current cache metrics.
        """
        return self._metrics

    def evict_expired(self) -> None:
        """
        Evict expired cache entries.

        TTLCache automatically evicts expired entries, but this method
        also checks for access-time-based expiration.
        """
        with self._lock:
            current_time = time.time()
            expire_after_access_seconds = self._config.expire_after_access.total_seconds()

            # Find keys expired by access time
            expired_keys = [
                key for key, access_time in self._access_times.items()
                if current_time - access_time > expire_after_access_seconds
            ]

            # Remove expired entries
            for key in expired_keys:
                self._evict_entry(key)

            if expired_keys:
                logger.debug("Evicted %d expired cache entries", len(expired_keys))

    def clear_all(self) -> None:
        """
        Clear all cache entries.
        """
        with self._lock:
            size_before = len(self._cache)
            self._cache.clear()
            self._access_times.clear()
            self._metrics.record_eviction()
            logger.debug("Cache cleared: %d entries removed", size_before)
            logger.info("Cache cleared completely: %d entries removed", size_before)

    def remove(self, key: str) -> bool:
        """
        Remove a specific cache entry.

        Args:
            key: Cache key to remove.

        Returns:
            True if entry was removed, False if not found.
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._access_times.pop(key, None)
                self._metrics.record_eviction()
                logger.debug("Cache entry removed: %s", key)
                return True

            logger.debug("Attempted to remove non-existent cache entry: %s", key)
            return False

    def size(self) -> int:
        """
        Get current cache size.

        Returns:
            Number of entries in cache.
        """
        with self._lock:
            return len(self._cache)

    def generate_contextual_key(
        self,
        original_selector: str,
        description: str,
        context: Optional[ElementContext] = None
    ) -> str:
        """
        Generate a contextual cache key that includes element context.

        This creates a unique key that incorporates not just the selector,
        but also contextual information like parent container, position,
        and sibling elements.

        Args:
            original_selector: The original CSS selector.
            description: Human-readable element description.
            context: Element context information.

        Returns:
            Contextual cache key.

        Examples:
            >>> cache = CachetoolsSelectorCache(config)
            >>> key = cache.generate_contextual_key(
            ...     "#submit-btn",
            ...     "Submit button",
            ...     ElementContext.builder()
            ...         .parent_container("form.login")
            ...         .build()
            ... )
            >>> print(key)
            "#submit-btn|Submit button|parent:form.login"
        """
        key_parts = [original_selector, description]

        if context is not None:
            if context.parent_container:
                key_parts.append(f"parent:{context.parent_container}")

            if context.relative_position:
                pos = context.relative_position
                key_parts.append(f"pos:{pos.x},{pos.y}")

            if context.sibling_elements:
                siblings_str = ",".join(context.sibling_elements)
                key_parts.append(f"siblings:{siblings_str}")

        return "|".join(key_parts)

    def get_underlying_cache(self) -> TTLCache[str, CachedSelector]:
        """
        Get the underlying cachetools cache for advanced operations.

        This is primarily for testing and debugging purposes.

        Returns:
            The TTLCache instance.
        """
        return self._cache

    def _evict_entry(self, key: str) -> None:
        """
        Internal method to evict an entry.

        Args:
            key: Cache key to evict.
        """
        self._cache.pop(key, None)
        self._access_times.pop(key, None)
        self._metrics.record_eviction()
