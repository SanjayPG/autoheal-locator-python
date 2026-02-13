"""
Utility module for the AutoHeal framework.

This module provides utility functions for selector detection, parsing,
and manipulation.
"""

from autoheal.utils.locator_type_detector import (
    detect_type,
    create_by,
    auto_create_by,
    get_detection_description,
    needs_healing_context,
)
from autoheal.utils.selector_utils import (
    parse_selector,
    is_xpath,
    is_id,
    is_class,
    normalize_selector,
    extract_element_type,
    generate_fallback_selectors,
    selector_complexity_score,
    is_stable_selector,
)
from autoheal.utils.playwright_locator_converter import (
    PlaywrightLocatorConverter,
    NativeLocatorInfo,
)

__all__ = [
    # Locator type detection
    "detect_type",
    "create_by",
    "auto_create_by",
    "get_detection_description",
    "needs_healing_context",
    # Selector utilities
    "parse_selector",
    "is_xpath",
    "is_id",
    "is_class",
    "normalize_selector",
    "extract_element_type",
    "generate_fallback_selectors",
    "selector_complexity_score",
    "is_stable_selector",
    # Playwright locator converter
    "PlaywrightLocatorConverter",
    "NativeLocatorInfo",
]
