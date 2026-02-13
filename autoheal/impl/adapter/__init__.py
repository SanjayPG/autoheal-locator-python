"""
Web automation adapter implementations.

This module provides adapter implementations for different web automation
frameworks including Selenium and Playwright.
"""

from autoheal.impl.adapter.selenium_adapter import SeleniumWebAutomationAdapter
from autoheal.impl.adapter.playwright_adapter import PlaywrightWebAutomationAdapter

__all__ = [
    "SeleniumWebAutomationAdapter",
    "PlaywrightWebAutomationAdapter",
]
