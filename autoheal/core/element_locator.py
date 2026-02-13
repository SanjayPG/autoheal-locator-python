"""
ElementLocator interface for finding web elements.

This module defines the abstract interface for element location strategies
used by the AutoHeal framework.
"""

from abc import ABC, abstractmethod

from autoheal.models.enums import LocatorStrategy


class ElementLocator(ABC):
    """
    Enterprise-grade element locator with async processing, circuit breaker,
    multiple strategies, and advanced caching.

    This interface defines the contract for element location implementations
    that can use different strategies (DOM analysis, visual analysis, hybrid, etc.)
    to locate web elements.
    """

    @abstractmethod
    async def locate(self, request: "LocatorRequest") -> "LocatorResult":
        """
        Locate an element asynchronously using the configured strategy.

        Args:
            request: The locator request containing selector, description, and options

        Returns:
            LocatorResult containing the found element(s) and metadata

        Raises:
            ElementNotFoundException: If the element cannot be found
            AutoHealException: For other locator failures
        """
        pass

    @abstractmethod
    def supports(self, strategy: LocatorStrategy) -> bool:
        """
        Check if this locator supports the given strategy.

        Args:
            strategy: The locator strategy to check

        Returns:
            True if supported, False otherwise
        """
        pass

    @abstractmethod
    def get_metrics(self) -> "LocatorMetrics":
        """
        Get performance and usage metrics for this locator.

        Returns:
            Current metrics snapshot including success rates, latencies, and costs
        """
        pass


# Import at end to avoid circular dependencies
from autoheal.models.locator_request import LocatorRequest  # noqa: E402
from autoheal.models.locator_result import LocatorResult  # noqa: E402
from autoheal.metrics.locator_metrics import LocatorMetrics  # noqa: E402
