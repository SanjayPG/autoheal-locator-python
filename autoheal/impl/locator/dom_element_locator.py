"""
DOM-based element locator implementation.

This module provides the DOMElementLocator class that uses AI to analyze
the page's DOM structure and locate elements based on natural language descriptions.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from selenium.webdriver.remote.webelement import WebElement

from autoheal.core.element_locator import ElementLocator
from autoheal.core.ai_service import AIService
from autoheal.models.locator_request import LocatorRequest
from autoheal.models.locator_result import LocatorResult
from autoheal.models.enums import LocatorStrategy
from autoheal.metrics.locator_metrics import LocatorMetrics
from autoheal.utils import locator_type_detector
from autoheal.exception.exceptions import ElementNotFoundException

logger = logging.getLogger(__name__)


class DOMElementLocator(ElementLocator):
    """
    DOM-based element locator using AI to analyze page structure.

    This locator retrieves the page's HTML source and uses AI to analyze
    it and suggest the best selector for the target element. It validates
    the AI's suggestion and uses disambiguation when multiple elements match.

    Attributes:
        ai_service: AI service for DOM analysis and element disambiguation.
        metrics: Metrics tracker for performance monitoring.

    Examples:
        >>> from autoheal.impl.ai import MockAIService
        >>> from autoheal.config.ai_config import AIConfig
        >>>
        >>> ai_config = AIConfig.builder().build()
        >>> ai_service = MockAIService(ai_config)
        >>> locator = DOMElementLocator(ai_service)
        >>>
        >>> request = LocatorRequest.builder() \\
        ...     .original_selector("#old-id") \\
        ...     .description("Submit button") \\
        ...     .adapter(adapter) \\
        ...     .build()
        >>>
        >>> result = await locator.locate(request)
        >>> print(f"Found element using: {result.actual_selector}")
    """

    def __init__(self, ai_service: AIService):
        """
        Initialize the DOM element locator.

        Args:
            ai_service: AI service for DOM analysis.
        """
        self.ai_service = ai_service
        self.metrics = LocatorMetrics()
        logger.info("DOMElementLocator initialized")

    async def locate(self, request: LocatorRequest) -> LocatorResult:
        """
        Locate an element using DOM analysis with AI.

        This method:
        1. Retrieves the page source (HTML)
        2. Sends it to AI for analysis
        3. Validates the AI's suggested selector
        4. Uses disambiguation if multiple elements are found
        5. Returns the located element with metadata

        Args:
            request: The locator request with selector, description, and adapter.

        Returns:
            LocatorResult with the found element and metadata.

        Raises:
            ElementNotFoundException: If no element can be found.
            Exception: For other analysis failures.
        """
        start_time = datetime.now()
        logger.debug("Starting DOM analysis for selector: %s", request.original_selector)

        try:
            # Step 1: Get page source
            html = await request.adapter.get_page_source()

            # Truncate large HTML to avoid exceeding AI token limits
            MAX_HTML_SIZE = 50_000
            if len(html) > MAX_HTML_SIZE:
                logger.warning(
                    "HTML truncated from %d to %d chars for AI analysis",
                    len(html), MAX_HTML_SIZE
                )
                html = html[:MAX_HTML_SIZE]

            logger.debug(
                "Retrieved page source (length: %d chars), analyzing with AI",
                len(html)
            )

            # Step 2: Analyze with AI
            ai_result = await self.ai_service.analyze_dom(
                html=html,
                description=request.description,
                previous_selector=request.original_selector,
                framework=request.adapter.get_framework_type()
            )

            logger.debug(
                "AI analysis completed, recommended selector: %s (confidence: %.2f)",
                ai_result.recommended_selector,
                ai_result.confidence
            )

            # Step 3: Validate and return result
            result = await self._validate_and_return_result(
                request,
                ai_result,
                start_time
            )

            # Record success metrics
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.metrics.record_request(
                success=True,
                latency_ms=execution_time_ms,
                from_cache=False
            )

            logger.info(
                "DOM locator successfully found element using selector: %s",
                result.actual_selector
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
                "DOM analysis failed for selector '%s': %s",
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
            True if strategy is DOM_ANALYSIS, False otherwise.
        """
        return strategy == LocatorStrategy.DOM_ANALYSIS

    def get_metrics(self) -> LocatorMetrics:
        """
        Get performance metrics for this locator.

        Returns:
            Current metrics snapshot.
        """
        return self.metrics

    # Private helper methods

    async def _validate_and_return_result(
        self,
        request: LocatorRequest,
        ai_result,
        start_time: datetime
    ) -> LocatorResult:
        """
        Validate AI-suggested selector and build result.

        Args:
            request: Original locator request.
            ai_result: AI analysis result with suggested selector.
            start_time: Request start time for duration calculation.

        Returns:
            LocatorResult with found element.

        Raises:
            ElementNotFoundException: If selector finds no elements.
        """
        # Handle Playwright locator responses
        if ai_result.playwright_locator is not None:
            return await self._validate_playwright_result(request, ai_result, start_time)

        # Handle Selenium/CSS selector responses
        if not ai_result.recommended_selector:
            raise ElementNotFoundException(
                "AI analysis returned no selector or locator"
            )

        # Auto-detect the selector type and create By tuple
        by_tuple = locator_type_detector.auto_create_by(ai_result.recommended_selector)

        # Find elements using the adapter
        elements = await request.adapter.find_elements(by_tuple)

        if not elements:
            logger.warning(
                "AI suggested selector found no elements: %s",
                ai_result.recommended_selector
            )
            raise ElementNotFoundException(
                f"AI suggested selector found no elements: {ai_result.recommended_selector}"
            )

        logger.debug("Validated AI suggestion: found %d elements", len(elements))

        # Disambiguate if multiple elements found
        if len(elements) > 1:
            logger.debug("Multiple elements found, using AI for disambiguation")
            selected_element = await self.ai_service.select_best_matching_element(
                elements,
                request.description
            )
        else:
            selected_element = elements[0]

        # Calculate execution time
        execution_time = datetime.now() - start_time

        # Build and return result
        result = LocatorResult.builder() \
            .element(selected_element) \
            .actual_selector(ai_result.recommended_selector) \
            .strategy(LocatorStrategy.DOM_ANALYSIS) \
            .execution_time(execution_time) \
            .from_cache(False) \
            .confidence(ai_result.confidence) \
            .reasoning(ai_result.reasoning) \
            .tokens_used(ai_result.tokens_used) \
            .build()

        return result

    async def _validate_playwright_result(
        self,
        request: LocatorRequest,
        ai_result,
        start_time: datetime
    ) -> LocatorResult:
        """
        Validate Playwright locator and build result.

        Args:
            request: Original locator request.
            ai_result: AI analysis result with Playwright locator.
            start_time: Request start time for duration calculation.

        Returns:
            LocatorResult with found element.

        Raises:
            ElementNotFoundException: If locator finds no elements.
        """
        from autoheal.models.playwright_locator import PlaywrightLocatorType

        playwright_locator = ai_result.playwright_locator

        # Get selector string representation for logging and result
        selector_str = playwright_locator.to_selector_string()

        logger.debug(
            "Validating Playwright locator: %s",
            selector_str
        )

        try:
            # Check if adapter supports Playwright locator execution
            if hasattr(request.adapter, 'execute_playwright_locator'):
                # Execute Playwright locator
                locator = await request.adapter.execute_playwright_locator(playwright_locator)
                count = await request.adapter.count_elements(locator)

                if count == 0:
                    logger.warning(
                        "Playwright locator found no elements: %s",
                        selector_str
                    )
                    raise ElementNotFoundException(
                        f"Playwright locator found no elements: {selector_str}"
                    )

                if count > 1:
                    logger.warning(
                        "Playwright locator is ambiguous (found %d elements): %s",
                        count, selector_str
                    )
                    raise ElementNotFoundException(
                        f"Playwright locator is ambiguous (found {count} elements): {selector_str}"
                    )

                logger.debug("Validated Playwright locator: found 1 element")

                # For Playwright, we return the locator itself as the "element"
                # Playwright locators are lazy and don't resolve until action
                selected_element = locator

            else:
                # Fallback: For CSS/XPath types, use the value directly
                if playwright_locator.type in (PlaywrightLocatorType.CSS_SELECTOR, PlaywrightLocatorType.XPATH):
                    css_selector = playwright_locator.value
                else:
                    raise ElementNotFoundException(
                        f"Adapter does not support Playwright locators and cannot convert: {selector_str}"
                    )

                by_tuple = locator_type_detector.auto_create_by(css_selector)
                elements = await request.adapter.find_elements(by_tuple)

                if not elements:
                    raise ElementNotFoundException(
                        f"Playwright locator (as CSS) found no elements: {css_selector}"
                    )

                selected_element = elements[0]
                selector_str = css_selector

        except ElementNotFoundException:
            raise
        except Exception as e:
            logger.error("Failed to validate Playwright locator: %s", str(e))
            raise ElementNotFoundException(
                f"Failed to validate Playwright locator: {e}"
            )

        # Calculate execution time
        execution_time = datetime.now() - start_time

        # Build and return result
        result = LocatorResult.builder() \
            .element(selected_element) \
            .actual_selector(selector_str) \
            .strategy(LocatorStrategy.DOM_ANALYSIS) \
            .execution_time(execution_time) \
            .from_cache(False) \
            .confidence(ai_result.confidence) \
            .reasoning(ai_result.reasoning) \
            .tokens_used(ai_result.tokens_used) \
            .build()

        return result
