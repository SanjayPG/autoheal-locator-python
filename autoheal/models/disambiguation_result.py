"""
Disambiguation result model for AI disambiguation calls.

This module defines the result type returned when AI selects the best
matching element from multiple candidates.
"""

from dataclasses import dataclass


@dataclass
class DisambiguationResult:
    """
    Result from AI disambiguation call.

    Attributes:
        selected_index: 1-based index of the selected element.
        tokens_used: Total tokens used in the AI API call.
    """
    selected_index: int
    tokens_used: int = 0

    def __str__(self) -> str:
        return f"DisambiguationResult(selected_index={self.selected_index}, tokens_used={self.tokens_used})"
