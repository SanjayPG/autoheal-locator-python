"""
Main AutoHeal Locator facade providing enterprise-grade element location.

This module provides the AutoHealLocator class, the main entry point for
the AutoHeal framework. It orchestrates all components including caching,
AI healing, metrics tracking, and element location strategies.
"""

import asyncio
import logging
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from selenium.webdriver.remote.webelement import WebElement

from autoheal.config.autoheal_config import AutoHealConfiguration
from autoheal.config.cache_config import CacheConfig, CacheType as ConfigCacheType
from autoheal.config.locator_options import LocatorOptions
from autoheal.core.web_automation_adapter import WebAutomationAdapter
from autoheal.core.selector_cache import SelectorCache
from autoheal.core.ai_service import AIService
from autoheal.core.element_locator import ElementLocator
from autoheal.impl.ai.resilient_ai_service import ResilientAIService
from autoheal.impl.cache.cachetools_selector_cache import CachetoolsSelectorCache
# Lazy imports for optional cache backends
# from autoheal.impl.cache.redis_selector_cache import RedisSelectorCache
# from autoheal.impl.cache.file_selector_cache import FileSelectorCache
from autoheal.impl.locator.dom_element_locator import DOMElementLocator
from autoheal.impl.locator.visual_element_locator import VisualElementLocator
from autoheal.impl.locator.cost_optimized_hybrid_element_locator import CostOptimizedHybridElementLocator
from autoheal.models.locator_request import LocatorRequest
from autoheal.models.locator_result import LocatorResult
from autoheal.models.disambiguation_result import DisambiguationResult
from autoheal.models.enums import LocatorStrategy, CacheType, LocatorType
from autoheal.models.cached_selector import CachedSelector
from autoheal.metrics.locator_metrics import LocatorMetrics
from autoheal.metrics.cache_metrics import CacheMetrics
from autoheal.exception.exceptions import (
    AutoHealException,
    ElementNotFoundException,
    ConfigurationException
)
from autoheal.utils import locator_type_detector
from autoheal.utils.playwright_locator_converter import PlaywrightLocatorConverter

logger = logging.getLogger(__name__)


