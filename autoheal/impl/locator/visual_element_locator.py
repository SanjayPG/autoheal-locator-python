"""
Visual element locator implementation using AI-powered screenshot analysis.

This module provides the VisualElementLocator class that uses AI vision models
to analyze screenshots and locate elements based on visual characteristics.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from selenium.webdriver.remote.webelement import WebElement

from autoheal.core.element_locator import ElementLocator
from autoheal.core.ai_service import AIService
from autoheal.models.locator_request import LocatorRequest
from autoheal.models.locator_result import LocatorResult
from autoheal.models.enums import LocatorStrategy
from autoheal.models.element_candidate import ElementCandidate
from autoheal.metrics.locator_metrics import LocatorMetrics
from autoheal.utils import locator_type_detector
from autoheal.exception.exceptions import ElementNotFoundException

logger = logging.getLogger(__name__)


class VisualElementLocator(ElementLocator):
    """
    Visual element locator using AI-powered screenshot analysis.

    This locator captures a screenshot of the page and uses AI vision models
    to analyze it and suggest the best selector for the target element. It
    validates the AI's suggestion and falls back to alternative selectors if needed.

    Attributes:
        ai_service: AI service for visual analysis.
        metrics: Metrics tracker for performance monitoring.

    Examples:
        >>> from autoheal.impl.ai import ResilientAIService
        >>> from autoheal.config.ai_config import AIConfig
        >>> from autoheal.models.enums import AIProvider
        >>>
        >>> ai_config = AIConfig.builder() \\
        ...     .provider(AIProvider.OPENAI) \\
        ...     .api_key("sk-...") \\
        ...     .build()
        >>> ai_service = ResilientAIService(ai_config)
        >>> locator = VisualElementLocator(ai_service)
        >>>
        >>> request = LocatorRequest.builder() \\
        ...     .original_selector("#old-id") \\
        ...     .description("Submit button") \\
        ...     .adapter(adapter) \\
        ...     .enable_visual_analysis(True) \\
        ...     .build()
        >>>
        >>> result = await locator.locate(request)
        >>> print(f"Found element using: {result.actual_selector}")
    """

    def __init__(self, ai_service: AIService):
        """
        Initialize the visual element locator.

        Args:
            ai_service: AI service for visual analysis.
        """
        self.ai_service = ai_service
        self.metrics = LocatorMetrics()
        logger.info("VisualElementLocator initialized")

    async def locate(self, request: LocatorRequest) -> LocatorResult:
        """
        Locate an element using visual analysis with AI.

        This method:
        1. Checks if visual analysis is enabled
        2. Takes a screenshot of the page
        3. Sends it to AI for visual analysis
        4. Validates the AI's suggested selector
        5. Falls back to alternatives if primary fails
        6. Uses heuristics to select best element from multiple matches

        Args:
            request: The locator request with selector, description, and options.

        Returns:
            LocatorResult with the found element and metadata.

        Raises:
            UnsupportedOperationException: If visual analysis is disabled.
            ElementNotFoundException: If no element can be found.
            Exception: For other analysis failures.
        """
        # Check if visual analysis is enabled
        if not request.options.enable_visual_analysis:
            raise Exception("Visual analysis is disabled for this request")

        start_time = datetime.now()
        logger.debug("Starting visual analysis for selector: %s", request.original_selector)

        try:
            # Step 1: Take screenshot and analyze
            ai_result = await self._take_screenshot_and_analyze(request, start_time)

            # Step 2: Validate and return result
            result = await self._validate_and_return_result(
                ai_result,
                request,
                start_time
            )

            # Record success metrics
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.metrics.record_request(
                success=True,
                latency_ms=execution_time_ms,
                from_cache=False
            )

            return result

        except Exception as e:
            # Record failure metrics
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.metrics.record_request(
                success=False,
                latency_ms=execution_time_ms,
                from_cache=False
            )

            logger.error(
                "Visual analysis failed for selector '%s': %s",
                request.original_selector,
                str(e)
            )
            raise

    def supports(self, strategy: LocatorStrategy) -> bool:
        """
        Check if this locator supports the given strategy.

        Args:
            strategy: The locator strategy to check.

        Returns:
            True if strategy is VISUAL_ANALYSIS, False otherwise.
        """
        return strategy == LocatorStrategy.VISUAL_ANALYSIS

    def get_metrics(self) -> LocatorMetrics:
        """
        Get performance metrics for this locator.

        Returns:
            Current metrics snapshot.
        """
        return self.metrics

    def can_handle(self, request: LocatorRequest) -> bool:
        """
        Check if this locator can handle the given request.

        Args:
            request: The locator request to check.

        Returns:
            True if visual analysis is enabled and AI service is healthy.
        """
        return (
            request.options.enable_visual_analysis and
            self.ai_service.is_healthy()
        )

    # Private helper methods

    async def _take_screenshot_and_analyze(
        self,
        request: LocatorRequest,
        start_time: datetime
    ):
        """
        Take screenshot and analyze with AI.

        Args:
            request: Locator request.
            start_time: Request start time.

        Returns:
            AI analysis result with suggested selector.

        Raises:
            Exception: If screenshot or analysis fails.
        """
        try:
            # Take screenshot
            screenshot = await request.adapter.take_screenshot()
            logger.debug("Screenshot taken (size: %d bytes), analyzing with AI", len(screenshot))

            # Analyze with AI
            ai_result = await self.ai_service.analyze_visual(
                screenshot=screenshot,
                description=request.description
            )

            logger.debug(
                "Visual analysis completed with confidence: %.2f",
                ai_result.confidence
            )

            return ai_result

        except Exception as e:
            logger.error("Failed to take screenshot or analyze visually: %s", str(e))
            raise

    async def _validate_and_return_result(
        self,
        ai_result,
        request: LocatorRequest,
        start_time: datetime
    ) -> LocatorResult:
        """
        Validate AI-suggested selector and build result.

        Args:
            ai_result: AI analysis result with suggested selector.
            request: Original locator request.
            start_time: Request start time for duration calculation.

        Returns:
            LocatorResult with found element.

        Raises:
            ElementNotFoundException: If no selector works.
        """
        recommended_selector = ai_result.recommended_selector

        logger.debug(
            "Trying primary selector from enhanced visual analysis: %s",
            recommended_selector
        )

        # Try the AI-recommended primary selector
        by_tuple = locator_type_detector.auto_create_by(recommended_selector)
        elements = await request.adapter.find_elements(by_tuple)

        if elements:
            element = self._select_best_element(elements, request)

            logger.debug(
                "Primary visual selector succeeded: %s (confidence: %.2f)",
                recommended_selector,
                ai_result.confidence
            )

            execution_time = datetime.now() - start_time

            return LocatorResult.builder() \
                .element(element) \
                .actual_selector(recommended_selector) \
                .strategy(LocatorStrategy.VISUAL_ANALYSIS) \
                .execution_time(execution_time) \
                .from_cache(False) \
                .confidence(ai_result.confidence) \
                .reasoning(f"Enhanced Visual AI analysis (primary): {ai_result.reasoning}") \
                .build()
        else:
            # Try robust alternative selectors if primary failed
            logger.debug(
                "Primary visual selector failed, trying %d alternatives",
                len(ai_result.alternatives)
            )
            return await self._try_robust_alternative_selectors(
                ai_result,
                request,
                start_time
            )

    async def _try_robust_alternative_selectors(
        self,
        ai_result,
        request: LocatorRequest,
        start_time: datetime
    ) -> LocatorResult:
        """
        Try alternative selectors if primary fails.

        Args:
            ai_result: AI analysis result with alternatives.
            request: Original locator request.
            start_time: Request start time.

        Returns:
            LocatorResult if any alternative succeeds.

        Raises:
            ElementNotFoundException: If all selectors fail.
        """
        alternatives = ai_result.alternatives

        # Sort alternatives by confidence (highest first)
        alternatives_sorted = sorted(
            alternatives,
            key=lambda x: x.confidence,
            reverse=True
        )

        attempted_selectors = [ai_result.recommended_selector]

        for i, candidate in enumerate(alternatives_sorted):
            alt_selector = candidate.selector

            try:
                logger.debug(
                    "Trying robust alternative %d of %d: %s (confidence: %.2f)",
                    i + 1,
                    len(alternatives_sorted),
                    alt_selector,
                    candidate.confidence
                )

                by_tuple = locator_type_detector.auto_create_by(alt_selector)
                elements = await request.adapter.find_elements(by_tuple)

                if elements:
                    element = self._select_best_element(elements, request)

                    # Determine the type of alternative for better reasoning
                    alternative_type = "alternative"
                    if "text-based" in candidate.description.lower():
                        alternative_type = "text-based"
                    elif "attribute-based" in candidate.description.lower():
                        alternative_type = "attribute-based"

                    logger.debug(
                        "Robust %s selector succeeded: %s (confidence: %.2f)",
                        alternative_type,
                        alt_selector,
                        candidate.confidence
                    )

                    execution_time = datetime.now() - start_time

                    return LocatorResult.builder() \
                        .element(element) \
                        .actual_selector(alt_selector) \
                        .strategy(LocatorStrategy.VISUAL_ANALYSIS) \
                        .execution_time(execution_time) \
                        .from_cache(False) \
                        .confidence(candidate.confidence) \
                        .reasoning(
                            f"Enhanced Visual AI analysis ({alternative_type} fallback): "
                            f"{ai_result.reasoning}"
                        ) \
                        .build()

                attempted_selectors.append(alt_selector)

            except Exception as e:
                logger.debug("Robust alternative selector failed: %s - %s", alt_selector, str(e))
                attempted_selectors.append(alt_selector)

        # All robust selectors failed
        logger.warning(
            "All enhanced visual analysis selectors failed. Primary: %s, Alternatives: %s",
            ai_result.recommended_selector,
            attempted_selectors[1:]
        )

        raise ElementNotFoundException(
            f"Enhanced visual analysis found {len(attempted_selectors)} robust selectors "
            f"but none worked. Primary: {ai_result.recommended_selector}, "
            f"Alternatives: {attempted_selectors[1:]}. "
            f"This suggests the page structure may have changed significantly."
        )

    def _select_best_element(
        self,
        elements: List["WebElement"],
        request: LocatorRequest
    ) -> "WebElement":
        """
        Select the best element from multiple matches using heuristics.

        Heuristics:
        1. Prefer visible elements
        2. Prefer elements with text matching description
        3. Fallback to first element

        Args:
            elements: List of candidate elements.
            request: Original locator request.

        Returns:
            Best matching element.
        """
        if len(elements) == 1:
            return elements[0]

        # First, try to find visible elements
        visible_elements = []
        for element in elements:
            try:
                if element.is_displayed():
                    visible_elements.append(element)
            except Exception:
                # Ignore elements that can't be checked
                pass

        if visible_elements:
            elements = visible_elements

        # If we still have multiple elements, try to match by text content
        description_lower = request.description.lower()
        for element in elements:
            try:
                text = element.text.lower()
                if text and (description_lower in text or text in description_lower):
                    logger.debug("Selected element based on text match: '%s'", element.text)
                    return element
            except Exception:
                # Ignore and continue
                pass

        # Fallback: return the first element
        logger.debug("Multiple elements found, returning first one")
        return elements[0]
