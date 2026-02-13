"""
WebAutomationAdapter interface for web automation frameworks.

This module defines the abstract interface that adapts different web automation
frameworks (Selenium, Playwright) to work with the AutoHeal locator system.
"""

from abc import ABC, abstractmethod
from typing import List, Union
import sys

# Type imports for documentation
if sys.version_info >= (3, 11):
    from typing import TYPE_CHECKING
else:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.remote.webelement import WebElement

from autoheal.models.enums import AutomationFramework


class WebAutomationAdapter(ABC):
    """
    Adapter interface for web automation frameworks.

    This interface provides a unified abstraction over different web automation
    frameworks, allowing the AutoHeal locator system to work with both Selenium
    and Playwright.
    """

    @abstractmethod
    def get_framework_type(self) -> AutomationFramework:
        """
        Get the automation framework type of this adapter.

        Returns:
            The automation framework type (SELENIUM or PLAYWRIGHT)
        """
        pass

    @abstractmethod
    async def find_elements(
        self,
        selector: Union[str, "By"],
    ) -> List["WebElement"]:
        """
        Find elements using the given selector.

        This method accepts either a string selector (CSS, XPath, etc.) or
        a Selenium By object.

        Args:
            selector: CSS selector, XPath, or Selenium By locator object

        Returns:
            List of matching WebElements (may be empty if none found)

        Raises:
            AdapterException: If the adapter encounters an error
        """
        pass

    @abstractmethod
    async def get_page_source(self, include_shadow_dom: bool = True) -> str:
        """
        Get the current page source, optionally including shadow DOM content.

        Args:
            include_shadow_dom: If True, extracts and includes shadow DOM content
                               within special comment markers. Defaults to True
                               for better AI healing support.

        Returns:
            HTML page source as a string. When include_shadow_dom is True,
            shadow root content is included with markers like:
            <!-- shadow-root mode="open" -->...<!-- /shadow-root -->

        Raises:
            AdapterException: If the adapter cannot retrieve page source
        """
        pass

    @abstractmethod
    async def take_screenshot(self) -> bytes:
        """
        Take a screenshot of the current page.

        Returns:
            Screenshot as bytes (typically PNG format)

        Raises:
            AdapterException: If the adapter cannot take a screenshot
        """
        pass

    @abstractmethod
    async def get_element_context(self, element: "WebElement") -> "ElementContext":
        """
        Extract contextual information about an element.

        This method retrieves information about the element's position, visibility,
        attributes, and surrounding context to help with element identification.

        Args:
            element: The element to analyze

        Returns:
            ElementContext containing detailed information about the element

        Raises:
            AdapterException: If the adapter cannot extract element context
        """
        pass


# Import at end to avoid circular dependencies
from autoheal.models.element_context import ElementContext  # noqa: E402
