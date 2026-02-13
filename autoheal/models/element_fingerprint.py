"""
Element Fingerprint model.

This module provides the ElementFingerprint class for creating unique
fingerprints to identify elements across page changes.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from autoheal.models.position import Position


class ElementFingerprint(BaseModel):
    """
    Unique fingerprint for identifying elements across page changes.

    Creates a fingerprint based on multiple element characteristics including
    parent chain, position, styles, text content, and nearby elements.

    Attributes:
        parent_chain: Chain of parent elements (e.g., "html>body>div>form").
        screen_position: Position and size of the element.
        computed_styles: Key computed CSS styles.
        text_content: Text content of the element.
        nearby_elements: List of nearby element identifiers.
        visual_hash: Hash of visual appearance (if available).

    Examples:
        >>> fingerprint = (ElementFingerprint.builder()
        ...     .parent_chain("html>body>div#main>form")
        ...     .text("Submit")
        ...     .position(Position(100, 200, 150, 40))
        ...     .computed_styles({"color": "blue", "font-size": "14px"})
        ...     .build())

        >>> # Calculate similarity
        >>> similarity = fingerprint.calculate_similarity(other_fingerprint)
        >>> print(f"Similarity: {similarity:.2f}")
    """

    parent_chain: str = Field(default="")
    screen_position: Optional[Position] = None
    computed_styles: Dict[str, str] = Field(default_factory=dict)
    text_content: str = Field(default="")
    nearby_elements: List[str] = Field(default_factory=list)
    visual_hash: Optional[str] = None

    model_config = ConfigDict(validate_assignment=True)

    def calculate_similarity(self, other: "ElementFingerprint") -> float:
        """
        Calculate similarity score between this fingerprint and another.

        Uses weighted combination of:
        - Parent chain similarity (30%)
        - Position similarity (20%)
        - Text content similarity (30%)
        - Style similarity (20%)

        Args:
            other: The other fingerprint to compare.

        Returns:
            Similarity score between 0.0 and 1.0.

        Examples:
            >>> fp1 = ElementFingerprint(parent_chain="html>body>div", text_content="Submit")
            >>> fp2 = ElementFingerprint(parent_chain="html>body>div", text_content="Submit")
            >>> similarity = fp1.calculate_similarity(fp2)
            >>> assert similarity == 1.0
        """
        parent_similarity = self._calculate_string_similarity(self.parent_chain, other.parent_chain)
        position_similarity = self._calculate_position_similarity(self.screen_position, other.screen_position)
        text_similarity = self._calculate_string_similarity(self.text_content, other.text_content)
        style_similarity = self._calculate_style_similarity(self.computed_styles, other.computed_styles)

        return (parent_similarity * 0.3 + position_similarity * 0.2 +
                text_similarity * 0.3 + style_similarity * 0.2)

    def _calculate_string_similarity(self, s1: Optional[str], s2: Optional[str]) -> float:
        """Calculate similarity between two strings."""
        if s1 is None or s2 is None:
            return 0.0
        if s1 == s2:
            return 1.0
        # Simple similarity based on length difference
        return 1.0 - abs(len(s1) - len(s2)) / max(len(s1), len(s2))

    def _calculate_position_similarity(self, p1: Optional[Position], p2: Optional[Position]) -> float:
        """Calculate similarity between two positions."""
        if p1 is None or p2 is None:
            return 0.0

        distance = ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
        # Normalize by max expected distance (1000 pixels)
        return max(0.0, 1.0 - distance / 1000.0)

    def _calculate_style_similarity(self, styles1: Dict[str, str], styles2: Dict[str, str]) -> float:
        """Calculate similarity between two style dictionaries."""
        if not styles1 and not styles2:
            return 1.0

        all_keys = set(styles1.keys()) | set(styles2.keys())
        if not all_keys:
            return 1.0

        matches = sum(1 for key in all_keys if styles1.get(key) == styles2.get(key))
        return matches / len(all_keys)

    @classmethod
    def builder(cls) -> "ElementFingerprintBuilder":
        """
        Create a builder for fluent API construction.

        Returns:
            ElementFingerprintBuilder instance for method chaining.

        Examples:
            >>> fingerprint = (ElementFingerprint.builder()
            ...     .parent_chain("html>body>div")
            ...     .text("Login")
            ...     .build())
        """
        return ElementFingerprintBuilder()


class ElementFingerprintBuilder:
    """
    Builder class for fluent ElementFingerprint construction.

    Provides a chainable API for building ElementFingerprint instances.

    Examples:
        >>> fingerprint = (ElementFingerprint.builder()
        ...     .tag_name("button")
        ...     .id("submit-btn")
        ...     .class_name("btn btn-primary")
        ...     .text("Submit")
        ...     .position(Position(100, 200, 150, 40))
        ...     .parent_chain("html>body>div#main>form")
        ...     .computed_styles({"color": "blue"})
        ...     .nearby_elements(["#username", "#password"])
        ...     .visual_hash("abc123")
        ...     .build())
    """

    def __init__(self):
        """Initialize builder with default values."""
        self._tag_name: Optional[str] = None
        self._id: Optional[str] = None
        self._class_name: Optional[str] = None
        self._text: Optional[str] = None
        self._position: Optional[Position] = None
        self._parent_chain: Optional[str] = None
        self._computed_styles: Dict[str, str] = {}
        self._nearby_elements: List[str] = []
        self._visual_hash: Optional[str] = None

    def tag_name(self, tag_name: str) -> "ElementFingerprintBuilder":
        """Set the tag name."""
        self._tag_name = tag_name
        return self

    def id(self, element_id: str) -> "ElementFingerprintBuilder":
        """Set the element ID."""
        self._id = element_id
        return self

    def class_name(self, class_name: str) -> "ElementFingerprintBuilder":
        """Set the class name."""
        self._class_name = class_name
        return self

    def text(self, text: str) -> "ElementFingerprintBuilder":
        """Set the text content."""
        self._text = text
        return self

    def position(self, position: Position) -> "ElementFingerprintBuilder":
        """Set the position."""
        self._position = position
        return self

    def parent_chain(self, parent_chain: str) -> "ElementFingerprintBuilder":
        """Set the parent chain."""
        self._parent_chain = parent_chain
        return self

    def computed_styles(self, styles: Dict[str, str]) -> "ElementFingerprintBuilder":
        """Set the computed styles."""
        self._computed_styles = dict(styles)
        return self

    def nearby_elements(self, elements: List[str]) -> "ElementFingerprintBuilder":
        """Set the nearby elements."""
        self._nearby_elements = list(elements)
        return self

    def visual_hash(self, hash_value: str) -> "ElementFingerprintBuilder":
        """Set the visual hash."""
        self._visual_hash = hash_value
        return self

    def build(self) -> ElementFingerprint:
        """
        Build and return the ElementFingerprint instance.

        Returns:
            Configured ElementFingerprint instance.
        """
        return ElementFingerprint(
            parent_chain=self._parent_chain or "",
            screen_position=self._position,
            computed_styles=self._computed_styles,
            text_content=self._text or "",
            nearby_elements=self._nearby_elements,
            visual_hash=self._visual_hash,
        )
