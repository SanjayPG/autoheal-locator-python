"""
AIService interface for AI-powered element analysis.

This module defines the abstract interface for AI services that analyze
web pages to locate elements using natural language descriptions.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import sys

# Type imports for documentation
if sys.version_info >= (3, 11):
    from typing import TYPE_CHECKING
else:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from selenium.webdriver.remote.webelement import WebElement

from autoheal.models.enums import AutomationFramework


class AIService(ABC):
    """
    Interface for AI-powered element analysis services.

    This interface defines methods for analyzing web pages using AI to locate
    elements based on natural language descriptions. Supports both DOM-based
    (text) and visual (screenshot) analysis.
    """

    @abstractmethod
    async def analyze_dom(
        self,
        html: str,
        description: str,
        previous_selector: Optional[str] = None,
        framework: AutomationFramework = AutomationFramework.SELENIUM,
    ) -> "AIAnalysisResult":
        """
        Analyze DOM structure to find element selectors with framework awareness.

        Args:
            html: The HTML content to analyze
            description: Human-readable description of the target element
            previous_selector: The selector that previously worked but now fails
            framework: The automation framework (SELENIUM or PLAYWRIGHT)

        Returns:
            AIAnalysisResult containing suggested selectors and confidence scores

        Raises:
            AIServiceException: If the AI service fails or is unavailable
        """
        pass

    @abstractmethod
    async def analyze_visual(
        self,
        screenshot: bytes,
        description: str,
    ) -> "AIAnalysisResult":
        """
        Analyze visual screenshot to find element locations.

        Args:
            screenshot: The screenshot data as bytes
            description: Human-readable description of the target element

        Returns:
            AIAnalysisResult containing suggested selectors and confidence scores

        Raises:
            AIServiceException: If the AI service fails or is unavailable
        """
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """
        Check if the AI service is healthy and responsive.

        Returns:
            True if service is healthy, False otherwise
        """
        pass

    @abstractmethod
    def get_metrics(self) -> "AIServiceMetrics":
        """
        Get performance metrics for the AI service.

        Returns:
            Current AI service metrics including request counts, latencies, and costs
        """
        pass

    @abstractmethod
    async def select_best_matching_element(
        self,
        elements: List["WebElement"],
        description: str,
    ) -> Optional["WebElement"]:
        """
        Select the best matching element from a list based on description.

        When multiple elements match a selector, this method uses AI to determine
        which element best matches the provided description.

        Args:
            elements: List of candidate WebElements
            description: Human-readable description of the target element

        Returns:
            The best matching WebElement, or None if no good match is found

        Raises:
            AIServiceException: If the AI service fails or is unavailable
        """
        pass


# Import at end to avoid circular dependencies
from autoheal.models.ai_analysis_result import AIAnalysisResult  # noqa: E402
from autoheal.metrics.ai_service_metrics import AIServiceMetrics  # noqa: E402
