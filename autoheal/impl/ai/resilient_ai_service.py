"""
Resilient AI Service implementation with circuit breaker and retry logic.

This module provides the main AI service that routes requests to specific
AI providers (OpenAI, Anthropic, Gemini, etc.) with resilience features.
"""

import asyncio
import json
import logging
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

import aiohttp

if TYPE_CHECKING:
    from selenium.webdriver.remote.webelement import WebElement

from autoheal.core.ai_service import AIService
from autoheal.config.ai_config import AIConfig
from autoheal.config.resilience_config import ResilienceConfig
from autoheal.models.ai_analysis_result import AIAnalysisResult
from autoheal.models.enums import AIProvider, AutomationFramework
from autoheal.models.element_candidate import ElementCandidate
from autoheal.metrics.ai_service_metrics import AIServiceMetrics
from autoheal.metrics.cost_metrics import CostMetrics
from autoheal.resilience.circuit_breaker import CircuitBreaker
from autoheal.exception.exceptions import (
    CircuitBreakerOpenException,
    AIServiceException
)

# Import providers
from autoheal.impl.ai.providers.openai_provider import OpenAIProvider
from autoheal.impl.ai.providers.base_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class ResilientAIService(AIService):
    """
    Resilient AI service with provider routing, circuit breaker, and retry logic.

    This service acts as the main entry point for AI-powered element analysis.
    It routes requests to specific AI providers based on configuration and provides
    resilience features like circuit breaker, retry with exponential backoff, and
    comprehensive metrics tracking.

    Attributes:
        config: AI configuration including provider, API keys, etc.
        resilience_config: Configuration for circuit breaker and retry logic.
        provider: The active AI provider instance.
        circuit_breaker: Circuit breaker for fault tolerance.
        metrics: AI service performance metrics.
        cost_metrics: Token and cost tracking metrics.

    Examples:
        >>> config = AIConfig.builder() \\
        ...     .provider(AIProvider.OPENAI) \\
        ...     .api_key("sk-...") \\
        ...     .build()
        >>> resilience = ResilienceConfig.builder().build()
        >>> service = ResilientAIService(config, resilience)
        >>> result = await service.analyze_dom(
        ...     html="<html>...</html>",
        ...     description="Find submit button",
        ...     framework=AutomationFramework.SELENIUM
        ... )
    """

    def __init__(
        self,
        ai_config: AIConfig,
        resilience_config: ResilienceConfig
    ):
        """
        Initialize the resilient AI service.

        Args:
            ai_config: AI configuration.
            resilience_config: Resilience configuration for circuit breaker.
        """
        self.config = ai_config
        self.resilience_config = resilience_config

        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=resilience_config.circuit_breaker_failure_threshold,
            timeout=resilience_config.circuit_breaker_timeout
        )

        # Initialize metrics
        self.metrics = AIServiceMetrics()
        self.cost_metrics = CostMetrics()

        # Initialize the appropriate provider
        self.provider = self._initialize_provider(ai_config)

        logger.info(
            "ResilientAIService initialized with provider: %s, model: %s",
            ai_config.provider.value,
            ai_config.model
        )

    def _initialize_provider(self, config: AIConfig) -> BaseAIProvider:
        """
        Initialize the AI provider based on configuration.

        Args:
            config: AI configuration.

        Returns:
            Initialized provider instance.

        Raises:
            ValueError: If provider is not supported.
        """
        provider_type = config.provider

        if provider_type == AIProvider.OPENAI:
            return OpenAIProvider(
                api_key=config.api_key,
                api_url=config.api_url,
                model=config.model,
                timeout=config.timeout
            )
        elif provider_type == AIProvider.ANTHROPIC_CLAUDE:
            # Import here to avoid circular dependency
            try:
                from autoheal.impl.ai.providers.anthropic_provider import AnthropicProvider
                return AnthropicProvider(
                    api_key=config.api_key,
                    api_url=config.api_url,
                    model=config.model,
                    timeout=config.timeout
                )
            except ImportError:
                raise ValueError("Anthropic provider not yet implemented")
        elif provider_type == AIProvider.GOOGLE_GEMINI:
            try:
                from autoheal.impl.ai.providers.gemini_provider import GeminiProvider
                return GeminiProvider(
                    api_key=config.api_key,
                    api_url=config.api_url,
                    model=config.model,
                    timeout=config.timeout
                )
            except ImportError:
                raise ValueError("Gemini provider not yet implemented")
        elif provider_type == AIProvider.DEEPSEEK:
            try:
                from autoheal.impl.ai.providers.deepseek_provider import DeepSeekProvider
                return DeepSeekProvider(
                    api_key=config.api_key,
                    api_url=config.api_url,
                    model=config.model,
                    timeout=config.timeout
                )
            except ImportError:
                raise ValueError("DeepSeek provider not yet implemented")
        elif provider_type == AIProvider.GROK:
            try:
                from autoheal.impl.ai.providers.grok_provider import GrokProvider
                return GrokProvider(
                    api_key=config.api_key,
                    api_url=config.api_url,
                    model=config.model,
                    timeout=config.timeout
                )
            except ImportError:
                raise ValueError("Grok provider not yet implemented")
        elif provider_type == AIProvider.GROQ:
            try:
                from autoheal.impl.ai.providers.groq_provider import GroqProvider
                return GroqProvider(
                    api_key=config.api_key,
                    api_url=config.api_url,
                    model=config.model,
                    timeout=config.timeout
                )
            except ImportError:
                raise ValueError("Groq provider not yet implemented")
        elif provider_type == AIProvider.LOCAL_MODEL:
            try:
                from autoheal.impl.ai.providers.ollama_provider import OllamaProvider
                return OllamaProvider(
                    api_key=config.api_key or "",  # Ollama doesn't need API key
                    api_url=config.api_url or "http://localhost:11434",
                    model=config.model,
                    timeout=config.timeout
                )
            except ImportError:
                raise ValueError("Ollama provider not yet implemented")
        elif provider_type == AIProvider.MOCK:
            from autoheal.impl.ai.mock_ai_service import MockAIService
            # Return a mock that implements BaseAIProvider interface
            # For now, raise an error as MockAIService is separate
            raise ValueError("MOCK provider should use MockAIService directly, not ResilientAIService")
        else:
            raise ValueError(f"Unsupported AI provider: {provider_type}")

    async def analyze_dom(
        self,
        html: str,
        description: str,
        previous_selector: Optional[str] = None,
        framework: AutomationFramework = AutomationFramework.SELENIUM
    ) -> AIAnalysisResult:
        """
        Analyze DOM structure to find element selectors with framework awareness.

        Args:
            html: The HTML content to analyze.
            description: Human-readable description of the target element.
            previous_selector: The selector that previously worked but now fails.
            framework: The automation framework (SELENIUM or PLAYWRIGHT).

        Returns:
            AIAnalysisResult containing suggested selectors and confidence scores.

        Raises:
            CircuitBreakerOpenException: If circuit breaker is open.
            AIServiceException: If the AI service fails.
        """
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            self.metrics.record_circuit_breaker_open()
            raise CircuitBreakerOpenException("AI Service circuit breaker is open")

        start_time = datetime.now()

        try:
            # Build framework-appropriate prompt
            prompt = self._build_dom_prompt(html, description, previous_selector, framework)

            # Call provider with retry logic
            result = await self._call_with_retry(
                lambda: self.provider.analyze_dom(
                    prompt=prompt,
                    framework=framework,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature
                )
            )

            # Record success
            self.circuit_breaker.record_success()
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.metrics.record_request(success=True, latency_ms=latency_ms)
            self.cost_metrics.record_dom_request()

            logger.debug(
                "%s DOM analysis completed for '%s' (framework: %s, latency: %dms)",
                framework.value,
                description,
                framework.value,
                latency_ms
            )

            return result

        except Exception as e:
            # Record failure
            self.circuit_breaker.record_failure()
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.metrics.record_request(success=False, latency_ms=latency_ms)

            logger.error(
                "DOM analysis failed for '%s' (framework: %s): %s",
                description,
                framework.value,
                str(e)
            )
            raise AIServiceException(f"AI DOM analysis failed: {e}")

    async def analyze_visual(
        self,
        screenshot: bytes,
        description: str
    ) -> AIAnalysisResult:
        """
        Analyze visual screenshot to find element locations.

        Args:
            screenshot: The screenshot data as bytes.
            description: Human-readable description of the target element.

        Returns:
            AIAnalysisResult containing suggested selectors and confidence scores.

        Raises:
            CircuitBreakerOpenException: If circuit breaker is open.
            AIServiceException: If the AI service fails or visual analysis is not supported.
        """
        # Check if visual analysis is enabled
        if not self.config.visual_analysis_enabled:
            raise AIServiceException("Visual analysis is disabled in configuration")

        # Check if provider supports visual analysis
        if not self.provider.supports_visual_analysis():
            raise AIServiceException(
                f"Visual analysis is not supported by provider: {self.config.provider.value}"
            )

        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            self.metrics.record_circuit_breaker_open()
            raise CircuitBreakerOpenException("AI Service circuit breaker is open")

        start_time = datetime.now()

        try:
            # Build visual analysis prompt
            prompt = self._build_visual_prompt(description)

            # Call provider with retry logic
            result = await self._call_with_retry(
                lambda: self.provider.analyze_visual(
                    prompt=prompt,
                    screenshot=screenshot,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature
                )
            )

            # Record success
            self.circuit_breaker.record_success()
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.metrics.record_request(success=True, latency_ms=latency_ms)
            self.cost_metrics.record_visual_request()

            logger.debug(
                "Visual analysis completed for '%s' (latency: %dms)",
                description,
                latency_ms
            )

            return result

        except Exception as e:
            # Record failure
            self.circuit_breaker.record_failure()
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.metrics.record_request(success=False, latency_ms=latency_ms)

            logger.error("Visual analysis failed for '%s': %s", description, str(e))
            raise AIServiceException(f"AI visual analysis failed: {e}")

    async def select_best_matching_element(
        self,
        elements: List["WebElement"],
        description: str
    ) -> Optional["WebElement"]:
        """
        Select the best matching element from a list based on description.

        When multiple elements match a selector, this method uses AI to determine
        which element best matches the provided description.

        Args:
            elements: List of candidate WebElements.
            description: Human-readable description of the target element.

        Returns:
            The best matching WebElement, or None if no good match is found.

        Raises:
            AIServiceException: If the AI service fails.
        """
        if not elements:
            raise ValueError("Elements list cannot be empty")

        if len(elements) == 1:
            return elements[0]

        try:
            logger.debug(
                "AI disambiguation for %d elements with description: %s",
                len(elements),
                description
            )

            # Build element context
            elements_context = self._build_elements_context(elements)

            # Build disambiguation prompt
            prompt = self._build_disambiguation_prompt(description, elements_context)

            # Call provider with retry logic
            disambiguation_result = await self._call_with_retry(
                lambda: self.provider.disambiguate(prompt=prompt, max_tokens=10)
            )
            selected_index = disambiguation_result.selected_index

            # Validate index
            if selected_index < 1 or selected_index > len(elements):
                logger.warning(
                    "AI returned invalid element index %d, falling back to first element",
                    selected_index
                )
                return elements[0]

            selected_element = elements[selected_index - 1]  # Convert to 0-based
            logger.debug("AI selected element %d out of %d", selected_index, len(elements))

            return selected_element

        except Exception as e:
            logger.warning(
                "AI disambiguation failed, returning first element: %s",
                str(e)
            )
            return elements[0]

    def is_healthy(self) -> bool:
        """
        Check if the AI service is healthy and responsive.

        Returns:
            True if service is healthy, False otherwise.
        """
        return not self.circuit_breaker.is_open() and self.metrics.success_rate > 0.7

    def get_metrics(self) -> AIServiceMetrics:
        """
        Get performance metrics for the AI service.

        Returns:
            Current AI service metrics including request counts, latencies, and costs.
        """
        return self.metrics

    def get_cost_metrics(self) -> CostMetrics:
        """
        Get cost tracking metrics.

        Returns:
            Current cost metrics with token usage and estimated costs.
        """
        return self.cost_metrics

    # Private helper methods

    def _build_dom_prompt(
        self,
        html: str,
        description: str,
        previous_selector: Optional[str],
        framework: AutomationFramework
    ) -> str:
        """
        Build DOM analysis prompt based on framework.

        Args:
            html: HTML content.
            description: Element description.
            previous_selector: Previous selector that failed.
            framework: Target automation framework.

        Returns:
            Formatted prompt string.
        """
        if framework == AutomationFramework.PLAYWRIGHT:
            return self._build_playwright_dom_prompt(html, description, previous_selector)
        else:
            return self._build_selenium_dom_prompt(html, description, previous_selector)

    def _build_selenium_dom_prompt(
        self,
        html: str,
        description: str,
        previous_selector: Optional[str]
    ) -> str:
        """Build Selenium-specific DOM analysis prompt."""
        prev_info = f'The selector "{previous_selector}" is broken.' if previous_selector else ""

        return f"""You are a web automation expert. Find the best CSS selector for: "{description}"

{prev_info} Analyze the HTML and find the correct element.

HTML:
{html}

REQUIREMENTS:
- Look for elements with matching id, name, class, or text content
- Prefer ID selectors (#id) when available
- Ensure the selector matches exactly one element
- The selector must be valid CSS syntax
- Do NOT include any prefixes like "selector:" or "css:"

Respond with valid JSON only:
{{
    "selector": "css-selector-here",
    "confidence": 0.95,
    "reasoning": "brief explanation",
    "alternatives": ["alt1", "alt2"]
}}"""

    def _build_playwright_dom_prompt(
        self,
        html: str,
        description: str,
        previous_locator: Optional[str]
    ) -> str:
        """Build Playwright-specific DOM analysis prompt."""
        prev_info = f'The previous locator "{previous_locator}" is broken.' if previous_locator else ""

        return f"""You are a Playwright automation expert. Find the best UNIQUE locator for: "{description}"

{prev_info} Analyze the HTML and find the correct element.

HTML:
{html}

CRITICAL REQUIREMENT:
The locator MUST match EXACTLY ONE element. If multiple elements have the same text/role, you MUST use a unique identifier like ID, data-testid, or a more specific CSS selector.

PRIORITY ORDER (try in this sequence, but ONLY if it matches exactly one element):
1. getByTestId() - Test ID attribute (data-testid, data-test) - PREFERRED for unique elements
2. css with ID - CSS selector with #id (e.g., "#secondSubmit") - VERY RELIABLE
3. getByRole() - ARIA role with accessible name - ONLY if unique
4. getByLabel() - Form label text associated with input
5. getByPlaceholder() - Input placeholder text
6. getByText() - Visible text content - ONLY if unique
7. CSS Selector - Fallback with class or attribute selectors

RULES:
- MOST IMPORTANT: The locator must match exactly ONE element, not multiple
- If description mentions "first", "second", "last" etc., find the specific element by its unique ID or data-testid
- If multiple elements have the same text (e.g., two "Submit" buttons), use ID or data-testid instead of getByRole/getByText
- Look for id attributes and data-testid attributes first - they are usually unique
- Avoid locators that would match multiple elements

Respond with valid JSON only:
{{
    "locatorType": "getByRole|getByLabel|getByPlaceholder|getByText|getByTestId|css",
    "value": "button|Username|#secondSubmit",
    "options": {{"name": "Submit"}},
    "confidence": 0.95,
    "reasoning": "brief explanation why this locator was chosen",
    "alternatives": [
        {{"type": "css", "value": "#username"}},
        {{"type": "getByTestId", "value": "user-input"}}
    ]
}}

Examples:
- Second button with ID: {{"locatorType": "css", "value": "#secondSubmit", "confidence": 0.98, "reasoning": "Using unique ID for the second Submit button"}}
- Button with test-id: {{"locatorType": "getByTestId", "value": "submit-second", "confidence": 0.95}}
- Unique button: {{"locatorType": "getByRole", "value": "button", "options": {{"name": "Login"}}}}
- Input with label: {{"locatorType": "getByLabel", "value": "Username"}}
- Fallback CSS: {{"locatorType": "css", "value": "[data-testid='submit-second']"}}"""

    def _build_visual_prompt(self, description: str) -> str:
        """Build visual analysis prompt."""
        return f"""Analyze the screenshot to locate the element: "{description}"

Identify the best CSS selector for this element based on its visual characteristics and position.

Respond with valid JSON only:
{{
    "selector": "css-selector-here",
    "confidence": 0.95,
    "reasoning": "brief explanation based on visual analysis",
    "alternatives": ["alt1", "alt2"]
}}"""

    def _build_disambiguation_prompt(
        self,
        description: str,
        elements_context: str
    ) -> str:
        """Build element disambiguation prompt."""
        return f"""Multiple elements match the selector. Select the best match for: "{description}"

{elements_context}

Respond with only the number (1, 2, 3, etc.) of the element that best matches the description."""

    def _build_elements_context(self, elements: List["WebElement"]) -> str:
        """
        Build context information about elements for disambiguation.

        Args:
            elements: List of web elements.

        Returns:
            Formatted context string.
        """
        context_parts = []

        for i, element in enumerate(elements, start=1):
            context_parts.append(f"Element {i}:")
            context_parts.append(f"  Tag: {element.tag_name}")
            context_parts.append(f"  Text: {self._get_element_text(element)}")
            context_parts.append(f"  ID: {element.get_attribute('id')}")
            context_parts.append(f"  Class: {element.get_attribute('class')}")
            context_parts.append(f"  Name: {element.get_attribute('name')}")
            context_parts.append(f"  Value: {element.get_attribute('value')}")
            context_parts.append(f"  Aria-label: {element.get_attribute('aria-label')}")
            context_parts.append(f"  Data-testid: {element.get_attribute('data-testid')}")
            context_parts.append("")

        return "\n".join(context_parts)

    def _get_element_text(self, element: "WebElement") -> str:
        """
        Get text content from element, handling exceptions.

        Args:
            element: Web element.

        Returns:
            Element text or empty string.
        """
        try:
            return element.text or ""
        except Exception:
            return ""

    async def _call_with_retry(self, api_call):
        """
        Call AI provider with exponential backoff retry logic.

        Args:
            api_call: Async callable that makes the API request.

        Returns:
            Result from the API call.

        Raises:
            Exception: If all retry attempts fail.
        """
        max_retries = self.config.max_retries
        last_exception = None

        # Errors that are worth retrying (transient network/server issues)
        retryable_errors = (
            aiohttp.ClientError,
            asyncio.TimeoutError,
            ConnectionError,
            OSError,
        )

        for attempt in range(max_retries):
            try:
                result = await api_call()
                return result
            except retryable_errors as e:
                last_exception = e
                logger.warning(
                    "AI API call failed (attempt %d/%d, retryable): %s",
                    attempt + 1,
                    max_retries,
                    str(e)
                )

                # Exponential backoff before retry (except on last attempt)
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 1s, 2s, 4s, 8s...
                    logger.debug("Retrying in %d seconds...", wait_time)
                    await asyncio.sleep(wait_time)
            except (ValueError, json.JSONDecodeError, KeyError, TypeError) as e:
                # Permanent errors — retrying won't help
                logger.error("AI API call failed with non-retryable error: %s", str(e))
                raise

        # All retries failed
        raise Exception(
            f"AI call failed after {max_retries} attempts: {last_exception}"
        )

    def shutdown(self):
        """
        Shutdown the service and cleanup resources.

        This method should be called when the service is no longer needed
        to properly release resources.
        """
        logger.info("ResilientAIService shutdown completed")
