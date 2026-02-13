"""
Resilience Configuration for AutoHeal framework.

This module provides configuration for resilience patterns including
circuit breaker, retry logic, and timeout handling.
"""

from datetime import timedelta

from pydantic import BaseModel, ConfigDict, Field


class ResilienceConfig(BaseModel):
    """
    Configuration for resilience patterns (circuit breaker, retry, etc.).

    Controls how the system handles failures and recovers from errors.

    Attributes:
        circuit_breaker_failure_threshold: Number of failures before circuit opens.
        circuit_breaker_timeout: Time to wait before attempting to close circuit.
        retry_max_attempts: Maximum number of retry attempts.
        retry_delay: Delay between retry attempts.

    Examples:
        >>> # Create with defaults
        >>> config = ResilienceConfig()

        >>> # Create with custom settings
        >>> config = ResilienceConfig(
        ...     circuit_breaker_failure_threshold=10,
        ...     retry_max_attempts=5,
        ...     retry_delay=timedelta(seconds=2)
        ... )

        >>> # Use builder pattern
        >>> config = (ResilienceConfig.builder()
        ...     .circuit_breaker_failure_threshold(3)
        ...     .circuit_breaker_timeout(timedelta(minutes=10))
        ...     .build())
    """

    circuit_breaker_failure_threshold: int = Field(default=5, ge=1, le=100)
    circuit_breaker_timeout: timedelta = Field(default=timedelta(minutes=5))
    retry_max_attempts: int = Field(default=3, ge=0, le=10)
    retry_delay: timedelta = Field(default=timedelta(seconds=1))

    model_config = ConfigDict(use_enum_values=False, validate_assignment=True)

    @classmethod
    def builder(cls) -> "ResilienceConfigBuilder":
        """
        Create a builder for fluent API construction.

        Returns:
            ResilienceConfigBuilder instance for method chaining.

        Examples:
            >>> config = (ResilienceConfig.builder()
            ...     .circuit_breaker_failure_threshold(8)
            ...     .retry_max_attempts(5)
            ...     .build())
        """
        return ResilienceConfigBuilder()

    def __str__(self) -> str:
        """String representation of the configuration."""
        return (
            f"ResilienceConfig(circuit_breaker_threshold={self.circuit_breaker_failure_threshold}, "
            f"retry_max_attempts={self.retry_max_attempts})"
        )


class ResilienceConfigBuilder:
    """
    Builder class for fluent ResilienceConfig construction.

    Provides a chainable API for building ResilienceConfig instances.

    Examples:
        >>> config = (ResilienceConfig.builder()
        ...     .circuit_breaker_failure_threshold(10)
        ...     .circuit_breaker_timeout(timedelta(minutes=15))
        ...     .retry_max_attempts(5)
        ...     .retry_delay(timedelta(seconds=2))
        ...     .build())
    """

    def __init__(self):
        """Initialize builder with default values."""
        self._circuit_breaker_failure_threshold = 5
        self._circuit_breaker_timeout = timedelta(minutes=5)
        self._retry_max_attempts = 3
        self._retry_delay = timedelta(seconds=1)

    def circuit_breaker_failure_threshold(self, threshold: int) -> "ResilienceConfigBuilder":
        """Set the circuit breaker failure threshold."""
        self._circuit_breaker_failure_threshold = threshold
        return self

    def circuit_breaker_timeout(self, timeout: timedelta) -> "ResilienceConfigBuilder":
        """Set the circuit breaker timeout."""
        self._circuit_breaker_timeout = timeout
        return self

    def retry_max_attempts(self, max_attempts: int) -> "ResilienceConfigBuilder":
        """Set the maximum retry attempts."""
        self._retry_max_attempts = max_attempts
        return self

    def retry_delay(self, delay: timedelta) -> "ResilienceConfigBuilder":
        """Set the retry delay."""
        self._retry_delay = delay
        return self

    def build(self) -> ResilienceConfig:
        """
        Build and return the ResilienceConfig instance.

        Returns:
            Configured ResilienceConfig instance.
        """
        return ResilienceConfig(
            circuit_breaker_failure_threshold=self._circuit_breaker_failure_threshold,
            circuit_breaker_timeout=self._circuit_breaker_timeout,
            retry_max_attempts=self._retry_max_attempts,
            retry_delay=self._retry_delay,
        )
