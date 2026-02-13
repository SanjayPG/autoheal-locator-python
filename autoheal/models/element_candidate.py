"""
Element Candidate model.

This module provides the ElementCandidate class for representing
candidate elements with selector and confidence information.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class ElementCandidate(BaseModel):
    """
    Represents a candidate element with selector and confidence information.

    Contains information about a potential element match including its selector,
    confidence score, description, context, and additional properties.

    Attributes:
        selector: The CSS/XPath selector for this candidate element.
        confidence: Confidence score (0.0-1.0) for this candidate.
        description: Human-readable description of the element.
        context: Contextual information about the element.
        properties: Additional properties as key-value pairs.

    Examples:
        >>> from autoheal.models.element_context import ElementContext
        >>> context = ElementContext.builder().parent_container("div#main").build()
        >>> candidate = ElementCandidate(
        ...     selector="#submit-button",
        ...     confidence=0.95,
        ...     description="Submit button",
        ...     context=context,
        ...     properties={"tagName": "button", "type": "submit"}
        ... )
    """

    selector: str
    confidence: float = Field(ge=0.0, le=1.0)
    description: str
    context: Optional["ElementContext"] = None
    properties: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)


# Import after class definition to avoid circular imports
from autoheal.models.element_context import ElementContext

# Update forward references
ElementCandidate.model_rebuild()
