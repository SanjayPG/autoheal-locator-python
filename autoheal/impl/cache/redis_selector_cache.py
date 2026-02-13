"""
Redis-based persistent cache implementation for AutoHeal selectors.

This module provides a distributed cache using Redis, which persists across
application restarts and can be shared across multiple instances.
"""

import json
import logging
from datetime import datetime
from typing import Optional

import redis
from redis.connection import ConnectionPool

from autoheal.config.cache_config import CacheConfig
from autoheal.core.selector_cache import SelectorCache
from autoheal.metrics.cache_metrics import CacheMetrics
from autoheal.models.cached_selector import CachedSelector
from autoheal.models.element_context import ElementContext
from autoheal.models.position import Position

logger = logging.getLogger(__name__)


class RedisSelectorCache(SelectorCache):
    """
    Redis-based persistent cache implementation for AutoHeal selectors.

    Provides persistent storage that survives application restarts and can
    be shared across multiple application instances.

    Attributes:
        redis_client: Redis client instance.
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
        >>> cache = RedisSelectorCache(
        ...     config=config,
        ...     redis_host="localhost",
        ...     redis_port=6379
        ... )
        >>>
        >>> # Test connection
        >>> if cache.is_healthy():
        ...     print("Redis connected successfully")
    """

    CACHE_KEY_PREFIX = "autoheal:selector:"

    def __init__(
        self,
        config: CacheConfig,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        password: Optional[str] = None,
        db: int = 0,
        max_connections: int = 10
    ) -> None:
        """
        Create a new Redis-based selector cache.

        Args:
            config: Cache configuration settings.
            redis_host: Redis server hostname.
            redis_port: Redis server port.
            password: Redis password (optional).
            db: Redis database number (default: 0).
            max_connections: Maximum number of connections in pool.

        Raises:
            RuntimeError: If Redis connection fails.
        """
        self._config = config
        self._metrics = CacheMetrics()

        # Configure connection pool
        pool = ConnectionPool(
            host=redis_host,
            port=redis_port,
            password=password,
            db=db,
            max_connections=max_connections,
            decode_responses=True,  # Automatically decode responses to strings
            socket_connect_timeout=2,
            socket_timeout=2
        )

        try:
            self._redis_client = redis.Redis(connection_pool=pool)
            # Test connection
            self._redis_client.ping()
            logger.info(
                "RedisSelectorCache initialized successfully. Host: %s:%d",
                redis_host,
                redis_port
            )
        except Exception as e:
            logger.error(
                "Failed to initialize Redis connection to %s:%d",
                redis_host,
                redis_port,
                exc_info=True
            )
            raise RuntimeError(f"Redis connection failed: {e}") from e

    def get(self, key: str) -> Optional[CachedSelector]:
        """
        Retrieve a cached selector by key.

        Args:
            key: Cache key.

        Returns:
            CachedSelector if found, None otherwise.
        """
        redis_key = self.CACHE_KEY_PREFIX + key

        try:
            json_value = self._redis_client.get(redis_key)

            if json_value is not None:
                cached_selector = self._deserialize_selector(json_value)
                self._metrics.record_hit()
                logger.debug("Redis cache hit for key: %s", key)
                logger.debug("Cache HIT: %s", key)
                return cached_selector
            else:
                self._metrics.record_miss()
                logger.debug("Redis cache miss for key: %s", key)
                logger.debug("Cache MISS: %s", key)
                return None

        except Exception as e:
            logger.error("Redis cache get failed for key: %s", key, exc_info=True)
            self._metrics.record_miss()
            logger.debug("Cache GET ERROR: %s", e)
            return None

    def put(self, key: str, selector: CachedSelector) -> None:
        """
        Store a selector in the cache.

        Args:
            key: Cache key.
            selector: Selector to cache.
        """
        import time
        start_time = time.time()
        redis_key = self.CACHE_KEY_PREFIX + key

        try:
            json_value = self._serialize_selector(selector)

            # Set with TTL based on config
            ttl_seconds = int(self._config.expire_after_write.total_seconds())
            self._redis_client.setex(redis_key, ttl_seconds, json_value)

            elapsed_ms = int((time.time() - start_time) * 1000)
            self._metrics.record_load(elapsed_ms)
            logger.debug("Cached selector in Redis for key: %s (TTL: %ds)", key, ttl_seconds)
            logger.debug("Cache STORED: %s (TTL: %ds)", key, ttl_seconds)

        except Exception as e:
            logger.error("Redis cache put failed for key: %s", key, exc_info=True)
            logger.debug("Cache STORE ERROR: %s", e)

    def update_success(self, key: str, success: bool) -> None:
        """
        Update success rate for a cached selector.

        Args:
            key: Cache key.
            success: Whether the selector usage was successful.
        """
        redis_key = self.CACHE_KEY_PREFIX + key

        try:
            json_value = self._redis_client.get(redis_key)
            if json_value is not None:
                cached_selector = self._deserialize_selector(json_value)
                cached_selector.record_usage(success)

                # Update with same TTL
                ttl = self._redis_client.ttl(redis_key)
                if ttl > 0:
                    updated_json = self._serialize_selector(cached_selector)
                    self._redis_client.setex(redis_key, ttl, updated_json)
                    logger.debug(
                        "Updated success rate for Redis key: %s (success: %s)",
                        key,
                        success
                    )

        except Exception as e:
            logger.error("Redis cache updateSuccess failed for key: %s", key, exc_info=True)

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

        Redis handles TTL automatically, so no manual eviction is needed.
        """
        logger.debug("Redis TTL-based eviction is automatic, no manual action required")

    def clear_all(self) -> None:
        """
        Clear all cache entries.
        """
        try:
            # Get count before clearing using SCAN for better performance
            pattern = self.CACHE_KEY_PREFIX + "*"
            keys = list(self._redis_client.scan_iter(match=pattern, count=100))
            size_before = len(keys)

            # Delete all cache keys
            if keys:
                self._redis_client.delete(*keys)

            self._metrics.record_eviction()
            logger.debug("Cache cleared: %d entries removed", size_before)
            logger.info("Redis cache cleared completely: %d entries removed", size_before)

        except Exception as e:
            logger.error("Redis cache clearAll failed", exc_info=True)

    def remove(self, key: str) -> bool:
        """
        Remove a specific cache entry.

        Args:
            key: Cache key to remove.

        Returns:
            True if entry was removed, False if not found.
        """
        redis_key = self.CACHE_KEY_PREFIX + key

        try:
            deleted = self._redis_client.delete(redis_key)
            if deleted > 0:
                self._metrics.record_eviction()
                logger.debug("Cache entry removed: %s", key)
                logger.debug("Redis cache entry removed: %s", key)
                return True
            return False

        except Exception as e:
            logger.error("Redis cache remove failed for key: %s", key, exc_info=True)
            return False

    def size(self) -> int:
        """
        Get current cache size.

        Returns:
            Number of entries in cache.
        """
        try:
            # Use SCAN for efficient counting
            pattern = self.CACHE_KEY_PREFIX + "*"
            count = 0
            for _ in self._redis_client.scan_iter(match=pattern, count=100):
                count += 1
            return count

        except Exception as e:
            logger.error("Redis cache size calculation failed", exc_info=True)
            return 0

    def generate_contextual_key(
        self,
        original_selector: str,
        description: str,
        context: Optional[ElementContext] = None
    ) -> str:
        """
        Generate a contextual cache key that includes element context.

        Args:
            original_selector: The original CSS selector.
            description: Human-readable element description.
            context: Element context information.

        Returns:
            Contextual cache key.
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

    def is_healthy(self) -> bool:
        """
        Check Redis connection health.

        Returns:
            True if Redis is reachable and responding, False otherwise.
        """
        try:
            response = self._redis_client.ping()
            return response is True
        except Exception as e:
            logger.error("Redis health check failed", exc_info=True)
            return False

    def get_connection_info(self) -> str:
        """
        Get Redis connection information.

        Returns:
            Connection info string.
        """
        try:
            info = self._redis_client.info("server")
            redis_version = info.get("redis_version", "unknown")
            return f"Redis connected: version {redis_version}"
        except Exception as e:
            return f"Redis connection failed: {e}"

    def shutdown(self) -> None:
        """
        Cleanup resources and close Redis connection.
        """
        try:
            if self._redis_client:
                self._redis_client.close()
                logger.info("Redis connection pool closed")
        except Exception as e:
            logger.error("Error closing Redis connection", exc_info=True)

    def _serialize_selector(self, selector: CachedSelector) -> str:
        """
        Serialize a CachedSelector to JSON.

        Args:
            selector: Selector to serialize.

        Returns:
            JSON string representation.
        """
        # Convert to dictionary using Pydantic's model_dump
        data = selector.model_dump(mode='json')
        return json.dumps(data)

    def _deserialize_selector(self, json_str: str) -> CachedSelector:
        """
        Deserialize a CachedSelector from JSON.

        Args:
            json_str: JSON string to deserialize.

        Returns:
            CachedSelector instance.
        """
        data = json.loads(json_str)
        return CachedSelector.model_validate(data)
