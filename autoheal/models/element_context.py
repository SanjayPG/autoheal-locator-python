"""
Element Context model.

This module provides the ElementContext class for storing contextual
information about an element's position and relationships.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from autoheal.models.element_fingerprint import ElementFingerprint
from autoheal.models.position import Position


class ElementContext(BaseModel):
    """
    Contextual information about an element's position and relationships.

    Stores information about the element's parent container, relative position,
    sibling elements, attributes, text content, and fingerprint.

    Attributes:
        parent_container: Selector or description of parent container.
        relative_position: Position relative to parent.
        sibling_elements: List of sibling element selectors.
        attributes: Element attributes as key-value pairs.
        text_content: Text content of the element.
        fingerprint: Unique fingerprint for the element.

    Examples:
        >>> context = (ElementContext.builder()
        ...     .parent_container("div#main-content")
        ...     .relative_position(Position(10, 20, 100, 30))
        ...     .sibling_elements(["#username", "#password"])
        ...     .attributes({"type": "submit", "class": "btn"})
        ...     .text_content("Login")
        ...     .build())
    """

    parent_container: Optional[str] = None
    relative_position: Optional[Position] = None
    sibling_elements: List[str] = Field(default_factory=list)
    attributes: Dict[str, str] = Field(default_factory=dict)
    text_content: Optional[str] = None
    fingerprint: Optional[ElementFingerprint] = None

    class Config:
        """Pydantic model configuration."""
        validate_assignment = True
        arbitrary_types_allowed = True

    @classmethod
    def builder(cls) -> "ElementContextBuilder":
        """
        Create a builder for fluent API construction.

        Returns:
            ElementContextBuilder instance for method chaining.

        Examples:
            >>> context = (ElementContext.builder()
            ...     .parent_container("form#login")
            ...     .text_content("Submit")
            ...     .build())
        """
        return ElementContextBuilder()


class ElementContextBuilder:
    """
    Builder class for fluent ElementContext construction.

    Provides a chainable API for building ElementContext instances.

    Examples:
        >>> context = (ElementContext.builder()
        ...     .parent_container("div#container")
        ...     .relative_position(Position(50, 100, 200, 40))
        ...     .sibling_elements(["input#username", "input#password"])
        ...     .attributes({"type": "button", "disabled": "false"})
        ...     .text_content("Click me")
        ...     .fingerprint(fingerprint_obj)
        ...     .build())
    """

    def __init__(self):
        """Initialize builder with default values."""
        self._parent_container: Optional[str] = None
        self._relative_position: Optional[Position] = None
        self._sibling_elements: List[str] = []
        self._attributes: Dict[str, str] = {}
        self._text_content: Optional[str] = None
        self._fingerprint: Optional[ElementFingerprint] = None

    def parent_container(self, parent: str) -> "ElementContextBuilder":
        """Set the parent container."""
        self._parent_container = parent
        return self

    def relative_position(self, position: Position) -> "ElementContextBuilder":
        """Set the relative position."""
        self._relative_position = position
        return self

    def sibling_elements(self, siblings: List[str]) -> "ElementContextBuilder":
        """Set the sibling elements."""
        self._sibling_elements = list(siblings)
        return self

    def attributes(self, attrs: Dict[str, str]) -> "ElementContextBuilder":
        """Set the attributes."""
        self._attributes = dict(attrs)
        return self

    def text_content(self, text: str) -> "ElementContextBuilder":
        """Set the text content."""
        self._text_content = text
        return self

    def fingerprint(self, fingerprint: ElementFingerprint) -> "ElementContextBuilder":
        """Set the fingerprint."""
        self._fingerprint = fingerprint
        return self

    def element(self, element: Any) -> "ElementContextBuilder":
        """
        Store element reference (for compatibility).

        Note: This method is provided for API compatibility but the element
        is not stored as we focus on contextual information.

        Args:
            element: Web element reference (ignored).

        Returns:
            Self for method chaining.
        """
        # Element reference not stored - focusing on contextual information
        return self

    def page_url(self, url: str) -> "ElementContextBuilder":
        """
        Store page URL in attributes.

        Args:
            url: Page URL.

        Returns:
            Self for method chaining.
        """
        self._attributes["pageUrl"] = url
        return self

    def build(self) -> ElementContext:
        """
        Build and return the ElementContext instance.

        Returns:
            Configured ElementContext instance.
        """
        return ElementContext(
            parent_container=self._parent_container,
            relative_position=self._relative_position,
            sibling_elements=self._sibling_elements,
            attributes=self._attributes,
            text_content=self._text_content,
            fingerprint=self._fingerprint,
        )
