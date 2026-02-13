"""
Locator Result model.

This module provides the LocatorResult class for representing the
result of an element location operation.
"""

from datetime import timedelta
from typing import Any, Optional

from pydantic import BaseModel, Field

from autoheal.models.enums import LocatorStrategy


class LocatorResult(BaseModel):
    """
    Represents the result of an element location operation.

    Contains the located element, actual selector used, strategy applied,
    execution metrics, and confidence information.

    Attributes:
        element: The located web element (WebElement or Playwright Locator).
        actual_selector: The actual selector that was used successfully.
        strategy: The locator strategy that was used.
        execution_time: Time taken to locate the element.
        from_cache: Whether the result was retrieved from cache.
        confidence: Confidence score for the result (0.0-1.0).
        reasoning: AI reasoning for selector selection (if applicable).

    Examples:
        >>> result = (LocatorResult.builder()
        ...     .element(web_element)
        ...     .actual_selector("#submit-button")
        ...     .strategy(LocatorStrategy.DOM_ANALYSIS)
        ...     .execution_time(timedelta(milliseconds=250))
        ...     .from_cache(False)
        ...     .confidence(0.95)
        ...     .reasoning("Selected based on stable ID attribute")
        ...     .build())
    """

    element: Optional[Any] = None
    actual_selector: Optional[str] = None
    strategy: Optional[LocatorStrategy] = None
    execution_time: Optional[timedelta] = None
    from_cache: bool = Field(default=False)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    tokens_used: int = Field(default=0, description="Total tokens used in AI API calls")

    class Config:
        """Pydantic model configuration."""
        validate_assignment = True
        arbitrary_types_allowed = True

    @classmethod
    def builder(cls) -> "LocatorResultBuilder":
        """
        Create a builder for fluent API construction.

        Returns:
            LocatorResultBuilder instance for method chaining.

        Examples:
            >>> result = (LocatorResult.builder()
            ...     .actual_selector("#login")
            ...     .strategy(LocatorStrategy.CACHED)
            ...     .from_cache(True)
            ...     .build())
        """
        return LocatorResultBuilder()


class LocatorResultBuilder:
    """
    Builder class for fluent LocatorResult construction.

    Provides a chainable API for building LocatorResult instances.

    Examples:
        >>> result = (LocatorResult.builder()
        ...     .element(selenium_element)
        ...     .actual_selector("//button[@id='submit']")
        ...     .strategy(LocatorStrategy.VISUAL_ANALYSIS)
        ...     .execution_time(timedelta(seconds=1.5))
        ...     .from_cache(False)
        ...     .confidence(0.92)
        ...     .reasoning("Identified via visual pattern matching")
        ...     .build())
    """

    def __init__(self):
        """Initialize builder with default values."""
        self._element: Optional[Any] = None
        self._actual_selector: Optional[str] = None
        self._strategy: Optional[LocatorStrategy] = None
        self._execution_time: Optional[timedelta] = None
        self._from_cache: bool = False
        self._confidence: float = 1.0
        self._reasoning: Optional[str] = None
        self._tokens_used: int = 0

    def element(self, element: Any) -> "LocatorResultBuilder":
        """Set the web element."""
        self._element = element
        return self

    def actual_selector(self, selector: str) -> "LocatorResultBuilder":
        """Set the actual selector."""
        self._actual_selector = selector
        return self

    def strategy(self, strategy: LocatorStrategy) -> "LocatorResultBuilder":
        """Set the locator strategy."""
        self._strategy = strategy
        return self

    def execution_time(self, execution_time: timedelta) -> "LocatorResultBuilder":
        """Set the execution time."""
        self._execution_time = execution_time
        return self

    def from_cache(self, from_cache: bool) -> "LocatorResultBuilder":
        """Set whether from cache."""
        self._from_cache = from_cache
        return self

    def confidence(self, confidence: float) -> "LocatorResultBuilder":
        """Set the confidence score."""
        self._confidence = confidence
        return self

    def reasoning(self, reasoning: str) -> "LocatorResultBuilder":
        """Set the reasoning."""
        self._reasoning = reasoning
        return self

    def tokens_used(self, tokens: int) -> "LocatorResultBuilder":
        """Set the tokens used."""
        self._tokens_used = tokens
        return self

    def build(self) -> LocatorResult:
        """
        Build and return the LocatorResult instance.

        Returns:
            Configured LocatorResult instance.
        """
        return LocatorResult(
            element=self._element,
            actual_selector=self._actual_selector,
            strategy=self._strategy,
            execution_time=self._execution_time,
            from_cache=self._from_cache,
            confidence=self._confidence,
            reasoning=self._reasoning,
            tokens_used=self._tokens_used,
        )
