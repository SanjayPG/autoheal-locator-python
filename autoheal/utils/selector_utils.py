"""
Selector utilities for parsing and manipulating selectors.

This module provides utilities for selector parsing, normalization,
and manipulation.
"""

import re
from typing import List, Optional, Tuple

from selenium.webdriver.common.by import By


# Regex patterns for selector detection
XPATH_PATTERN = re.compile(r"^(//|\().*")
ID_PATTERN = re.compile(r"^#[a-zA-Z][a-zA-Z0-9_-]*$")
CLASS_PATTERN = re.compile(r"^\.[a-zA-Z][a-zA-Z0-9_-]*$")


def parse_selector(selector: str) -> Tuple[str, str]:
    """
    Parse a selector string into a Selenium By locator.

    Args:
        selector: The selector string.

    Returns:
        Tuple of (By strategy, selector value).

    Raises:
        ValueError: If selector is None or empty.

    Examples:
        >>> parse_selector("//div[@id='test']")
        (By.XPATH, "//div[@id='test']")
        >>> parse_selector("#myId")
        (By.ID, "myId")
        >>> parse_selector(".myClass")
        (By.CLASS_NAME, "myClass")
    """
    if not selector or not selector.strip():
        raise ValueError("Selector cannot be None or empty")

    selector = selector.strip()

    if is_xpath(selector):
        return (By.XPATH, selector)
    elif is_id(selector):
        return (By.ID, selector[1:])  # Remove # prefix
    elif is_class(selector):
        return (By.CLASS_NAME, selector[1:])  # Remove . prefix
    else:
        # Default to CSS selector
        return (By.CSS_SELECTOR, selector)


def is_xpath(selector: str) -> bool:
    """
    Check if selector is XPath.

    Args:
        selector: The selector to check.

    Returns:
        True if XPath, False otherwise.

    Examples:
        >>> is_xpath("//div[@id='test']")
        True
        >>> is_xpath("#myId")
        False
    """
    return bool(XPATH_PATTERN.match(selector))


def is_id(selector: str) -> bool:
    """
    Check if selector is ID selector.

    Args:
        selector: The selector to check.

    Returns:
        True if ID selector, False otherwise.

    Examples:
        >>> is_id("#myId")
        True
        >>> is_id("myId")
        False
    """
    return bool(ID_PATTERN.match(selector))


def is_class(selector: str) -> bool:
    """
    Check if selector is class selector.

    Args:
        selector: The selector to check.

    Returns:
        True if class selector, False otherwise.

    Examples:
        >>> is_class(".myClass")
        True
        >>> is_class("myClass")
        False
    """
    return bool(CLASS_PATTERN.match(selector))


def normalize_selector(selector: Optional[str]) -> Optional[str]:
    """
    Normalize selector for consistent caching.

    Removes extra whitespace and standardizes formatting for
    consistent cache key generation.

    Args:
        selector: The selector to normalize.

    Returns:
        Normalized selector, or None if input is None.

    Examples:
        >>> normalize_selector("div  >  span")
        "div>span"
        >>> normalize_selector("div   +   p")
        "div+p"
    """
    if selector is None:
        return None

    # Multiple spaces to single space
    normalized = re.sub(r"\s+", " ", selector.strip())

    # Remove spaces around combinators
    normalized = re.sub(r"\s*>\s*", ">", normalized)  # child combinator
    normalized = re.sub(r"\s*\+\s*", "+", normalized)  # adjacent sibling
    normalized = re.sub(r"\s*~\s*", "~", normalized)  # general sibling

    return normalized


def extract_element_type(selector: Optional[str]) -> str:
    """
    Extract element type from selector for logging/metrics.

    Args:
        selector: The selector to analyze.

    Returns:
        Element type or "unknown".

    Examples:
        >>> extract_element_type("button[type='submit']")
        "button"
        >>> extract_element_type("//div[@class='container']")
        "div"
        >>> extract_element_type("#unknown")
        "element"
    """
    if not selector or not selector.strip():
        return "unknown"

    selector_lower = selector.strip().lower()

    # Common element types
    element_types = [
        "button",
        "input",
        "select",
        "textarea",
        ("a", "link"),
        "img",
        "div",
        "span",
        "form",
    ]

    for elem in element_types:
        if isinstance(elem, tuple):
            elem_type, return_name = elem
            if elem_type in selector_lower:
                return return_name
        elif elem in selector_lower:
            return elem

    return "element"


