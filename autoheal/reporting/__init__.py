"""
AutoHeal Reporting Module.

This module provides comprehensive reporting capabilities for the AutoHeal framework,
including tracking selector usage, healing strategies, AI metrics, and generating
reports in multiple formats (HTML, JSON, text).

Classes:
    SelectorStrategy: Enumeration of selector resolution strategies.
    SelectorReport: Data class representing a single selector usage event.
    AutoHealReporter: Main reporter class for tracking and generating reports.
    ReportingAutoHealLocator: Wrapper that automatically tracks all selector usage.

Examples:
    >>> from autoheal.reporting import AutoHealReporter, SelectorStrategy
    >>>
    >>> # Create a reporter
    >>> reporter = AutoHealReporter()
    >>>
    >>> # Record selector usage
    >>> reporter.record_selector_usage(
    ...     original_selector="#login",
    ...     description="Login button",
    ...     strategy=SelectorStrategy.ORIGINAL_SELECTOR,
    ...     execution_time_ms=50,
    ...     success=True,
    ...     actual_selector="#login",
    ...     element_details="button#login.btn",
    ...     reasoning="Original selector worked"
    ... )
    >>>
    >>> # Generate reports
    >>> reporter.generate_html_report()
    >>> reporter.generate_json_report()
    >>> reporter.generate_text_report()

    >>> # Using the reporting wrapper
    >>> from autoheal.reporting import ReportingAutoHealLocator
    >>> from autoheal.impl.adapter.selenium_adapter import SeleniumAdapter
    >>> from autoheal.config.autoheal_config import AutoHealConfiguration
    >>>
    >>> adapter = SeleniumAdapter(driver)
    >>> config = AutoHealConfiguration()
    >>> locator = ReportingAutoHealLocator(adapter, config)
    >>>
    >>> # All selector usage is automatically tracked
    >>> element = locator.find_element("#login", "Login button")
    >>>
    >>> # Generate reports at the end
    >>> locator.generate_reports()
"""

from autoheal.reporting.autoheal_reporter import (
    AutoHealReporter,
    SelectorReport,
    SelectorStrategy
)
from autoheal.reporting.reporting_autoheal_locator import (
    ReportingAutoHealLocator
)

__all__ = [
    "AutoHealReporter",
    "SelectorReport",
    "SelectorStrategy",
    "ReportingAutoHealLocator"
]
