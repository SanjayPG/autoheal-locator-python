"""
Selenium WebDriver adapter implementation.

This module provides the Selenium adapter for the AutoHeal locator system,
allowing it to work with Selenium WebDriver for web automation.
"""

import asyncio
import hashlib
import logging
from typing import List, Union, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver
    from selenium.webdriver.remote.webelement import WebElement
    from selenium.webdriver.common.by import By

from autoheal.core.web_automation_adapter import WebAutomationAdapter
from autoheal.models.enums import AutomationFramework
from autoheal.models.element_context import ElementContext
from autoheal.models.element_fingerprint import ElementFingerprint
from autoheal.models.position import Position
from autoheal.utils import locator_type_detector
from autoheal.exception.exceptions import AdapterException

logger = logging.getLogger(__name__)


class SeleniumWebAutomationAdapter(WebAutomationAdapter):
    """
    Selenium WebDriver adapter for the AutoHeal locator system.

    This adapter provides a bridge between the AutoHeal framework and Selenium
    WebDriver, enabling element finding, screenshot capture, and context extraction.

    Attributes:
        driver: Selenium WebDriver instance.

    Examples:
        >>> from selenium import webdriver
        >>> driver = webdriver.Chrome()
        >>> adapter = SeleniumWebAutomationAdapter(driver)
        >>> elements = await adapter.find_elements("#submit-button")
        >>> page_source = await adapter.get_page_source()
        >>> screenshot = await adapter.take_screenshot()
    """

    def __init__(self, driver: "WebDriver"):
        """
        Initialize the Selenium adapter.

        Args:
            driver: Selenium WebDriver instance.
        """
        self.driver = driver
        logger.info("SeleniumWebAutomationAdapter initialized")

    def get_framework_type(self) -> AutomationFramework:
        """
        Get the automation framework type.

        Returns:
            AutomationFramework.SELENIUM
        """
        return AutomationFramework.SELENIUM

    async def find_elements(
        self,
        selector: Union[str, "By"]
    ) -> List["WebElement"]:
        """
        Find elements using the given selector.

        Args:
            selector: CSS selector, XPath, or Selenium By locator object.

        Returns:
            List of matching WebElements (may be empty if none found).

        Raises:
            AdapterException: If the adapter encounters an error.
        """
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            elements = await loop.run_in_executor(
                None,
                self._find_elements_sync,
                selector
            )
            logger.debug("Found %d elements for selector: %s", len(elements), selector)
            return elements
        except Exception as e:
            logger.error("Failed to find elements with selector: %s", selector, exc_info=True)
            raise AdapterException(f"Failed to find elements with selector: {selector}") from e

    def _find_elements_sync(self, selector: Union[str, "By"]) -> List["WebElement"]:
        """
        Synchronous helper to find elements.

        Args:
            selector: CSS selector, XPath, or Selenium By locator object.

        Returns:
            List of matching WebElements.
        """
        from selenium.webdriver.common.by import By

        if isinstance(selector, str):
            # Auto-detect locator type and create By tuple
            by_locator = locator_type_detector.auto_create_by(selector)
            return self.driver.find_elements(by_locator[0], by_locator[1])
        elif isinstance(selector, By):
            # Direct By object
            return self.driver.find_elements(selector)
        else:
            # Assume it's a tuple (By, value)
            return self.driver.find_elements(selector[0], selector[1])

    async def find_elements_quick(
        self,
        selector: Union[str, "By"]
    ) -> List["WebElement"]:
        """
        Find elements with zero implicit wait (quick check).

        Temporarily sets implicit wait to 0, finds elements, then restores
        the original implicit wait. Use this for quick checks where you don't
        want to wait for the full implicit wait timeout.

        Args:
            selector: CSS selector, XPath, or Selenium By locator object.

        Returns:
            List of matching WebElements (may be empty if none found).
        """
        try:
            loop = asyncio.get_event_loop()
            elements = await loop.run_in_executor(
                None,
                self._find_elements_quick_sync,
                selector
            )
            logger.debug("Quick check found %d elements for selector: %s", len(elements), selector)
            return elements
        except Exception as e:
            logger.debug("Quick check failed for selector: %s - %s", selector, str(e))
            return []

    def _find_elements_quick_sync(self, selector: Union[str, "By"]) -> List["WebElement"]:
        """
        Synchronous helper for quick element finding with zero implicit wait.
        """
        from selenium.webdriver.common.by import By

        # Store original implicit wait and set to 0
        # Note: Selenium doesn't have a getter for implicit wait, so we set to 0 and restore later
        self.driver.implicitly_wait(0)

        try:
            if isinstance(selector, str):
                by_locator = locator_type_detector.auto_create_by(selector)
                return self.driver.find_elements(by_locator[0], by_locator[1])
            elif isinstance(selector, By):
                return self.driver.find_elements(selector)
            else:
                return self.driver.find_elements(selector[0], selector[1])
        finally:
            # Restore implicit wait (default 10 seconds, configurable)
            # This is a limitation - we can't know the original value
            # Users should configure via AUTOHEAL_IMPLICIT_WAIT_SEC env var
            import os
            implicit_wait = int(os.getenv("AUTOHEAL_IMPLICIT_WAIT_SEC", "10"))
            self.driver.implicitly_wait(implicit_wait)

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
            loop = asyncio.get_event_loop()
            if include_shadow_dom:
                page_source = await loop.run_in_executor(
                    None,
                    self._get_page_source_with_shadow_dom_sync
                )
            else:
                page_source = await loop.run_in_executor(
                    None,
                    lambda: self.driver.page_source
                )
            logger.debug("Retrieved page source (length: %d characters)", len(page_source))
            return page_source
        except Exception as e:
            logger.error("Failed to get page source", exc_info=True)
            raise AdapterException("Failed to get page source") from e

    def _get_page_source_with_shadow_dom_sync(self) -> str:
        """
        Extract page source including shadow DOM content (synchronous).

        Uses JavaScript to recursively traverse the DOM and serialize
        shadow root contents with special markers for AI analysis.

        Returns:
            HTML string with shadow DOM content included.
        """
        try:
            # Check if driver supports JavaScript execution
            if not hasattr(self.driver, 'execute_script'):
                logger.warning("Driver does not support JavaScript, returning regular page source")
                return self.driver.page_source

            # JavaScript to recursively extract DOM including shadow roots
            shadow_dom_script = """
            function serializeNode(node, depth) {
                depth = depth || 0;
                if (!node) return '';

                // Handle text nodes
                if (node.nodeType === Node.TEXT_NODE) {
                    return node.textContent;
                }

                // Handle element nodes
                if (node.nodeType !== Node.ELEMENT_NODE) {
                    return '';
                }

                var element = node;
                var tagName = element.tagName.toLowerCase();

                // Build opening tag with attributes
                var html = '<' + tagName;
                for (var i = 0; i < element.attributes.length; i++) {
                    var attr = element.attributes[i];
                    html += ' ' + attr.name + '="' + attr.value.replace(/"/g, '&quot;') + '"';
                }
                html += '>';

                // Check for shadow root and serialize it
                if (element.shadowRoot) {
                    html += '<!-- shadow-root mode="' + (element.shadowRoot.mode || 'open') + '" -->';
                    var shadowChildren = element.shadowRoot.childNodes;
                    for (var j = 0; j < shadowChildren.length; j++) {
                        html += serializeNode(shadowChildren[j], depth + 1);
                    }
                    html += '<!-- /shadow-root -->';
                }

                // Serialize light DOM children
                var children = element.childNodes;
                for (var k = 0; k < children.length; k++) {
                    html += serializeNode(children[k], depth + 1);
                }

                // Self-closing tags
                var selfClosing = ['area', 'base', 'br', 'col', 'embed', 'hr', 'img',
                                   'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'];
                if (selfClosing.indexOf(tagName) === -1) {
                    html += '</' + tagName + '>';
                }

                return html;
            }

            // Start serialization from documentElement (includes <html>)
            var doctype = document.doctype
                ? '<!DOCTYPE ' + document.doctype.name + '>'
                : '<!DOCTYPE html>';
            return doctype + serializeNode(document.documentElement);
            """

            page_source = self.driver.execute_script(shadow_dom_script)

            if page_source:
                logger.debug(
                    "Retrieved page source with shadow DOM (length: %d characters)",
                    len(page_source)
                )
                return page_source
            else:
                # Fallback to regular page_source if execution fails
                logger.warning("Shadow DOM extraction returned empty, falling back to regular page source")
                return self.driver.page_source

        except Exception as e:
            logger.warning(
                "Failed to extract shadow DOM, falling back to regular page source: %s",
                str(e)
            )
            # Fallback to regular page_source on any error
            return self.driver.page_source

    async def take_screenshot(self) -> bytes:
        """
        Take a screenshot of the current page.

        Returns:
            Screenshot as bytes (PNG format).

        Raises:
            AdapterException: If the adapter cannot take a screenshot.
        """
        try:
            loop = asyncio.get_event_loop()
            screenshot = await loop.run_in_executor(
                None,
                self._take_screenshot_sync
            )
            logger.debug("Screenshot taken (size: %d bytes)", len(screenshot))
            return screenshot
        except Exception as e:
            logger.error("Failed to take screenshot", exc_info=True)
            raise AdapterException("Failed to take screenshot") from e

    def _take_screenshot_sync(self) -> bytes:
        """
        Synchronous helper to take screenshot.

        Returns:
            Screenshot as bytes.

        Raises:
            Exception: If driver doesn't support screenshots.
        """
        from selenium.webdriver.common.actions.action_builder import ActionBuilder

        # Check if driver supports screenshots
        if not hasattr(self.driver, 'get_screenshot_as_png'):
            raise Exception("Driver does not support screenshots")

        return self.driver.get_screenshot_as_png()

    async def get_element_context(self, element: "WebElement") -> ElementContext:
        """
        Extract contextual information about an element.

        Args:
            element: The element to analyze.

        Returns:
            ElementContext containing detailed information about the element.

        Raises:
            AdapterException: If the adapter cannot extract element context.
        """
        try:
            loop = asyncio.get_event_loop()
            context = await loop.run_in_executor(
                None,
                self._get_element_context_sync,
                element
            )
            logger.debug("Extracted context for element: %s", element.tag_name)
            return context
        except Exception as e:
            logger.error("Failed to extract element context", exc_info=True)
            raise AdapterException("Failed to extract element context") from e

    def _get_element_context_sync(self, element: "WebElement") -> ElementContext:
        """
        Synchronous helper to extract element context.

        Args:
            element: The element to analyze.

        Returns:
            ElementContext with element details.
        """
        # Extract element context information
        parent_container = self._extract_parent_container(element)
        position = self._extract_position(element)
        siblings = self._extract_sibling_elements(element)
        attributes = self._extract_attributes(element)
        text_content = self._get_element_text(element)

        # Create fingerprint
        fingerprint = ElementFingerprint(
            parent_container=parent_container,
            position=position,
            computed_styles=self._extract_computed_styles(element),
            text_content=text_content,
            sibling_elements=siblings,
            visual_hash=self._generate_visual_hash(element)
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

    # Private helper methods

    def _extract_parent_container(self, element: "WebElement") -> str:
        """
        Extract parent container information.

        Args:
            element: The element whose parent to extract.

        Returns:
            Parent container identifier string.
        """
        try:
            from selenium.webdriver.common.by import By

            parent = element.find_element(By.XPATH, "..")
            class_name = parent.get_attribute("class")
            elem_id = parent.get_attribute("id")

            result = parent.tag_name
            if class_name:
                result += "." + class_name.split(" ")[0]
            if elem_id:
                result += "#" + elem_id

            return result
        except Exception:
            return "unknown"

    def _extract_position(self, element: "WebElement") -> Position:
        """
        Extract element position and size.

        Args:
            element: The element to analyze.

        Returns:
            Position with x, y, width, height.
        """
        try:
            rect = element.rect
            return Position(
                x=rect['x'],
                y=rect['y'],
                width=rect['width'],
                height=rect['height']
            )
        except Exception:
            return Position(x=0, y=0, width=0, height=0)

    def _extract_sibling_elements(self, element: "WebElement") -> List[str]:
        """
        Extract sibling element information.

        Args:
            element: The element whose siblings to extract.

        Returns:
            List of sibling element tag names (limited to 5).
        """
        try:
            from selenium.webdriver.common.by import By

            siblings = element.find_elements(By.XPATH, "..//*")
            return [sibling.tag_name for sibling in siblings[:5]]
        except Exception:
            return []

    def _extract_attributes(self, element: "WebElement") -> Dict[str, str]:
        """
        Extract common element attributes.

        Args:
            element: The element to analyze.

        Returns:
            Dictionary of attribute name-value pairs.
        """
        attributes = {}
        try:
            # Common attributes to extract
            attr_names = ["id", "class", "name", "type", "value", "href", "src", "data-testid", "aria-label"]

            for attr_name in attr_names:
                value = element.get_attribute(attr_name)
                if value:
                    attributes[attr_name] = value
        except Exception:
            # Ignore extraction errors
            pass

        return attributes

    def _extract_computed_styles(self, element: "WebElement") -> Dict[str, str]:
        """
        Extract computed CSS styles using JavaScript.

        Args:
            element: The element to analyze.

        Returns:
            Dictionary of CSS property-value pairs.
        """
        styles = {}
        try:
            # Check if driver supports JavaScript execution
            if not hasattr(self.driver, 'execute_script'):
                return styles

            # Extract key CSS properties
            properties = ["display", "visibility", "position", "z-index", "background-color", "color"]

            for prop in properties:
                value = self.driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).getPropertyValue(arguments[1]);",
                    element,
                    prop
                )
                if value:
                    styles[prop] = value
        except Exception:
            # Ignore style extraction errors
            pass

        return styles

    def _generate_visual_hash(self, element: "WebElement") -> str:
        """
        Generate a visual hash based on element properties.

        Args:
            element: The element to hash.

        Returns:
            Hash string representing visual characteristics.
        """
        try:
            # Build hash from element properties
            hash_components = [
                element.tag_name,
                self._get_element_text(element),
                str(element.size),
                str(element.location)
            ]

            hash_string = "".join(hash_components)
            return hashlib.md5(hash_string.encode()).hexdigest()[:8]
        except Exception:
            return "unknown"

    def _get_element_text(self, element: "WebElement") -> str:
        """
        Get element text content, handling exceptions.

        Args:
            element: The element.

        Returns:
            Text content or empty string.
        """
        try:
            return element.text or ""
        except Exception:
            return ""

    def shutdown(self):
        """
        Shutdown the adapter and cleanup resources.

        This method is called when the adapter is no longer needed.
        """
        logger.info("SeleniumWebAutomationAdapter shutdown completed")
