"""
Locator Filter model for Playwright.

This module provides the LocatorFilter class for representing filters
applied to Playwright locators.
"""

import re
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class FilterType(Enum):
    """
    Types of filters that can be applied to Playwright locators.

    Attributes:
        HAS_TEXT: Filter by text content.
        HAS_NOT_TEXT: Filter by excluding text content.
        HAS: Filter by nested locator (Phase 2).
        HAS_NOT: Filter by excluding nested locator (Phase 2).
    """

    HAS_TEXT = "has_text"
    HAS_NOT_TEXT = "has_not_text"
    HAS = "has"
    HAS_NOT = "has_not"


class LocatorFilter(BaseModel):
    """
    Represents a filter applied to a Playwright locator.

    Supports: hasText, hasNotText, has (nested locator), hasNot (nested locator).

    Attributes:
        type: Type of filter to apply.
        value: Text value or nested locator string.
        is_regex: True if value is a regex pattern like /pattern/flags.

    Examples:
        >>> # Text filter
        >>> filter1 = LocatorFilter(type=FilterType.HAS_TEXT, value="Product", is_regex=False)

        >>> # Regex filter
        >>> filter2 = LocatorFilter(type=FilterType.HAS_TEXT, value="/product/i", is_regex=True)

        >>> # Using builder
        >>> filter3 = (LocatorFilter.builder()
        ...     .has_text("Submit")
        ...     .build())
    """

    type: FilterType
    value: str
    is_regex: bool = False

    class Config:
        """Pydantic model configuration."""
        use_enum_values = False

    def to_javascript_string(self) -> str:
        """
        Convert filter to JavaScript-style format for caching.

        Returns:
            JavaScript-style filter string.

        Examples:
            >>> filter = LocatorFilter(type=FilterType.HAS_TEXT, value="Product", is_regex=False)
            >>> print(filter.to_javascript_string())
            filter({ hasText: 'Product' })

            >>> filter_regex = LocatorFilter(type=FilterType.HAS_TEXT, value="/product/i", is_regex=True)
            >>> print(filter_regex.to_javascript_string())
            filter({ hasText: /product/i })
        """
        option_name_map = {
            FilterType.HAS_TEXT: "hasText",
            FilterType.HAS_NOT_TEXT: "hasNotText",
            FilterType.HAS: "has",
            FilterType.HAS_NOT: "hasNot",
        }
        option_name = option_name_map[self.type]

        if self.is_regex:
            # Regex pattern: /pattern/flags
            value_str = self.value
        elif self.type in (FilterType.HAS, FilterType.HAS_NOT):
            # Nested locator: don't quote
            value_str = self.value
        else:
            # Regular text: quote it
            value_str = f"'{self.value.replace(chr(39), chr(92) + chr(39))}'"

        return f"filter({{ {option_name}: {value_str} }})"

    def to_python_string(self) -> str:
        """
        Convert filter to Python Playwright code.

        Returns:
            Python Playwright filter code.

        Examples:
            >>> filter = LocatorFilter(type=FilterType.HAS_TEXT, value="Product", is_regex=False)
            >>> print(filter.to_python_string())
            .filter(has_text="Product")

            >>> filter_regex = LocatorFilter(type=FilterType.HAS_TEXT, value="/product/i", is_regex=True)
            >>> print(filter_regex.to_python_string())
            .filter(has_text=re.compile("product", re.IGNORECASE))
        """
        method_name_map = {
            FilterType.HAS_TEXT: "has_text",
            FilterType.HAS_NOT_TEXT: "has_not_text",
            FilterType.HAS: "has",
            FilterType.HAS_NOT: "has_not",
        }
        method_name = method_name_map[self.type]

        if self.is_regex and self.type in (FilterType.HAS_TEXT, FilterType.HAS_NOT_TEXT):
            # Convert /pattern/flags to re.compile()
            value_str = self._convert_regex_to_python_pattern(self.value)
        elif self.type in (FilterType.HAS, FilterType.HAS_NOT):
            # Nested locator: use as-is
            value_str = self.value
        else:
            # Regular text: quote it
            escaped = self.value.replace(chr(92), chr(92) + chr(92)).replace('"', chr(92) + '"')
            value_str = f'"{escaped}"'

        return f".filter({method_name}={value_str})"

    def _convert_regex_to_python_pattern(self, regex_literal: str) -> str:
        """
        Convert JavaScript regex literal to Python re.compile() call.

        Args:
            regex_literal: JavaScript regex like /submit/i.

        Returns:
            Python re.compile() string.

        Examples:
            >>> filter = LocatorFilter(type=FilterType.HAS_TEXT, value="", is_regex=False)
            >>> result = filter._convert_regex_to_python_pattern("/submit/i")
            >>> print(result)
            re.compile("submit", re.IGNORECASE)
        """
        if not regex_literal.startswith("/"):
            escaped = regex_literal.replace(chr(92), chr(92) + chr(92)).replace('"', chr(92) + '"')
            return f'"{escaped}"'

        last_slash = regex_literal.rfind("/")
        if last_slash <= 0:
            escaped = regex_literal.replace(chr(92), chr(92) + chr(92)).replace('"', chr(92) + '"')
            return f'"{escaped}"'

        pattern = regex_literal[1:last_slash]
        flags = regex_literal[last_slash + 1:]

        # Escape special characters in pattern
        pattern = pattern.replace(chr(92), chr(92) + chr(92)).replace('"', chr(92) + '"')

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
            return f're.compile("{pattern}", {flags_str})'
        else:
            return f're.compile("{pattern}")'

    @classmethod
    def builder(cls) -> "LocatorFilterBuilder":
        """
        Create a builder for fluent API construction.

        Returns:
            LocatorFilterBuilder instance for method chaining.

        Examples:
            >>> filter = (LocatorFilter.builder()
            ...     .has_text("Submit")
            ...     .build())
        """
        return LocatorFilterBuilder()


