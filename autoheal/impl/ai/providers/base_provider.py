"""
Base provider abstract class for AI services.

This module defines the abstract interface that all AI providers must implement.
"""

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Dict, Any, Optional, Union
import logging

from autoheal.models.ai_analysis_result import AIAnalysisResult
from autoheal.models.disambiguation_result import DisambiguationResult
from autoheal.models.enums import AutomationFramework

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    """
    Abstract base class for AI service providers.

    All AI providers (OpenAI, Anthropic, Gemini, etc.) must implement this interface.

    Attributes:
        api_key: API key for authentication.
        api_url: Base URL for the API endpoint.
        model: Model name/identifier.
        timeout: Request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str,
        api_url: str,
        model: str,
        timeout: Union[int, timedelta] = 30
    ):
        """
        Initialize the base provider.

        Args:
            api_key: API key for authentication.
            api_url: Base URL for the API endpoint.
            model: Model name/identifier.
            timeout: Request timeout in seconds (int) or timedelta.
        """
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        # Convert timedelta to seconds if needed
        if isinstance(timeout, timedelta):
            self.timeout = int(timeout.total_seconds())
        else:
            self.timeout = timeout

    @abstractmethod
    async def analyze_dom(
        self,
        prompt: str,
        framework: AutomationFramework,
        max_tokens: int,
        temperature: float
    ) -> AIAnalysisResult:
        """
        Perform DOM analysis using the provider's API.

        Args:
            prompt: The analysis prompt.
            framework: Target automation framework (SELENIUM or PLAYWRIGHT).
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature (0.0-1.0).

        Returns:
            AIAnalysisResult with recommended selectors.

        Raises:
            Exception: If the API call fails.
        """
        pass

    @abstractmethod
    async def analyze_visual(
        self,
        prompt: str,
        screenshot: bytes,
        max_tokens: int,
        temperature: float
    ) -> AIAnalysisResult:
        """
        Perform visual analysis using screenshot.

        Args:
            prompt: The analysis prompt.
            screenshot: Screenshot image data.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.

        Returns:
            AIAnalysisResult with recommended selectors.

        Raises:
            Exception: If the API call fails.
            NotImplementedError: If provider doesn't support visual analysis.
        """
        pass

    @abstractmethod
    async def disambiguate(
        self,
        prompt: str,
        max_tokens: int = 10
    ) -> DisambiguationResult:
        """
        Select best matching element index from multiple candidates.

        Args:
            prompt: Disambiguation prompt with element details.
            max_tokens: Maximum tokens (usually very small for number response).

        Returns:
            DisambiguationResult with selected index and tokens used.

        Raises:
            Exception: If the API call fails.
        """
        pass

    @abstractmethod
    def supports_visual_analysis(self) -> bool:
        """
        Check if this provider supports visual/image analysis.

        Returns:
            True if visual analysis is supported, False otherwise.
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the provider name for logging/debugging.

        Returns:
            Provider name (e.g., "OpenAI", "Anthropic", "Gemini").
        """
        pass

    def _clean_markdown(self, content: str) -> str:
        """
        Clean markdown formatting from AI response content.

        Many AI models return JSON wrapped in markdown code blocks.
        This utility removes those wrappers.

        Args:
            content: Raw content from AI response.

        Returns:
            Cleaned content without markdown formatting.

        Examples:
            >>> provider._clean_markdown("```json\\n{...}\\n```")
            '{...}'
            >>> provider._clean_markdown("```\\n{...}\\n```")
            '{...}'
        """
        clean_content = content.strip()

        # Remove ```json prefix
        if clean_content.startswith("```json"):
            clean_content = clean_content[7:]

        # Remove ``` prefix
        if clean_content.startswith("```"):
            clean_content = clean_content[3:]

        # Remove ``` suffix
        if clean_content.endswith("```"):
            clean_content = clean_content[:-3]

        return clean_content.strip()

    def _create_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Create HTTP headers for API request.

        Args:
            additional_headers: Optional additional headers to include.

        Returns:
            Dictionary of HTTP headers.
        """
        headers = {
            "Content-Type": "application/json"
        }

        if additional_headers:
            headers.update(additional_headers)

        return headers

    def _log_request(self, endpoint: str, framework: Optional[AutomationFramework] = None) -> None:
        """
        Log API request for debugging.

        Args:
            endpoint: API endpoint being called.
            framework: Optional framework context.
        """
        if framework:
            logger.debug(
                "%s API request to %s (framework: %s)",
                self.get_provider_name(),
                endpoint,
                framework.value
            )
        else:
            logger.debug(
                "%s API request to %s",
                self.get_provider_name(),
                endpoint
            )

    def _log_response(self, response_length: int, processing_time_ms: int) -> None:
        """
        Log API response for debugging.

        Args:
            response_length: Length of response content.
            processing_time_ms: Time taken to process request.
        """
        logger.debug(
            "%s API response received (length: %d, time: %dms)",
            self.get_provider_name(),
            response_length,
            processing_time_ms
        )
