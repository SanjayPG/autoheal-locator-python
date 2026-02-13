"""
Core interfaces for the AutoHeal locator system.

This module provides the abstract interfaces that define the contracts
for AI services, element locators, caches, and automation adapters.
"""

from autoheal.core.ai_service import AIService
from autoheal.core.element_locator import ElementLocator
from autoheal.core.selector_cache import SelectorCache
from autoheal.core.web_automation_adapter import WebAutomationAdapter

__all__ = [
    "AIService",
    "ElementLocator",
    "SelectorCache",
    "WebAutomationAdapter",
]
