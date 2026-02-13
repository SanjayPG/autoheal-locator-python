"""
Circuit Breaker implementation for AI service resilience.

This module provides a circuit breaker pattern implementation to protect
against cascading failures when AI services become unavailable.
"""

import threading
import time
from datetime import timedelta
from enum import Enum
from typing import Optional


class CircuitBreakerState(Enum):
    """
    Circuit breaker states.

    Attributes:
        CLOSED: Normal operation, requests pass through.
        OPEN: Failing state, blocking requests to protect system.
        HALF_OPEN: Testing state, allowing limited requests to check recovery.
    """

    CLOSED = "closed"
    """Normal operation"""

    OPEN = "open"
    """Failing, blocking requests"""

    HALF_OPEN = "half_open"
    """Testing if service has recovered"""


class CircuitBreaker:
    """
    Circuit Breaker implementation for AI service resilience.

    The circuit breaker monitors failures and automatically blocks requests
    when a threshold is exceeded, giving the downstream service time to recover.

    All methods are thread-safe.

    Attributes:
        failure_threshold: Number of failures before opening circuit.
        timeout: Duration to wait before attempting half-open.

    Examples:
        >>> from datetime import timedelta
        >>> cb = CircuitBreaker(failure_threshold=5, timeout=timedelta(minutes=5))
        >>>
        >>> if cb.can_execute():
        ...     try:
        ...         # Execute operation
        ...         result = call_ai_service()
        ...         cb.record_success()
        ...     except Exception:
        ...         cb.record_failure()
    """

    def __init__(
        self,
        failure_threshold: int,
        timeout: timedelta,
    ) -> None:
        """
        Create a new circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit.
            timeout: Duration to wait before attempting half-open.
        """
        self._lock = threading.Lock()
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._failure_threshold = failure_threshold
        self._timeout_ms = timeout.total_seconds() * 1000

    def can_execute(self) -> bool:
        """
        Check if requests can be executed.

        Returns:
            True if request can proceed, False if circuit is open.
        """
        with self._lock:
            current_state = self._state

            if current_state == CircuitBreakerState.CLOSED:
                return True
            elif current_state == CircuitBreakerState.OPEN:
                # Check if timeout has elapsed
                if (time.time() * 1000) - self._last_failure_time > self._timeout_ms:
                    self._state = CircuitBreakerState.HALF_OPEN
                    return True
                return False
            elif current_state == CircuitBreakerState.HALF_OPEN:
                return True
            else:
                return False

    def record_success(self) -> None:
        """
        Record a successful operation.

        Resets failure count and closes the circuit if it was open or half-open.
        """
        with self._lock:
            self._failure_count = 0
            self._state = CircuitBreakerState.CLOSED

    def record_failure(self) -> None:
        """
        Record a failed operation.

        Increments failure count and opens the circuit if threshold is exceeded.
        """
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time() * 1000

            if self._failure_count >= self._failure_threshold:
                self._state = CircuitBreakerState.OPEN

    def is_open(self) -> bool:
        """
        Check if circuit breaker is open.

        Returns:
            True if circuit is open (blocking requests), False otherwise.
        """
        with self._lock:
            return self._state == CircuitBreakerState.OPEN

    def get_state(self) -> CircuitBreakerState:
        """
        Get current state.

        Returns:
            Current circuit breaker state.
        """
        with self._lock:
            return self._state

    def get_failure_count(self) -> int:
        """
        Get current failure count.

        Returns:
            Number of recent failures.
        """
        with self._lock:
            return self._failure_count

    def reset(self) -> None:
        """
        Manually reset the circuit breaker to closed state.

        This should only be used for testing or manual intervention.
        """
        with self._lock:
            self._state = CircuitBreakerState.CLOSED
            self._failure_count = 0
            self._last_failure_time = 0.0

    def __str__(self) -> str:
        """Return string representation of circuit breaker."""
        return (
            f"CircuitBreaker(state={self.get_state().value}, "
            f"failures={self.get_failure_count()}/{self._failure_threshold})"
        )
