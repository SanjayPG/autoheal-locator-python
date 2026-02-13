"""
Mock AI service for testing purposes.

This module provides a simple mock implementation of the AIService interface
for testing and development without making actual API calls.
"""

import asyncio
import logging
from typing import Dict, List, Optional

from autoheal.core.ai_service import AIService
from autoheal.metrics.ai_service_metrics import AIServiceMetrics
from autoheal.models.ai_analysis_result import AIAnalysisResult
from autoheal.models.element_candidate import ElementCandidate
from autoheal.models.enums import AutomationFramework
from autoheal.models.playwright_locator import PlaywrightLocator

logger = logging.getLogger(__name__)


class MockAIService(AIService):
    """
    Mock AI service for testing purposes.

    Provides predefined responses without making actual API calls.
    Useful for unit testing and development.

    Attributes:
        mock_responses: Dictionary mapping descriptions to mock results.
        metrics: Service metrics tracking.

    Examples:
        >>> service = MockAIService()
        >>> service.add_mock_response("Login button", "#login-btn", 0.95)
        >>> result = await service.analyze_dom("<html>...", "Login button", None)
        >>> assert result.recommended_selector == "#login-btn"
    """

    def __init__(self) -> None:
        """Initialize the mock AI service."""
        self._mock_responses: Dict[str, AIAnalysisResult] = {}
        self._metrics = AIServiceMetrics()
        logger.debug("MockAIService initialized")

    def add_mock_response(
        self,
        description: str,
        selector: str,
        confidence: float,
        framework: AutomationFramework = AutomationFramework.SELENIUM
    ) -> None:
        """
        Add a mock response for a specific description.

        Args:
            description: Element description to match.
            selector: Mock selector to return.
            confidence: Confidence score (0.0-1.0).
            framework: Target framework.

        Examples:
            >>> service = MockAIService()
            >>> service.add_mock_response(
            ...     "Submit button",
            ...     "#submit",
            ...     0.90,
            ...     AutomationFramework.SELENIUM
            ... )
        """
        result = AIAnalysisResult.builder() \
            .recommended_selector(selector) \
            .target_framework(framework) \
            .confidence(confidence) \
            .reasoning(f"Mock AI response for: {description}") \
            .build()

        self._mock_responses[description] = result
        logger.debug(
            "Added mock AI response: %s -> %s (confidence: %.2f)",
            description,
            selector,
            confidence
        )

    def add_mock_result(self, description: str, result: AIAnalysisResult) -> None:
        """
        Add a complete mock AIAnalysisResult for a specific description.

        Args:
            description: Element description to match.
            result: Complete AIAnalysisResult to return.
        """
        self._mock_responses[description] = result
        logger.debug("Added mock AI result for input: %s", description)

    async def analyze_dom(
        self,
        html: str,
        description: str,
        previous_selector: Optional[str] = None,
        framework: AutomationFramework = AutomationFramework.SELENIUM,
    ) -> AIAnalysisResult:
        """
        Perform mock DOM analysis.

        Args:
            html: HTML content (ignored in mock).
            description: Element description.
            previous_selector: Previous selector (ignored in mock).
            framework: Target automation framework.

        Returns:
            Mock AIAnalysisResult.
        """
        import time
        start_time = time.time()

        # Simulate processing time
        await asyncio.sleep(0.1)

        # Return mock response if available, otherwise return default
        if description in self._mock_responses:
            result = self._mock_responses[description]
        else:
            # Generate framework-specific default mock response
            if framework == AutomationFramework.PLAYWRIGHT:
                pw_locator = PlaywrightLocator.builder() \
                    .by_test_id("mock-element") \
                    .build()

                result = AIAnalysisResult.builder() \
                    .playwright_locator(pw_locator) \
                    .target_framework(AutomationFramework.PLAYWRIGHT) \
                    .confidence(0.85) \
                    .reasoning(f"Mock Playwright analysis for: {description}") \
                    .alternatives([
                        ElementCandidate(
                            selector="getByRole('button', {'name': 'Mock'})",
                            confidence=0.80,
                            description=f"{description} (role alternative)",
                            element_fingerprint=None,
                            attributes={}
                        )
                    ]) \
                    .build()
            else:
                # Selenium default
                result = AIAnalysisResult.builder() \
                    .recommended_selector("button[data-testid='mock-element']") \
                    .target_framework(AutomationFramework.SELENIUM) \
                    .confidence(0.85) \
                    .reasoning(f"Mock Selenium analysis for: {description}") \
                    .alternatives([
                        ElementCandidate(
                            selector="#mock-button",
                            confidence=0.80,
                            description=f"{description} (ID alternative)",
                            element_fingerprint=None,
                            attributes={}
                        ),
                        ElementCandidate(
                            selector="button.mock-class",
                            confidence=0.75,
                            description=f"{description} (class alternative)",
                            element_fingerprint=None,
                            attributes={}
                        )
                    ]) \
                    .build()

        # Record metrics
        elapsed_ms = int((time.time() - start_time) * 1000)
        self._metrics.record_request(True, elapsed_ms)

        logger.debug(
            "Mock AI analyzed DOM for: %s (framework: %s) -> %s",
            description,
            framework,
            result.recommended_selector or str(result.playwright_locator)
        )

        return result

    async def analyze_visual(
        self,
        screenshot: bytes,
        description: str,
    ) -> AIAnalysisResult:
        """
        Perform mock visual analysis.

        Args:
            screenshot: Screenshot data (ignored in mock).
            description: Element description.

        Returns:
            Mock AIAnalysisResult.
        """
        # Return mock visual analysis result
        result = AIAnalysisResult.builder() \
            .recommended_selector(self._generate_mock_selector_from_description(description)) \
            .confidence(0.75) \
            .reasoning(f"Mock visual analysis for: {description}") \
            .alternatives([
                ElementCandidate(
                    selector="input[type='text']",
                    confidence=0.70,
                    description=f"{description} (text input alternative)",
                    element_fingerprint=None,
                    attributes={}
                )
            ]) \
            .build()

        logger.debug(
            "Mock AI visual analysis for: %s -> %s",
            description,
            result.recommended_selector
        )

        return result

    def is_healthy(self) -> bool:
        """
        Check if the mock service is healthy.

        Returns:
            Always True for mock service.
        """
        return True

    def get_metrics(self) -> AIServiceMetrics:
        """
        Get mock service metrics.

        Returns:
            Current metrics.
        """
        return self._metrics

    async def select_best_matching_element(
        self,
        elements: List,  # List[WebElement] - avoiding import
        description: str
    ):
        """
        Select best matching element from multiple candidates (mock implementation).

        Args:
            elements: List of web elements.
            description: Element description.

        Returns:
            Best matching element (first element with matching text/attributes).

        Raises:
            ValueError: If elements list is empty.
        """
        if not elements:
            raise ValueError("Elements list cannot be empty")

        if len(elements) == 1:
            return elements[0]

        logger.debug(
            "Mock AI disambiguation for %d elements with description: %s",
            len(elements),
            description
        )

        desc_lower = description.lower()

        # Simple mock logic - look for element with matching text
        for element in elements:
            try:
                element_text = element.text
                if element_text and desc_lower in element_text.lower():
                    logger.debug("Mock AI selected element with text: %s", element_text)
                    return element
            except Exception:
                # Continue to next element if there's an issue getting text
                pass

        # Try matching by attributes
        for element in elements:
            try:
                aria_label = element.get_attribute("aria-label")
                elem_id = element.get_attribute("id")
                class_name = element.get_attribute("class")

                if (aria_label and desc_lower in aria_label.lower()) or \
                   (elem_id and desc_lower in elem_id.lower()) or \
                   (class_name and desc_lower in class_name.lower()):
                    logger.debug("Mock AI selected element by attributes")
                    return element
            except Exception:
                # Continue to next element if there's an issue getting attributes
                pass

        # Fallback to first element
        logger.debug("Mock AI falling back to first element")
        return elements[0]

    def _generate_mock_selector_from_description(self, description: str) -> str:
        """
        Generate a mock selector based on element description.

        Args:
            description: Element description.

        Returns:
            Mock CSS selector.
        """
        desc = description.lower()

        if "username" in desc or "user" in desc:
            return "#user-name"
        elif "password" in desc:
            return "#password"
        elif "login" in desc and "button" in desc:
            return "#login-button"
        elif "button" in desc:
            return "button[type='submit']"
        elif "input" in desc or "field" in desc:
            return "input[type='text']"
        else:
            # Generic fallback
            first_word = description.split()[0] if description.split() else "element"
            return f"*[contains(text(), '{first_word}')]"
