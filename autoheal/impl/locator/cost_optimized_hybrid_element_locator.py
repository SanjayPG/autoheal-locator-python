"""
Cost-optimized hybrid element locator with configurable execution strategies.

This module provides the CostOptimizedHybridElementLocator class that optimizes
AI API costs by using different execution strategies (sequential, parallel,
smart sequential, DOM-only, visual-first).
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
from autoheal.models.enums import LocatorStrategy, ExecutionStrategy
from autoheal.metrics.locator_metrics import LocatorMetrics
from autoheal.exception.exceptions import ElementNotFoundException

logger = logging.getLogger(__name__)


class CostOptimizedHybridElementLocator(ElementLocator):
    """
    Cost-optimized hybrid element locator with configurable execution strategies.

    This locator provides multiple execution strategies to optimize AI API costs:

    - **SEQUENTIAL**: Try each locator in order, stop at first success
      (Lowest cost - only pays for successful strategy)

    - **PARALLEL**: Run all locators in parallel, select best result
      (Highest cost - pays for all strategies, but fastest)

    - **SMART_SEQUENTIAL**: Try DOM first (cheaper), then Visual if DOM fails
      (Medium cost - optimal balance of cost and reliability)

    - **DOM_ONLY**: Skip visual analysis entirely
      (Lowest cost - DOM analysis only)

    - **VISUAL_FIRST**: Try visual first, then DOM if visual fails
      (High cost - visual analysis is expensive)

    Attributes:
        locators: List of element locators to use.
        execution_strategy: Strategy for executing locators.
        metrics: Metrics tracker for performance monitoring.

    Examples:
        >>> from autoheal.impl.ai import ResilientAIService
        >>> from autoheal.impl.locator import DOMElementLocator, VisualElementLocator
        >>> from autoheal.models.enums import ExecutionStrategy
        >>>
        >>> ai_service = ResilientAIService(ai_config)
        >>> dom_locator = DOMElementLocator(ai_service)
        >>> visual_locator = VisualElementLocator(ai_service)
        >>>
        >>> # Smart sequential: DOM first, then visual if needed
        >>> locator = CostOptimizedHybridElementLocator(
        ...     [dom_locator, visual_locator],
        ...     ExecutionStrategy.SMART_SEQUENTIAL
        ... )
        >>>
        >>> result = await locator.locate(request)
        >>> print(f"Strategy used: {result.reasoning}")
    """

    def __init__(
        self,
        locators: List[ElementLocator],
        execution_strategy: ExecutionStrategy = ExecutionStrategy.SMART_SEQUENTIAL
    ):
        """
        Initialize the cost-optimized hybrid element locator.

        Args:
            locators: List of element locators to use.
            execution_strategy: Strategy for executing locators (default: SMART_SEQUENTIAL).
        """
        self.locators = list(locators)  # Create a copy
        self.execution_strategy = execution_strategy
        self.metrics = LocatorMetrics()
        logger.info(
            "CostOptimizedHybridElementLocator initialized with %d strategies using %s execution",
            len(locators),
            execution_strategy.name
        )

    async def locate(self, request: LocatorRequest) -> LocatorResult:
        """
        Locate an element using the configured execution strategy.

        Args:
            request: The locator request with selector, description, and options.

        Returns:
            LocatorResult with the found element and metadata.

        Raises:
            ElementNotFoundException: If all locator strategies fail.
            Exception: For configuration or execution errors.
        """
        start_time = datetime.now()
        logger.debug(
            "Starting %s location strategy for selector: %s",
            self.execution_strategy.name,
            request.original_selector
        )

        try:
            # Execute based on strategy
            if self.execution_strategy == ExecutionStrategy.SEQUENTIAL:
                result = await self._execute_sequential(request, start_time)
            elif self.execution_strategy == ExecutionStrategy.PARALLEL:
                result = await self._execute_parallel(request, start_time)
            elif self.execution_strategy == ExecutionStrategy.SMART_SEQUENTIAL:
                result = await self._execute_smart_sequential(request, start_time)
            elif self.execution_strategy == ExecutionStrategy.DOM_ONLY:
                result = await self._execute_dom_only(request, start_time)
            elif self.execution_strategy == ExecutionStrategy.VISUAL_FIRST:
                result = await self._execute_visual_first(request, start_time)
            else:
                raise ValueError(f"Unknown execution strategy: {self.execution_strategy}")

            # Record success metrics
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.metrics.record_request(
                success=True,
                latency_ms=execution_time_ms,
                from_cache=False
            )

            logger.info(
                "Cost-optimized locator succeeded in %dms using %s strategy",
                execution_time_ms,
                self.execution_strategy.name
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

            logger.warning(
                "Cost-optimized locator failed after %dms: %s",
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

    def get_execution_strategy(self) -> ExecutionStrategy:
        """
        Get the configured execution strategy.

        Returns:
            The execution strategy.
        """
        return self.execution_strategy

    def get_locators(self) -> List[ElementLocator]:
        """
        Get the underlying locators for inspection.

        Returns:
            List of configured locators (copy).
        """
        return list(self.locators)

    # Private execution strategy methods

    async def _execute_sequential(
        self,
        request: LocatorRequest,
        start_time: datetime
    ) -> LocatorResult:
        """
        Execute locators sequentially, stop at first success.
        Cost: Lowest (only pays for successful strategy).

        Args:
            request: Locator request.
            start_time: Request start time.

        Returns:
            LocatorResult from first successful locator.

        Raises:
            ElementNotFoundException: If all locators fail.
        """
        for i, locator in enumerate(self.locators):
            logger.debug(
                "Trying locator %d of %d: %s",
                i + 1,
                len(self.locators),
                locator.__class__.__name__
            )

            try:
                result = await locator.locate(request)
                if result is not None and result.element is not None:
                    logger.info(
                        "Sequential strategy succeeded with %s: confidence=%.2f",
                        locator.__class__.__name__,
                        result.confidence
                    )
                    return self._build_hybrid_result(result, start_time)
                else:
                    logger.debug(
                        "Locator %s failed, trying next",
                        locator.__class__.__name__
                    )
            except Exception as e:
                logger.debug(
                    "Locator %s failed with exception: %s",
                    locator.__class__.__name__,
                    str(e)
                )

        raise ElementNotFoundException(
            f"All locator strategies failed for selector: {request.original_selector}"
        )

    async def _execute_parallel(
        self,
        request: LocatorRequest,
        start_time: datetime
    ) -> LocatorResult:
        """
        Execute all locators in parallel, select best result.
        Cost: Highest (pays for all strategies).

        Args:
            request: Locator request.
            start_time: Request start time.

        Returns:
            LocatorResult with highest confidence.

        Raises:
            ElementNotFoundException: If all locators fail.
        """
        # Create tasks for all locators
        tasks = []
        for locator in self.locators:
            logger.debug("Starting parallel locator: %s", locator.__class__.__name__)
            task = self._execute_locator_safely(locator, request)
            tasks.append(task)

        # Wait for all to complete, capturing exceptions instead of failing
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results, logging any failures
        successful_results = []
        for r in results:
            if isinstance(r, Exception):
                logger.warning("Parallel locator failed: %s", r)
                continue
            if r is not None and r.element is not None:
                successful_results.append(r)

        if not successful_results:
            raise ElementNotFoundException(
                f"All parallel locator strategies failed for selector: {request.original_selector}"
            )

        # Select best result based on confidence
        best_result = max(successful_results, key=lambda r: r.confidence)

        logger.info(
            "Parallel strategy selected best result: strategy=%s, confidence=%.2f",
            best_result.strategy,
            best_result.confidence
        )

        return self._build_hybrid_result(best_result, start_time)

    async def _execute_smart_sequential(
        self,
        request: LocatorRequest,
        start_time: datetime
    ) -> LocatorResult:
        """
        Smart strategy: Try DOM first (cheaper), then Visual if DOM fails.
        Cost: Medium (DOM is cheaper, Visual only if needed).

        Args:
            request: Locator request.
            start_time: Request start time.

        Returns:
            LocatorResult from DOM or fallback to visual.

        Raises:
            ElementNotFoundException: If all locators fail.
        """
        # Import here to avoid circular dependency
        from autoheal.impl.locator.dom_element_locator import DOMElementLocator

        # Find DOM locator first (cheaper)
        dom_locator = None
        for locator in self.locators:
            if isinstance(locator, DOMElementLocator):
                dom_locator = locator
                break

        if dom_locator is not None:
            logger.debug("Smart strategy: Trying DOM analysis first (cost-effective)")
            try:
                result = await dom_locator.locate(request)
                if result is not None and result.element is not None:
                    logger.info("Smart strategy: DOM analysis succeeded, skipping visual (cost saved!)")
                    return self._build_hybrid_result(result, start_time)
                else:
                    logger.debug("Smart strategy: DOM failed, trying visual analysis")
            except Exception as e:
                logger.debug("Smart strategy: DOM failed with exception, trying visual analysis: %s", str(e))

            # DOM failed, try remaining locators
            return await self._try_remaining_locators(request, start_time, dom_locator)
        else:
            # No DOM locator, fall back to sequential
            logger.debug("Smart strategy: No DOM locator found, falling back to sequential")
            return await self._execute_sequential(request, start_time)

    async def _execute_dom_only(
        self,
        request: LocatorRequest,
        start_time: datetime
    ) -> LocatorResult:
        """
        DOM-only strategy: Skip visual analysis entirely.
        Cost: Lowest (DOM only).

        Args:
            request: Locator request.
            start_time: Request start time.

        Returns:
            LocatorResult from DOM analysis.

        Raises:
            ElementNotFoundException: If DOM analysis fails.
            Exception: If no DOM locator is available.
        """
        # Import here to avoid circular dependency
        from autoheal.impl.locator.dom_element_locator import DOMElementLocator

        # Find DOM locator
        dom_locator = None
        for locator in self.locators:
            if isinstance(locator, DOMElementLocator):
                dom_locator = locator
                break

        if dom_locator is None:
            raise Exception("DOM_ONLY strategy requested but no DOM locator available")

        logger.debug("DOM-only strategy: Using only DOM analysis (maximum cost savings)")

        result = await dom_locator.locate(request)
        if result is not None and result.element is not None:
            logger.info("DOM-only strategy succeeded: confidence=%.2f", result.confidence)
            return self._build_hybrid_result(result, start_time)
        else:
            raise ElementNotFoundException(
                f"DOM-only strategy failed for selector: {request.original_selector}"
            )

    async def _execute_visual_first(
        self,
        request: LocatorRequest,
        start_time: datetime
    ) -> LocatorResult:
        """
        Visual-first strategy: Try visual first, then DOM if visual fails.
        Cost: High (Visual is expensive).

        Args:
            request: Locator request.
            start_time: Request start time.

        Returns:
            LocatorResult from visual or fallback to DOM.

        Raises:
            ElementNotFoundException: If all locators fail.
        """
        # Import here to avoid circular dependency
        from autoheal.impl.locator.visual_element_locator import VisualElementLocator

        # Find visual locator
        visual_locator = None
        for locator in self.locators:
            if isinstance(locator, VisualElementLocator):
                visual_locator = locator
                break

        if visual_locator is not None:
            logger.debug("Visual-first strategy: Trying visual analysis first")
            try:
                result = await visual_locator.locate(request)
                if result is not None and result.element is not None:
                    logger.info("Visual-first strategy: Visual analysis succeeded")
                    return self._build_hybrid_result(result, start_time)
                else:
                    logger.debug("Visual-first strategy: Visual failed, trying DOM analysis")
            except Exception as e:
                logger.debug("Visual-first strategy: Visual failed with exception, trying DOM: %s", str(e))

            # Visual failed, try remaining locators
            return await self._try_remaining_locators(request, start_time, visual_locator)
        else:
            # No visual locator, fall back to sequential
            logger.debug("Visual-first strategy: No visual locator found, falling back to sequential")
            return await self._execute_sequential(request, start_time)

    async def _try_remaining_locators(
        self,
        request: LocatorRequest,
        start_time: datetime,
        exclude_locator: ElementLocator
    ) -> LocatorResult:
        """
        Try remaining locators excluding the specified one.

        Args:
            request: Locator request.
            start_time: Request start time.
            exclude_locator: Locator to exclude from execution.

        Returns:
            LocatorResult from remaining locators.

        Raises:
            ElementNotFoundException: If all remaining locators fail.
        """
        remaining_locators = [
            loc for loc in self.locators
            if loc is not exclude_locator
        ]

        if not remaining_locators:
            raise ElementNotFoundException(
                f"No remaining locators to try for selector: {request.original_selector}"
            )

        # Create a new instance with remaining locators and sequential strategy
        temp_locator = CostOptimizedHybridElementLocator(
            remaining_locators,
            ExecutionStrategy.SEQUENTIAL
        )
        return await temp_locator.locate(request)

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
                result.confidence if result else 0.0
            )
            return result
        except Exception as e:
            logger.debug(
                "Locator %s failed: %s",
                locator.__class__.__name__,
                str(e)
            )
            return None

    def _build_hybrid_result(
        self,
        original_result: LocatorResult,
        start_time: datetime
    ) -> LocatorResult:
        """
        Build a hybrid result from an original result.

        Args:
            original_result: The original locator result.
            start_time: Request start time.

        Returns:
            LocatorResult with HYBRID strategy and updated metadata.
        """
        execution_time = datetime.now() - start_time

        return LocatorResult.builder() \
            .element(original_result.element) \
            .actual_selector(original_result.actual_selector) \
            .strategy(LocatorStrategy.HYBRID) \
            .execution_time(execution_time) \
            .from_cache(False) \
            .confidence(original_result.confidence) \
            .reasoning(
                f"Cost-optimized {self.execution_strategy.name} strategy: "
                f"{original_result.reasoning}"
            ) \
            .tokens_used(original_result.tokens_used) \
            .build()
