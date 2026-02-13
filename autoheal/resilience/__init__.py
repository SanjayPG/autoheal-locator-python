"""
Resilience components for the AutoHeal framework.

This module provides resilience patterns including circuit breakers
to protect against cascading failures.
"""

from autoheal.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerState

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerState",
]
