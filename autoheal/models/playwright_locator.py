"""
Playwright Locator model.

This module provides the PlaywrightLocator class for representing
Playwright locators with their type and parameters, including filter support.
"""

import re
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from autoheal.models.locator_filter import LocatorFilter


class PlaywrightLocatorType(Enum):
    """
    Enum representing Playwright locator types.

    Attributes:
        GET_BY_ROLE: getByRole locator.
        GET_BY_LABEL: getByLabel locator.
        GET_BY_PLACEHOLDER: getByPlaceholder locator.
        GET_BY_TEXT: getByText locator.
        GET_BY_ALT_TEXT: getByAltText locator.
        GET_BY_TITLE: getByTitle locator.
        GET_BY_TEST_ID: getByTestId locator.
        CSS_SELECTOR: CSS selector via locator().
        XPATH: XPath expression via locator().
    """

    GET_BY_ROLE = "get_by_role"
    GET_BY_LABEL = "get_by_label"
    GET_BY_PLACEHOLDER = "get_by_placeholder"
    GET_BY_TEXT = "get_by_text"
    GET_BY_ALT_TEXT = "get_by_alt_text"
    GET_BY_TITLE = "get_by_title"
    GET_BY_TEST_ID = "get_by_test_id"
    CSS_SELECTOR = "css_selector"
    XPATH = "xpath"