def generate_fallback_selectors(original_selector: Optional[str]) -> List[str]:
    """
    Generate fallback selectors for an element.

    Creates alternative selector strategies when the original fails.

    Args:
        original_selector: The original selector that failed.

    Returns:
        List of fallback selectors to try.

    Examples:
        >>> generate_fallback_selectors("#myId")
        ["[id='myId']", ...]
        >>> generate_fallback_selectors(".myClass")
        ["[class*='myClass']", ...]
    """
    if not original_selector or not original_selector.strip():
        return []

    fallbacks = []

    # Convert ID selector to attribute selector
    if original_selector.startswith("#"):
        id_value = original_selector[1:]
        fallbacks.append(f"[id='{id_value}']")
        fallbacks.append(f"//*[@id='{id_value}']")

    # Convert class selector to attribute selector
    elif original_selector.startswith("."):
        class_value = original_selector[1:]
        fallbacks.append(f"[class*='{class_value}']")
        fallbacks.append(f"//*[contains(@class, '{class_value}')]")

    # For other selectors, provide generic fallbacks
    else:
        # Try converting CSS to XPath-style attribute selectors
        if "#" in original_selector:
            fallbacks.append(original_selector.replace("#", "[id='") + "']")
        if "." in original_selector:
            fallbacks.append(original_selector.replace(".", "[class*='") + "']")

    return fallbacks


def selector_complexity_score(selector: str) -> int:
    """
    Calculate complexity score for a selector.

    Higher scores indicate more complex selectors that may be more fragile.

    Args:
        selector: The selector to analyze.

    Returns:
        Complexity score (higher = more complex).

    Examples:
        >>> selector_complexity_score("div")
        1
        >>> selector_complexity_score("div > span.class[attr='value']")
        4
    """
    if not selector:
        return 0

    score = 0

    # Count combinators
    score += selector.count(">")  # Child combinator
    score += selector.count("+")  # Adjacent sibling
    score += selector.count("~")  # General sibling
    score += selector.count(" ") // 2  # Descendant combinator (spaces)

    # Count attribute selectors
    score += selector.count("[")

    # Count pseudo-classes/elements
    score += selector.count(":")

    # Count class selectors
    score += selector.count(".")

    # Base score for any selector
    score += 1

    return score


def is_stable_selector(selector: str) -> bool:
    """
    Determine if a selector is likely to be stable over time.

    Stable selectors use semantic attributes (id, data-testid, aria-label)
    rather than fragile ones (position, class).

    Args:
        selector: The selector to analyze.

    Returns:
        True if selector is likely stable, False otherwise.

    Examples:
        >>> is_stable_selector("#userId")
        True
        >>> is_stable_selector("[data-testid='submit-btn']")
        True
        >>> is_stable_selector("div:nth-child(3) > span")
        False
    """
    if not selector:
        return False

    selector_lower = selector.lower()

    # Stable patterns
    stable_indicators = [
        "id=",
        "data-testid=",
        "data-test-id=",
        "aria-label=",
        "name=",
        "role=",
    ]

    if any(indicator in selector_lower for indicator in stable_indicators):
        return True

    # Unstable patterns
    unstable_indicators = [
        ":nth-child",
        ":nth-of-type",
        ":first-child",
        ":last-child",
        "class*=",
    ]

    if any(indicator in selector_lower for indicator in unstable_indicators):
        return False

    # Simple ID selectors are stable
    if selector.startswith("#") and ID_PATTERN.match(selector):
        return True

    # Complex selectors are generally less stable
    return selector_complexity_score(selector) <= 2
