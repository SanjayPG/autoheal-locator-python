"""
Locator Type Detector utility for automatically detecting locator types.

This module provides utilities to automatically detect locator types and convert
them to appropriate Selenium By objects.
"""

import logging
import re
from typing import Optional, TYPE_CHECKING, Tuple, Any

if TYPE_CHECKING:
    from selenium.webdriver.common.by import By

from autoheal.models.enums import LocatorType

logger = logging.getLogger(__name__)


# Regex patterns for detection
XPATH_PATTERN = re.compile(r"^(//|/|\.//|\.\.//).*")
CSS_ID_PATTERN = re.compile(r"^#[a-zA-Z][a-zA-Z0-9_-]*$")
CSS_CLASS_PATTERN = re.compile(r"^\.[a-zA-Z][a-zA-Z0-9_-]*$")
CSS_ATTRIBUTE_PATTERN = re.compile(r".*\[.*=.*\].*")
CSS_PSEUDO_PATTERN = re.compile(r".*:.*")
CSS_COMBINATOR_PATTERN = re.compile(r".*[>+~].*")
CSS_MULTIPLE_PATTERN = re.compile(r".*[#\.].*")

# Simple identifier patterns
SIMPLE_ID_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$")
TAG_NAME_PATTERN = re.compile(
    r"^(a|abbr|address|area|article|aside|audio|b|base|bdi|bdo|big|blockquote|body|br|"
    r"button|canvas|caption|cite|code|col|colgroup|data|datalist|dd|del|details|dfn|"
    r"dialog|div|dl|dt|em|embed|fieldset|figcaption|figure|footer|form|h1|h2|h3|h4|h5|"
    r"h6|head|header|hr|html|i|iframe|img|input|ins|kbd|label|legend|li|link|main|map|"
    r"mark|meta|meter|nav|noscript|object|ol|optgroup|option|output|p|param|picture|pre|"
    r"progress|q|rp|rt|ruby|s|samp|script|section|select|small|source|span|strong|style|"
    r"sub|summary|sup|svg|table|tbody|td|textarea|tfoot|th|thead|time|title|tr|track|u|"
    r"ul|var|video|wbr)$"
)


def detect_type(locator: str) -> LocatorType:
    """
    Detect the locator type based on the locator string.

    Args:
        locator: The locator string to analyze.

    Returns:
        The detected LocatorType.

    Raises:
        ValueError: If locator is None or empty.

    Examples:
        >>> detect_type("//div[@id='test']")
        LocatorType.XPATH
        >>> detect_type("#myId")
        LocatorType.CSS
        >>> detect_type("button")
        LocatorType.TAG_NAME
    """
    if not locator or not locator.strip():
        raise ValueError("Locator cannot be None or empty")

    trimmed_locator = locator.strip()
    logger.debug(f"Detecting locator type for: '{trimmed_locator}'")

    # 1. Check for XPath (starts with // or / or ./ or ../)
    if XPATH_PATTERN.match(trimmed_locator):
        logger.debug(f"Detected as XPath: '{trimmed_locator}'")
        return LocatorType.XPATH

    # 2. Check for CSS ID selector (#id)
    if CSS_ID_PATTERN.match(trimmed_locator):
        logger.debug(f"Detected as CSS ID selector: '{trimmed_locator}'")
        return LocatorType.CSS

    # 3. Check for CSS class selector (.class)
    if CSS_CLASS_PATTERN.match(trimmed_locator):
        logger.debug(f"Detected as CSS class selector: '{trimmed_locator}'")
        return LocatorType.CSS

    # 4. Check for complex CSS selectors
    if (
        CSS_ATTRIBUTE_PATTERN.match(trimmed_locator)
        or CSS_PSEUDO_PATTERN.match(trimmed_locator)
        or CSS_COMBINATOR_PATTERN.match(trimmed_locator)
        or CSS_MULTIPLE_PATTERN.match(trimmed_locator)
    ):
        logger.debug(f"Detected as complex CSS selector: '{trimmed_locator}'")
        return LocatorType.CSS

    # 5. Check for HTML tag names
    if TAG_NAME_PATTERN.match(trimmed_locator.lower()):
        logger.debug(f"Detected as tag name: '{trimmed_locator}'")
        return LocatorType.TAG_NAME

    # 6. Check if it looks like link text (contains spaces or common link words)
    if _is_likely_link_text(trimmed_locator):
        logger.debug(f"Detected as link text: '{trimmed_locator}'")
        return LocatorType.LINK_TEXT

    # 7. Default to ID for simple identifiers, NAME as fallback
    if SIMPLE_ID_PATTERN.match(trimmed_locator):
        logger.debug(f"Detected as simple identifier (ID): '{trimmed_locator}'")
        return LocatorType.ID

    # 8. If nothing else matches, treat as name attribute (fallback)
    logger.debug(f"Detected as name attribute (fallback): '{trimmed_locator}'")
    return LocatorType.NAME


