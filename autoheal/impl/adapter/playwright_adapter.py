"""
Playwright adapter implementation.

This module provides the Playwright adapter for the AutoHeal locator system,
allowing it to work with Playwright for web automation.
"""

import asyncio
import hashlib
import logging
from typing import List, Union, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page, ElementHandle, Locator
    from selenium.webdriver.remote.webelement import WebElement
    from selenium.webdriver.common.by import By

from autoheal.core.web_automation_adapter import WebAutomationAdapter
from autoheal.models.enums import AutomationFramework
from autoheal.models.element_context import ElementContext
from autoheal.models.element_fingerprint import ElementFingerprint
from autoheal.models.position import Position
from autoheal.models.playwright_locator import PlaywrightLocator, PlaywrightLocatorType
from autoheal.exception.exceptions import AdapterException

logger = logging.getLogger(__name__)


class PlaywrightWebAutomationAdapter(WebAutomationAdapter):
    """
    Playwright adapter for the AutoHeal locator system.

    This adapter provides a bridge between the AutoHeal framework and Playwright,
    enabling element finding, screenshot capture, and context extraction using
    Playwright's modern locator APIs.

    Attributes:
        page: Playwright Page instance.

    Examples:
        >>> from playwright.async_api import async_playwright
        >>> async with async_playwright() as p:
        ...     browser = await p.chromium.launch()
        ...     page = await browser.new_page()
        ...     adapter = PlaywrightWebAutomationAdapter(page)
        ...     await page.goto("https://example.com")
        ...     elements = await adapter.find_elements("#submit-button")
    """

    def __init__(self, page: "Page"):
        """
        Initialize the Playwright adapter.

        Args:
            page: Playwright Page instance.
        """
        self.page = page
        logger.info("PlaywrightWebAutomationAdapter initialized")

    def get_framework_type(self) -> AutomationFramework:
        """
        Get the automation framework type.

        Returns:
            AutomationFramework.PLAYWRIGHT
        """
        return AutomationFramework.PLAYWRIGHT

    async def find_elements(
        self,
        selector: Union[str, "By"]
    ) -> List["WebElement"]:
        """
        Find elements using the given selector.

        Args:
            selector: CSS selector, XPath, or Selenium By locator object.

        Returns:
            List of matching ElementHandles (may be empty if none found).

        Raises:
            AdapterException: If the adapter encounters an error.

        Note:
            Playwright ElementHandles are returned. For Playwright locators,
            use execute_playwright_locator() method instead.
        """
        try:
            # Convert selector to string if it's a By object
            if not isinstance(selector, str):
                selector = self._convert_by_to_selector(selector)

            # Use Playwright's query_selector_all
            elements = await self.page.query_selector_all(selector)
            logger.debug("Found %d elements for selector: %s", len(elements), selector)
            return elements
        except Exception as e:
            logger.error("Failed to find elements with selector: %s", selector, exc_info=True)
            # Return empty list instead of raising for compatibility
            return []

    async def get_page_source(self, include_shadow_dom: bool = True) -> str:
        """
        Get the current page source, optionally including shadow DOM content.

        Args:
            include_shadow_dom: If True, extracts and includes shadow DOM content.
                               Defaults to True for better AI healing support.

        Returns:
            HTML page source as a string, with shadow DOM content included
            if include_shadow_dom is True.

        Raises:
            AdapterException: If the adapter cannot retrieve page source.
        """
        try:
            if include_shadow_dom:
                page_source = await self._get_page_source_with_shadow_dom()
            else:
                page_source = await self.page.content()
            logger.debug("Retrieved page source (length: %d characters)", len(page_source))
            return page_source
        except Exception as e:
            logger.error("Failed to get page source", exc_info=True)
            raise AdapterException("Failed to get page source") from e

    async def _get_page_source_with_shadow_dom(self) -> str:
        """
        Extract page source including shadow DOM content.

        Uses JavaScript to recursively traverse the DOM and serialize
        shadow root contents with special markers for AI analysis.

        Returns:
            HTML string with shadow DOM content included.
        """
        try:
            # JavaScript to recursively extract DOM including shadow roots
            shadow_dom_script = """
            () => {
                function serializeNode(node, depth = 0) {
                    if (!node) return '';

                    // Handle text nodes
                    if (node.nodeType === Node.TEXT_NODE) {
                        return node.textContent;
                    }

                    // Handle element nodes
                    if (node.nodeType !== Node.ELEMENT_NODE) {
                        return '';
                    }

                    const element = node;
                    const tagName = element.tagName.toLowerCase();

                    // Build opening tag with attributes
                    let html = '<' + tagName;
                    for (const attr of element.attributes) {
                        html += ' ' + attr.name + '="' + attr.value.replace(/"/g, '&quot;') + '"';
                    }
                    html += '>';

                    // Check for shadow root and serialize it
                    if (element.shadowRoot) {
                        html += '<!-- shadow-root mode="' + (element.shadowRoot.mode || 'open') + '" -->';
                        for (const child of element.shadowRoot.childNodes) {
                            html += serializeNode(child, depth + 1);
                        }
                        html += '<!-- /shadow-root -->';
                    }

                    // Serialize light DOM children
                    for (const child of element.childNodes) {
                        html += serializeNode(child, depth + 1);
                    }

                    // Self-closing tags
                    const selfClosing = ['area', 'base', 'br', 'col', 'embed', 'hr', 'img',
                                        'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'];
                    if (!selfClosing.includes(tagName)) {
                        html += '</' + tagName + '>';
                    }

                    return html;
                }

                // Start serialization from documentElement (includes <html>)
                const doctype = document.doctype
                    ? '<!DOCTYPE ' + document.doctype.name + '>'
                    : '<!DOCTYPE html>';
                return doctype + serializeNode(document.documentElement);
            }
            """

            page_source = await self.page.evaluate(shadow_dom_script)

            if page_source:
                logger.debug(
                    "Retrieved page source with shadow DOM (length: %d characters)",
                    len(page_source)
                )
                return page_source
            else:
                # Fallback to regular content if evaluation fails
                logger.warning("Shadow DOM extraction returned empty, falling back to regular content")
                return await self.page.content()

        except Exception as e:
            logger.warning(
                "Failed to extract shadow DOM, falling back to regular content: %s",
                str(e)
            )
            # Fallback to regular page.content() on any error
            return await self.page.content()

    async def take_screenshot(self) -> bytes:
        """
        Take a screenshot of the current page.

        Returns:
            Screenshot as bytes (PNG format).

        Raises:
            AdapterException: If the adapter cannot take a screenshot.
        """
        try:
            screenshot = await self.page.screenshot()
            logger.debug("Screenshot taken (size: %d bytes)", len(screenshot))
            return screenshot
        except Exception as e:
            logger.error("Failed to take screenshot", exc_info=True)
            raise AdapterException("Failed to take screenshot") from e

    async def get_element_context(self, element: "ElementHandle") -> ElementContext:
        """
        Extract contextual information about an element.

        Args:
            element: Playwright ElementHandle to analyze.

        Returns:
            ElementContext containing detailed information about the element.

        Raises:
            AdapterException: If the adapter cannot extract element context.
        """
        try:
            context = await self._get_element_context_async(element)
            logger.debug("Extracted context for element")
            return context
        except Exception as e:
            logger.error("Failed to extract element context", exc_info=True)
            raise AdapterException("Failed to extract element context") from e

    # Playwright-specific methods

    async def execute_playwright_locator(
        self,
        playwright_locator: PlaywrightLocator
    ) -> "Locator":
        """
        Execute a PlaywrightLocator and return native Playwright Locator object.

        Args:
            playwright_locator: The PlaywrightLocator to execute.

        Returns:
            Native Playwright Locator.

        Examples:
            >>> from autoheal.models.playwright_locator import PlaywrightLocator
            >>> locator_model = PlaywrightLocator.builder() \\
            ...     .by_role("button", "Submit") \\
            ...     .build()
            >>> locator = await adapter.execute_playwright_locator(locator_model)
            >>> await locator.click()
        """
        locator_type = playwright_locator.type
        value = playwright_locator.value
        options = playwright_locator.options

        # Execute based on locator type
        if locator_type == PlaywrightLocatorType.GET_BY_ROLE:
            locator = self._get_by_role(value, options)
        elif locator_type == PlaywrightLocatorType.GET_BY_LABEL:
            locator = self.page.get_by_label(value)
        elif locator_type == PlaywrightLocatorType.GET_BY_PLACEHOLDER:
            locator = self.page.get_by_placeholder(value)
        elif locator_type == PlaywrightLocatorType.GET_BY_TEXT:
            locator = self.page.get_by_text(value)
        elif locator_type == PlaywrightLocatorType.GET_BY_ALT_TEXT:
            locator = self.page.get_by_alt_text(value)
        elif locator_type == PlaywrightLocatorType.GET_BY_TITLE:
            locator = self.page.get_by_title(value)
        elif locator_type == PlaywrightLocatorType.GET_BY_TEST_ID:
            locator = self.page.get_by_test_id(value)
        elif locator_type in [PlaywrightLocatorType.CSS_SELECTOR, PlaywrightLocatorType.XPATH]:
            locator = self.page.locator(value)
        else:
            raise ValueError(f"Unsupported locator type: {locator_type}")

        # Apply filters if present
        for filter_obj in playwright_locator.filters:
            if filter_obj.has_text:
                locator = locator.filter(has_text=filter_obj.has_text)
            if filter_obj.has_not_text:
                locator = locator.filter(has_not_text=filter_obj.has_not_text)
            if filter_obj.has:
                # has requires a Locator, convert selector to locator
                has_locator = self.page.locator(filter_obj.has)
                locator = locator.filter(has=has_locator)
            if filter_obj.has_not:
                has_not_locator = self.page.locator(filter_obj.has_not)
                locator = locator.filter(has_not=has_not_locator)

        return locator

    async def count_elements(self, locator: "Locator") -> int:
        """
        Count elements matching a Playwright locator.

        Args:
            locator: Playwright Locator object.

        Returns:
            Number of matching elements, or 0 if failed.
        """
        try:
            count = await locator.count()
            return count
        except Exception as e:
            logger.debug("Failed to count elements: %s", str(e))
            return 0

    def get_page(self) -> "Page":
        """
        Get the underlying Playwright Page object.

        Returns:
            Playwright Page instance.
        """
        return self.page

    # Private helper methods

    def _convert_by_to_selector(self, by: Union["By", tuple]) -> str:
        """
        Convert Selenium By object to selector string.

        Args:
            by: Selenium By object or tuple (strategy, value).

        Returns:
            Selector string compatible with Playwright.
        """
        # Handle tuple format (strategy, value)
        if isinstance(by, tuple):
            strategy, value = by
            by_string = f"By.{strategy}: {value}"
        else:
            by_string = str(by)

        # Parse By string format
        if by_string.startswith("By.id: "):
            return "#" + by_string[7:]
        elif by_string.startswith("By.className: ") or by_string.startswith("By.class name: "):
            prefix_len = 14 if "className" in by_string else 15
            return "." + by_string[prefix_len:]
        elif by_string.startswith("By.cssSelector: ") or by_string.startswith("By.css selector: "):
            prefix_len = 16 if "cssSelector" in by_string else 17
            return by_string[prefix_len:]
        elif by_string.startswith("By.xpath: "):
            return by_string[10:]
        elif by_string.startswith("By.tagName: ") or by_string.startswith("By.tag name: "):
            prefix_len = 12 if "tagName" in by_string else 13
            return by_string[prefix_len:]
        else:
            # Default to treating as CSS selector
            logger.warning("Unknown By format: %s, treating as CSS", by_string)
            return by_string

    def _get_by_role(self, role_name: str, options: Dict[str, Any]) -> "Locator":
        """
        Create getByRole locator with proper role parsing.

        Args:
            role_name: Role name (e.g., "button", "textbox").
            options: Additional options like {"name": "Submit"}.

        Returns:
            Playwright Locator.
        """
        # Playwright Python uses string roles, not enums
        # Common roles: button, checkbox, textbox, link, heading, etc.
        role_name = role_name.lower().strip()

        if options and "name" in options:
            return self.page.get_by_role(role_name, name=options["name"])
        else:
            return self.page.get_by_role(role_name)

    async def _get_element_context_async(self, element: "ElementHandle") -> ElementContext:
        """
        Async helper to extract element context.

        Args:
            element: Playwright ElementHandle.

        Returns:
            ElementContext with element details.
        """
        # Extract element properties using JavaScript evaluation
        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
        text_content = await element.text_content() or ""

        # Get attributes
        attributes = await self._extract_attributes_async(element)

        # Get position
        position = await self._extract_position_async(element)

        # Get parent container
        parent_container = await self._extract_parent_container_async(element)

        # Get siblings (limited)
        siblings = await self._extract_siblings_async(element)

        # Get computed styles
        computed_styles = await self._extract_computed_styles_async(element)

        # Generate visual hash
        visual_hash = await self._generate_visual_hash_async(element)

        # Create fingerprint
        fingerprint = ElementFingerprint(
            parent_container=parent_container,
            position=position,
            computed_styles=computed_styles,
            text_content=text_content,
            sibling_elements=siblings,
            visual_hash=visual_hash
        )

        # Build context
        context = ElementContext.builder() \
            .parent_container(parent_container) \
            .relative_position(position) \
            .sibling_elements(siblings) \
            .attributes(attributes) \
            .text_content(text_content) \
            .fingerprint(fingerprint) \
            .build()

        return context

    async def _extract_attributes_async(self, element: "ElementHandle") -> Dict[str, str]:
        """Extract common element attributes."""
        attributes = {}
        attr_names = ["id", "class", "name", "type", "value", "href", "src", "data-testid", "aria-label"]

        for attr_name in attr_names:
            value = await element.get_attribute(attr_name)
            if value:
                attributes[attr_name] = value

        return attributes

    async def _extract_position_async(self, element: "ElementHandle") -> Position:
        """Extract element position and size."""
        try:
            bounding_box = await element.bounding_box()
            if bounding_box:
                return Position(
                    x=int(bounding_box['x']),
                    y=int(bounding_box['y']),
                    width=int(bounding_box['width']),
                    height=int(bounding_box['height'])
                )
        except Exception:
            pass

        return Position(x=0, y=0, width=0, height=0)

    async def _extract_parent_container_async(self, element: "ElementHandle") -> str:
        """Extract parent container information."""
        try:
            parent_info = await element.evaluate("""
                el => {
                    const parent = el.parentElement;
                    if (!parent) return 'unknown';
                    const tag = parent.tagName.toLowerCase();
                    const id = parent.id ? '#' + parent.id : '';
                    const cls = parent.className ? '.' + parent.className.split(' ')[0] : '';
                    return tag + cls + id;
                }
            """)
            return parent_info
        except Exception:
            return "unknown"

    async def _extract_siblings_async(self, element: "ElementHandle") -> List[str]:
        """Extract sibling element information (limited to 5)."""
        try:
            siblings = await element.evaluate("""
                el => {
                    const parent = el.parentElement;
                    if (!parent) return [];
                    return Array.from(parent.children)
                        .slice(0, 5)
                        .map(child => child.tagName.toLowerCase());
                }
            """)
            return siblings
        except Exception:
            return []

    async def _extract_computed_styles_async(self, element: "ElementHandle") -> Dict[str, str]:
        """Extract computed CSS styles."""
        try:
            styles = await element.evaluate("""
                el => {
                    const computed = window.getComputedStyle(el);
                    return {
                        display: computed.display,
                        visibility: computed.visibility,
                        position: computed.position,
                        'z-index': computed.zIndex,
                        'background-color': computed.backgroundColor,
                        color: computed.color
                    };
                }
            """)
            # Filter out None/null values
            return {k: v for k, v in styles.items() if v}
        except Exception:
            return {}

    async def _generate_visual_hash_async(self, element: "ElementHandle") -> str:
        """Generate a visual hash based on element properties."""
        try:
            hash_data = await element.evaluate("""
                el => {
                    const rect = el.getBoundingClientRect();
                    return el.tagName + el.textContent +
                           rect.width + 'x' + rect.height +
                           '@' + rect.x + ',' + rect.y;
                }
            """)
            return hashlib.md5(hash_data.encode()).hexdigest()[:8]
        except Exception:
            return "unknown"

    def shutdown(self):
        """
        Shutdown the adapter and cleanup resources.

        This method is called when the adapter is no longer needed.
        """
        logger.info("PlaywrightWebAutomationAdapter shutdown completed")
