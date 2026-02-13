"""
OpenAI provider implementation for AI services.

This module provides OpenAI API integration for DOM and visual analysis.
Supports GPT-4, GPT-4o, GPT-4o-mini, and other OpenAI models.
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


class OpenAIProvider(BaseAIProvider):
    """
    OpenAI API provider for AI-powered element analysis.

    Supports both DOM analysis (text-based) and visual analysis (image-based)
    using OpenAI's GPT models including GPT-4 Vision.

    Attributes:
        api_key: OpenAI API key.
        api_url: OpenAI API endpoint (default: https://api.openai.com/v1/chat/completions).
        model: Model name (e.g., 'gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo').
        timeout: Request timeout in seconds.

    Examples:
        >>> provider = OpenAIProvider(
        ...     api_key="sk-...",
        ...     api_url="https://api.openai.com/v1/chat/completions",
        ...     model="gpt-4o-mini"
        ... )
        >>> result = await provider.analyze_dom(
        ...     prompt="Find submit button",
        ...     framework=AutomationFramework.SELENIUM,
        ...     max_tokens=2000,
        ...     temperature=0.7
        ... )
    """

    DEFAULT_API_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(
        self,
        api_key: str,
        api_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
        timeout: int = 30
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key.
            api_url: Optional custom API URL.
            model: Model name to use.
            timeout: Request timeout in seconds.
        """
        super().__init__(
            api_key=api_key,
            api_url=api_url or self.DEFAULT_API_URL,
            model=model,
            timeout=timeout
        )
        logger.info("OpenAIProvider initialized with model: %s", model)

    async def analyze_dom(
        self,
        prompt: str,
        framework: AutomationFramework,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> AIAnalysisResult:
        """
        Perform DOM analysis using OpenAI API.

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
                    "Authorization": f"Bearer {self.api_key}"
                })

                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        logger.error("OpenAI API call failed: %d - %s", response.status, error_text)
                        raise Exception(f"OpenAI API call failed: {response.status}")

                    response_data = await response.json()
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    self._log_response(len(str(response_data)), processing_time_ms)

                    # Extract token usage from response
                    tokens_used = self._extract_token_usage(response_data)

                    result = self._parse_dom_response(response_data, framework)
                    result.tokens_used = tokens_used
                    return result

        except aiohttp.ClientError as e:
            logger.error("OpenAI DOM analysis failed: %s", str(e))
            raise Exception(f"OpenAI DOM analysis failed: {e}")

    async def analyze_visual(
        self,
        prompt: str,
        screenshot: bytes,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> AIAnalysisResult:
        """
        Perform visual analysis using OpenAI Vision API.

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
                    "Authorization": f"Bearer {self.api_key}"
                })

                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        logger.error("OpenAI Vision API call failed: %d - %s", response.status, error_text)
                        raise Exception(f"OpenAI Vision API call failed: {response.status}")

                    response_data = await response.json()
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    self._log_response(len(str(response_data)), processing_time_ms)

                    # Extract token usage from response
                    tokens_used = self._extract_token_usage(response_data)

                    result = self._parse_visual_response(response_data)
                    result.tokens_used = tokens_used
                    return result

        except aiohttp.ClientError as e:
            logger.error("OpenAI visual analysis failed: %s", str(e))
            raise Exception(f"OpenAI visual analysis failed: {e}")

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
                    "Authorization": f"Bearer {self.api_key}"
                })

                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        logger.error("OpenAI disambiguation failed: %d - %s", response.status, error_text)
                        raise Exception(f"OpenAI disambiguation failed: {response.status}")

                    response_data = await response.json()
                    choices = response_data.get("choices", [])
                    if not choices:
                        raise ValueError("Empty choices array in OpenAI response")
                    content = choices[0].get("message", {}).get("content", "").strip()
                    tokens_used = self._extract_token_usage(response_data)
                    selected_index = ResponseParser.parse_disambiguation_response(content)

                    return DisambiguationResult(
                        selected_index=selected_index,
                        tokens_used=tokens_used
                    )

        except Exception as e:
            logger.error("OpenAI disambiguation failed: %s", str(e))
            # Default to first element on error
            return DisambiguationResult(selected_index=1, tokens_used=0)

    def supports_visual_analysis(self) -> bool:
        """
        Check if OpenAI supports visual analysis.

        Returns:
            True (OpenAI GPT-4 Vision models support image analysis).
        """
        return True

    def get_provider_name(self) -> str:
        """
        Get provider name.

        Returns:
            "OpenAI"
        """
        return "OpenAI"

    # Private helper methods

    def _create_dom_request_body(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """
        Create request body for DOM analysis.

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
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert web automation engineer. Analyze HTML DOM to find the correct "
                        "CSS selector for elements. Always respond with valid JSON containing: selector, "
                        "confidence (0.0-1.0), reasoning, and alternatives array."
                    )
                },
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
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
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
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a web automation expert. When given multiple elements and a description, "
                        "respond with only the number of the element that best matches the description. "
                        "Respond with just the number, no other text."
                    )
                },
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
        Parse OpenAI DOM analysis response.

        Args:
            response_data: Raw API response.
            framework: Target automation framework.

        Returns:
            Parsed AIAnalysisResult.

        Raises:
            Exception: If parsing fails.
        """
        try:
            choices = response_data.get("choices", [])
            if not choices:
                raise ValueError("Empty choices array in OpenAI response")
            content = choices[0].get("message", {}).get("content", "")
            logger.debug("Raw OpenAI response content: %s", content[:200])

            # Clean markdown formatting
            clean_content = self._clean_markdown(content)
            logger.debug("Cleaned content: %s", clean_content[:200])

            # Parse JSON
            content_json = json.loads(clean_content)

            # Use ResponseParser to handle framework-specific parsing
            return ResponseParser.parse_dom_response(content_json, framework)

        except Exception as e:
            logger.error("Failed to parse OpenAI response: %s", str(e))
            raise Exception(f"Failed to parse OpenAI response: {e}")

    def _extract_token_usage(self, response_data: Dict[str, Any]) -> int:
        """
        Extract total token usage from OpenAI API response.

        Args:
            response_data: Raw API response.

        Returns:
            Total tokens used (input + output), or 0 if not available.
        """
        try:
            usage = response_data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            total = input_tokens + output_tokens
            logger.debug("Token usage - input: %d, output: %d, total: %d",
                        input_tokens, output_tokens, total)
            return total
        except Exception as e:
            logger.debug("Could not extract token usage: %s", str(e))
            return 0

    def _parse_visual_response(
        self,
        response_data: Dict[str, Any]
    ) -> AIAnalysisResult:
        """
        Parse OpenAI visual analysis response.

        Args:
            response_data: Raw API response.

        Returns:
            Parsed AIAnalysisResult.

        Raises:
            Exception: If parsing fails.
        """
        try:
            choices = response_data.get("choices", [])
            if not choices:
                raise ValueError("Empty choices array in OpenAI response")
            content = choices[0].get("message", {}).get("content", "")
            logger.debug("Raw OpenAI visual response: %s", content[:200])

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
            logger.error("Failed to parse OpenAI visual response: %s", str(e))
            raise Exception(f"Failed to parse OpenAI visual response: {e}")
