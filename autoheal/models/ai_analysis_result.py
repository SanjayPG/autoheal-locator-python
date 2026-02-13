"""
AI Analysis Result model.

This module provides the AIAnalysisResult class for representing the
result of AI analysis containing recommended selectors and confidence scores.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from autoheal.models.element_candidate import ElementCandidate
from autoheal.models.enums import AutomationFramework
from autoheal.models.playwright_locator import PlaywrightLocator


class AIAnalysisResult(BaseModel):
    """
    Result of AI analysis containing recommended selectors and confidence scores.

    Supports both Selenium (CSS/XPath strings) and Playwright (user-facing locators).

    Attributes:
        recommended_selector: Recommended CSS/XPath selector (for Selenium).
        playwright_locator: Recommended Playwright locator (for Playwright).
        target_framework: Target automation framework.
        confidence: Confidence score (0.0-1.0) for the recommendation.
        reasoning: AI reasoning for the recommendation.
        alternatives: List of alternative element candidates.
        metadata: Additional metadata as key-value pairs.

    Examples:
        >>> # Selenium result
        >>> result = (AIAnalysisResult.builder()
        ...     .recommended_selector("#submit-button")
        ...     .target_framework(AutomationFramework.SELENIUM)
        ...     .confidence(0.95)
        ...     .reasoning("ID is stable and unique")
        ...     .build())

        >>> # Playwright result
        >>> pw_locator = PlaywrightLocator.builder().by_role("button", "Submit").build()
        >>> result = (AIAnalysisResult.builder()
        ...     .playwright_locator(pw_locator)
        ...     .target_framework(AutomationFramework.PLAYWRIGHT)
        ...     .confidence(0.98)
        ...     .reasoning("Using semantic locator for better resilience")
        ...     .build())
    """

    recommended_selector: Optional[str] = None
    playwright_locator: Optional[PlaywrightLocator] = None
    target_framework: AutomationFramework = Field(default=AutomationFramework.SELENIUM)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    alternatives: List[ElementCandidate] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tokens_used: int = Field(default=0, description="Total tokens used in AI API call")

    model_config = ConfigDict(use_enum_values=False, validate_assignment=True)

    def is_playwright(self) -> bool:
        """
        Check if this result is for Playwright framework.

        Returns:
            True if target_framework is PLAYWRIGHT.

        Examples:
            >>> result = AIAnalysisResult(target_framework=AutomationFramework.PLAYWRIGHT)
            >>> assert result.is_playwright() == True
        """
        return self.target_framework == AutomationFramework.PLAYWRIGHT

    def is_selenium(self) -> bool:
        """
        Check if this result is for Selenium framework.

        Returns:
            True if target_framework is SELENIUM.

        Examples:
            >>> result = AIAnalysisResult(target_framework=AutomationFramework.SELENIUM)
            >>> assert result.is_selenium() == True
        """
        return self.target_framework == AutomationFramework.SELENIUM

    @classmethod
    def builder(cls) -> "AIAnalysisResultBuilder":
        """
        Create a builder for fluent API construction.

        Returns:
            AIAnalysisResultBuilder instance for method chaining.

        Examples:
            >>> result = (AIAnalysisResult.builder()
            ...     .recommended_selector("button.submit")
            ...     .confidence(0.92)
            ...     .reasoning("Class-based selector is stable")
            ...     .build())
        """
        return AIAnalysisResultBuilder()


class AIAnalysisResultBuilder:
    """
    Builder class for fluent AIAnalysisResult construction.

    Provides a chainable API for building AIAnalysisResult instances.

    Examples:
        >>> result = (AIAnalysisResult.builder()
        ...     .recommended_selector("#login-btn")
        ...     .target_framework(AutomationFramework.SELENIUM)
        ...     .confidence(0.95)
        ...     .reasoning("Stable ID attribute")
        ...     .alternatives([candidate1, candidate2])
        ...     .metadata({"source": "dom_analysis", "tokens_used": 450})
        ...     .build())
    """

    def __init__(self):
        """Initialize builder with default values."""
        self._recommended_selector: Optional[str] = None
        self._playwright_locator: Optional[PlaywrightLocator] = None
        self._target_framework = AutomationFramework.SELENIUM
        self._confidence = 0.0
        self._reasoning: Optional[str] = None
        self._alternatives: List[ElementCandidate] = []
        self._metadata: Dict[str, Any] = {}
        self._tokens_used: int = 0

    def recommended_selector(self, selector: str) -> "AIAnalysisResultBuilder":
        """Set the recommended selector."""
        self._recommended_selector = selector
        return self

    def playwright_locator(self, locator: PlaywrightLocator) -> "AIAnalysisResultBuilder":
        """Set the Playwright locator."""
        self._playwright_locator = locator
        return self

    def target_framework(self, framework: AutomationFramework) -> "AIAnalysisResultBuilder":
        """Set the target framework."""
        self._target_framework = framework
        return self

    def confidence(self, confidence: float) -> "AIAnalysisResultBuilder":
        """Set the confidence score."""
        self._confidence = confidence
        return self

    def reasoning(self, reasoning: str) -> "AIAnalysisResultBuilder":
        """Set the reasoning."""
        self._reasoning = reasoning
        return self

    def alternatives(self, alternatives: List[ElementCandidate]) -> "AIAnalysisResultBuilder":
        """Set the alternatives."""
        self._alternatives = list(alternatives)
        return self

    def metadata(self, metadata: Dict[str, Any]) -> "AIAnalysisResultBuilder":
        """Set the metadata."""
        self._metadata = dict(metadata)
        return self

    def tokens_used(self, tokens: int) -> "AIAnalysisResultBuilder":
        """Set the tokens used."""
        self._tokens_used = tokens
        return self

    def build(self) -> AIAnalysisResult:
        """
        Build and return the AIAnalysisResult instance.

        Returns:
            Configured AIAnalysisResult instance.
        """
        return AIAnalysisResult(
            recommended_selector=self._recommended_selector,
            playwright_locator=self._playwright_locator,
            target_framework=self._target_framework,
            confidence=self._confidence,
            reasoning=self._reasoning,
            alternatives=self._alternatives,
            metadata=self._metadata,
            tokens_used=self._tokens_used,
        )
