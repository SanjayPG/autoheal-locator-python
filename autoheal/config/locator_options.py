"""
Locator Options for AutoHeal framework.

This module provides configuration options for element location operations.
"""

from datetime import timedelta

from pydantic import BaseModel, Field


class LocatorOptions(BaseModel):
    """
    Configuration options for element location operations.

    Controls timeouts, analysis features, caching, and confidence thresholds.

    Attributes:
        timeout: Timeout for locator operations.
        enable_visual_analysis: Whether visual analysis is enabled.
        enable_caching: Whether caching is enabled.
        confidence_threshold: Minimum confidence score for accepting results (0.0-1.0).
        max_candidates: Maximum number of candidate elements to consider.

    Examples:
        >>> # Create with defaults
        >>> options = LocatorOptions()

        >>> # Create with custom settings
        >>> options = LocatorOptions(
        ...     timeout=timedelta(seconds=15),
        ...     confidence_threshold=0.8,
        ...     max_candidates=10
        ... )

        >>> # Use builder pattern
        >>> options = (LocatorOptions.builder()
        ...     .timeout(timedelta(seconds=20))
        ...     .enable_visual_analysis(True)
        ...     .confidence_threshold(0.75)
        ...     .build())
    """

    timeout: timedelta = Field(default=timedelta(seconds=10))
    enable_visual_analysis: bool = Field(default=True)
    enable_caching: bool = Field(default=True)
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_candidates: int = Field(default=5, ge=1, le=100)

    class Config:
        """Pydantic model configuration."""
        validate_assignment = True

    @classmethod
    def default_options(cls) -> "LocatorOptions":
        """
        Create default locator options.

        Returns:
            LocatorOptions with default settings.

        Examples:
            >>> options = LocatorOptions.default_options()
            >>> assert options.timeout == timedelta(seconds=10)
        """
        return cls()

    @classmethod
    def builder(cls) -> "LocatorOptionsBuilder":
        """
        Create a builder for fluent API construction.

        Returns:
            LocatorOptionsBuilder instance for method chaining.

        Examples:
            >>> options = (LocatorOptions.builder()
            ...     .timeout(timedelta(seconds=15))
            ...     .enable_visual_analysis(True)
            ...     .build())
        """
        return LocatorOptionsBuilder()

    def __str__(self) -> str:
        """String representation of the options."""
        return (
            f"LocatorOptions(timeout={self.timeout}, enable_visual_analysis={self.enable_visual_analysis}, "
            f"confidence_threshold={self.confidence_threshold}, max_candidates={self.max_candidates})"
        )


class LocatorOptionsBuilder:
    """
    Builder class for fluent LocatorOptions construction.

    Provides a chainable API for building LocatorOptions instances.

    Examples:
        >>> options = (LocatorOptions.builder()
        ...     .timeout(timedelta(seconds=20))
        ...     .enable_visual_analysis(True)
        ...     .enable_caching(True)
        ...     .confidence_threshold(0.8)
        ...     .max_candidates(10)
        ...     .build())
    """

    def __init__(self):
        """Initialize builder with default values."""
        self._timeout = timedelta(seconds=10)
        self._enable_visual_analysis = True
        self._enable_caching = True
        self._confidence_threshold = 0.7
        self._max_candidates = 5

    def timeout(self, timeout: timedelta) -> "LocatorOptionsBuilder":
        """Set the timeout."""
        self._timeout = timeout
        return self

    def enable_visual_analysis(self, enable: bool) -> "LocatorOptionsBuilder":
        """Set whether visual analysis is enabled."""
        self._enable_visual_analysis = enable
        return self

    def enable_caching(self, enable: bool) -> "LocatorOptionsBuilder":
        """Set whether caching is enabled."""
        self._enable_caching = enable
        return self

    def confidence_threshold(self, threshold: float) -> "LocatorOptionsBuilder":
        """Set the confidence threshold."""
        self._confidence_threshold = threshold
        return self

    def max_candidates(self, max_candidates: int) -> "LocatorOptionsBuilder":
        """Set the maximum candidates."""
        self._max_candidates = max_candidates
        return self

    def build(self) -> LocatorOptions:
        """
        Build and return the LocatorOptions instance.

        Returns:
            Configured LocatorOptions instance.
        """
        return LocatorOptions(
            timeout=self._timeout,
            enable_visual_analysis=self._enable_visual_analysis,
            enable_caching=self._enable_caching,
            confidence_threshold=self._confidence_threshold,
            max_candidates=self._max_candidates,
        )
