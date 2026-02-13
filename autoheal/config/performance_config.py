"""
Performance Configuration for AutoHeal framework.

This module provides configuration for performance tuning including
thread pool size, timeouts, metrics, and execution strategies.
"""

import multiprocessing
from datetime import timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from autoheal.models.enums import ExecutionStrategy


class PerformanceConfig(BaseModel):
    """
    Configuration for performance tuning.

    Controls thread pool sizing, timeouts, metrics collection, and execution strategies.

    Attributes:
        thread_pool_size: Number of threads in the pool for concurrent operations.
        element_timeout: Timeout for element location operations.
        enable_metrics: Whether to enable performance metrics collection.
        max_concurrent_requests: Maximum number of concurrent AI requests.
        execution_strategy: Strategy for executing healing operations.

    Examples:
        >>> # Create with defaults
        >>> config = PerformanceConfig()

        >>> # Create with custom settings
        >>> config = PerformanceConfig(
        ...     thread_pool_size=16,
        ...     element_timeout=timedelta(seconds=15),
        ...     execution_strategy=ExecutionStrategy.PARALLEL
        ... )

        >>> # Use builder pattern
        >>> config = (PerformanceConfig.builder()
        ...     .thread_pool_size(8)
        ...     .element_timeout(timedelta(seconds=20))
        ...     .enable_metrics(True)
        ...     .build())
    """

    thread_pool_size: int = Field(
        default_factory=lambda: multiprocessing.cpu_count() * 2,
        ge=1,
        le=100
    )
    element_timeout: timedelta = Field(default=timedelta(seconds=10))
    quick_check_timeout: timedelta = Field(default=timedelta(milliseconds=500))
    """Quick timeout for initial selector check before falling back to cache.

    This allows correct selectors to work fast while quickly failing on wrong
    selectors to check the cache. Default: 500ms. Increase for slow pages.
    """
    enable_metrics: bool = Field(default=True)
    max_concurrent_requests: int = Field(default=50, ge=1, le=1000)
    execution_strategy: ExecutionStrategy = Field(default=ExecutionStrategy.SEQUENTIAL)

    model_config = ConfigDict(use_enum_values=False, validate_assignment=True)

    @classmethod
    def builder(cls) -> "PerformanceConfigBuilder":
        """
        Create a builder for fluent API construction.

        Returns:
            PerformanceConfigBuilder instance for method chaining.

        Examples:
            >>> config = (PerformanceConfig.builder()
            ...     .thread_pool_size(12)
            ...     .execution_strategy(ExecutionStrategy.SMART_SEQUENTIAL)
            ...     .build())
        """
        return PerformanceConfigBuilder()

    def __str__(self) -> str:
        """String representation of the configuration."""
        return (
            f"PerformanceConfig(thread_pool_size={self.thread_pool_size}, "
            f"execution_strategy={self.execution_strategy}, enable_metrics={self.enable_metrics})"
        )


class PerformanceConfigBuilder:
    """
    Builder class for fluent PerformanceConfig construction.

    Provides a chainable API for building PerformanceConfig instances.

    Examples:
        >>> config = (PerformanceConfig.builder()
        ...     .thread_pool_size(16)
        ...     .element_timeout(timedelta(seconds=15))
        ...     .enable_metrics(True)
        ...     .max_concurrent_requests(100)
        ...     .execution_strategy(ExecutionStrategy.PARALLEL)
        ...     .build())
    """

    def __init__(self):
        """Initialize builder with default values."""
        self._thread_pool_size = multiprocessing.cpu_count() * 2
        self._element_timeout = timedelta(seconds=10)
        self._quick_check_timeout = timedelta(milliseconds=500)
        self._enable_metrics = True
        self._max_concurrent_requests = 50
        self._execution_strategy = ExecutionStrategy.SEQUENTIAL

    def thread_pool_size(self, size: int) -> "PerformanceConfigBuilder":
        """Set the thread pool size."""
        self._thread_pool_size = size
        return self

    def element_timeout(self, timeout: timedelta) -> "PerformanceConfigBuilder":
        """Set the element timeout."""
        self._element_timeout = timeout
        return self

    def quick_check_timeout(self, timeout: timedelta) -> "PerformanceConfigBuilder":
        """Set the quick check timeout for initial selector validation.

        This is used to quickly test if the original selector works before
        falling back to cache. Default: 500ms. Increase for slow pages.
        """
        self._quick_check_timeout = timeout
        return self

    def enable_metrics(self, enable: bool) -> "PerformanceConfigBuilder":
        """Set whether to enable metrics."""
        self._enable_metrics = enable
        return self

    def max_concurrent_requests(self, max_requests: int) -> "PerformanceConfigBuilder":
        """Set the maximum concurrent requests."""
        self._max_concurrent_requests = max_requests
        return self

    def execution_strategy(self, strategy: ExecutionStrategy) -> "PerformanceConfigBuilder":
        """Set the execution strategy."""
        self._execution_strategy = strategy
        return self

    def build(self) -> PerformanceConfig:
        """
        Build and return the PerformanceConfig instance.

        Returns:
            Configured PerformanceConfig instance.
        """
        return PerformanceConfig(
            thread_pool_size=self._thread_pool_size,
            element_timeout=self._element_timeout,
            quick_check_timeout=self._quick_check_timeout,
            enable_metrics=self._enable_metrics,
            max_concurrent_requests=self._max_concurrent_requests,
            execution_strategy=self._execution_strategy,
        )
