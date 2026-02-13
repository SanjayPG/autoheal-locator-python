"""
Google Gemini provider implementation for AI services.

This module provides Google Gemini API integration for DOM and visual analysis.
Supports Gemini 1.5 Pro and Gemini 1.5 Flash models.
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


class GeminiProvider(BaseAIProvider):
    """
    Google Gemini API provider for AI-powered element analysis.

    Supports both DOM analysis (text-based) and visual analysis (image-based)
    using Google's Gemini 1.5 family of models including Pro and Flash.

    Attributes:
        api_key: Google API key.
        api_url: Gemini API base URL (default: https://generativelanguage.googleapis.com/v1).
        model: Model name (e.g., 'gemini-1.5-pro', 'gemini-1.5-flash').
        timeout: Request timeout in seconds.

    Examples:
        >>> provider = GeminiProvider(
        ...     api_key="AIza...",
        ...     api_url="https://generativelanguage.googleapis.com/v1",
        ...     model="gemini-1.5-flash"
        ... )
        >>> result = await provider.analyze_dom(
        ...     prompt="Find submit button",
        ...     framework=AutomationFramework.SELENIUM,
        ...     max_tokens=2000,
        ...     temperature=0.7
        ... )
    """

    DEFAULT_API_URL = "https://generativelanguage.googleapis.com/v1"

    def __init__(
        self,
        api_key: str,
        api_url: Optional[str] = None,
        model: str = "gemini-1.5-flash",
        timeout: int = 30
    ):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google API key.
            api_url: Optional custom API base URL.
            model: Model name to use.
            timeout: Request timeout in seconds.
        """
        super().__init__(
            api_key=api_key,
            api_url=api_url or self.DEFAULT_API_URL,
            model=model,
            timeout=timeout
        )
        logger.info("GeminiProvider initialized with model: %s", model)

    def _get_endpoint_url(self) -> str:
        """
        Build the full endpoint URL for Gemini API.

        Gemini uses the format: {base_url}/models/{model}:generateContent

        Returns:
            Full API endpoint URL.
        """
        return f"{self.api_url}/models/{self.model}:generateContent"

    async def analyze_dom(
        self,
        prompt: str,
        framework: AutomationFramework,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> AIAnalysisResult:
        """
        Perform DOM analysis using Google Gemini API.

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
        endpoint_url = self._get_endpoint_url()
        self._log_request(endpoint_url, framework)

        request_body = self._create_dom_request_body(prompt, max_tokens, temperature)

        try:
            # Gemini uses API key as query parameter
            url_with_key = f"{endpoint_url}?key={self.api_key}"

            async with aiohttp.ClientSession() as session:
                headers = self._create_headers()

                async with session.post(
                    url_with_key,
                    headers=headers,
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        logger.error("Gemini API call failed: %d - %s", response.status, error_text)
                        raise Exception(f"Gemini API call failed: {response.status}")

                    response_data = await response.json()
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    self._log_response(len(str(response_data)), processing_time_ms)

                    # Extract token usage from response
                    tokens_used = self._extract_token_usage(response_data)

                    result = self._parse_dom_response(response_data, framework)
                    result.tokens_used = tokens_used
                    return result

        except aiohttp.ClientError as e:
            logger.error("Gemini DOM analysis failed: %s", str(e))
            raise Exception(f"Gemini DOM analysis failed: {e}")

    async def analyze_visual(
        self,
        prompt: str,
        screenshot: bytes,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> AIAnalysisResult:
        """
        Perform visual analysis using Google Gemini Vision API.

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
        endpoint_url = self._get_endpoint_url()
        self._log_request(endpoint_url)

        # Encode screenshot to base64
        base64_image = base64.b64encode(screenshot).decode('utf-8')

        request_body = self._create_visual_request_body(
            prompt,
            base64_image,
            max_tokens,
            temperature
        )

        try:
            url_with_key = f"{endpoint_url}?key={self.api_key}"

            async with aiohttp.ClientSession() as session:
                headers = self._create_headers()

                async with session.post(
                    url_with_key,
                    headers=headers,
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        logger.error("Gemini Vision API call failed: %d - %s", response.status, error_text)
                        raise Exception(f"Gemini Vision API call failed: {response.status}")

                    response_data = await response.json()
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    self._log_response(len(str(response_data)), processing_time_ms)

                    # Extract token usage from response
                    tokens_used = self._extract_token_usage(response_data)

                    result = self._parse_visual_response(response_data)
                    result.tokens_used = tokens_used
                    return result

        except aiohttp.ClientError as e:
            logger.error("Gemini visual analysis failed: %s", str(e))
            raise Exception(f"Gemini visual analysis failed: {e}")

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
        endpoint_url = self._get_endpoint_url()
        request_body = self._create_disambiguation_request_body(prompt, max_tokens)

        try:
            url_with_key = f"{endpoint_url}?key={self.api_key}"

            async with aiohttp.ClientSession() as session:
                headers = self._create_headers()

                async with session.post(
                    url_with_key,
                    headers=headers,
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        logger.error("Gemini disambiguation failed: %d - %s", response.status, error_text)
                        raise Exception(f"Gemini disambiguation failed: {response.status}")

                    response_data = await response.json()
                    # Gemini response format: candidates[0].content.parts[0].text
                    candidates = response_data.get("candidates", [])
                    if not candidates:
                        raise ValueError("Empty candidates array in Gemini response")
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if not parts:
                        raise ValueError("Empty parts array in Gemini response")
                    content = parts[0].get("text", "").strip()
                    tokens_used = self._extract_token_usage(response_data)
                    selected_index = ResponseParser.parse_disambiguation_response(content)

                    return DisambiguationResult(
                        selected_index=selected_index,
                        tokens_used=tokens_used
                    )

        except Exception as e:
            logger.error("Gemini disambiguation failed: %s", str(e))
            # Default to first element on error
            return DisambiguationResult(selected_index=1, tokens_used=0)

    def supports_visual_analysis(self) -> bool:
        """
        Check if Gemini supports visual analysis.

        Returns:
            True (Gemini 1.5 models support multimodal input).
        """
        return True

    def get_provider_name(self) -> str:
        """
        Get provider name.

        Returns:
            "Gemini"
        """
        return "Gemini"

    def _extract_token_usage(self, response_data: Dict[str, Any]) -> int:
        """
        Extract total token usage from Gemini API response.

        Args:
            response_data: Raw API response.

        Returns:
            Total tokens used (input + output), or 0 if not available.
        """
        try:
            # Gemini uses usageMetadata with promptTokenCount and candidatesTokenCount
            usage = response_data.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)
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

        Gemini uses a different structure with "contents" and "parts".

        Args:
            prompt: Analysis prompt.
            max_tokens: Maximum tokens.
            temperature: Sampling temperature.

        Returns:
            Request body dictionary.
        """
        # Add system instruction to the prompt
        system_instruction = (
            "You are an expert web automation engineer. Analyze HTML DOM to find the correct "
            "CSS selector for elements. Always respond with valid JSON containing: selector, "
            "confidence (0.0-1.0), reasoning, and alternatives array.\n\n"
        )

        return {
            "contents": [
                {
                    "parts": [
                        {
                            "text": system_instruction + prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
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

        Gemini multimodal format with image and text parts.

        Args:
            prompt: Analysis prompt.
            base64_image: Base64-encoded screenshot.
            max_tokens: Maximum tokens.
            temperature: Sampling temperature.

        Returns:
            Request body dictionary.
        """
        return {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": base64_image
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
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
        system_instruction = (
            "You are a web automation expert. When given multiple elements and a description, "
            "respond with only the number of the element that best matches the description. "
            "Respond with just the number, no other text.\n\n"
        )

        return {
            "contents": [
                {
                    "parts": [
                        {
                            "text": system_instruction + prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,  # Low temperature for deterministic selection
                "maxOutputTokens": max_tokens
            }
        }

    def _parse_dom_response(
        self,
        response_data: Dict[str, Any],
        framework: AutomationFramework
    ) -> AIAnalysisResult:
        """
        Parse Gemini DOM analysis response.

        Gemini response format:
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "...JSON..."}
                        ]
                    }
                }
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
            # Extract text from Gemini's nested structure
            candidates = response_data.get("candidates", [])
            if not candidates:
                raise ValueError("Empty candidates array in Gemini response")
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise ValueError("Empty parts array in Gemini response")
            content = parts[0].get("text", "")
            logger.debug("Raw Gemini response content: %s", content[:200])

            # Clean markdown formatting
            clean_content = self._clean_markdown(content)
            logger.debug("Cleaned content: %s", clean_content[:200])

            # Parse JSON
            content_json = json.loads(clean_content)

            # Use ResponseParser to handle framework-specific parsing
            return ResponseParser.parse_dom_response(content_json, framework)

        except Exception as e:
            logger.error("Failed to parse Gemini response: %s", str(e))
            raise Exception(f"Failed to parse Gemini response: {e}")

    def _parse_visual_response(
        self,
        response_data: Dict[str, Any]
    ) -> AIAnalysisResult:
        """
        Parse Gemini visual analysis response.

        Args:
            response_data: Raw API response.

        Returns:
            Parsed AIAnalysisResult.

        Raises:
            Exception: If parsing fails.
        """
        try:
            # Extract text from Gemini's nested structure
            candidates = response_data.get("candidates", [])
            if not candidates:
                raise ValueError("Empty candidates array in Gemini response")
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise ValueError("Empty parts array in Gemini response")
            content = parts[0].get("text", "")
            logger.debug("Raw Gemini visual response: %s", content[:200])

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
            logger.error("Failed to parse Gemini visual response: %s", str(e))
            raise Exception(f"Failed to parse Gemini visual response: {e}")
