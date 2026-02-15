"""
ReportingAutoHealLocator - AutoHealLocator wrapper that automatically reports all selector usage.

This module provides a wrapper around AutoHealLocator that tracks and reports all
selector usage with detailed metrics and strategy information.
"""

import os
import time
from typing import Any, List, Optional

from selenium.webdriver.remote.webelement import WebElement

from autoheal.autoheal_locator import AutoHealLocator
from autoheal.config.autoheal_config import AutoHealConfiguration
from autoheal.core.web_automation_adapter import WebAutomationAdapter
from autoheal.models.enums import LocatorStrategy
from autoheal.reporting.autoheal_reporter import (
    AutoHealReporter,
    SelectorStrategy
)
from autoheal.utils.playwright_locator_converter import PlaywrightLocatorConverter

# Map real LocatorStrategy to report SelectorStrategy
_STRATEGY_MAP = {
    LocatorStrategy.ORIGINAL_SELECTOR: SelectorStrategy.ORIGINAL_SELECTOR,
    LocatorStrategy.DOM_ANALYSIS: SelectorStrategy.DOM_ANALYSIS,
    LocatorStrategy.VISUAL_ANALYSIS: SelectorStrategy.VISUAL_ANALYSIS,
    LocatorStrategy.AI_DISAMBIGUATION: SelectorStrategy.AI_DISAMBIGUATION,
    LocatorStrategy.CACHED: SelectorStrategy.CACHED,
    LocatorStrategy.HYBRID: SelectorStrategy.DOM_ANALYSIS,
}

# Estimated token usage per strategy (same approach as Java implementation)
_ESTIMATED_TOKENS = {
    SelectorStrategy.DOM_ANALYSIS: 1500,
    SelectorStrategy.VISUAL_ANALYSIS: 45000,
    SelectorStrategy.AI_DISAMBIGUATION: 500,  # Disambiguation uses fewer tokens
    SelectorStrategy.ORIGINAL_SELECTOR: 0,
    SelectorStrategy.CACHED: 0,
    SelectorStrategy.FAILED: 0,
}