class AutoHealLocator:
    """
    Main AutoHeal Locator facade providing enterprise-grade element location.

    This class is the main entry point for the AutoHeal framework. It provides:
    - Auto-healing element location with AI assistance
    - Intelligent caching with multiple backend options
    - Both synchronous and asynchronous APIs
    - Performance metrics and health monitoring
    - Cost-optimized execution strategies

    The healing process follows this sequence:
    1. Try the original selector (fastest, no cost)
    2. Check cache for previously healed selector
    3. Use AI to heal the selector (DOM or Visual analysis)
    4. Cache successful results for future use

    Examples:
        >>> # Basic usage with builder
        >>> from autoheal import AutoHealLocator
        >>> from autoheal.impl.adapter import SeleniumWebAutomationAdapter
        >>> from selenium import webdriver
        >>>
        >>> driver = webdriver.Chrome()
        >>> adapter = SeleniumWebAutomationAdapter(driver)
        >>>
        >>> locator = AutoHealLocator.builder() \\
        ...     .with_web_adapter(adapter) \\
        ...     .build()
        >>>
        >>> # Find element with auto-healing
        >>> element = await locator.find_element_async(
        ...     "#login-button",
        ...     "Login button on homepage"
        ... )
        >>>
        >>> # Synchronous API
        >>> element = locator.find_element("#login-button", "Login button")
        >>>
        >>> # Check metrics
        >>> metrics = locator.get_metrics()
        >>> print(f"Success rate: {metrics.get_success_rate():.2%}")
        >>>
        >>> # Cleanup
        >>> await locator.shutdown()
    """

    def __init__(
        self,
        adapter: WebAutomationAdapter,
        configuration: AutoHealConfiguration,
        selector_cache: SelectorCache,
        ai_service: AIService
    ):
        """
        Initialize AutoHealLocator (use builder() instead).

        Args:
            adapter: Web automation adapter (Selenium/Playwright).
            configuration: AutoHeal configuration.
            selector_cache: Selector cache implementation.
            ai_service: AI service for healing.
        """
        self.adapter = adapter
        self.configuration = configuration
        self.selector_cache = selector_cache
        self.ai_service = ai_service
        self.metrics = LocatorMetrics()

        # Initialize element locators with cost optimization
        locators = [
            DOMElementLocator(ai_service),
            VisualElementLocator(ai_service)
        ]
        self.element_locator = CostOptimizedHybridElementLocator(
            locators,
            configuration.performance_config.execution_strategy
        )

        logger.info("AutoHealLocator initialized successfully")

    @staticmethod
    def builder():
        """
        Create a new Builder instance.

        Returns:
            Builder instance for fluent configuration.
        """
        return AutoHealLocator.Builder()

    class Builder:
        """
        Builder for fluent AutoHealLocator configuration.

        Examples:
            >>> locator = AutoHealLocator.builder() \\
            ...     .with_web_adapter(adapter) \\
            ...     .with_configuration(config) \\
            ...     .with_cache(custom_cache) \\
            ...     .with_ai_service(custom_ai) \\
            ...     .build()
        """

        def __init__(self):
            """Initialize builder with defaults."""
            self._adapter: Optional[WebAutomationAdapter] = None
            self._configuration: Optional[AutoHealConfiguration] = None
            self._custom_cache: Optional[SelectorCache] = None
            self._custom_ai_service: Optional[AIService] = None

        def with_web_adapter(self, adapter: WebAutomationAdapter) -> "AutoHealLocator.Builder":
            """
            Set the web automation adapter.

            Args:
                adapter: Selenium or Playwright adapter.

            Returns:
                Builder instance for chaining.
            """
            self._adapter = adapter
            return self

        def with_configuration(self, configuration: AutoHealConfiguration) -> "AutoHealLocator.Builder":
            """
            Set the AutoHeal configuration.

            Args:
                configuration: Configuration instance.

            Returns:
                Builder instance for chaining.
            """
            self._configuration = configuration
            return self

        def with_cache(self, cache: SelectorCache) -> "AutoHealLocator.Builder":
            """
            Set a custom cache implementation.

            Args:
                cache: Custom selector cache.

            Returns:
                Builder instance for chaining.
            """
            self._custom_cache = cache
            return self

        def with_ai_service(self, ai_service: AIService) -> "AutoHealLocator.Builder":
            """
            Set a custom AI service.

            Args:
                ai_service: Custom AI service implementation.

            Returns:
                Builder instance for chaining.
            """
            self._custom_ai_service = ai_service
            return self

        def build(self) -> "AutoHealLocator":
            """
            Build the AutoHealLocator instance.

            Returns:
                Configured AutoHealLocator instance.

            Raises:
                ConfigurationException: If required configuration is missing.
            """
            if self._adapter is None:
                raise ConfigurationException("WebAutomationAdapter is required")

            # Lazy initialization of configuration if not set
            configuration = self._configuration
            if configuration is None:
                configuration = AutoHealConfiguration.builder().build()

            # Initialize cache
            cache = self._custom_cache
            if cache is None:
                cache = _create_cache_based_on_config(configuration.cache_config)

            # Initialize AI service
            ai_service = self._custom_ai_service
            if ai_service is None:
                ai_service = ResilientAIService(configuration.ai_config, configuration.resilience_config)

            return AutoHealLocator(self._adapter, configuration, cache, ai_service)

    # ==================== PUBLIC API METHODS ====================

    async def find_element_async(
        self,
        selector: str,
        description: str,
        options: Optional[LocatorOptions] = None
    ) -> "WebElement":
        """
        Find element with auto-healing capabilities (async).

        Args:
            selector: CSS selector, XPath, or other locator.
            description: Human-readable description for AI healing.
            options: Optional locator options (uses defaults if not provided).

        Returns:
            Found WebElement.

        Raises:
            ElementNotFoundException: If element cannot be found.
            AutoHealException: For other errors.
        """
        if options is None:
            options = LocatorOptions.default_options()

        # Auto-detect locator type
        detected_type = locator_type_detector.detect_type(selector)
        by_tuple = locator_type_detector.create_by(selector, detected_type)

        logger.debug("Auto-detected '%s' as %s locator", selector, detected_type.name)

        # Build request
        request = LocatorRequest.builder() \
            .original_selector(selector) \
            .description(description) \
            .options(options) \
            .adapter(self.adapter) \
            .locator_type(detected_type) \
            .build()

        # Locate with healing
        try:
            result = await self._locate_element_with_healing(request)
            self.metrics.record_request(success=True)
            return result.element
        except Exception:
            self.metrics.record_request(success=False)
            raise

    async def find_element_async_with_result(
        self,
        selector: str,
        description: str,
        options: Optional[LocatorOptions] = None
    ) -> LocatorResult:
        """
        Find element with auto-healing and return the full LocatorResult.

        Same as find_element_async but returns LocatorResult containing the
        element, actual selector, strategy used, cache status, and timing.

        Args:
            selector: CSS selector, XPath, or other locator.
            description: Human-readable description for AI healing.
            options: Optional locator options (uses defaults if not provided).

        Returns:
            LocatorResult with element, strategy, actual_selector, from_cache, etc.
        """
        if options is None:
            options = LocatorOptions.default_options()

        detected_type = locator_type_detector.detect_type(selector)
        locator_type_detector.create_by(selector, detected_type)

        request = LocatorRequest.builder() \
            .original_selector(selector) \
            .description(description) \
            .options(options) \
            .adapter(self.adapter) \
            .locator_type(detected_type) \
            .build()

        try:
            result = await self._locate_element_with_healing(request)
            self.metrics.record_request(success=True)
            return result
        except Exception:
            self.metrics.record_request(success=False)
            raise

    def find_element(
        self,
        selector: str,
        description: str,
        options: Optional[LocatorOptions] = None
    ) -> "WebElement":
        """
        Find element with auto-healing capabilities (sync).

        Args:
            selector: CSS selector, XPath, or other locator.
            description: Human-readable description for AI healing.
            options: Optional locator options (uses defaults if not provided).

        Returns:
            Found WebElement.

        Raises:
            ElementNotFoundException: If element cannot be found.
            AutoHealException: For other errors.
        """
        return asyncio.run(self.find_element_async(selector, description, options))

    def find_element_with_result(
        self,
        selector: str,
        description: str,
        options: Optional[LocatorOptions] = None
    ) -> LocatorResult:
        """
        Find element with auto-healing and return the full LocatorResult (sync).

        Same as find_element but returns LocatorResult containing the
        element, actual selector, strategy used, cache status, and timing.

        Args:
            selector: CSS selector, XPath, or other locator.
            description: Human-readable description for AI healing.
            options: Optional locator options (uses defaults if not provided).

        Returns:
            LocatorResult with element, strategy, actual_selector, from_cache, etc.
        """
        return asyncio.run(self.find_element_async_with_result(selector, description, options))

    async def find_elements_async(
        self,
        selector: str,
        description: str,
        options: Optional[LocatorOptions] = None
    ) -> List["WebElement"]:
        """
        Find multiple elements with healing (async).

        Args:
            selector: CSS selector, XPath, or other locator.
            description: Human-readable description.
            options: Optional locator options.

        Returns:
            List of found WebElements.

        Raises:
            ElementNotFoundException: If no elements can be found.
        """
        # Find first element to ensure selector works
        first_element = await self.find_element_async(selector, description, options)

        # Get the last successful selector from cache or use original
        successful_selector = self._get_last_successful_selector(selector, description)
        by_tuple = locator_type_detector.auto_create_by(successful_selector)

        # Find all elements with successful selector
        try:
            elements = await self.adapter.find_elements(by_tuple)
            return elements if elements else [first_element]
        except Exception:
            return [first_element]

    def find_elements(
        self,
        selector: str,
        description: str,
        options: Optional[LocatorOptions] = None
    ) -> List["WebElement"]:
        """
        Find multiple elements with healing (sync).

        Args:
            selector: CSS selector, XPath, or other locator.
            description: Human-readable description.
            options: Optional locator options.

        Returns:
            List of found WebElements.

        Raises:
            ElementNotFoundException: If no elements can be found.
        """
        return asyncio.run(self.find_elements_async(selector, description, options))

    async def is_element_present_async(
        self,
        selector: str,
        description: str,
        options: Optional[LocatorOptions] = None
    ) -> bool:
        """
        Check if element is present without throwing exceptions (async).

        Args:
            selector: CSS selector, XPath, or other locator.
            description: Human-readable description.
            options: Optional locator options.

        Returns:
            True if element is present, False otherwise.
        """
        try:
            elements = await self.adapter.find_elements(selector)
            return len(elements) > 0
        except Exception:
            return False

    def is_element_present(
        self,
        selector: str,
        description: str,
        options: Optional[LocatorOptions] = None
    ) -> bool:
        """
        Check if element is present without throwing exceptions (sync).

        Args:
            selector: CSS selector, XPath, or other locator.
            description: Human-readable description.
            options: Optional locator options.

        Returns:
            True if element is present, False otherwise.
        """
        return asyncio.run(self.is_element_present_async(selector, description, options))

    # ==================== NATIVE PLAYWRIGHT LOCATOR API ====================

    async def find_async(
        self,
        playwright_locator,
        description: str,
        options: Optional[LocatorOptions] = None
    ):
        """
        Find element using a native Playwright Locator with auto-healing.

        Accepts a native Playwright Locator object (e.g., page.get_by_role(),
        page.get_by_label()) and returns a native Playwright Locator. If the
        original locator fails, AI healing is used to find a working alternative.

        Args:
            playwright_locator: Native Playwright Locator object.
            description: Human-readable description for AI healing.
            options: Optional locator options (uses defaults if not provided).

        Returns:
            Native Playwright Locator that resolves to the target element.

        Raises:
            ElementNotFoundException: If element cannot be found.
            AutoHealException: For other errors.

        Examples:
            >>> button = await locator.find_async(
            ...     page.get_by_role("button", name="Submit"),
            ...     "Submit button"
            ... )
            >>> await button.click()
        """
        if options is None:
            options = LocatorOptions.default_options()

        result = await self._locate_with_native_locator_healing(
            playwright_locator, description, options
        )
        return result.element

    async def find_async_with_result(
        self,
        playwright_locator,
        description: str,
        options: Optional[LocatorOptions] = None
    ) -> LocatorResult:
        """
        Find element using a native Playwright Locator and return the full LocatorResult.

        Same as find_async but returns LocatorResult containing the locator,
        actual selector, strategy used, cache status, and timing.

        Args:
            playwright_locator: Native Playwright Locator object.
            description: Human-readable description for AI healing.
            options: Optional locator options (uses defaults if not provided).

        Returns:
            LocatorResult with element, strategy, actual_selector, from_cache, etc.
        """
        if options is None:
            options = LocatorOptions.default_options()

        return await self._locate_with_native_locator_healing(
            playwright_locator, description, options
        )

    def find(
        self,
        playwright_locator,
        description: str,
        options: Optional[LocatorOptions] = None
    ):
        """
        Find element using a native Playwright Locator with auto-healing (sync).

        Synchronous version of find_async(). See find_async() for details.

        Args:
            playwright_locator: Native Playwright Locator object.
            description: Human-readable description for AI healing.
            options: Optional locator options (uses defaults if not provided).

        Returns:
            Native Playwright Locator that resolves to the target element.

        Raises:
            ElementNotFoundException: If element cannot be found.
            AutoHealException: For other errors.
        """
        return asyncio.run(self.find_async(playwright_locator, description, options))

    async def _locate_with_native_locator_healing(
        self,
        native_locator,
        description: str,
        options: LocatorOptions
    ) -> LocatorResult:
        """
        Core healing logic for native Playwright Locators.

        Flow: try original locator -> check cache -> AI healing.

        Args:
            native_locator: Native Playwright Locator object.
            description: Human-readable description.
            options: Locator options.

        Returns:
            LocatorResult with the native Playwright Locator as element.

        Raises:
            ElementNotFoundException: If all strategies fail.
        """
        start_time = datetime.now()

        # Extract selector info for cache keys and healing
        locator_info = PlaywrightLocatorConverter.extract_selector_info(native_locator)
        readable_selector = locator_info.readable_selector

        logger.debug(
            "find_async called with native locator: %s", readable_selector
        )

        # Step 1: Try the original native locator directly
        original_count = 0
        try:
            original_count = await native_locator.count()
            if original_count == 1:
                logger.info("Original native locator worked: %s", readable_selector)

                # Cache the readable selector
                if options.enable_caching:
                    cache_key = f"{readable_selector}|{description}"
                    cached_selector = CachedSelector(
                        selector=readable_selector,
                        fingerprint=None,
                    )
                    self.selector_cache.put(cache_key, cached_selector)

                return LocatorResult.builder() \
                    .element(native_locator) \
                    .actual_selector(readable_selector) \
                    .strategy(LocatorStrategy.ORIGINAL_SELECTOR) \
                    .from_cache(False) \
                    .execution_time(datetime.now() - start_time) \
                    .reasoning("Original native locator worked") \
                    .build()
            elif original_count > 1:
                logger.info(
                    "Original native locator matched %d elements (strict mode violation): %s "
                    "- checking cache before AI disambiguation",
                    original_count, readable_selector
                )
        except Exception as e:
            logger.debug(
                "Original native locator failed: %s - %s",
                readable_selector, str(e)
            )

        # Step 2: Check cache for a previously healed/disambiguated selector
        if options.enable_caching:
            cache_key = f"{readable_selector}|{description}"
            cached = self.selector_cache.get(cache_key)

            if cached and cached.current_success_rate > 0.7:
                healed_locator = self._create_locator_from_healed_selector(
                    cached.selector
                )
                if healed_locator is not None:
                    try:
                        count = await healed_locator.count()
                        if count == 1:
                            self.selector_cache.update_success(cache_key, True)
                            logger.info(
                                "Cache hit for native locator: %s -> %s",
                                readable_selector, cached.selector
                            )
                            return LocatorResult.builder() \
                                .element(healed_locator) \
                                .actual_selector(cached.selector) \
                                .strategy(LocatorStrategy.CACHED) \
                                .from_cache(True) \
                                .execution_time(datetime.now() - start_time) \
                                .reasoning("Retrieved from cache") \
                                .build()
                        else:
                            self.selector_cache.update_success(cache_key, False)
                            logger.warning(
                                "Cached Playwright locator no longer works "
                                "(found %d elements): %s",
                                count, cached.selector
                            )
                    except Exception:
                        self.selector_cache.update_success(cache_key, False)

        # Step 3: If original matched multiple elements and no cache hit, try disambiguation
        if original_count > 1:
            logger.info(
                "No cache hit, attempting AI disambiguation for %d elements: %s",
                original_count, readable_selector
            )
            disambiguated = await self._disambiguate_native_locator(
                native_locator, original_count, description, readable_selector, start_time, options
            )
            if disambiguated is not None:
                return disambiguated

            logger.debug(
                "Disambiguation failed, falling through to full AI healing"
            )

        # Step 4: Perform AI healing via the existing pipeline
        request = LocatorRequest.builder() \
            .original_selector(readable_selector) \
            .description(description) \
            .options(options) \
            .adapter(self.adapter) \
            .native_locator(native_locator) \
            .build()

        try:
            logger.info(
                "Performing AI healing for native locator: %s",
                readable_selector
            )
            result = await self.element_locator.locate(request)

            # Convert the healed result to a native Locator
            healed_locator = self._create_locator_from_healed_selector(
                result.actual_selector
            )
            if healed_locator is None:
                # Fallback: wrap via the adapter's page.locator()
                page = self.adapter.get_page()
                healed_locator = page.locator(result.actual_selector)

            # Validate healed locator: must match exactly 1 element (strict mode)
            healed_count = await healed_locator.count()
            if healed_count == 1:
                logger.info(
                    "Successfully healed native locator: %s -> %s",
                    readable_selector, result.actual_selector
                )

                # Cache the healed selector only after validation
                if options.enable_caching:
                    cache_key = f"{readable_selector}|{description}"
                    cached_selector = CachedSelector(
                        selector=result.actual_selector,
                        fingerprint=None,
                    )
                    self.selector_cache.put(cache_key, cached_selector)

                return LocatorResult.builder() \
                    .element(healed_locator) \
                    .actual_selector(result.actual_selector) \
                    .strategy(result.strategy or LocatorStrategy.DOM_ANALYSIS) \
                    .from_cache(False) \
                    .execution_time(datetime.now() - start_time) \
                    .reasoning(result.reasoning or "AI healing used") \
                    .tokens_used(getattr(result, 'tokens_used', 0)) \
                    .build()
            elif healed_count > 1:
                # Healed locator matches multiple elements - try disambiguation
                logger.info(
                    "Healed locator matched %d elements, attempting disambiguation: %s",
                    healed_count, result.actual_selector
                )
                disambiguated = await self._disambiguate_native_locator(
                    healed_locator, healed_count, description,
                    result.actual_selector, start_time, options
                )
                if disambiguated is not None:
                    return disambiguated

                logger.warning(
                    "Disambiguation failed for healed locator: %s",
                    result.actual_selector
                )
            else:
                logger.warning(
                    "Healed locator found no elements: %s",
                    result.actual_selector
                )

            raise ElementNotFoundException(
                f"Could not find element even after healing: {description}"
            )

        except ElementNotFoundException:
            raise
        except Exception as e:
            raise ElementNotFoundException(
                f"All healing strategies failed for native locator: {readable_selector}"
            ) from e

    def _create_locator_from_healed_selector(self, selector: str):
        """
        Create a native Playwright Locator from a healed selector string.

        Handles both CSS/XPath strings and PlaywrightLocator-style strings
        (e.g., 'page.get_by_role("button", name="Submit")').

        Args:
            selector: Healed selector string.

        Returns:
            Native Playwright Locator, or None if creation fails.
        """
        try:
            if not hasattr(self.adapter, 'get_page'):
                return None

            page = self.adapter.get_page()

            # Try to execute via adapter if it looks like a PlaywrightLocator
            if hasattr(self.adapter, 'execute_playwright_locator'):
                from autoheal.models.playwright_locator import PlaywrightLocator as PLModel
                from autoheal.models.playwright_locator import PlaywrightLocatorType

                # Check if the selector is a readable PlaywrightLocator string
                if 'get_by_' in selector or 'page.locator(' in selector:
                    return self._parse_and_execute_readable_selector(
                        page, selector
                    )

            # Default: treat as CSS or XPath
            if selector.startswith("//") or selector.startswith("xpath="):
                return page.locator(selector)
            return page.locator(selector)

        except Exception as e:
            logger.debug(
                "Could not create locator from healed selector: %s - %s",
                selector, str(e)
            )
            return None

    def _parse_and_execute_readable_selector(self, page, selector: str):
        """
        Parse a readable selector string and execute it on the page.

        Handles strings like:
        - 'page.get_by_role("button", name="Submit")'
        - 'page.get_by_role("button", name="Submit").nth(1)'
        Falls back to page.locator() if parsing fails.

        Args:
            page: Playwright Page object.
            selector: Readable selector string.

        Returns:
            Native Playwright Locator.
        """
        import re

        # Check for .nth() suffix and extract index
        nth_match = re.search(r'\.nth\((\d+)\)$', selector)
        nth_index = None
        base_selector = selector
        if nth_match:
            nth_index = int(nth_match.group(1))
            base_selector = selector[:nth_match.start()]

        # Parse the base selector
        locator = self._parse_base_selector(page, base_selector)

        # Apply .nth() if present
        if nth_index is not None:
            locator = locator.nth(nth_index)

        return locator

    def _parse_base_selector(self, page, selector: str):
        """
        Parse a base selector string (without .nth()) and execute it.

        Args:
            page: Playwright Page object.
            selector: Base selector string.

        Returns:
            Native Playwright Locator.
        """
        import re

        # page.get_by_role("button", name="Submit")
        role_match = re.match(
            r'page\.get_by_role\("(\w+)"(?:,\s*name="([^"]*)")?\)', selector
        )
        if role_match:
            role = role_match.group(1)
            name = role_match.group(2)
            if name:
                return page.get_by_role(role, name=name)
            return page.get_by_role(role)

        # page.get_by_label("...")
        label_match = re.match(r'page\.get_by_label\("([^"]*)"\)', selector)
        if label_match:
            return page.get_by_label(label_match.group(1))

        # page.get_by_placeholder("...")
        ph_match = re.match(r'page\.get_by_placeholder\("([^"]*)"\)', selector)
        if ph_match:
            return page.get_by_placeholder(ph_match.group(1))

        # page.get_by_text("...")
        text_match = re.match(r'page\.get_by_text\("([^"]*)"\)', selector)
        if text_match:
            return page.get_by_text(text_match.group(1))

        # page.get_by_test_id("...")
        tid_match = re.match(r'page\.get_by_test_id\("([^"]*)"\)', selector)
        if tid_match:
            return page.get_by_test_id(tid_match.group(1))

        # page.get_by_alt_text("...")
        alt_match = re.match(r'page\.get_by_alt_text\("([^"]*)"\)', selector)
        if alt_match:
            return page.get_by_alt_text(alt_match.group(1))

        # page.get_by_title("...")
        title_match = re.match(r'page\.get_by_title\("([^"]*)"\)', selector)
        if title_match:
            return page.get_by_title(title_match.group(1))

        # page.locator("...")
        loc_match = re.match(r'page\.locator\("([^"]*)"\)', selector)
        if loc_match:
            return page.locator(loc_match.group(1))

        # Fallback
        return page.locator(selector)

    async def _disambiguate_native_locator(
        self,
        native_locator,
        count: int,
        description: str,
        readable_selector: str,
        start_time,
        options: LocatorOptions
    ) -> Optional[LocatorResult]:
        """
        Disambiguate a native Playwright locator that matches multiple elements.

        Uses AI to select the best matching element based on the description,
        then returns a locator using .nth(index) to target that specific element.

        Args:
            native_locator: Native Playwright Locator matching multiple elements.
            count: Number of matched elements.
            description: Human-readable description of the target element.
            readable_selector: Readable selector string for logging/caching.
            start_time: Request start time for duration calculation.
            options: Locator options.

        Returns:
            LocatorResult with disambiguated locator, or None if disambiguation fails.
        """
        try:
            # Build context for each matching element
            context_parts = []
            for i in range(count):
                element = native_locator.nth(i)
                tag = await element.evaluate("el => el.tagName.toLowerCase()")
                text = await element.text_content() or ""
                el_id = await element.get_attribute("id") or ""
                el_class = await element.get_attribute("class") or ""
                el_name = await element.get_attribute("name") or ""
                el_value = await element.get_attribute("value") or ""
                aria_label = await element.get_attribute("aria-label") or ""
                data_testid = await element.get_attribute("data-testid") or ""

                context_parts.append(f"Element {i + 1}:")
                context_parts.append(f"  Tag: {tag}")
                context_parts.append(f"  Text: {text.strip()}")
                context_parts.append(f"  ID: {el_id}")
                context_parts.append(f"  Class: {el_class}")
                context_parts.append(f"  Name: {el_name}")
                context_parts.append(f"  Value: {el_value}")
                context_parts.append(f"  Aria-label: {aria_label}")
                context_parts.append(f"  Data-testid: {data_testid}")
                context_parts.append("")

            elements_context = "\n".join(context_parts)

            # Build disambiguation prompt (same format as ResilientAIService)
            prompt = (
                f'Multiple elements match the selector. '
                f'Select the best match for: "{description}"\n\n'
                f'{elements_context}\n'
                f'Respond with only the number (1, 2, 3, etc.) of the element '
                f'that best matches the description.'
            )

            logger.debug(
                "Disambiguating %d elements for description: %s",
                count, description
            )

            # Call AI provider's disambiguate method
            disamb_result = await self._call_ai_disambiguate(prompt)
            selected_index = disamb_result.selected_index
            tokens_used = disamb_result.tokens_used

            # Validate index (1-based from AI)
            if selected_index < 1 or selected_index > count:
                logger.warning(
                    "AI returned invalid element index %d (expected 1-%d), "
                    "disambiguation failed",
                    selected_index, count
                )
                return None

            # Convert to 0-based index for Playwright .nth()
            nth_index = selected_index - 1
            disambiguated_locator = native_locator.nth(nth_index)

            # Validate the disambiguated locator resolves to exactly 1 element
            disambiguated_count = await disambiguated_locator.count()
            if disambiguated_count != 1:
                logger.warning(
                    "Disambiguated locator .nth(%d) matched %d elements, expected 1",
                    nth_index, disambiguated_count
                )
                return None

            # Log the element ID for debugging
            element_id = await disambiguated_locator.get_attribute("id") or "no-id"
            logger.debug(
                "Disambiguated locator points to element with id='%s'",
                element_id
            )

            # Build the actual selector string for caching/reporting
            actual_selector = f"{readable_selector}.nth({nth_index})"

            logger.info(
                "AI disambiguation selected element %d of %d: %s (id=%s, tokens=%d)",
                selected_index, count, actual_selector, element_id, tokens_used
            )

            # Cache the disambiguated selector
            if options.enable_caching:
                cache_key = f"{readable_selector}|{description}"
                cached_selector = CachedSelector(
                    selector=actual_selector,
                    fingerprint=None,
                )
                self.selector_cache.put(cache_key, cached_selector)

            return LocatorResult.builder() \
                .element(disambiguated_locator) \
                .actual_selector(actual_selector) \
                .strategy(LocatorStrategy.DOM_ANALYSIS) \
                .from_cache(False) \
                .execution_time(datetime.now() - start_time) \
                .reasoning(
                    f"AI disambiguation selected element {selected_index} of {count}"
                ) \
                .tokens_used(tokens_used) \
                .build()

        except Exception as e:
            logger.warning(
                "AI disambiguation failed for %d elements: %s",
                count, str(e)
            )
            return None

    async def _call_ai_disambiguate(self, prompt: str) -> DisambiguationResult:
        """
        Call the AI service to disambiguate elements.

        Args:
            prompt: Disambiguation prompt with element context.

        Returns:
            DisambiguationResult with selected index and tokens used.

        Raises:
            Exception: If AI call fails or returns invalid response.
        """
        # Use the AI service's provider directly for disambiguation
        if hasattr(self.ai_service, 'provider'):
            result = await self.ai_service.provider.disambiguate(
                prompt=prompt, max_tokens=10
            )
            return result
        else:
            raise RuntimeError("AI service does not support disambiguation")

    # ==================== CORE HEALING LOGIC ====================

    async def _locate_element_with_healing(self, request: LocatorRequest) -> LocatorResult:
        """
        Core healing logic: quick check -> cache -> full timeout -> AI healing.

        Flow:
        1. Quick check original selector (configurable, default 500ms)
        2. If works -> return immediately (correct selectors are fast)
        3. If fails fast -> check cache
        4. If cache hit -> use cached selector
        5. If no cache -> try with full timeout, then AI healing

        Args:
            request: Locator request.

        Returns:
            LocatorResult with found element.

        Raises:
            ElementNotFoundException: If all strategies fail.
        """
        start_time = datetime.now()

        # Step 1: Quick check original selector (correct selectors work fast)
        quick_timeout = self.configuration.performance_config.quick_check_timeout
        quick_timeout_seconds = quick_timeout.total_seconds()

        by_tuple = locator_type_detector.auto_create_by(request.original_selector)

        try:
            original_element = await asyncio.wait_for(
                self._try_selector_quick(by_tuple, request),
                timeout=quick_timeout_seconds
            )

            if original_element is not None:
                # Original selector worked! Cache it and return
                await self._cache_successful_selector(
                    request,
                    request.original_selector,
                    original_element
                )

                execution_time = datetime.now() - start_time
                logger.info(
                    "[QUICK] Original selector worked in %dms: %s",
                    int(execution_time.total_seconds() * 1000),
                    request.original_selector
                )
                return LocatorResult.builder() \
                    .element(original_element) \
                    .actual_selector(request.original_selector) \
                    .strategy(LocatorStrategy.ORIGINAL_SELECTOR) \
                    .execution_time(execution_time) \
                    .from_cache(False) \
                    .confidence(1.0) \
                    .reasoning("Original selector worked") \
                    .build()
        except asyncio.TimeoutError:
            logger.debug(
                "[QUICK] Original selector timed out after %dms, checking cache: %s",
                int(quick_timeout_seconds * 1000),
                request.original_selector
            )
        except Exception as e:
            logger.debug(
                "[QUICK] Original selector failed quickly: %s - %s",
                request.original_selector, str(e)
            )

        # Step 2: Quick check failed, try cache
        return await self._try_cache_or_heal(request, start_time)

    async def _try_selector_quick(
        self,
        by_tuple: tuple,
        request: LocatorRequest
    ) -> Optional["WebElement"]:
        """
        Quick selector check without waiting for implicit timeout.

        Uses adapter's find_elements_quick method if available (Selenium),
        which temporarily sets implicit wait to 0 for instant checking.

        Args:
            by_tuple: (By type, selector value) tuple.
            request: Locator request for disambiguation.

        Returns:
            WebElement if found immediately, None otherwise.
        """
        try:
            # Use find_elements_quick if available (Selenium adapter)
            if hasattr(self.adapter, 'find_elements_quick'):
                elements = await self.adapter.find_elements_quick(by_tuple)
            else:
                # Fallback for other adapters (Playwright doesn't have implicit wait)
                elements = await self.adapter.find_elements(by_tuple)

            if elements:
                return await self._disambiguate_elements(elements, request)
            return None
        except Exception:
            return None

    async def _try_cache_or_heal(
        self,
        request: LocatorRequest,
        start_time: datetime
    ) -> LocatorResult:
        """
        Try cache, then perform healing if cache misses.

        Args:
            request: Locator request.
            start_time: Request start time.

        Returns:
            LocatorResult.

        Raises:
            ElementNotFoundException: If all strategies fail.
        """
        if not request.options.enable_caching:
            return await self._perform_healing(request, start_time)

        # Check cache
        cache_key = self._generate_cache_key(request)
        cached = self.selector_cache.get(cache_key)

        if cached and cached.current_success_rate > 0.7:
            element = None

            # Check if cached selector is a Playwright-style selector
            if 'get_by_' in cached.selector or 'page.locator(' in cached.selector:
                healed_locator = self._create_locator_from_healed_selector(cached.selector)
                if healed_locator is not None:
                    try:
                        count = await healed_locator.count()
                        if count == 1:
                            element = await healed_locator.element_handle()
                        elif count > 1:
                            logger.warning(
                                "Cached Playwright locator is ambiguous "
                                "(found %d elements): %s",
                                count, cached.selector
                            )
                    except Exception:
                        pass
            else:
                # Standard CSS/XPath selector
                by_tuple = locator_type_detector.auto_create_by(cached.selector)
                element = await self._try_selector_with_by(by_tuple, request)

            if element is not None:
                # Cache hit!
                self.selector_cache.update_success(cache_key, True)
                logger.info("Cache hit for %s", request.original_selector)

                execution_time = datetime.now() - start_time
                return LocatorResult.builder() \
                    .element(element) \
                    .actual_selector(cached.selector) \
                    .strategy(LocatorStrategy.CACHED) \
                    .execution_time(execution_time) \
                    .from_cache(True) \
                    .confidence(cached.current_success_rate) \
                    .reasoning("Retrieved from cache") \
                    .build()
            else:
                # Cache miss
                self.selector_cache.update_success(cache_key, False)
                logger.debug("Cached selector failed for %s", request.original_selector)

        # No cache or cache failed - perform healing
        return await self._perform_healing(request, start_time)

    async def _perform_healing(
        self,
        request: LocatorRequest,
        start_time: datetime
    ) -> LocatorResult:
        """
        Perform AI healing using configured element locator.

        Args:
            request: Locator request.
            start_time: Request start time.

        Returns:
            LocatorResult with healed selector.

        Raises:
            ElementNotFoundException: If healing fails.
        """
        try:
            result = await self.element_locator.locate(request)

            # Cache successful result
            if result.element is not None:
                await self._cache_successful_selector(
                    request,
                    result.actual_selector,
                    result.element
                )

            return result

        except Exception as e:
            raise ElementNotFoundException(
                f"All healing strategies failed for selector: {request.original_selector}"
            ) from e

    async def _try_selector_with_by(
        self,
        by_tuple: tuple,
        request: LocatorRequest
    ) -> Optional["WebElement"]:
        """
        Try a selector and return element if found.

        Args:
            by_tuple: (By type, selector value) tuple.
            request: Locator request for disambiguation.

        Returns:
            WebElement if found, None otherwise.
        """
        try:
            elements = await self.adapter.find_elements(by_tuple)
            if elements:
                return await self._disambiguate_elements(elements, request)
            return None
        except Exception:
            return None

    async def _disambiguate_elements(
        self,
        elements: List["WebElement"],
        request: LocatorRequest
    ) -> "WebElement":
        """
        Disambiguate multiple elements using AI.

        Uses AI to select the best matching element based on the description,
        mirroring Java's disambiguateElements method.

        Args:
            elements: List of candidate elements.
            request: Locator request with description.

        Returns:
            Best matching element.
        """
        if len(elements) == 1:
            return elements[0]

        # Multiple elements found - use AI for disambiguation
        try:
            logger.debug(
                "Multiple elements found (%d), using AI for disambiguation "
                "with description: %s",
                len(elements), request.description
            )
            selected = await self.ai_service.select_best_matching_element(
                elements, request.description
            )
            if selected is not None:
                return selected
        except Exception as e:
            logger.warning(
                "AI disambiguation failed, falling back to first element: %s",
                str(e)
            )

        return elements[0]

    async def _cache_successful_selector(
        self,
        request: LocatorRequest,
        successful_selector: str,
        element: "WebElement"
    ) -> None:
        """
        Cache a successful selector for future use.

        Args:
            request: Original locator request.
            successful_selector: The selector that worked.
            element: The found element.
        """
        if not request.options.enable_caching:
            return

        try:
            cache_key = self._generate_cache_key(request)

            # Get element context for fingerprinting
            context = await self.adapter.get_element_context(element)

            # Create and cache selector
            cached_selector = CachedSelector(
                selector=successful_selector,
                fingerprint=context.fingerprint
            )
            self.selector_cache.put(cache_key, cached_selector)

            logger.debug("Cached selector: %s -> %s", request.original_selector, successful_selector)

        except Exception as e:
            logger.error("Failed to cache selector: %s", str(e))

    def _generate_cache_key(self, request: LocatorRequest) -> str:
        """
        Generate cache key for a request.

        Args:
            request: Locator request.

        Returns:
            Cache key string.
        """
        return f"{request.original_selector}|{request.description}"

    def _get_last_successful_selector(
        self,
        original_selector: str,
        description: str
    ) -> str:
        """
        Get the last successful selector from cache.

        Args:
            original_selector: Original selector.
            description: Element description.

        Returns:
            Cached selector if available, original selector otherwise.
        """
        cache_key = f"{original_selector}|{description}"
        cached = self.selector_cache.get(cache_key)
        return cached.selector if cached else original_selector

    # ==================== CACHE MANAGEMENT ====================

    def clear_cache(self) -> None:
        """Clear all cached selectors."""
        self.selector_cache.clear_all()
        logger.info("Cache cleared")

    def remove_cached_selector(self, selector: str, description: str) -> bool:
        """
        Remove a specific cached selector.

        Args:
            selector: Original selector.
            description: Element description.

        Returns:
            True if removed, False if not found.
        """
        cache_key = f"{selector}|{description}"
        return self.selector_cache.remove(cache_key)

    def get_cache_size(self) -> int:
        """
        Get current cache size.

        Returns:
            Number of cached entries.
        """
        return self.selector_cache.size()

    def get_cache_metrics(self) -> CacheMetrics:
        """
        Get cache performance metrics.

        Returns:
            Cache metrics.
        """
        return self.selector_cache.get_metrics()

    def cleanup_expired_cache(self) -> None:
        """Manually clean up expired cache entries."""
        self.selector_cache.evict_expired()

    # ==================== METRICS AND HEALTH ====================

    def get_metrics(self) -> LocatorMetrics:
        """
        Get locator performance metrics.

        Returns:
            Locator metrics.
        """
        return self.metrics

    def get_health_status(self) -> dict:
        """
        Get health status for monitoring.

        Returns:
            Dictionary with health status information.
        """
        success_rate = self.metrics.get_success_rate()
        cache_hit_rate = self.selector_cache.get_metrics().get_hit_rate()

        return {
            "overall": success_rate > 0.8,
            "success_rate": success_rate,
            "cache_hit_rate": cache_hit_rate,
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests
        }

    # ==================== LIFECYCLE ====================

    async def shutdown(self) -> None:
        """
        Graceful shutdown of AutoHealLocator.

        Performs cleanup and releases resources.
        """
        logger.info("AutoHealLocator shutdown initiated")

        # Cleanup cache
        if hasattr(self.selector_cache, 'close'):
            try:
                await self.selector_cache.close()
            except Exception as e:
                logger.error("Error closing cache: %s", str(e))

        logger.info("AutoHealLocator shutdown completed")


