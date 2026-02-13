"""
Grok (X.AI) provider implementation for AI services.

This module provides Grok API integration for DOM analysis.
Grok uses an OpenAI-compatible API, so this is a thin wrapper around OpenAIProvider.
"""

import logging
from typing import Optional

from autoheal.impl.ai.providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class GrokProvider(OpenAIProvider):
    """
    Grok (X.AI) API provider for AI-powered element analysis.

    Grok provides an OpenAI-compatible API, making integration straightforward.
    This provider inherits all functionality from OpenAIProvider with Grok-specific defaults.

    Note: Grok does NOT support visual analysis (no vision models currently).

    Attributes:
        api_key: Grok API key.
        api_url: Grok API endpoint (default: https://api.x.ai/v1/chat/completions).
        model: Model name (e.g., 'grok-beta').
        timeout: Request timeout in seconds.

    Examples:
        >>> provider = GrokProvider(
        ...     api_key="xai-...",
        ...     api_url="https://api.x.ai/v1/chat/completions",
        ...     model="grok-beta"
        ... )
        >>> result = await provider.analyze_dom(
        ...     prompt="Find submit button",
        ...     framework=AutomationFramework.SELENIUM,
        ...     max_tokens=2000,
        ...     temperature=0.7
        ... )
    """

    DEFAULT_API_URL = "https://api.x.ai/v1/chat/completions"
    DEFAULT_MODEL = "grok-beta"

    def __init__(
        self,
        api_key: str,
        api_url: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: int = 30
    ):
        """
        Initialize Grok provider.

        Args:
            api_key: Grok API key.
            api_url: Optional custom API URL.
            model: Model name to use.
            timeout: Request timeout in seconds.
        """
        # Call parent OpenAIProvider constructor with Grok defaults
        super().__init__(
            api_key=api_key,
            api_url=api_url or self.DEFAULT_API_URL,
            model=model,
            timeout=timeout
        )
        logger.info("GrokProvider initialized with model: %s", model)

    def supports_visual_analysis(self) -> bool:
        """
        Check if Grok supports visual analysis.

        Returns:
            False (Grok does not currently support visual/image analysis).
        """
        return False

    def get_provider_name(self) -> str:
        """
        Get provider name.

        Returns:
            "Grok"
        """
        return "Grok"

    async def analyze_visual(
        self,
        prompt: str,
        screenshot: bytes,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ):
        """
        Visual analysis is not supported by Grok.

        Args:
            prompt: Analysis prompt.
            screenshot: Screenshot image data.
            max_tokens: Maximum tokens.
            temperature: Sampling temperature.

        Raises:
            NotImplementedError: Always raises as Grok doesn't support visual analysis.
        """
        raise NotImplementedError(
            "Grok does not currently support visual analysis. "
            "Use OpenAI, Anthropic, or Gemini for visual analysis capabilities."
        )
