"""
Locator metrics module for tracking element locator performance and usage.

This module provides metrics collection for locator requests, success rates,
and execution times.
"""

import threading
from typing import Dict, Any


class LocatorMetrics:
    """
    Metrics for element locator performance and usage.

    This class tracks locator requests, success rates, cache hit rates,
    and execution times.

    All methods are thread-safe.
    """

    def __init__(self) -> None:
        """Initialize locator metrics with zero counters."""
        self._lock = threading.Lock()
        self._total_requests = 0
        self._successful_requests = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_execution_time = 0

    def record_request(
        self,
        success: bool,
        execution_time_ms: int = None,
        from_cache: bool = False,
        latency_ms: int = None,
    ) -> None:
        """
        Record a locator request with its outcome.

        Args:
            success: True if request was successful
            execution_time_ms: Execution time in milliseconds (deprecated, use latency_ms)
            from_cache: True if result came from cache
            latency_ms: Latency time in milliseconds (preferred)
        """
        # Support both parameter names for backward compatibility
        time_ms = latency_ms if latency_ms is not None else execution_time_ms
        if time_ms is None:
            time_ms = 0

        with self._lock:
            self._total_requests += 1
            if success:
                self._successful_requests += 1
            self._total_execution_time += time_ms

            if from_cache:
                self._cache_hits += 1
            else:
                self._cache_misses += 1

    def get_success_rate(self) -> float:
        """
        Calculate current success rate.

        Returns:
            Success rate between 0.0 and 1.0
        """
        with self._lock:
            return (
                self._successful_requests / self._total_requests
                if self._total_requests > 0
                else 0.0
            )

    def get_cache_hit_rate(self) -> float:
        """
        Calculate cache hit rate.

        Returns:
            Cache hit rate between 0.0 and 1.0
        """
        with self._lock:
            total = self._cache_hits + self._cache_misses
            return self._cache_hits / total if total > 0 else 0.0

    def get_average_execution_time(self) -> float:
        """
        Calculate average execution time.

        Returns:
            Average execution time in milliseconds
        """
        with self._lock:
            return (
                self._total_execution_time / self._total_requests
                if self._total_requests > 0
                else 0.0
            )

    # Getters for raw values
    @property
    def total_requests(self) -> int:
        """Get total number of requests."""
        with self._lock:
            return self._total_requests

    @property
    def successful_requests(self) -> int:
        """Get number of successful requests."""
        with self._lock:
            return self._successful_requests

    @property
    def cache_hits(self) -> int:
        """Get number of cache hits."""
        with self._lock:
            return self._cache_hits

    @property
    def cache_misses(self) -> int:
        """Get number of cache misses."""
        with self._lock:
            return self._cache_misses

    @property
    def total_execution_time(self) -> int:
        """Get total accumulated execution time."""
        with self._lock:
            return self._total_execution_time

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metrics to dictionary format.

        Returns:
            Dictionary containing all metrics
        """
        with self._lock:
            return {
                "total_requests": self._total_requests,
                "successful_requests": self._successful_requests,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "success_rate": self.get_success_rate(),
                "cache_hit_rate": self.get_cache_hit_rate(),
                "average_execution_time_ms": self.get_average_execution_time(),
            }

    def __str__(self) -> str:
        """Return string representation of metrics."""
        return (
            f"LocatorMetrics(requests={self.total_requests}, "
            f"success_rate={self.get_success_rate():.2%}, "
            f"cache_hit_rate={self.get_cache_hit_rate():.2%})"
        )