class LocatorFilterBuilder:
    """
    Builder class for fluent LocatorFilter construction.

    Examples:
        >>> filter = (LocatorFilter.builder()
        ...     .type(FilterType.HAS_TEXT)
        ...     .value("Product")
        ...     .is_regex(False)
        ...     .build())

        >>> # Convenience method
        >>> filter = (LocatorFilter.builder()
        ...     .has_text("Login")
        ...     .build())

        >>> # Regex pattern
        >>> filter = (LocatorFilter.builder()
        ...     .has_text_pattern("/submit/i")
        ...     .build())
    """

    def __init__(self):
        """Initialize builder with default values."""
        self._type: Optional[FilterType] = None
        self._value: Optional[str] = None
        self._is_regex: bool = False

    def type(self, filter_type: FilterType) -> "LocatorFilterBuilder":
        """Set the filter type."""
        self._type = filter_type
        return self

    def value(self, value: str) -> "LocatorFilterBuilder":
        """Set the filter value."""
        self._value = value
        return self

    def is_regex(self, is_regex: bool) -> "LocatorFilterBuilder":
        """Set whether the value is a regex."""
        self._is_regex = is_regex
        return self

    def has_text(self, text: str) -> "LocatorFilterBuilder":
        """Convenience method for HAS_TEXT filter."""
        self._type = FilterType.HAS_TEXT
        self._value = text
        self._is_regex = False
        return self

    def has_text_pattern(self, pattern: str) -> "LocatorFilterBuilder":
        """Convenience method for HAS_TEXT with regex pattern."""
        self._type = FilterType.HAS_TEXT
        self._value = pattern
        self._is_regex = True
        return self

    def has_not_text(self, text: str) -> "LocatorFilterBuilder":
        """Convenience method for HAS_NOT_TEXT filter."""
        self._type = FilterType.HAS_NOT_TEXT
        self._value = text
        self._is_regex = False
        return self

    def build(self) -> LocatorFilter:
        """
        Build and return the LocatorFilter instance.

        Returns:
            Configured LocatorFilter instance.

        Raises:
            ValueError: If type or value is not set.
        """
        if self._type is None or self._value is None:
            raise ValueError("Type and value must be set")

        return LocatorFilter(
            type=self._type,
            value=self._value,
            is_regex=self._is_regex,
        )
