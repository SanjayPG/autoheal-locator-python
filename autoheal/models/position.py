"""
Position model for element positioning and size.

This module provides the Position class for representing the position
and dimensions of web elements.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    """
    Represents the position and size of an element.

    This is an immutable data class that stores the x, y coordinates
    and width, height dimensions of a web element.

    Attributes:
        x: The x-coordinate of the element's position.
        y: The y-coordinate of the element's position.
        width: The width of the element.
        height: The height of the element.

    Examples:
        >>> pos = Position(x=100, y=200, width=300, height=50)
        >>> print(pos)
        Position(x=100, y=200, width=300, height=50)

        >>> # Immutable - this will raise an error
        >>> # pos.x = 150  # FrozenInstanceError
    """

    x: int
    y: int
    width: int
    height: int

    def __str__(self) -> str:
        """String representation of the position."""
        return f"Position(x={self.x}, y={self.y}, width={self.width}, height={self.height})"
