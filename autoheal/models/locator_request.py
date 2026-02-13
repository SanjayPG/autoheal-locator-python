"""
Locator Request model.

This module provides the LocatorRequest class for representing a request
to locate an element with auto-healing capabilities.
"""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from autoheal.config.locator_options import LocatorOptions
from autoheal.models.element_context import ElementContext
from autoheal.models.enums import LocatorType


class LocatorRequest(BaseModel):
    """
    Represents a request to locate an element with auto-healing capabilities.

    Contains all information needed to perform element location including
    the original selector, description, options, adapter, context, and type.

    Attributes:
        original_selector: The original selector to try first.
        description: Human-readable description of the element.
        options: Locator options for timeout, caching, etc.
        adapter: Web automation adapter (Selenium/Playwright).
        context: Contextual information about the element.
        locator_type: Type of locator (CSS, XPath, etc.).
        selenium_by: Selenium By object (for Selenium framework).

    Examples:
        >>> request = (LocatorRequest.builder()
        ...     .selector("#login-button")
        ...     .description("Login button on main page")
        ...     .options(LocatorOptions.default_options())
        ...     .locator_type(LocatorType.CSS)
        ...     .build())
    """

    original_selector: Optional[str] = None
    description: Optional[str] = None
    options: LocatorOptions = LocatorOptions()
    adapter: Optional[Any] = None
    context: Optional[ElementContext] = None
    locator_type: Optional[LocatorType] = None
    selenium_by: Optional[Any] = None
    native_locator: Optional[Any] = None

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    @classmethod
    def builder(cls) -> "LocatorRequestBuilder":
        """
        Create a builder for fluent API construction.

        Returns:
            LocatorRequestBuilder instance for method chaining.

        Examples:
            >>> request = (LocatorRequest.builder()
            ...     .selector("//button[@type='submit']")
            ...     .description("Submit button")
            ...     .locator_type(LocatorType.XPATH)
            ...     .build())
        """
        return LocatorRequestBuilder()


class LocatorRequestBuilder:
    """
    Builder class for fluent LocatorRequest construction.

    Provides a chainable API for building LocatorRequest instances.

    Examples:
        >>> from autoheal.config.locator_options import LocatorOptions
        >>> request = (LocatorRequest.builder()
        ...     .selector("#submit")
        ...     .description("Submit button")
        ...     .options(LocatorOptions(timeout=timedelta(seconds=15)))
        ...     .adapter(driver_adapter)
        ...     .context(element_context)
        ...     .locator_type(LocatorType.CSS)
        ...     .selenium_by(By.CSS_SELECTOR)
        ...     .build())
    """

    def __init__(self):
        """Initialize builder with default values."""
        self._original_selector: Optional[str] = None
        self._description: Optional[str] = None
        self._options: LocatorOptions = LocatorOptions()
        self._adapter: Optional[Any] = None
        self._context: Optional[ElementContext] = None
        self._locator_type: Optional[LocatorType] = None
        self._selenium_by: Optional[Any] = None
        self._native_locator: Optional[Any] = None

    def selector(self, selector: str) -> "LocatorRequestBuilder":
        """Set the original selector."""
        self._original_selector = selector
        return self

    def original_selector(self, selector: str) -> "LocatorRequestBuilder":
        """Set the original selector (alias for selector)."""
        self._original_selector = selector
        return self

    def description(self, description: str) -> "LocatorRequestBuilder":
        """Set the description."""
        self._description = description
        return self

    def options(self, options: LocatorOptions) -> "LocatorRequestBuilder":
        """Set the locator options."""
        self._options = options
        return self

    def adapter(self, adapter: Any) -> "LocatorRequestBuilder":
        """Set the web automation adapter."""
        self._adapter = adapter
        return self

    def context(self, context: ElementContext) -> "LocatorRequestBuilder":
        """Set the element context."""
        self._context = context
        return self

    def locator_type(self, locator_type: LocatorType) -> "LocatorRequestBuilder":
        """Set the locator type."""
        self._locator_type = locator_type
        return self

    def selenium_by(self, selenium_by: Any) -> "LocatorRequestBuilder":
        """Set the Selenium By object."""
        self._selenium_by = selenium_by
        return self

    def native_locator(self, native_locator: Any) -> "LocatorRequestBuilder":
        """Set the native Playwright Locator object."""
        self._native_locator = native_locator
        return self

    def build(self) -> LocatorRequest:
        """
        Build and return the LocatorRequest instance.

        Returns:
            Configured LocatorRequest instance.
        """
        return LocatorRequest(
            original_selector=self._original_selector,
            description=self._description,
            options=self._options,
            adapter=self._adapter,
            context=self._context,
            locator_type=self._locator_type,
            selenium_by=self._selenium_by,
            native_locator=self._native_locator,
        )
