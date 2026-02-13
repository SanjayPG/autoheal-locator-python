"""
Cache metrics module for tracking cache performance and efficiency.

This module provides metrics collection for cache hits, misses, evictions,
and load operations.
"""

import threading
from typing import Dict, Any


class CacheMetrics:
    """
    Metrics for cache performance and efficiency.

    This class tracks cache operations and provides statistics about
    cache performance including hit rate and average load time.

    All methods are thread-safe.
    """

    def __init__(self) -> None:
        """Initialize cache metrics with zero counters."""
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._load_count = 0
        self._total_load_time = 0

    def record_hit(self) -> None:
        """Record a cache hit."""
        with self._lock:
            self._hits += 1

    def record_miss(self) -> None:
        """Record a cache miss."""
        with self._lock:
            self._misses += 1

    def record_eviction(self) -> None:
        """Record a cache eviction."""
        with self._lock:
            self._evictions += 1

    def record_load(self, load_time_ms: int) -> None:
        """
        Record a cache load operation.

        Args:
            load_time_ms: Time taken to load in milliseconds
        """
        with self._lock:
            self._load_count += 1
            self._total_load_time += load_time_ms

    def get_hit_rate(self) -> float:
        """
        Calculate cache hit rate.

        Returns:
            Hit rate between 0.0 and 1.0
        """
        with self._lock:
            total = self._hits + self._misses
            return self._hits / total if total > 0 else 0.0

    def get_average_load_time(self) -> float:
        """
        Calculate average load time.

        Returns:
            Average load time in milliseconds
        """
        with self._lock:
            return self._total_load_time / self._load_count if self._load_count > 0 else 0.0

    # Getters for raw values
    @property
    def hits(self) -> int:
        """Get total number of cache hits."""
        with self._lock:
            return self._hits

    @property
    def total_hits(self) -> int:
        """Get total number of cache hits (alias for hits)."""
        with self._lock:
            return self._hits

    @property
    def misses(self) -> int:
        """Get total number of cache misses."""
        with self._lock:
            return self._misses

    @property
    def total_misses(self) -> int:
        """Get total number of cache misses (alias for misses)."""
        with self._lock:
            return self._misses

    @property
    def evictions(self) -> int:
        """Get total number of cache evictions."""
        with self._lock:
            return self._evictions

    @property
    def load_count(self) -> int:
        """Get total number of cache loads."""
        with self._lock:
            return self._load_count

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metrics to dictionary format.

        Returns:
            Dictionary containing all metrics
        """
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "load_count": self._load_count,
                "hit_rate": self.get_hit_rate(),
                "average_load_time_ms": self.get_average_load_time(),
            }

    def __str__(self) -> str:
        """Return string representation of metrics."""
        return (
            f"CacheMetrics(hits={self.hits}, misses={self.misses}, "
            f"hit_rate={self.get_hit_rate():.2%}, evictions={self.evictions})"
        )
