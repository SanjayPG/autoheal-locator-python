"""
AI Service metrics module for tracking AI service performance and reliability.

This module provides metrics collection for AI service requests, success rates,
and response times.
"""

import threading
from typing import Dict, Any


class AIServiceMetrics:
    """
    Metrics for AI service performance and reliability.

    This class tracks AI service requests, success/failure rates, response times,
    and circuit breaker events.

    All methods are thread-safe.
    """

    def __init__(self) -> None:
        """Initialize AI service metrics with zero counters."""
        self._lock = threading.Lock()
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._total_response_time = 0
        self._circuit_breaker_open_count = 0

    def record_request(self, success: bool, response_time_ms: int = None, latency_ms: int = None) -> None:
        """
        Record an AI service request.

        Args:
            success: True if request was successful
            response_time_ms: Response time in milliseconds (deprecated, use latency_ms)
            latency_ms: Latency time in milliseconds (preferred)
        """
        # Support both parameter names for backward compatibility
        time_ms = latency_ms if latency_ms is not None else response_time_ms
        if time_ms is None:
            time_ms = 0

        with self._lock:
            self._total_requests += 1
            self._total_response_time += time_ms

            if success:
                self._successful_requests += 1
            else:
                self._failed_requests += 1

    def record_circuit_breaker_open(self) -> None:
        """Record circuit breaker opening event."""
        with self._lock:
            self._circuit_breaker_open_count += 1

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

    def get_average_response_time(self) -> float:
        """
        Calculate average response time.

        Returns:
            Average response time in milliseconds
        """
        with self._lock:
            return (
                self._total_response_time / self._total_requests
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
    def failed_requests(self) -> int:
        """Get number of failed requests."""
        with self._lock:
            return self._failed_requests

    @property
    def total_response_time(self) -> int:
        """Get total accumulated response time."""
        with self._lock:
            return self._total_response_time

    @property
    def circuit_breaker_open_count(self) -> int:
        """Get number of times circuit breaker opened."""
        with self._lock:
            return self._circuit_breaker_open_count

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
                "failed_requests": self._failed_requests,
                "success_rate": self.get_success_rate(),
                "average_response_time_ms": self.get_average_response_time(),
                "circuit_breaker_open_count": self._circuit_breaker_open_count,
            }

    def __str__(self) -> str:
        """Return string representation of metrics."""
        return (
            f"AIServiceMetrics(requests={self.total_requests}, "
            f"success_rate={self.get_success_rate():.2%}, "
            f"avg_response={self.get_average_response_time():.1f}ms)"
        )