def _create_cache_based_on_config(cache_config: CacheConfig) -> SelectorCache:
    """
    Create cache instance based on configuration.

    Args:
        cache_config: Cache configuration.

    Returns:
        Configured selector cache.
    """
    if cache_config.cache_type == ConfigCacheType.PERSISTENT_FILE:
        try:
            # Lazy import to avoid import errors if not used
            from autoheal.impl.cache.file_selector_cache import FileSelectorCache
            return FileSelectorCache(cache_config)
        except Exception as e:
            logger.error("Failed to initialize file cache: %s. Falling back to Cachetools.", str(e))
            return CachetoolsSelectorCache(cache_config)

    elif cache_config.cache_type == ConfigCacheType.REDIS:
        try:
            # Lazy import to avoid import errors if redis is not installed
            from autoheal.impl.cache.redis_selector_cache import RedisSelectorCache
            return RedisSelectorCache(
                cache_config,
                cache_config.redis_host,
                cache_config.redis_port,
                cache_config.redis_password
            )
        except Exception as e:
            logger.error("Failed to initialize Redis cache: %s. Falling back to Cachetools.", str(e))
            return CachetoolsSelectorCache(cache_config)

    elif cache_config.cache_type == ConfigCacheType.HYBRID:
        # TODO: Implement hybrid cache (Cachetools L1 + Redis L2)
        logger.info("Hybrid cache not yet implemented, using Cachetools")
        return CachetoolsSelectorCache(cache_config)

    else:  # ConfigCacheType.CAFFEINE or default
        return CachetoolsSelectorCache(cache_config)