class PlaywrightLocator(BaseModel):
    """
    Model representing a Playwright locator with its type and parameters.

    Supports filters like .filter(has_text="text").

    Attributes:
        type: The locator type.
        value: The primary value (e.g., "button" for role, "Username" for label).
        options: Additional options (e.g., {"name": "Submit"} for role).
        filters: List of filters applied to this locator.

    Examples:
        >>> # Simple locator
        >>> locator = PlaywrightLocator(
        ...     type=PlaywrightLocatorType.GET_BY_ROLE,
        ...     value="button",
        ...     options={"name": "Submit"}
        ... )

        >>> # Locator with filter
        >>> filter = LocatorFilter.builder().has_text("Product 2").build()
        >>> locator = PlaywrightLocator(
        ...     type=PlaywrightLocatorType.GET_BY_ROLE,
        ...     value="button",
        ...     filters=[filter]
        ... )

        >>> # Using builder
        >>> locator = (PlaywrightLocator.builder()
        ...     .by_role("button", "Submit")
        ...     .build())
    """

    type: PlaywrightLocatorType
    value: str
    options: Dict[str, Any] = Field(default_factory=dict)
    filters: List[LocatorFilter] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=False)

    def has_filters(self) -> bool:
        """Check if this locator has filters applied."""
        return len(self.filters) > 0

    def to_selector_string(self) -> str:
        """
        Convert to Python Playwright code syntax.

        Returns:
            Python code representation.

        Examples:
            >>> locator = PlaywrightLocator.builder().by_role("button").build()
            >>> print(locator.to_selector_string())
            page.get_by_role("button")
        """
        base_locator = self._build_base_locator_string()

        if self.has_filters():
            result = base_locator
            for filter_obj in self.filters:
                result += filter_obj.to_python_string()
            return result

        return base_locator

    def _build_base_locator_string(self) -> str:
        """Build the base locator string without filters."""
        if self.type == PlaywrightLocatorType.GET_BY_ROLE:
            name = self.options.get("name")
            is_regex = self.options.get("isRegex")

            if name:
                if is_regex == "true" and str(name).startswith("/"):
                    regex_str = self._convert_regex_to_python_pattern(str(name))
                    return f'page.get_by_role("{self.value}", name={regex_str})'
                else:
                    return f'page.get_by_role("{self.value}", name="{self._escape_python_string(str(name))}")'
            else:
                return f'page.get_by_role("{self.value}")'

        elif self.type == PlaywrightLocatorType.GET_BY_LABEL:
            return f'page.get_by_label("{self._escape_python_string(self.value)}")'

        elif self.type == PlaywrightLocatorType.GET_BY_PLACEHOLDER:
            return f'page.get_by_placeholder("{self._escape_python_string(self.value)}")'

        elif self.type == PlaywrightLocatorType.GET_BY_TEXT:
            is_regex = self.options.get("isRegex")
            exact = self.options.get("exact")

            if is_regex == "true" and self.value.startswith("/"):
                regex_str = self._convert_regex_to_python_pattern(self.value)
                return f'page.get_by_text({regex_str})'
            elif exact == "true":
                return f'page.get_by_text("{self._escape_python_string(self.value)}", exact=True)'
            else:
                return f'page.get_by_text("{self._escape_python_string(self.value)}")'

        elif self.type == PlaywrightLocatorType.GET_BY_ALT_TEXT:
            return f'page.get_by_alt_text("{self._escape_python_string(self.value)}")'

        elif self.type == PlaywrightLocatorType.GET_BY_TITLE:
            return f'page.get_by_title("{self._escape_python_string(self.value)}")'

        elif self.type == PlaywrightLocatorType.GET_BY_TEST_ID:
            return f'page.get_by_test_id("{self._escape_python_string(self.value)}")'

        elif self.type in (PlaywrightLocatorType.CSS_SELECTOR, PlaywrightLocatorType.XPATH):
            return f'page.locator("{self._escape_python_string(self.value)}")'

        return ""

    def _escape_python_string(self, s: str) -> str:
        """Escape special characters in Python strings."""
        if s is None:
            return ""
        return (s.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t"))

    def _convert_regex_to_python_pattern(self, regex_literal: str) -> str:
        """
        Convert JavaScript regex literal to Python re.compile() call.

        Args:
            regex_literal: JavaScript regex like /submit/i.

        Returns:
            Python re.compile() string.
        """
        if not regex_literal.startswith("/"):
            return f'"{self._escape_python_string(regex_literal)}"'

        last_slash = regex_literal.rfind("/")
        if last_slash <= 0:
            return f'"{self._escape_python_string(regex_literal)}"'

        pattern = regex_literal[1:last_slash]
        flags = regex_literal[last_slash + 1:]

        # Convert flags to Python re constants
        python_flags = []
        if "i" in flags:
            python_flags.append("re.IGNORECASE")
        if "m" in flags:
            python_flags.append("re.MULTILINE")
        if "s" in flags:
            python_flags.append("re.DOTALL")

        if python_flags:
            flags_str = " | ".join(python_flags)
            return f're.compile("{self._escape_python_string(pattern)}", {flags_str})'
        else:
            return f're.compile("{self._escape_python_string(pattern)}")'

    def __str__(self) -> str:
        """String representation."""
        return self.to_selector_string()

    @classmethod
    def builder(cls) -> "PlaywrightLocatorBuilder":
        """
        Create a builder for fluent API construction.

        Returns:
            PlaywrightLocatorBuilder instance for method chaining.
        """
        return PlaywrightLocatorBuilder()


class PlaywrightLocatorBuilder:
    """
    Builder class for fluent PlaywrightLocator construction.

    Examples:
        >>> locator = (PlaywrightLocator.builder()
        ...     .by_role("button", "Submit")
        ...     .filter(LocatorFilter.builder().has_text("Click me").build())
        ...     .build())
    """

    def __init__(self):
        """Initialize builder with default values."""
        self._type: Optional[PlaywrightLocatorType] = None
        self._value: Optional[str] = None
        self._options: Dict[str, Any] = {}
        self._filters: List[LocatorFilter] = []

    def type(self, locator_type: PlaywrightLocatorType) -> "PlaywrightLocatorBuilder":
        """Set the locator type."""
        self._type = locator_type
        return self

    def value(self, value: str) -> "PlaywrightLocatorBuilder":
        """Set the value."""
        self._value = value
        return self

    def option(self, key: str, value: Any) -> "PlaywrightLocatorBuilder":
        """Add an option."""
        self._options[key] = value
        return self

    def options(self, options: Dict[str, Any]) -> "PlaywrightLocatorBuilder":
        """Set all options."""
        self._options = dict(options)
        return self

    def filter(self, filter_obj: LocatorFilter) -> "PlaywrightLocatorBuilder":
        """Add a filter."""
        self._filters.append(filter_obj)
        return self

    def filters(self, filters: List[LocatorFilter]) -> "PlaywrightLocatorBuilder":
        """Set all filters."""
        self._filters = list(filters)
        return self

    def add_filter(self, filter_obj: LocatorFilter) -> "PlaywrightLocatorBuilder":
        """Add a filter (alias for filter())."""
        return self.filter(filter_obj)

    # Convenience methods
    def by_role(self, role: str, name: Optional[str] = None) -> "PlaywrightLocatorBuilder":
        """Convenience method for getByRole."""
        self._type = PlaywrightLocatorType.GET_BY_ROLE
        self._value = role
        if name:
            self._options["name"] = name
        return self

    def by_label(self, label: str) -> "PlaywrightLocatorBuilder":
        """Convenience method for getByLabel."""
        self._type = PlaywrightLocatorType.GET_BY_LABEL
        self._value = label
        return self

    def by_placeholder(self, placeholder: str) -> "PlaywrightLocatorBuilder":
        """Convenience method for getByPlaceholder."""
        self._type = PlaywrightLocatorType.GET_BY_PLACEHOLDER
        self._value = placeholder
        return self

    def by_text(self, text: str) -> "PlaywrightLocatorBuilder":
        """Convenience method for getByText."""
        self._type = PlaywrightLocatorType.GET_BY_TEXT
        self._value = text
        return self

    def by_test_id(self, test_id: str) -> "PlaywrightLocatorBuilder":
        """Convenience method for getByTestId."""
        self._type = PlaywrightLocatorType.GET_BY_TEST_ID
        self._value = test_id
        return self

    def by_alt_text(self, alt_text: str) -> "PlaywrightLocatorBuilder":
        """Convenience method for getByAltText."""
        self._type = PlaywrightLocatorType.GET_BY_ALT_TEXT
        self._value = alt_text
        return self

    def by_title(self, title: str) -> "PlaywrightLocatorBuilder":
        """Convenience method for getByTitle."""
        self._type = PlaywrightLocatorType.GET_BY_TITLE
        self._value = title
        return self

    def by_css(self, css_selector: str) -> "PlaywrightLocatorBuilder":
        """Convenience method for CSS selector."""
        self._type = PlaywrightLocatorType.CSS_SELECTOR
        self._value = css_selector
        return self

    def css_selector(self, css_selector: str) -> "PlaywrightLocatorBuilder":
        """Alias for by_css."""
        return self.by_css(css_selector)

    def xpath(self, xpath_expression: str) -> "PlaywrightLocatorBuilder":
        """Convenience method for XPath."""
        self._type = PlaywrightLocatorType.XPATH
        self._value = xpath_expression
        return self

    def build(self) -> PlaywrightLocator:
        """
        Build and return the PlaywrightLocator instance.

        Returns:
            Configured PlaywrightLocator instance.

        Raises:
            ValueError: If type or value is not set.
        """
        if self._type is None or self._value is None:
            raise ValueError("Type and value must be set")

        return PlaywrightLocator(
            type=self._type,
            value=self._value,
            options=self._options,
            filters=self._filters,
        )
