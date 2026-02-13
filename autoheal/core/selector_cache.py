"""
SelectorCache interface for caching element selectors.

This module defines the abstract interface for selector caching implementations
that store previously successful selectors to improve performance.
"""

from abc import ABC, abstractmethod
from typing import Optional


class SelectorCache(ABC):
    """
    Interface for selector caching implementations.

    Selector caches store previously successful element selectors to avoid
    repeated AI API calls and improve performance. Different implementations
    provide different trade-offs between performance, persistence, and scalability.
    """

    @abstractmethod
    def get(self, key: str) -> Optional["CachedSelector"]:
        """
        Retrieve a cached selector by key.

        Args:
            key: The cache key (typically derived from description and page context)

        Returns:
            CachedSelector if found, None otherwise
        """
        pass

    @abstractmethod
    def put(self, key: str, selector: "CachedSelector") -> None:
        """
        Store a selector in the cache.

        Args:
            key: The cache key
            selector: The selector to cache
        """
        pass

    @abstractmethod
    def update_success(self, key: str, success: bool) -> None:
        """
        Update the success rate of a cached selector.

        This method tracks how often cached selectors successfully locate elements,
        allowing the cache to prioritize or evict selectors based on reliability.

        Args:
            key: The cache key
            success: Whether the selector was successful
        """
        pass

    @abstractmethod
    def get_metrics(self) -> "CacheMetrics":
        """
        Get cache performance metrics.

        Returns:
            Current cache metrics including hit rates, size, and eviction counts
        """
        pass

    @abstractmethod
    def evict_expired(self) -> None:
        """
        Remove expired entries from the cache.

        This method should be called periodically to clean up stale entries
        and free memory/storage.
        """
        pass

    @abstractmethod
    def clear_all(self) -> None:
        """
        Clear all entries from the cache.

        This operation removes all cached selectors, forcing fresh AI analysis
        for subsequent requests.
        """
        pass

    @abstractmethod
    def remove(self, key: str) -> bool:
        """
        Remove a specific entry from the cache.

        Args:
            key: The cache key to remove

        Returns:
            True if the entry was removed, False if it didn't exist
        """
        pass

    @abstractmethod
    def size(self) -> int:
        """
        Get the current size of the cache.

        Returns:
            Number of entries in the cache
        """
        pass


# Import at end to avoid circular dependencies
from autoheal.models.cached_selector import CachedSelector  # noqa: E402
from autoheal.metrics.cache_metrics import CacheMetrics  # noqa: E402
