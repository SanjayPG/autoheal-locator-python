"""
Ollama provider implementation for AI services.

This module provides local AI model integration supporting both:
- Ollama native API (/api/chat with streaming)
- OpenAI-compatible API (/v1/chat/completions)

Auto-detects the API format based on the endpoint URL.
"""

import base64
import json
import time
import logging
from typing import Dict, Any, Optional, Tuple

import aiohttp

from autoheal.impl.ai.providers.base_provider import BaseAIProvider
from autoheal.impl.ai.providers.response_parser import ResponseParser
from autoheal.models.ai_analysis_result import AIAnalysisResult
from autoheal.models.disambiguation_result import DisambiguationResult
from autoheal.models.enums import AutomationFramework

logger = logging.getLogger(__name__)


class OllamaProvider(BaseAIProvider):
    """
    Local AI provider supporting both Ollama native and OpenAI-compatible APIs.

    Auto-detects the API format based on the endpoint URL:
    - URLs containing '/v1/' use OpenAI-compatible format
    - Other URLs use Ollama native streaming format

    Attributes:
        api_key: Not required for local models (kept for interface compatibility).
        api_url: API endpoint URL. Can be:
            - Ollama native: "http://localhost:11434" (appends /api/chat)
            - OpenAI-compatible: "http://localhost:11434/v1/chat/completions"
        model: Model name (e.g., 'llama2', 'deepseek-coder-v2:16b').
        timeout: Request timeout in seconds.

    Examples:
        >>> # OpenAI-compatible endpoint
        >>> provider = OllamaProvider(
        ...     api_url="https://my-server.com/v1/chat/completions",
        ...     model="deepseek-coder-v2:16b"
        ... )

        >>> # Ollama native endpoint
        >>> provider = OllamaProvider(
        ...     api_url="http://localhost:11434",
        ...     model="llama2"
        ... )
    """

    DEFAULT_API_URL = "http://localhost:11434"
    DEFAULT_MODEL = "llama2"

    # Models known to support visual analysis
    VISION_MODELS = {"llava", "bakllava", "llava:13b", "llava:34b"}

    def __init__(
        self,
        api_key: str = "",
        api_url: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: int = 60
    ):
        super().__init__(
            api_key=api_key or "",
            api_url=api_url or self.DEFAULT_API_URL,
            model=model,
            timeout=timeout
        )
        self._openai_compat = self._detect_openai_compatible()
        mode = "OpenAI-compatible" if self._openai_compat else "Ollama native"
        logger.info(
            "OllamaProvider initialized with model: %s, mode: %s, url: %s",
            model, mode, self.api_url
        )

    def _detect_openai_compatible(self) -> bool:
        """Detect if the API URL is OpenAI-compatible based on path."""
        return "/v1/" in self.api_url

    def _get_chat_endpoint(self) -> str:
        """Get the chat endpoint URL based on detected mode."""
        if self._openai_compat:
            # URL is already the full endpoint (e.g., .../v1/chat/completions)
            return self.api_url
        # Ollama native: append /api/chat to base URL
        return f"{self.api_url}/api/chat"

    async def analyze_dom(
        self,
        prompt: str,
        framework: AutomationFramework,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> AIAnalysisResult:
        start_time = time.time()
        endpoint = self._get_chat_endpoint()
        self._log_request(endpoint, framework)

        request_body = self._create_dom_request_body(prompt, max_tokens, temperature)

        try:
            async with aiohttp.ClientSession() as session:
                headers = self._create_headers()

                async with session.post(
                    endpoint,
                    headers=headers,
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        logger.error("Ollama API call failed: %d - %s", response.status, error_text)
                        raise Exception(f"Ollama API call failed: {response.status}")

                    full_response, tokens_used = await self._read_response(response)
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    self._log_response(len(full_response), processing_time_ms)

                    result = self._parse_dom_response(full_response, framework)
                    result.tokens_used = tokens_used
                    return result

        except aiohttp.ClientError as e:
            logger.error("Ollama DOM analysis failed: %s", str(e))
            raise Exception(f"Ollama DOM analysis failed: {e}")

    async def analyze_visual(
        self,
        prompt: str,
        screenshot: bytes,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> AIAnalysisResult:
        if not self.supports_visual_analysis():
            raise NotImplementedError(
                f"Model '{self.model}' does not support visual analysis. "
                f"Use a vision-capable model like llava or bakllava."
            )

        start_time = time.time()
        endpoint = self._get_chat_endpoint()
        self._log_request(endpoint)

        base64_image = base64.b64encode(screenshot).decode('utf-8')
        request_body = self._create_visual_request_body(
            prompt, base64_image, max_tokens, temperature
        )

        try:
            async with aiohttp.ClientSession() as session:
                headers = self._create_headers()

                async with session.post(
                    endpoint,
                    headers=headers,
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        logger.error("Ollama Vision API call failed: %d - %s", response.status, error_text)
                        raise Exception(f"Ollama Vision API call failed: {response.status}")

                    full_response, tokens_used = await self._read_response(response)
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    self._log_response(len(full_response), processing_time_ms)

                    result = self._parse_visual_response(full_response)
                    result.tokens_used = tokens_used
                    return result

        except aiohttp.ClientError as e:
            logger.error("Ollama visual analysis failed: %s", str(e))
            raise Exception(f"Ollama visual analysis failed: {e}")

    async def disambiguate(
        self,
        prompt: str,
        max_tokens: int = 10
    ) -> DisambiguationResult:
        endpoint = self._get_chat_endpoint()
        request_body = self._create_disambiguation_request_body(prompt, max_tokens)

        try:
            async with aiohttp.ClientSession() as session:
                headers = self._create_headers()

                async with session.post(
                    endpoint,
                    headers=headers,
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        logger.error("Ollama disambiguation failed: %d - %s", response.status, error_text)
                        raise Exception(f"Ollama disambiguation failed: {response.status}")

                    full_response, tokens_used = await self._read_response(response)
                    content = full_response.strip()
                    selected_index = ResponseParser.parse_disambiguation_response(content)

                    return DisambiguationResult(
                        selected_index=selected_index,
                        tokens_used=tokens_used
                    )

        except Exception as e:
            logger.error("Ollama disambiguation failed: %s", str(e))
            return DisambiguationResult(selected_index=1, tokens_used=0)

    def supports_visual_analysis(self) -> bool:
        model_lower = self.model.lower()
        return model_lower in self.VISION_MODELS or any(
            model_lower.startswith(f"{vm}:") for vm in self.VISION_MODELS
        )

    def get_provider_name(self) -> str:
        return "Ollama"

    # ==================== Response Reading ====================

    async def _read_response(self, response: aiohttp.ClientResponse) -> Tuple[str, int]:
        """
        Read response in the appropriate format (OpenAI JSON or Ollama streaming).

        Returns:
            Tuple of (content_text, tokens_used).
        """
        if self._openai_compat:
            return await self._read_openai_response(response)
        return await self._collect_streaming_response(response)

    async def _read_openai_response(self, response: aiohttp.ClientResponse) -> Tuple[str, int]:
        """
        Parse a standard OpenAI-compatible JSON response.

        Expected format:
        {
            "choices": [{"message": {"content": "..."}}],
            "usage": {"prompt_tokens": N, "completion_tokens": N, "total_tokens": N}
        }
        """
        response_data = await response.json()
        choices = response_data.get("choices", [])
        if not choices:
            raise ValueError("Empty choices array in OpenAI-compatible response")
        content = choices[0].get("message", {}).get("content", "")

        tokens_used = 0
        usage = response_data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        tokens_used = prompt_tokens + completion_tokens
        logger.debug(
            "OpenAI-compat token usage - input: %d, output: %d, total: %d",
            prompt_tokens, completion_tokens, tokens_used
        )

        return content, tokens_used

    async def _collect_streaming_response(self, response: aiohttp.ClientResponse) -> Tuple[str, int]:
        """
        Collect full response from Ollama's native streaming JSON format.

        Ollama returns responses as streaming JSON lines, each containing a chunk.
        Token counts are available in the final chunk (done=true).
        """
        full_content = ""
        tokens_used = 0

        async for line in response.content:
            if line:
                try:
                    chunk = json.loads(line.decode('utf-8'))
                    if "message" in chunk and "content" in chunk["message"]:
                        full_content += chunk["message"]["content"]

                    if chunk.get("done", False):
                        prompt_tokens = chunk.get("prompt_eval_count", 0)
                        completion_tokens = chunk.get("eval_count", 0)
                        tokens_used = prompt_tokens + completion_tokens
                        logger.debug(
                            "Ollama token usage - input: %d, output: %d, total: %d",
                            prompt_tokens, completion_tokens, tokens_used
                        )
                        break
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Ollama streaming chunk: %s", line)
                    continue

        return full_content, tokens_used

    # ==================== Request Body Creation ====================

    def _create_dom_request_body(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Create request body for DOM analysis, adapting to the API format."""
        system_message = (
            "You are an expert web automation engineer. Analyze HTML DOM to find the correct "
            "CSS selector for elements. Always respond with valid JSON containing: selector, "
            "confidence (0.0-1.0), reasoning, and alternatives array."
        )

        if self._openai_compat:
            return {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ]
            }
        else:
            return {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "stream": True,
                "options": {"temperature": temperature}
            }

    def _create_visual_request_body(
        self,
        prompt: str,
        base64_image: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Create request body for visual analysis."""
        if self._openai_compat:
            return {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
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
        else:
            return {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [base64_image]
                    }
                ],
                "stream": True,
                "options": {"temperature": temperature}
            }

    def _create_disambiguation_request_body(
        self,
        prompt: str,
        max_tokens: int = 10
    ) -> Dict[str, Any]:
        """Create request body for element disambiguation."""
        system_message = (
            "You are a web automation expert. When given multiple elements and a description, "
            "respond with only the number of the element that best matches the description. "
            "Respond with just the number, no other text."
        )

        if self._openai_compat:
            return {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": 0.1,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ]
            }
        else:
            return {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "stream": True,
                "options": {"temperature": 0.1}
            }

    # ==================== Response Parsing ====================

    def _parse_dom_response(
        self,
        response_text: str,
        framework: AutomationFramework
    ) -> AIAnalysisResult:
        try:
            logger.debug("Raw Ollama response content: %s", response_text[:200])
            clean_content = self._clean_markdown(response_text)
            logger.debug("Cleaned content: %s", clean_content[:200])
            content_json = json.loads(clean_content)
            return ResponseParser.parse_dom_response(content_json, framework)
        except Exception as e:
            logger.error("Failed to parse Ollama response: %s", str(e))
            raise Exception(f"Failed to parse Ollama response: {e}")

    def _parse_visual_response(
        self,
        response_text: str
    ) -> AIAnalysisResult:
        try:
            logger.debug("Raw Ollama visual response: %s", response_text[:200])
            clean_content = self._clean_markdown(response_text)
            content_json = json.loads(clean_content)
            return ResponseParser.parse_dom_response(
                content_json, AutomationFramework.SELENIUM
            )
        except Exception as e:
            logger.error("Failed to parse Ollama visual response: %s", str(e))
            raise Exception(f"Failed to parse Ollama visual response: {e}")
