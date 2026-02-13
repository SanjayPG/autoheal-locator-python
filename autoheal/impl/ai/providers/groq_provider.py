"""
Groq inference provider implementation for AI services.

This module provides Groq API integration for DOM and visual analysis.
Groq uses an OpenAI-compatible API, so this is a thin wrapper around OpenAIProvider.
Groq offers fast, free inference for open-source models.
"""

import logging
from typing import Optional

from autoheal.impl.ai.providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class GroqProvider(OpenAIProvider):
    """
    Groq API provider for AI-powered element analysis.

    Groq provides an OpenAI-compatible API with fast inference for open-source models.
    This provider inherits all functionality from OpenAIProvider with Groq-specific defaults.

    Groq supports both text analysis (via Llama models) and visual analysis (via vision models).
    The service offers a generous free tier making it ideal for development and testing.

    Supported models:
        - Text: llama-3.3-70b-versatile, llama-3.1-70b-versatile, mixtral-8x7b
        - Vision: llama-3.2-11b-vision-preview, llama-3.2-90b-vision-preview

    Attributes:
        api_key: Groq API key.
        api_url: Groq API endpoint (default: https://api.groq.com/openai/v1/chat/completions).
        model: Model name (e.g., 'llama-3.3-70b-versatile').
        timeout: Request timeout in seconds.

    Examples:
        >>> # Text analysis with default model
        >>> provider = GroqProvider(
        ...     api_key="gsk_...",
        ...     model="llama-3.3-70b-versatile"
        ... )
        >>> result = await provider.analyze_dom(
        ...     prompt="Find submit button",
        ...     framework=AutomationFramework.SELENIUM,
        ...     max_tokens=2000,
        ...     temperature=0.7
        ... )

        >>> # Visual analysis with vision model
        >>> vision_provider = GroqProvider(
        ...     api_key="gsk_...",
        ...     model="llama-3.2-11b-vision-preview"
        ... )
        >>> result = await vision_provider.analyze_visual(
        ...     prompt="Find the login button",
        ...     screenshot=screenshot_bytes,
        ...     max_tokens=1000
        ... )
    """

    DEFAULT_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    DEFAULT_VISION_MODEL = "llama-3.2-11b-vision-preview"

    # Vision-capable models
    VISION_MODELS = {
        "llama-3.2-11b-vision-preview",
        "llama-3.2-90b-vision-preview",
    }

    def __init__(
        self,
        api_key: str,
        api_url: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: int = 30
    ):
        """
        Initialize Groq provider.

        Args:
            api_key: Groq API key (get free key from https://console.groq.com).
            api_url: Optional custom API URL.
            model: Model name to use.
            timeout: Request timeout in seconds.
        """
        # Call parent OpenAIProvider constructor with Groq defaults
        super().__init__(
            api_key=api_key,
            api_url=api_url or self.DEFAULT_API_URL,
            model=model,
            timeout=timeout
        )
        logger.info("GroqProvider initialized with model: %s", model)

    def supports_visual_analysis(self) -> bool:
        """
        Check if the current model supports visual analysis.

        Returns:
            True if using a vision-capable model, False otherwise.
        """
        return self.model in self.VISION_MODELS

    def get_provider_name(self) -> str:
        """
        Get provider name.

        Returns:
            "Groq"
        """
        return "Groq"

    async def analyze_visual(
        self,
        prompt: str,
        screenshot: bytes,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ):
        """
        Analyze screenshot to locate element using Groq's vision models.

        Args:
            prompt: Analysis prompt describing what to find.
            screenshot: Screenshot image data.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature (0.0-1.0).

        Returns:
            Analysis result with suggested selectors.

        Raises:
            NotImplementedError: If current model doesn't support visual analysis.
            AIServiceException: If API call fails.
        """
        if not self.supports_visual_analysis():
            raise NotImplementedError(
                f"Model '{self.model}' does not support visual analysis. "
                f"Use a vision model like '{self.DEFAULT_VISION_MODEL}' instead."
            )

        # Use parent OpenAIProvider's visual analysis implementation
        return await super().analyze_visual(prompt, screenshot, max_tokens, temperature)
