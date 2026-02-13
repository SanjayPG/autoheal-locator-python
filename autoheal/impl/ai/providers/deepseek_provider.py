"""
DeepSeek provider implementation for AI services.

This module provides DeepSeek API integration for DOM analysis.
DeepSeek uses an OpenAI-compatible API, so this is a thin wrapper around OpenAIProvider.
"""

import logging
from typing import Optional

from autoheal.impl.ai.providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class DeepSeekProvider(OpenAIProvider):
    """
    DeepSeek API provider for AI-powered element analysis.

    DeepSeek provides an OpenAI-compatible API, making integration straightforward.
    This provider inherits all functionality from OpenAIProvider with DeepSeek-specific defaults.

    Note: DeepSeek does NOT support visual analysis (no vision models).

    Attributes:
        api_key: DeepSeek API key.
        api_url: DeepSeek API endpoint (default: https://api.deepseek.com/v1/chat/completions).
        model: Model name (e.g., 'deepseek-chat', 'deepseek-coder').
        timeout: Request timeout in seconds.

    Examples:
        >>> provider = DeepSeekProvider(
        ...     api_key="sk-...",
        ...     api_url="https://api.deepseek.com/v1/chat/completions",
        ...     model="deepseek-chat"
        ... )
        >>> result = await provider.analyze_dom(
        ...     prompt="Find submit button",
        ...     framework=AutomationFramework.SELENIUM,
        ...     max_tokens=2000,
        ...     temperature=0.7
        ... )
    """

    DEFAULT_API_URL = "https://api.deepseek.com/v1/chat/completions"
    DEFAULT_MODEL = "deepseek-chat"

    def __init__(
        self,
        api_key: str,
        api_url: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: int = 30
    ):
        """
        Initialize DeepSeek provider.

        Args:
            api_key: DeepSeek API key.
            api_url: Optional custom API URL.
            model: Model name to use.
            timeout: Request timeout in seconds.
        """
        # Call parent OpenAIProvider constructor with DeepSeek defaults
        super().__init__(
            api_key=api_key,
            api_url=api_url or self.DEFAULT_API_URL,
            model=model,
            timeout=timeout
        )
        logger.info("DeepSeekProvider initialized with model: %s", model)

    def supports_visual_analysis(self) -> bool:
        """
        Check if DeepSeek supports visual analysis.

        Returns:
            False (DeepSeek does not support visual/image analysis).
        """
        return False

    def get_provider_name(self) -> str:
        """
        Get provider name.

        Returns:
            "DeepSeek"
        """
        return "DeepSeek"

    async def analyze_visual(
        self,
        prompt: str,
        screenshot: bytes,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ):
        """
        Visual analysis is not supported by DeepSeek.

        Args:
            prompt: Analysis prompt.
            screenshot: Screenshot image data.
            max_tokens: Maximum tokens.
            temperature: Sampling temperature.

        Raises:
            NotImplementedError: Always raises as DeepSeek doesn't support visual analysis.
        """
        raise NotImplementedError(
            "DeepSeek does not support visual analysis. "
            "Use OpenAI, Anthropic, or Gemini for visual analysis capabilities."
        )
