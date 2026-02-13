"""
Cache Configuration for AutoHeal framework.

This module provides configuration for selector caching behavior,
supporting multiple cache types including in-memory, Redis, file-based, and hybrid.
"""

from datetime import timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CacheType(Enum):
    """
    Types of cache implementations available.

    Attributes:
        CAFFEINE: In-memory only cache (Python equivalent using cachetools).
        REDIS: Persistent Redis cache for distributed caching.
        PERSISTENT_FILE: File-based persistent cache using diskcache.
        HYBRID: Two-tier cache with in-memory L1 and Redis L2.
    """

    CAFFEINE = "caffeine"
    """In-memory only (default) - fast, local cache"""

    REDIS = "redis"
    """Persistent Redis cache - distributed, shared across instances"""

    PERSISTENT_FILE = "persistent_file"
    """File-based persistent cache - local, survives restarts"""

    HYBRID = "hybrid"
    """Caffeine L1 + Redis L2 - best of both worlds"""


class CacheConfig(BaseModel):
    """
    Configuration for selector caching behavior.

    Supports multiple cache types with configurable size limits, expiration policies,
    and Redis connection settings.

    Attributes:
        maximum_size: Maximum number of entries in the cache.
        expire_after_write: Time to expire entries after write.
        expire_after_access: Time to expire entries after last access.
        record_stats: Whether to record cache statistics.
        cache_type: Type of cache implementation to use.
        redis_host: Redis server hostname (for Redis/Hybrid cache).
        redis_port: Redis server port (for Redis/Hybrid cache).
        redis_password: Redis server password (for Redis/Hybrid cache).

    Examples:
        >>> # Create with defaults
        >>> config = CacheConfig()

        >>> # Create with custom settings
        >>> config = CacheConfig(
        ...     maximum_size=5000,
        ...     cache_type=CacheType.REDIS,
        ...     redis_host="cache.example.com"
        ... )

        >>> # Use builder pattern
        >>> config = (CacheConfig.builder()
        ...     .maximum_size(20000)
        ...     .cache_type(CacheType.HYBRID)
        ...     .redis_host("redis.local")
        ...     .build())
    """

    maximum_size: int = Field(default=10000, ge=1, le=1000000)
    expire_after_write: timedelta = Field(default=timedelta(hours=24))
    expire_after_access: timedelta = Field(default=timedelta(hours=2))
    record_stats: bool = Field(default=True)
    cache_type: CacheType = Field(default=CacheType.CAFFEINE)
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379, ge=1, le=65535)
    redis_password: Optional[str] = Field(default=None, exclude=True)

    class Config:
        """Pydantic model configuration."""
        use_enum_values = False
        validate_assignment = True

    @classmethod
    def builder(cls) -> "CacheConfigBuilder":
        """
        Create a builder for fluent API construction.

        Returns:
            CacheConfigBuilder instance for method chaining.

        Examples:
            >>> config = (CacheConfig.builder()
            ...     .maximum_size(20000)
            ...     .expire_after_write(timedelta(days=7))
            ...     .cache_type(CacheType.REDIS)
            ...     .build())
        """
        return CacheConfigBuilder()

    def __str__(self) -> str:
        """String representation of the configuration."""
        return (
            f"CacheConfig(cache_type={self.cache_type}, maximum_size={self.maximum_size}, "
            f"expire_after_write={self.expire_after_write}, expire_after_access={self.expire_after_access})"
        )


class CacheConfigBuilder:
    """
    Builder class for fluent CacheConfig construction.

    Provides a chainable API for building CacheConfig instances.

    Examples:
        >>> config = (CacheConfig.builder()
        ...     .maximum_size(15000)
        ...     .expire_after_write(timedelta(days=3))
        ...     .expire_after_access(timedelta(hours=6))
        ...     .cache_type(CacheType.REDIS)
        ...     .redis_host("redis.example.com")
        ...     .redis_port(6380)
        ...     .record_stats(True)
        ...     .build())
    """

    def __init__(self):
        """Initialize builder with default values."""
        self._maximum_size = 10000
        self._expire_after_write = timedelta(hours=24)
        self._expire_after_access = timedelta(hours=2)
        self._record_stats = True
        self._cache_type = CacheType.CAFFEINE
        self._redis_host = "localhost"
        self._redis_port = 6379
        self._redis_password: Optional[str] = None

    def maximum_size(self, size: int) -> "CacheConfigBuilder":
        """Set the maximum cache size."""
        self._maximum_size = size
        return self

    def expire_after_write(self, duration: timedelta) -> "CacheConfigBuilder":
        """Set the expiration time after write."""
        self._expire_after_write = duration
        return self

    def expire_after_access(self, duration: timedelta) -> "CacheConfigBuilder":
        """Set the expiration time after access."""
        self._expire_after_access = duration
        return self

    def record_stats(self, record: bool) -> "CacheConfigBuilder":
        """Set whether to record statistics."""
        self._record_stats = record
        return self

    def cache_type(self, cache_type: CacheType) -> "CacheConfigBuilder":
        """Set the cache type."""
        self._cache_type = cache_type
        return self

    def redis_host(self, host: str) -> "CacheConfigBuilder":
        """Set the Redis host."""
        self._redis_host = host
        return self

    def redis_port(self, port: int) -> "CacheConfigBuilder":
        """Set the Redis port."""
        self._redis_port = port
        return self

    def redis_password(self, password: str) -> "CacheConfigBuilder":
        """Set the Redis password."""
        self._redis_password = password
        return self

    def build(self) -> CacheConfig:
        """
        Build and return the CacheConfig instance.

        Returns:
            Configured CacheConfig instance.
        """
        return CacheConfig(
            maximum_size=self._maximum_size,
            expire_after_write=self._expire_after_write,
            expire_after_access=self._expire_after_access,
            record_stats=self._record_stats,
            cache_type=self._cache_type,
            redis_host=self._redis_host,
            redis_port=self._redis_port,
            redis_password=self._redis_password,
        )
