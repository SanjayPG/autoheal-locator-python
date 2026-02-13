"""
Playwright native locator converter.

Extracts selector information from native Playwright Locator objects
and converts them to the AutoHeal PlaywrightLocator model.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from autoheal.models.playwright_locator import PlaywrightLocator, PlaywrightLocatorType

logger = logging.getLogger(__name__)


@dataclass
class NativeLocatorInfo:
    """
    Information extracted from a native Playwright Locator object.

    Attributes:
        internal_selector: Raw internal selector string from Playwright.
        readable_selector: Human-readable Python-style selector for cache keys/logging.
        playwright_locator: Parsed PlaywrightLocator model (None if chained or unparseable).
        is_chained: True if the selector contains chained locators (>> separator).
    """

    internal_selector: str
    readable_selector: str
    playwright_locator: Optional[PlaywrightLocator] = None
    is_chained: bool = False


# Regex patterns for Playwright internal selector formats
_ROLE_WITH_NAME_RE = re.compile(
    r'^internal:role=(\w+)\[name="([^"]*)"[is]?\]$'
)
_ROLE_WITHOUT_NAME_RE = re.compile(
    r'^internal:role=(\w+)$'
)
_LABEL_RE = re.compile(
    r'^internal:label="([^"]*)"[is]?$'
)
_TEXT_RE = re.compile(
    r'^internal:text="([^"]*)"[is]?$'
)
_TESTID_RE = re.compile(
    r'^internal:testid=\[data-testid="([^"]*)"[is]?\]$'
)
_ATTR_PLACEHOLDER_RE = re.compile(
    r'^internal:attr=\[placeholder="([^"]*)"[is]?\]$'
)
_ATTR_ALT_RE = re.compile(
    r'^internal:attr=\[alt="([^"]*)"[is]?\]$'
)
_ATTR_TITLE_RE = re.compile(
    r'^internal:attr=\[title="([^"]*)"[is]?\]$'
)
_CHAINED_RE = re.compile(r'\s*>>\s*')

# Chain-part patterns for converting chained selectors
_NTH_RE = re.compile(r'^nth=(\d+)$')
_HAS_TEXT_RE = re.compile(r'^internal:has-text="([^"]*)"[is]?$')
_HAS_NOT_TEXT_RE = re.compile(r'^internal:has-not-text="([^"]*)"[is]?$')
_HAS_RE = re.compile(r'^internal:has=(.+)$')
_HAS_NOT_RE = re.compile(r'^internal:has-not=(.+)$')


class PlaywrightLocatorConverter:
    """
    Converts native Playwright Locator objects to AutoHeal PlaywrightLocator models.

    Supports extracting selector info from Playwright's internal representation
    including role, label, text, test-id, placeholder, alt-text, title,
    CSS, and XPath selectors.
    """

    @staticmethod
    def extract_selector_info(native_locator: Any) -> NativeLocatorInfo:
        """
        Extract selector information from a native Playwright Locator.

        Args:
            native_locator: A Playwright Locator object.

        Returns:
            NativeLocatorInfo with parsed selector details.
        """
        internal_selector = PlaywrightLocatorConverter._extract_internal_selector(
            native_locator
        )

        # Check for chained locators
        parts = _CHAINED_RE.split(internal_selector)
        if len(parts) > 1:
            readable = PlaywrightLocatorConverter._convert_chained_selector(parts)
            logger.debug(
                "Chained locator detected with %d parts: %s",
                len(parts), internal_selector
            )
            return NativeLocatorInfo(
                internal_selector=internal_selector,
                readable_selector=readable,
                playwright_locator=None,
                is_chained=True,
            )

        # Parse single locator
        playwright_locator = PlaywrightLocatorConverter._parse_internal_selector(
            internal_selector
        )

        if playwright_locator is not None:
            readable = playwright_locator.to_selector_string()
        else:
            readable = internal_selector

        return NativeLocatorInfo(
            internal_selector=internal_selector,
            readable_selector=readable,
            playwright_locator=playwright_locator,
            is_chained=False,
        )

    @staticmethod
    def _convert_chained_selector(parts: list) -> str:
        """
        Convert chained internal selector parts to a readable Python-style locator string.

        The first part is converted via _parse_internal_selector -> to_selector_string().
        Remaining parts are matched against chain-specific patterns (nth, filter, has, etc.).

        Args:
            parts: List of selector parts split on '>>'.

        Returns:
            Human-readable chained locator string (e.g., 'page.get_by_role("button").nth(1)').
        """
        # Convert the base (first) part
        base_locator = PlaywrightLocatorConverter._parse_internal_selector(parts[0])
        if base_locator is not None:
            result = base_locator.to_selector_string()
        else:
            result = f'page.locator("{parts[0]}")'

        # Convert each remaining part
        for part in parts[1:]:
            match = _NTH_RE.match(part)
            if match:
                result += f'.nth({match.group(1)})'
                continue

            match = _HAS_TEXT_RE.match(part)
            if match:
                result += f'.filter(has_text="{match.group(1)}")'
                continue

            match = _HAS_NOT_TEXT_RE.match(part)
            if match:
                result += f'.filter(has_not_text="{match.group(1)}")'
                continue

            match = _HAS_RE.match(part)
            if match:
                inner_selector = match.group(1)
                # Playwright wraps has= inner selectors in quotes — strip them
                if inner_selector.startswith('"') and inner_selector.endswith('"'):
                    inner_selector = inner_selector[1:-1]
                inner_readable = PlaywrightLocatorConverter._convert_inner_selector(inner_selector)
                result += f'.filter(has={inner_readable})'
                continue

            match = _HAS_NOT_RE.match(part)
            if match:
                inner_selector = match.group(1)
                if inner_selector.startswith('"') and inner_selector.endswith('"'):
                    inner_selector = inner_selector[1:-1]
                inner_readable = PlaywrightLocatorConverter._convert_inner_selector(inner_selector)
                result += f'.filter(has_not={inner_readable})'
                continue

            # Unknown part — fall back to raw string
            result += f'.locator("{part}")'

        return result

    @staticmethod
    def _convert_inner_selector(inner_selector: str) -> str:
        """
        Convert an inner selector (from has=/has_not=) to a readable string.

        Handles both chained and single selectors, unescaping internal quotes.

        Args:
            inner_selector: The inner selector string (already stripped of outer quotes).

        Returns:
            Human-readable locator string.
        """
        # Unescape internal escaped quotes (Playwright escapes them as \")
        inner_selector = inner_selector.replace('\\"', '"')

        inner_parts = _CHAINED_RE.split(inner_selector)
        if len(inner_parts) > 1:
            return PlaywrightLocatorConverter._convert_chained_selector(inner_parts)

        inner_locator = PlaywrightLocatorConverter._parse_internal_selector(inner_selector)
        if inner_locator is not None:
            return inner_locator.to_selector_string()

        return f'page.locator("{inner_selector}")'

    @staticmethod
    def _extract_internal_selector(native_locator: Any) -> str:
        """
        Extract the raw internal selector string from a Playwright Locator.

        Tries _selector attribute first, falls back to str().

        Args:
            native_locator: A Playwright Locator object.

        Returns:
            Internal selector string.
        """
        # Primary: use _selector attribute (Playwright internal)
        # Async Locator wraps an impl object: locator._impl_obj._selector
        for attr_path in [
            lambda loc: loc._selector,
            lambda loc: loc._impl_obj._selector,
        ]:
            try:
                selector = attr_path(native_locator)
                if selector:
                    logger.debug("Extracted selector: %s", selector)
                    return str(selector)
            except (AttributeError, TypeError):
                continue

        # Fallback: parse from str() representation
        # Format: <Locator ... selector='internal:role=button[name="Login"i]'>
        str_repr = str(native_locator)
        import re
        match = re.search(r"selector='([^']+)'", str_repr)
        if match:
            selector = match.group(1)
            logger.debug("Extracted selector from str(): %s", selector)
            return selector

        logger.warning(
            "Could not extract selector, using raw str(): %s", str_repr
        )
        return str_repr

    @staticmethod
    def _parse_internal_selector(selector: str) -> Optional[PlaywrightLocator]:
        """
        Parse a Playwright internal selector string into a PlaywrightLocator model.

        Args:
            selector: Internal selector string (e.g., 'internal:role=button[name="Submit"i]').

        Returns:
            PlaywrightLocator if parseable, None otherwise.
        """
        # Role with name: internal:role=button[name="Submit"i]
        match = _ROLE_WITH_NAME_RE.match(selector)
        if match:
            return PlaywrightLocator(
                type=PlaywrightLocatorType.GET_BY_ROLE,
                value=match.group(1),
                options={"name": match.group(2)},
            )

        # Role without name: internal:role=button
        match = _ROLE_WITHOUT_NAME_RE.match(selector)
        if match:
            return PlaywrightLocator(
                type=PlaywrightLocatorType.GET_BY_ROLE,
                value=match.group(1),
            )

        # Label: internal:label="Username"i
        match = _LABEL_RE.match(selector)
        if match:
            return PlaywrightLocator(
                type=PlaywrightLocatorType.GET_BY_LABEL,
                value=match.group(1),
            )

        # Text: internal:text="Hello"i
        match = _TEXT_RE.match(selector)
        if match:
            return PlaywrightLocator(
                type=PlaywrightLocatorType.GET_BY_TEXT,
                value=match.group(1),
            )

        # Test ID: internal:testid=[data-testid="login"s]
        match = _TESTID_RE.match(selector)
        if match:
            return PlaywrightLocator(
                type=PlaywrightLocatorType.GET_BY_TEST_ID,
                value=match.group(1),
            )

        # Placeholder: internal:attr=[placeholder="Enter email"i]
        match = _ATTR_PLACEHOLDER_RE.match(selector)
        if match:
            return PlaywrightLocator(
                type=PlaywrightLocatorType.GET_BY_PLACEHOLDER,
                value=match.group(1),
            )

        # Alt text: internal:attr=[alt="Logo"i]
        match = _ATTR_ALT_RE.match(selector)
        if match:
            return PlaywrightLocator(
                type=PlaywrightLocatorType.GET_BY_ALT_TEXT,
                value=match.group(1),
            )

        # Title: internal:attr=[title="Home"i]
        match = _ATTR_TITLE_RE.match(selector)
        if match:
            return PlaywrightLocator(
                type=PlaywrightLocatorType.GET_BY_TITLE,
                value=match.group(1),
            )

        # XPath
        if selector.startswith("xpath="):
            return PlaywrightLocator(
                type=PlaywrightLocatorType.XPATH,
                value=selector[6:],
            )
        if selector.startswith("//") or selector.startswith("./"):
            return PlaywrightLocator(
                type=PlaywrightLocatorType.XPATH,
                value=selector,
            )

        # CSS (anything that doesn't match internal: patterns)
        if not selector.startswith("internal:"):
            return PlaywrightLocator(
                type=PlaywrightLocatorType.CSS_SELECTOR,
                value=selector,
            )

        # Unrecognized internal: format
        logger.warning("Unrecognized internal selector format: %s", selector)
        return None
