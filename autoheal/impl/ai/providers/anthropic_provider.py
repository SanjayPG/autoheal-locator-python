"""
Anthropic Claude provider implementation for AI services.

This module provides Anthropic Claude API integration for DOM and visual analysis.
Supports Claude 3 family models including Opus, Sonnet, and Haiku.
"""

import base64
import json
import time
import logging
from typing import Dict, Any, Optional

import aiohttp

from autoheal.impl.ai.providers.base_provider import BaseAIProvider
from autoheal.impl.ai.providers.response_parser import ResponseParser
from autoheal.models.ai_analysis_result import AIAnalysisResult
from autoheal.models.disambiguation_result import DisambiguationResult
from autoheal.models.enums import AutomationFramework

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseAIProvider):
    """
    Anthropic Claude API provider for AI-powered element analysis.

    Supports both DOM analysis (text-based) and visual analysis (image-based)
    using Anthropic's Claude 3 family of models including Opus, Sonnet, and Haiku.

    Attributes:
        api_key: Anthropic API key.
        api_url: Anthropic API endpoint (default: https://api.anthropic.com/v1/messages).
        model: Model name (e.g., 'claude-3-5-sonnet-20241022', 'claude-3-opus-20240229').
        timeout: Request timeout in seconds.
        anthropic_version: API version header (default: '2023-06-01').

    Examples:
        >>> provider = AnthropicProvider(
        ...     api_key="sk-ant-...",
        ...     api_url="https://api.anthropic.com/v1/messages",
        ...     model="claude-3-5-sonnet-20241022"
        ... )
        >>> result = await provider.analyze_dom(
        ...     prompt="Find submit button",
        ...     framework=AutomationFramework.SELENIUM,
        ...     max_tokens=2000,
        ...     temperature=0.7
        ... )
    """

    DEFAULT_API_URL = "https://api.anthropic.com/v1/messages"
    DEFAULT_VERSION = "2023-06-01"

    def __init__(
        self,
        api_key: str,
        api_url: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: int = 30,
        anthropic_version: str = DEFAULT_VERSION
    ):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key.
            api_url: Optional custom API URL.
            model: Model name to use.
            timeout: Request timeout in seconds.
            anthropic_version: API version (default: '2023-06-01').
        """
        super().__init__(
            api_key=api_key,
            api_url=api_url or self.DEFAULT_API_URL,
            model=model,
            timeout=timeout
        )
        self.anthropic_version = anthropic_version
        logger.info("AnthropicProvider initialized with model: %s", model)

    async def analyze_dom(
        self,
        prompt: str,
        framework: AutomationFramework,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> AIAnalysisResult:
        """
        Perform DOM analysis using Anthropic Claude API.

        Args:
            prompt: Analysis prompt with HTML and description.
            framework: Target automation framework.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature (0.0-1.0).

        Returns:
            AIAnalysisResult with recommended selectors.

        Raises:
            Exception: If API call fails.
        """
        start_time = time.time()
        self._log_request(self.api_url, framework)

        request_body = self._create_dom_request_body(prompt, max_tokens, temperature)

        try:
            async with aiohttp.ClientSession() as session:
                headers = self._create_headers({
                    "x-api-key": self.api_key,
                    "anthropic-version": self.anthropic_version
                })

                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        logger.error("Anthropic API call failed: %d - %s", response.status, error_text)
                        raise Exception(f"Anthropic API call failed: {response.status}")

                    response_data = await response.json()
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    self._log_response(len(str(response_data)), processing_time_ms)

                    # Extract token usage from response
                    tokens_used = self._extract_token_usage(response_data)

                    result = self._parse_dom_response(response_data, framework)
                    result.tokens_used = tokens_used
                    return result

        except aiohttp.ClientError as e:
            logger.error("Anthropic DOM analysis failed: %s", str(e))
            raise Exception(f"Anthropic DOM analysis failed: {e}")

    async def analyze_visual(
        self,
        prompt: str,
        screenshot: bytes,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> AIAnalysisResult:
        """
        Perform visual analysis using Anthropic Claude Vision API.

        Args:
            prompt: Analysis prompt describing the element.
            screenshot: Screenshot image data.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.

        Returns:
            AIAnalysisResult with recommended selectors.

        Raises:
            Exception: If API call fails.
        """
        start_time = time.time()
        self._log_request(self.api_url)

        # Encode screenshot to base64
        base64_image = base64.b64encode(screenshot).decode('utf-8')

        request_body = self._create_visual_request_body(
            prompt,
            base64_image,
            max_tokens,
            temperature
        )

        try:
            async with aiohttp.ClientSession() as session:
                headers = self._create_headers({
                    "x-api-key": self.api_key,
                    "anthropic-version": self.anthropic_version
                })

                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        logger.error("Anthropic Vision API call failed: %d - %s", response.status, error_text)
                        raise Exception(f"Anthropic Vision API call failed: {response.status}")

                    response_data = await response.json()
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    self._log_response(len(str(response_data)), processing_time_ms)

                    # Extract token usage from response
                    tokens_used = self._extract_token_usage(response_data)

                    result = self._parse_visual_response(response_data)
                    result.tokens_used = tokens_used
                    return result

        except aiohttp.ClientError as e:
            logger.error("Anthropic visual analysis failed: %s", str(e))
            raise Exception(f"Anthropic visual analysis failed: {e}")

    async def disambiguate(
        self,
        prompt: str,
        max_tokens: int = 10
    ) -> DisambiguationResult:
        """
        Select best matching element from multiple candidates.

        Args:
            prompt: Disambiguation prompt with element details.
            max_tokens: Maximum tokens (usually very small).

        Returns:
            DisambiguationResult with selected index and tokens used.

        Raises:
            Exception: If API call fails.
        """
        request_body = self._create_disambiguation_request_body(prompt, max_tokens)

        try:
            async with aiohttp.ClientSession() as session:
                headers = self._create_headers({
                    "x-api-key": self.api_key,
                    "anthropic-version": self.anthropic_version
                })

                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        logger.error("Anthropic disambiguation failed: %d - %s", response.status, error_text)
                        raise Exception(f"Anthropic disambiguation failed: {response.status}")

                    response_data = await response.json()
                    # Anthropic response format: content[0].text
                    content_blocks = response_data.get("content", [])
                    if not content_blocks:
                        raise ValueError("Empty content array in Anthropic response")
                    content = content_blocks[0].get("text", "").strip()
                    tokens_used = self._extract_token_usage(response_data)
                    selected_index = ResponseParser.parse_disambiguation_response(content)

                    return DisambiguationResult(
                        selected_index=selected_index,
                        tokens_used=tokens_used
                    )

        except Exception as e:
            logger.error("Anthropic disambiguation failed: %s", str(e))
            # Default to first element on error
            return DisambiguationResult(selected_index=1, tokens_used=0)

    def supports_visual_analysis(self) -> bool:
        """
        Check if Anthropic Claude supports visual analysis.

        Returns:
            True (Claude 3 models support image analysis).
        """
        return True

    def get_provider_name(self) -> str:
        """
        Get provider name.

        Returns:
            "Anthropic"
        """
        return "Anthropic"

    def _extract_token_usage(self, response_data: Dict[str, Any]) -> int:
        """
        Extract total token usage from Anthropic API response.

        Args:
            response_data: Raw API response.

        Returns:
            Total tokens used (input + output), or 0 if not available.
        """
        try:
            usage = response_data.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total = input_tokens + output_tokens
            logger.debug("Token usage - input: %d, output: %d, total: %d",
                        input_tokens, output_tokens, total)
            return total
        except Exception as e:
            logger.debug("Could not extract token usage: %s", str(e))
            return 0

    # Private helper methods

    def _create_dom_request_body(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """
        Create request body for DOM analysis.

        Note: Anthropic uses a different structure than OpenAI.
        System prompts are separate, messages don't include system role.

        Args:
            prompt: Analysis prompt.
            max_tokens: Maximum tokens.
            temperature: Sampling temperature.

        Returns:
            Request body dictionary.
        """
        return {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": (
                "You are an expert web automation engineer. Analyze HTML DOM to find the correct "
                "CSS selector for elements. Always respond with valid JSON containing: selector, "
                "confidence (0.0-1.0), reasoning, and alternatives array."
            ),
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

    def _create_visual_request_body(
        self,
        prompt: str,
        base64_image: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """
        Create request body for visual analysis.

        Anthropic uses a different multimodal structure with content blocks.

        Args:
            prompt: Analysis prompt.
            base64_image: Base64-encoded screenshot.
            max_tokens: Maximum tokens.
            temperature: Sampling temperature.

        Returns:
            Request body dictionary.
        """
        return {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }

    def _create_disambiguation_request_body(
        self,
        prompt: str,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        Create request body for element disambiguation.

        Args:
            prompt: Disambiguation prompt.
            max_tokens: Maximum tokens.

        Returns:
            Request body dictionary.
        """
        return {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": 0.1,  # Low temperature for deterministic selection
            "system": (
                "You are a web automation expert. When given multiple elements and a description, "
                "respond with only the number of the element that best matches the description. "
                "Respond with just the number, no other text."
            ),
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

    def _parse_dom_response(
        self,
        response_data: Dict[str, Any],
        framework: AutomationFramework
    ) -> AIAnalysisResult:
        """
        Parse Anthropic Claude DOM analysis response.

        Anthropic response format:
        {
            "content": [
                {"type": "text", "text": "...JSON..."}
            ]
        }

        Args:
            response_data: Raw API response.
            framework: Target automation framework.

        Returns:
            Parsed AIAnalysisResult.

        Raises:
            Exception: If parsing fails.
        """
        try:
            # Extract text from Anthropic's content array
            content_blocks = response_data.get("content", [])
            if not content_blocks:
                raise ValueError("Empty content array in Anthropic response")
            content = content_blocks[0].get("text", "")
            logger.debug("Raw Anthropic response content: %s", content[:200])

            # Clean markdown formatting
            clean_content = self._clean_markdown(content)
            logger.debug("Cleaned content: %s", clean_content[:200])

            # Parse JSON
            content_json = json.loads(clean_content)

            # Use ResponseParser to handle framework-specific parsing
            return ResponseParser.parse_dom_response(content_json, framework)

        except Exception as e:
            logger.error("Failed to parse Anthropic response: %s", str(e))
            raise Exception(f"Failed to parse Anthropic response: {e}")

    def _parse_visual_response(
        self,
        response_data: Dict[str, Any]
    ) -> AIAnalysisResult:
        """
        Parse Anthropic Claude visual analysis response.

        Args:
            response_data: Raw API response.

        Returns:
            Parsed AIAnalysisResult.

        Raises:
            Exception: If parsing fails.
        """
        try:
            # Extract text from Anthropic's content array
            content_blocks = response_data.get("content", [])
            if not content_blocks:
                raise ValueError("Empty content array in Anthropic response")
            content = content_blocks[0].get("text", "")
            logger.debug("Raw Anthropic visual response: %s", content[:200])

            # Clean markdown formatting
            clean_content = self._clean_markdown(content)

            # Parse JSON
            content_json = json.loads(clean_content)

            # Visual responses are typically in Selenium format (CSS selectors)
            return ResponseParser.parse_dom_response(
                content_json,
                AutomationFramework.SELENIUM
            )

        except Exception as e:
            logger.error("Failed to parse Anthropic visual response: %s", str(e))
            raise Exception(f"Failed to parse Anthropic visual response: {e}")
