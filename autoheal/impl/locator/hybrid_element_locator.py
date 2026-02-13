"""
Hybrid element locator combining multiple locator strategies.

This module provides the HybridElementLocator class that runs multiple
locator strategies in parallel and selects the best result based on confidence.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from selenium.webdriver.remote.webelement import WebElement

from autoheal.core.element_locator import ElementLocator
from autoheal.models.locator_request import LocatorRequest
from autoheal.models.locator_result import LocatorResult
from autoheal.models.enums import LocatorStrategy
from autoheal.metrics.locator_metrics import LocatorMetrics
from autoheal.exception.exceptions import ElementNotFoundException

logger = logging.getLogger(__name__)


class HybridElementLocator(ElementLocator):
    """
    Hybrid element locator that combines multiple locator strategies.

    This locator runs multiple locator strategies in parallel (DOM, Visual, etc.)
    and selects the best result based on confidence scores. This approach
    maximizes the chance of finding the element while also identifying the
    most reliable selector.

    The hybrid approach:
    1. Executes all configured locators simultaneously
    2. Waits for all to complete (successful or failed)
    3. Filters out failed attempts
    4. Selects the result with the highest confidence score
    5. Returns the winner with HYBRID strategy tag

    Attributes:
        locators: List of element locators to use.
        metrics: Metrics tracker for performance monitoring.

    Examples:
        >>> from autoheal.impl.ai import ResilientAIService
        >>> from autoheal.impl.locator import DOMElementLocator, VisualElementLocator
        >>> from autoheal.config.ai_config import AIConfig
        >>> from autoheal.models.enums import AIProvider
        >>>
        >>> ai_config = AIConfig.builder() \\
        ...     .provider(AIProvider.OPENAI) \\
        ...     .api_key("sk-...") \\
        ...     .build()
        >>> ai_service = ResilientAIService(ai_config)
        >>>
        >>> # Create individual locators
        >>> dom_locator = DOMElementLocator(ai_service)
        >>> visual_locator = VisualElementLocator(ai_service)
        >>>
        >>> # Combine them in hybrid locator
        >>> hybrid_locator = HybridElementLocator([dom_locator, visual_locator])
        >>>
        >>> request = LocatorRequest.builder() \\
        ...     .original_selector("#old-id") \\
        ...     .description("Submit button") \\
        ...     .adapter(adapter) \\
        ...     .enable_dom_analysis(True) \\
        ...     .enable_visual_analysis(True) \\
        ...     .build()
        >>>
        >>> result = await hybrid_locator.locate(request)
        >>> print(f"Best result: {result.strategy} with confidence {result.confidence}")
    """

    def __init__(self, locators: List[ElementLocator]):
        """
        Initialize the hybrid element locator.

        Args:
            locators: List of element locators to use in parallel.
        """
        self.locators = list(locators)  # Create a copy
        self.metrics = LocatorMetrics()
        logger.info("HybridElementLocator initialized with %d strategies", len(locators))

    async def locate(self, request: LocatorRequest) -> LocatorResult:
        """
        Locate an element using multiple strategies in parallel.

        This method:
        1. Runs all configured locators simultaneously
        2. Waits for all to complete
        3. Filters successful results
        4. Selects the best result by confidence
        5. Returns with HYBRID strategy

        Args:
            request: The locator request with selector, description, and options.

        Returns:
            LocatorResult with the best found element and metadata.

        Raises:
            ElementNotFoundException: If all locator strategies fail.
        """
        start_time = datetime.now()
        logger.debug(
            "Starting hybrid location strategy for selector: %s",
            request.original_selector
        )

        try:
            # Run all locators in parallel
            results = await self._run_locators_in_parallel(request)

            # Filter successful results
            successful_results = [
                r for r in results
                if r is not None and r.element is not None
            ]

            logger.debug(
                "Hybrid strategy completed: %d successful results out of %d attempts",
                len(successful_results),
                len(self.locators)
            )

            if not successful_results:
                raise ElementNotFoundException(
                    f"All locator strategies failed for selector: {request.original_selector}"
                )

            # Select best result based on confidence
            best_result = max(successful_results, key=lambda r: r.confidence)

            logger.info(
                "Best result selected: strategy=%s, confidence=%.2f, selector=%s",
                best_result.strategy,
                best_result.confidence,
                best_result.actual_selector
            )

            # Update result to reflect hybrid strategy
            execution_time = datetime.now() - start_time
            hybrid_result = LocatorResult.builder() \
                .element(best_result.element) \
                .actual_selector(best_result.actual_selector) \
                .strategy(LocatorStrategy.HYBRID) \
                .execution_time(execution_time) \
                .from_cache(False) \
                .confidence(best_result.confidence) \
                .reasoning(f"Hybrid strategy selected: {best_result.reasoning}") \
                .build()

            # Record success metrics
            execution_time_ms = int(execution_time.total_seconds() * 1000)
            self.metrics.record_request(
                success=True,
                latency_ms=execution_time_ms,
                from_cache=False
            )

            logger.info(
                "Hybrid locator successfully found element in %dms",
                execution_time_ms
            )

            return hybrid_result

        except Exception as e:
            # Record failure metrics
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.metrics.record_request(
                success=False,
                latency_ms=execution_time_ms,
                from_cache=False
            )

            logger.warning(
                "Hybrid locator failed after %dms: %s",
                execution_time_ms,
                str(e)
            )
            raise

    def supports(self, strategy: LocatorStrategy) -> bool:
        """
        Check if this locator supports the given strategy.

        Args:
            strategy: The locator strategy to check.

        Returns:
            True if strategy is HYBRID, False otherwise.
        """
        return strategy == LocatorStrategy.HYBRID

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
            True if at least one underlying locator can handle the request.
        """
        return any(locator.can_handle(request) for locator in self.locators)

    def get_locators(self) -> List[ElementLocator]:
        """
        Get the underlying locators for inspection.

        Returns:
            List of configured locators (copy).
        """
        return list(self.locators)

    # Private helper methods

    async def _run_locators_in_parallel(
        self,
        request: LocatorRequest
    ) -> List[Optional[LocatorResult]]:
        """
        Run all locators in parallel and collect results.

        Args:
            request: Locator request to execute.

        Returns:
            List of results (None for failed locators).
        """
        # Create tasks for all locators
        tasks = []
        for locator in self.locators:
            logger.debug("Starting locator: %s", locator.__class__.__name__)
            task = self._execute_locator_safely(locator, request)
            tasks.append(task)

        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=False)

        return results

    async def _execute_locator_safely(
        self,
        locator: ElementLocator,
        request: LocatorRequest
    ) -> Optional[LocatorResult]:
        """
        Execute a single locator and catch any exceptions.

        Args:
            locator: The locator to execute.
            request: The locator request.

        Returns:
            LocatorResult if successful, None if failed.
        """
        try:
            result = await locator.locate(request)
            logger.debug(
                "Locator %s succeeded with confidence %.2f",
                locator.__class__.__name__,
                result.confidence
            )
            return result
        except Exception as e:
            logger.debug(
                "Locator %s failed: %s",
                locator.__class__.__name__,
                str(e)
            )
            return None