class ReportingAutoHealLocator:
    """
    AutoHealLocator wrapper that automatically reports all selector usage.

    This class wraps an AutoHealLocator instance and tracks all selector operations,
    recording performance metrics, healing strategies, and generating comprehensive
    reports.

    Attributes:
        autoheal: The underlying AutoHealLocator instance.
        reporter: The AutoHealReporter for tracking and reporting.

    Examples:
        >>> from autoheal.impl.adapter.selenium_adapter import SeleniumAdapter
        >>> from autoheal.config.autoheal_config import AutoHealConfiguration
        >>>
        >>> # Create configuration
        >>> config = AutoHealConfiguration()
        >>>
        >>> # Create adapter (Selenium or Playwright)
        >>> adapter = SeleniumAdapter(driver)
        >>>
        >>> # Create reporting locator
        >>> locator = ReportingAutoHealLocator(adapter, config)
        >>>
        >>> # Use it to find elements - all usage is tracked
        >>> element = locator.find_element("#login-button", "Login button")
        >>>
        >>> # Generate reports at the end
        >>> locator.generate_reports()
        >>>
        >>> # Or generate specific report formats
        >>> locator.generate_html_report()
        >>> locator.generate_json_report()
        >>>
        >>> # Shutdown with reports
        >>> locator.shutdown()
    """

    def __init__(
        self,
        adapter: WebAutomationAdapter,
        config: AutoHealConfiguration
    ):
        """
        Initialize the ReportingAutoHealLocator.

        Args:
            adapter: The web automation adapter (Selenium or Playwright).
            config: The AutoHeal configuration.
        """
        # Create the underlying AutoHeal instance
        self.autoheal = AutoHealLocator.builder() \
            .with_web_adapter(adapter) \
            .with_configuration(config) \
            .build()

        # Create reporter with AI config if available
        ai_config = getattr(config, 'ai_config', None)
        self.reporter = AutoHealReporter(ai_config)

        # Store output directory from reporting config
        reporting_config = getattr(config, 'reporting_config', None)
        self.output_directory = getattr(reporting_config, 'output_directory', None)

        print("[AutoHeal] Reporting System ACTIVE")
        print("All selector usage will be tracked and reported!")

    def find_element(
        self,
        selector: str,
        description: str
    ) -> WebElement:
        """
        Find element with full reporting.

        Args:
            selector: The selector string to use.
            description: Human-readable description of the element.

        Returns:
            The located WebElement.

        Raises:
            Exception: If element cannot be found even after healing attempts.

        Examples:
            >>> element = locator.find_element("#login", "Login button")
        """
        start_time = time.time()

        try:
            # Use find_element_with_result to get actual strategy info
            result = self.autoheal.find_element_with_result(selector, description)
            duration_ms = int((time.time() - start_time) * 1000)

            # Use real data from LocatorResult
            strategy = _STRATEGY_MAP.get(result.strategy, SelectorStrategy.DOM_ANALYSIS)
            actual_selector = result.actual_selector or selector
            reasoning = result.reasoning if hasattr(result, 'reasoning') else strategy.value

            # Get element details
            element_details = self._format_element_details(result.element)

            # Use actual token usage from result, fallback to estimates if not available
            tokens = getattr(result, 'tokens_used', 0) or _ESTIMATED_TOKENS.get(strategy, 0)

            # Record the successful usage
            self.reporter.record_selector_usage(
                original_selector=selector,
                description=description,
                strategy=strategy,
                execution_time_ms=duration_ms,
                success=True,
                actual_selector=actual_selector,
                element_details=element_details,
                reasoning=reasoning,
                tokens_used=tokens
            )

            return result.element

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            # Record the failed usage
            self.reporter.record_selector_usage(
                original_selector=selector,
                description=description,
                strategy=SelectorStrategy.FAILED,
                execution_time_ms=duration_ms,
                success=False,
                actual_selector=None,
                element_details=None,
                reasoning=f"Failed: {str(e)}",
                tokens_used=_ESTIMATED_TOKENS.get(SelectorStrategy.FAILED, 0)
            )

            raise

    async def find_element_async(
        self,
        selector: str,
        description: str
    ) -> Any:
        """
        Find element asynchronously with reporting.

        Args:
            selector: The selector string to use.
            description: Human-readable description of the element.

        Returns:
            The located element (Playwright).

        Raises:
            Exception: If element cannot be found even after healing attempts.

        Examples:
            >>> element = await locator.find_element_async("#login", "Login button")
        """
        start_time = time.time()

        try:
            result = await self.autoheal.find_element_async_with_result(selector, description)
            duration_ms = int((time.time() - start_time) * 1000)

            # Use real data from LocatorResult
            strategy = _STRATEGY_MAP.get(result.strategy, SelectorStrategy.DOM_ANALYSIS)
            actual_selector = result.actual_selector or selector
            reasoning = result.reasoning if hasattr(result, 'reasoning') else strategy.value

            # Get element details
            element_details = await self._format_element_details_async(result.element)

            # Use actual token usage from result, fallback to estimates if not available
            tokens = getattr(result, 'tokens_used', 0) or _ESTIMATED_TOKENS.get(strategy, 0)

            self.reporter.record_selector_usage(
                original_selector=selector,
                description=description,
                strategy=strategy,
                execution_time_ms=duration_ms,
                success=True,
                actual_selector=actual_selector,
                element_details=element_details,
                reasoning=reasoning,
                tokens_used=tokens
            )

            return result.element

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            self.reporter.record_selector_usage(
                original_selector=selector,
                description=description,
                strategy=SelectorStrategy.FAILED,
                execution_time_ms=duration_ms,
                success=False,
                actual_selector=None,
                element_details=None,
                reasoning=f"Failed: {str(e)}",
                tokens_used=_ESTIMATED_TOKENS.get(SelectorStrategy.FAILED, 0)
            )

            raise

    async def find_async(
        self,
        playwright_locator: Any,
        description: str
    ) -> Any:
        """
        Find element using a native Playwright Locator with auto-healing and reporting.

        Accepts a native Playwright Locator object (e.g., page.get_by_role(),
        page.get_by_label()) and returns a native Playwright Locator. If the
        original locator fails, AI healing is used to find a working alternative.

        Args:
            playwright_locator: Native Playwright Locator object.
            description: Human-readable description for AI healing.

        Returns:
            Native Playwright Locator that resolves to the target element.

        Raises:
            Exception: If element cannot be found even after healing attempts.

        Examples:
            >>> locator = await reporting_locator.find_async(
            ...     page.get_by_role("button", name="Submit"),
            ...     "Submit button"
            ... )
            >>> await locator.click()
        """
        start_time = time.time()
        try:
            locator_info = PlaywrightLocatorConverter.extract_selector_info(playwright_locator)
            original_selector = locator_info.readable_selector
        except Exception:
            original_selector = str(playwright_locator)

        try:
            result = await self.autoheal.find_async_with_result(playwright_locator, description)
            duration_ms = int((time.time() - start_time) * 1000)

            # Use real data from LocatorResult
            strategy = _STRATEGY_MAP.get(result.strategy, SelectorStrategy.DOM_ANALYSIS)
            actual_selector = result.actual_selector or original_selector
            reasoning = result.reasoning or strategy.value

            # Get element details from the resulting locator
            element_details = await self._format_element_details_async(result.element)

            # Use actual token usage from result, fallback to estimates if not available
            tokens = getattr(result, 'tokens_used', 0) or _ESTIMATED_TOKENS.get(strategy, 0)

            self.reporter.record_selector_usage(
                original_selector=original_selector,
                description=description,
                strategy=strategy,
                execution_time_ms=duration_ms,
                success=True,
                actual_selector=actual_selector,
                element_details=element_details,
                reasoning=reasoning,
                tokens_used=tokens
            )

            return result.element

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            self.reporter.record_selector_usage(
                original_selector=original_selector,
                description=description,
                strategy=SelectorStrategy.FAILED,
                execution_time_ms=duration_ms,
                success=False,
                actual_selector=None,
                element_details=None,
                reasoning=f"Failed: {str(e)}",
                tokens_used=_ESTIMATED_TOKENS.get(SelectorStrategy.FAILED, 0)
            )

            raise

    def _format_element_details(self, element: WebElement) -> str:
        """
        Format element details for reporting.

        Args:
            element: The WebElement to format.

        Returns:
            Formatted string with element details.
        """
        try:
            tag_name = element.tag_name
            element_id = element.get_attribute("id") or "null"
            element_class = element.get_attribute("class") or "null"
            return f"{tag_name}#{element_id}.{element_class}"
        except Exception:
            return "unknown"

    async def _format_element_details_async(self, element: Any) -> str:
        """
        Format element details for reporting (async/Playwright).

        Args:
            element: The Playwright element to format.

        Returns:
            Formatted string with element details.
        """
        try:
            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
            element_id = await element.get_attribute("id") or "null"
            element_class = await element.get_attribute("class") or "null"
            return f"{tag_name}#{element_id}.{element_class}"
        except Exception:
            return "unknown"

    def _infer_strategy(
        self,
        duration_ms: int,
        original_selector: str,
        element: WebElement
    ) -> tuple[SelectorStrategy, str, str]:
        """
        Infer the strategy used based on timing and element properties.

        Args:
            duration_ms: Execution time in milliseconds.
            original_selector: The original selector string.
            element: The located element.

        Returns:
            Tuple of (strategy, reasoning, actual_selector).
        """
        # Infer strategy based on timing
        if duration_ms < 200:
            strategy = SelectorStrategy.ORIGINAL_SELECTOR
            reasoning = "Original selector worked immediately"
            actual_selector = original_selector
        elif duration_ms < 1500:
            strategy = SelectorStrategy.CACHED
            reasoning = "Retrieved from cache"
            actual_selector = self._infer_actual_selector(element)
        elif duration_ms > 3000:
            strategy = SelectorStrategy.DOM_ANALYSIS
            reasoning = "AI DOM analysis was used to heal broken selector"
            actual_selector = self._infer_actual_selector(element)
        else:
            strategy = SelectorStrategy.DOM_ANALYSIS
            reasoning = "Selector healing was attempted"
            actual_selector = self._infer_actual_selector(element)

        return strategy, reasoning, actual_selector

    async def _infer_strategy_async(
        self,
        duration_ms: int,
        original_selector: str,
        element: Any
    ) -> tuple[SelectorStrategy, str, str]:
        """
        Infer the strategy used based on timing and element properties (async).

        Args:
            duration_ms: Execution time in milliseconds.
            original_selector: The original selector string.
            element: The located element (Playwright).

        Returns:
            Tuple of (strategy, reasoning, actual_selector).
        """
        # Infer strategy based on timing
        if duration_ms < 200:
            strategy = SelectorStrategy.ORIGINAL_SELECTOR
            reasoning = "Original selector worked immediately"
            actual_selector = original_selector
        elif duration_ms < 1500:
            strategy = SelectorStrategy.CACHED
            reasoning = "Retrieved from cache"
            actual_selector = await self._infer_actual_selector_async(element)
        else:
            strategy = SelectorStrategy.DOM_ANALYSIS
            reasoning = "AI DOM analysis was used to heal broken selector"
            actual_selector = await self._infer_actual_selector_async(element)

        return strategy, reasoning, actual_selector

    def _infer_actual_selector(self, element: WebElement) -> str:
        """
        Try to infer the actual selector that was used.

        Args:
            element: The WebElement.

        Returns:
            Inferred selector string.
        """
        try:
            # Try to infer the actual selector
            element_id = element.get_attribute("id")
            if element_id and element_id.strip():
                return f"#{element_id}"

            name = element.get_attribute("name")
            if name and name.strip():
                return f"[name='{name}']"

            class_name = element.get_attribute("class")
            if class_name and class_name.strip():
                first_class = class_name.split()[0]
                return f".{first_class}"

            return element.tag_name
        except Exception:
            return "unknown"

    async def _infer_actual_selector_async(self, element: Any) -> str:
        """
        Try to infer the actual selector that was used (async/Playwright).

        Args:
            element: The Playwright element.

        Returns:
            Inferred selector string.
        """
        try:
            # Try to infer the actual selector
            element_id = await element.get_attribute("id")
            if element_id and element_id.strip():
                return f"#{element_id}"

            name = await element.get_attribute("name")
            if name and name.strip():
                return f"[name='{name}']"

            class_name = await element.get_attribute("class")
            if class_name and class_name.strip():
                first_class = class_name.split()[0]
                return f".{first_class}"

            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
            return tag_name
        except Exception:
            return "unknown"

    def _get_report_path(self, filename: str) -> str:
        """
        Build the full report file path using the configured output directory.

        Args:
            filename: The report filename.

        Returns:
            Full path to the report file.
        """
        if self.output_directory:
            os.makedirs(self.output_directory, exist_ok=True)
            return os.path.join(self.output_directory, filename)
        return filename

    def generate_reports(self) -> None:
        """
        Generate all report formats (HTML, JSON, and text).

        Examples:
            >>> locator.generate_reports()
            📝 Generating AutoHeal reports...
            HTML Report generated: /path/to/report.html
            JSON Report generated: /path/to/report.json
            Text Report generated: /path/to/report.txt
        """
        print("\nGenerating AutoHeal reports...")
        run_id = self.reporter.test_run_id
        self.reporter.generate_html_report(self._get_report_path(f"{run_id}_AutoHeal_Report.html"))
        self.reporter.generate_json_report(self._get_report_path(f"{run_id}_AutoHeal_Report.json"))
        self.reporter.generate_text_report(self._get_report_path(f"{run_id}_AutoHeal_Report.txt"))
        self.reporter.print_summary()

    def generate_html_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate HTML report only.

        Args:
            output_path: Optional custom output path.

        Returns:
            Path to the generated HTML file.
        """
        return self.reporter.generate_html_report(output_path)

    def generate_json_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate JSON report only.

        Args:
            output_path: Optional custom output path.

        Returns:
            Path to the generated JSON file.
        """
        return self.reporter.generate_json_report(output_path)

    def generate_text_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate text report only.

        Args:
            output_path: Optional custom output path.

        Returns:
            Path to the generated text file.
        """
        return self.reporter.generate_text_report(output_path)

    def is_element_present(
        self,
        selector: str,
        description: str
    ) -> bool:
        """
        Check if an element is present on the page.

        Args:
            selector: The selector string to use.
            description: Human-readable description of the element.

        Returns:
            True if the element is present, False otherwise.

        Examples:
            >>> if locator.is_element_present(".error", "Error message"):
            ...     print("Error found!")
        """
        return self.autoheal.is_element_present(selector, description)

    async def is_element_present_async(
        self,
        selector: str,
        description: str
    ) -> bool:
        """
        Check if an element is present on the page (async).

        Args:
            selector: The selector string to use.
            description: Human-readable description of the element.

        Returns:
            True if the element is present, False otherwise.

        Examples:
            >>> if await locator.is_element_present_async(".error", "Error message"):
            ...     print("Error found!")
        """
        return await self.autoheal.is_element_present_async(selector, description)

    async def find_elements_async(
        self,
        selector: str,
        description: str,
        options: Optional[Any] = None
    ) -> list:
        """
        Find multiple elements matching a selector (async).

        Note: This method does not apply healing - it returns all matching elements
        using the original selector via the adapter. Use find_element_async for
        single element location with healing support.

        Args:
            selector: The selector string to use.
            description: Human-readable description of the elements.
            options: Optional locator options.

        Returns:
            List of matching elements (may be empty).

        Examples:
            >>> items = await locator.find_elements_async(".product", "Product items")
            >>> for item in items:
            ...     print(await item.text_content())
        """
        return await self.autoheal.find_elements_async(selector, description, options)

    def find_elements(
        self,
        selector: str,
        description: str,
        options: Optional[Any] = None
    ) -> list:
        """
        Find multiple elements matching a selector (sync).

        Note: This method does not apply healing - it returns all matching elements
        using the original selector via the adapter. Use find_element for
        single element location with healing support.

        Args:
            selector: The selector string to use.
            description: Human-readable description of the elements.
            options: Optional locator options.

        Returns:
            List of matching elements (may be empty).

        Examples:
            >>> items = locator.find_elements(".product", "Product items")
            >>> for item in items:
            ...     print(item.text)
        """
        return self.autoheal.find_elements(selector, description, options)

    def get_cache_metrics(self):
        """Get cache performance metrics."""
        return self.autoheal.get_cache_metrics()

    def get_metrics(self):
        """Get locator performance metrics."""
        return self.autoheal.get_metrics()

    def get_health_status(self) -> dict:
        """Get health status for monitoring."""
        return self.autoheal.get_health_status()

    def clear_cache(self) -> None:
        """Clear all cached selectors."""
        self.autoheal.clear_cache()

    def get_autoheal(self) -> AutoHealLocator:
        """
        Get the underlying AutoHeal instance for advanced operations.

        Returns:
            The AutoHealLocator instance.
        """
        return self.autoheal

    def shutdown(self) -> None:
        """
        Shutdown with automatic report generation.

        Generates all report formats and shuts down the underlying AutoHeal instance.

        Examples:
            >>> locator.shutdown()
            Generating AutoHeal reports...
            ...
        """
        self.generate_reports()
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.autoheal.shutdown())
            else:
                loop.run_until_complete(self.autoheal.shutdown())
        except RuntimeError:
            asyncio.run(self.autoheal.shutdown())