def create_by(locator: str, locator_type: LocatorType) -> Tuple[str, str]:
    """
    Convert locator string to appropriate Selenium By tuple.

    Args:
        locator: The locator string.
        locator_type: The detected or specified locator type.

    Returns:
        Tuple of (By strategy, locator value).

    Raises:
        ValueError: If locator is None or empty.

    Examples:
        >>> create_by("#myId", LocatorType.CSS)
        ('css selector', '#myId')
        >>> create_by("//div[@id='test']", LocatorType.XPATH)
        ('xpath', "//div[@id='test']")
    """
    if not locator or not locator.strip():
        raise ValueError("Locator cannot be None or empty")

    trimmed_locator = locator.strip()
    logger.debug(f"Creating By object for '{trimmed_locator}' as {locator_type}")

    # Import By here to avoid circular imports
    from selenium.webdriver.common.by import By

    locator_map = {
        LocatorType.CSS: By.CSS_SELECTOR,
        LocatorType.XPATH: By.XPATH,
        LocatorType.ID: By.ID,
        LocatorType.NAME: By.NAME,
        LocatorType.CLASS_NAME: By.CLASS_NAME,
        LocatorType.TAG_NAME: By.TAG_NAME,
        LocatorType.LINK_TEXT: By.LINK_TEXT,
        LocatorType.PARTIAL_LINK_TEXT: By.PARTIAL_LINK_TEXT,
    }

    by_strategy = locator_map.get(locator_type)
    if by_strategy:
        return (by_strategy, trimmed_locator)
    else:
        logger.warning(f"Unknown locator type {locator_type}, defaulting to CSS selector")
        return (By.CSS_SELECTOR, trimmed_locator)


def auto_create_by(locator: str) -> Tuple[str, str]:
    """
    Auto-detect and create Selenium By tuple.

    Args:
        locator: The locator string.

    Returns:
        Tuple of (By strategy, locator value).

    Examples:
        >>> auto_create_by("//div[@id='test']")
        ('xpath', "//div[@id='test']")
        >>> auto_create_by("#myId")
        ('css selector', '#myId')
    """
    detected_type = detect_type(locator)
    return create_by(locator, detected_type)


def get_detection_description(locator: str, detected_type: LocatorType) -> str:
    """
    Get a human-readable description of what was detected.

    Args:
        locator: The original locator.
        detected_type: The detected type.

    Returns:
        Human-readable description.

    Examples:
        >>> get_detection_description("#myId", LocatorType.CSS)
        "Auto-detected '#myId' as CSS locator"
    """
    type_names = {
        LocatorType.CSS: "CSS",
        LocatorType.XPATH: "XPath",
        LocatorType.ID: "ID",
        LocatorType.NAME: "Name",
        LocatorType.CLASS_NAME: "Class Name",
        LocatorType.TAG_NAME: "Tag Name",
        LocatorType.LINK_TEXT: "Link Text",
        LocatorType.PARTIAL_LINK_TEXT: "Partial Link Text",
    }
    type_display = type_names.get(detected_type, detected_type.value)
    return f"Auto-detected '{locator}' as {type_display} locator"


def needs_healing_context(locator_type: LocatorType) -> bool:
    """
    Check if a locator needs healing context (for AI prompts).

    Args:
        locator_type: The locator type.

    Returns:
        True if this type benefits from healing context.

    Examples:
        >>> needs_healing_context(LocatorType.CSS)
        True
        >>> needs_healing_context(LocatorType.LINK_TEXT)
        False
    """
    return locator_type in (
        LocatorType.CSS,
        LocatorType.XPATH,
        LocatorType.ID,
        LocatorType.NAME,
    )


def _is_likely_link_text(locator: str) -> bool:
    """
    Check if the locator string looks like link text.

    Args:
        locator: The locator string to check.

    Returns:
        True if it looks like link text.
    """
    # Contains spaces (likely readable text)
    if " " in locator:
        return True

    # Common link text patterns
    lower_locator = locator.lower()
    link_keywords = [
        "click",
        "here",
        "more",
        "read",
        "view",
        "login",
        "logout",
        "sign",
        "register",
        "home",
        "about",
        "contact",
        "help",
        "support",
    ]

    if any(keyword in lower_locator for keyword in link_keywords):
        return True

    # Long text without CSS/XPath chars
    if len(lower_locator) > 15 and not re.search(r"[#.\[\]@/]", lower_locator):
        return True

    return False
