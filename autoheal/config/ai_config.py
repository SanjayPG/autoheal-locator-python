"""
AI Configuration for AutoHeal framework.

This module provides configuration for AI service integration with comprehensive
properties file support. Supports multiple AI providers with smart defaults and
environment variable overrides.
"""

import os
import re
from datetime import timedelta
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator

from autoheal.models.enums import AIProvider


# Provider-specific API endpoints
DEFAULT_API_ENDPOINTS: Dict[AIProvider, str] = {
    AIProvider.OPENAI: "https://api.openai.com/v1/chat/completions",
    AIProvider.GOOGLE_GEMINI: "https://generativelanguage.googleapis.com/v1",
    AIProvider.ANTHROPIC_CLAUDE: "https://api.anthropic.com/v1/messages",
    AIProvider.DEEPSEEK: "https://api.deepseek.com/chat/completions",
    AIProvider.GROK: "https://api.x.ai/v1/chat/completions",
    AIProvider.GROQ: "https://api.groq.com/openai/v1/chat/completions",
    AIProvider.LOCAL_MODEL: "http://localhost:11434/v1/chat/completions",
    AIProvider.MOCK: "http://localhost:8080/mock",
}

# Provider-specific environment variable names for API keys
API_KEY_ENV_VARS: Dict[AIProvider, str] = {
    AIProvider.OPENAI: "OPENAI_API_KEY",
    AIProvider.GOOGLE_GEMINI: "GEMINI_API_KEY",
    AIProvider.ANTHROPIC_CLAUDE: "ANTHROPIC_API_KEY",
    AIProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
    AIProvider.GROK: "GROK_API_KEY",
    AIProvider.GROQ: "GROQ_API_KEY",
    AIProvider.LOCAL_MODEL: "LOCAL_MODEL_API_KEY",
    AIProvider.MOCK: "MOCK_API_KEY",
}


class AIConfig(BaseModel):
    """
    Configuration for AI service integration.

    Supports multiple AI providers with smart defaults and environment variable overrides.
    Can be loaded from properties files, YAML, or environment variables.

    Attributes:
        provider: AI provider to use for analysis.
        model: Model name to use (defaults to provider's default).
        api_key: API key for authentication (can be loaded from env vars).
        api_url: API endpoint URL (defaults to provider's default).
        timeout: Request timeout duration.
        max_retries: Maximum number of retry attempts.
        visual_analysis_enabled: Whether visual screenshot analysis is enabled.
        max_tokens_dom: Maximum tokens for DOM analysis.
        max_tokens_visual: Maximum tokens for visual analysis.
        temperature_dom: Temperature setting for DOM analysis (0.0-2.0).
        temperature_visual: Temperature setting for visual analysis (0.0-2.0).

    Examples:
        >>> # Create with defaults
        >>> config = AIConfig()

        >>> # Create with custom provider
        >>> config = AIConfig(provider=AIProvider.ANTHROPIC_CLAUDE)

        >>> # Load from properties file
        >>> config = AIConfig.from_properties("autoheal-default.properties")

        >>> # Create with builder pattern
        >>> config = (AIConfig.builder()
        ...     .provider(AIProvider.OPENAI)
        ...     .model("gpt-4")
        ...     .timeout(timedelta(seconds=60))
        ...     .build())
    """

    provider: AIProvider = Field(default=AIProvider.OPENAI)
    model: Optional[str] = Field(default=None)
    api_key: Optional[str] = Field(default=None, exclude=True)  # Exclude from serialization
    api_url: Optional[str] = Field(default=None)
    timeout: timedelta = Field(default=timedelta(seconds=30))
    max_retries: int = Field(default=3, ge=0, le=10)
    visual_analysis_enabled: bool = Field(default=True)
    max_tokens_dom: int = Field(default=500, ge=1, le=10000)
    max_tokens_visual: int = Field(default=1000, ge=1, le=10000)
    temperature_dom: float = Field(default=0.1, ge=0.0, le=2.0)
    temperature_visual: float = Field(default=0.0, ge=0.0, le=2.0)

    @property
    def max_tokens(self) -> int:
        """Get max tokens for DOM analysis (backward compatibility)."""
        return self.max_tokens_dom

    @property
    def temperature(self) -> float:
        """Get temperature for DOM analysis (backward compatibility)."""
        return self.temperature_dom

    class Config:
        """Pydantic model configuration."""
        use_enum_values = False
        validate_assignment = True

    def model_post_init(self, __context) -> None:
        """
        Post-initialization hook to apply smart defaults.

        Called automatically after model initialization to set:
        - Model name from provider default if not specified
        - API URL from provider default if not specified
        - API key from environment variable if not specified
        """
        # Set model from provider default if not specified
        if self.model is None:
            self.model = self.provider.get_default_model()

        # Set API URL from provider default if not specified
        if self.api_url is None:
            self.api_url = DEFAULT_API_ENDPOINTS.get(self.provider)

        # Set API key from environment if not specified
        if self.api_key is None:
            self.api_key = self._get_api_key_from_env()

        # Validate configuration
        self._validate_config()

    def _get_api_key_from_env(self) -> Optional[str]:
        """
        Get API key from environment variable based on provider.

        Returns:
            API key from environment variable, or None if not found.
        """
        env_var = API_KEY_ENV_VARS.get(self.provider)
        if env_var:
            value = os.getenv(env_var)
            if value and value.strip():
                return value.strip()
        return None

    def _validate_config(self) -> None:
        """
        Validate configuration settings.

        Raises:
            ValueError: If configuration is invalid.
        """
        if not self.model or not self.model.strip():
            raise ValueError(f"AI model cannot be null or empty for provider: {self.provider}")

        if not self.api_url or not self.api_url.strip():
            raise ValueError(f"API URL cannot be null or empty for provider: {self.provider}")

        # Only require API key for non-local providers
        if self.provider not in (AIProvider.LOCAL_MODEL, AIProvider.MOCK):
            if not self.api_key or not self.api_key.strip():
                env_var = API_KEY_ENV_VARS.get(self.provider)
                raise ValueError(
                    f"API key is required for provider {self.provider}. "
                    f"Please set environment variable {env_var} or provide api_key in configuration."
                )

    @classmethod
    def builder(cls) -> "AIConfigBuilder":
        """
        Create a builder for fluent API construction.

        Returns:
            AIConfigBuilder instance for method chaining.

        Examples:
            >>> config = (AIConfig.builder()
            ...     .provider(AIProvider.OPENAI)
            ...     .model("gpt-4o")
            ...     .timeout(timedelta(seconds=60))
            ...     .build())
        """
        return AIConfigBuilder()

    @classmethod
    def from_properties(cls, filename: str = "autoheal-default.properties") -> "AIConfig":
        """
        Create AIConfig from properties file.

        Looks for the properties file in the current directory, then in the
        resources directory. Supports environment variable substitution using
        ${VAR_NAME:default_value} syntax.

        Args:
            filename: Name of the properties file to load.

        Returns:
            AIConfig instance with settings from the properties file.

        Raises:
            FileNotFoundError: If properties file cannot be found.

        Examples:
            >>> config = AIConfig.from_properties("autoheal-default.properties")
        """
        props = _load_properties(filename)
        return cls.from_dict(props)

    @classmethod
    def from_dict(cls, props: Dict[str, str]) -> "AIConfig":
        """
        Create AIConfig from dictionary (typically from properties file).

        Args:
            props: Dictionary of configuration properties.

        Returns:
            AIConfig instance with settings from the dictionary.

        Examples:
            >>> props = {"autoheal.ai.provider": "OPENAI", "autoheal.ai.model": "gpt-4"}
            >>> config = AIConfig.from_dict(props)
        """
        # Parse AI provider with validation
        provider_str = _get_property(props, "autoheal.ai.provider", "OPENAI")
        try:
            provider = AIProvider[provider_str.upper()]
        except KeyError:
            print(f"Warning: Unknown AI provider '{provider_str}', falling back to OPENAI")
            provider = AIProvider.OPENAI

        # Smart model selection - user override or provider default
        user_model = _get_property(props, "autoheal.ai.model", None)
        model = user_model.strip() if user_model and user_model.strip() else provider.get_default_model()

        # Smart API key selection based on provider
        api_key = _get_api_key_for_provider(props, provider)

        # Smart API URL - user override or provider default
        user_api_url = _get_property(props, "autoheal.ai.api-url", None)
        api_url = user_api_url.strip() if user_api_url and user_api_url.strip() else DEFAULT_API_ENDPOINTS.get(provider)

        # Parse other configuration with defaults
        timeout_str = _get_property(props, "autoheal.ai.timeout", "30s")
        timeout = _parse_duration(timeout_str)

        max_retries = int(_get_property(props, "autoheal.ai.max-retries", "3"))
        visual_analysis_enabled = _get_property(props, "autoheal.ai.visual-analysis-enabled", "true").lower() == "true"
        max_tokens_dom = int(_get_property(props, "autoheal.ai.max-tokens-dom", "500"))
        max_tokens_visual = int(_get_property(props, "autoheal.ai.max-tokens-visual", "1000"))
        temperature_dom = float(_get_property(props, "autoheal.ai.temperature-dom", "0.1"))
        temperature_visual = float(_get_property(props, "autoheal.ai.temperature-visual", "0.0"))

        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            api_url=api_url,
            timeout=timeout,
            max_retries=max_retries,
            visual_analysis_enabled=visual_analysis_enabled,
            max_tokens_dom=max_tokens_dom,
            max_tokens_visual=max_tokens_visual,
            temperature_dom=temperature_dom,
            temperature_visual=temperature_visual,
        )

    def __str__(self) -> str:
        """String representation of the configuration."""
        return (
            f"AIConfig(provider={self.provider}, model='{self.model}', "
            f"api_url='{self.api_url}', visual_analysis_enabled={self.visual_analysis_enabled}, "
            f"max_retries={self.max_retries})"
        )


class AIConfigBuilder:
    """
    Builder class for fluent AIConfig construction.

    Provides a chainable API for building AIConfig instances.

    Examples:
        >>> config = (AIConfig.builder()
        ...     .provider(AIProvider.OPENAI)
        ...     .model("gpt-4")
        ...     .api_key("sk-...")
        ...     .timeout(timedelta(seconds=60))
        ...     .max_retries(5)
        ...     .visual_analysis_enabled(True)
        ...     .build())
    """

    def __init__(self):
        """Initialize builder with default values."""
        self._provider = AIProvider.OPENAI
        self._model: Optional[str] = None
        self._api_key: Optional[str] = None
        self._api_url: Optional[str] = None
        self._timeout = timedelta(seconds=30)
        self._max_retries = 3
        self._visual_analysis_enabled = True
        self._max_tokens_dom = 500
        self._max_tokens_visual = 1000
        self._temperature_dom = 0.1
        self._temperature_visual = 0.0

    def provider(self, provider: AIProvider) -> "AIConfigBuilder":
        """Set the AI provider."""
        self._provider = provider
        return self

    def model(self, model: str) -> "AIConfigBuilder":
        """Set the model name."""
        self._model = model
        return self

    def api_key(self, api_key: str) -> "AIConfigBuilder":
        """Set the API key."""
        self._api_key = api_key
        return self

    def api_url(self, api_url: str) -> "AIConfigBuilder":
        """Set the API URL."""
        self._api_url = api_url
        return self

    def timeout(self, timeout: timedelta) -> "AIConfigBuilder":
        """Set the timeout duration."""
        self._timeout = timeout
        return self

    def max_retries(self, max_retries: int) -> "AIConfigBuilder":
        """Set the maximum number of retries."""
        self._max_retries = max_retries
        return self

    def visual_analysis_enabled(self, enabled: bool) -> "AIConfigBuilder":
        """Set whether visual analysis is enabled."""
        self._visual_analysis_enabled = enabled
        return self

    def max_tokens_dom(self, max_tokens: int) -> "AIConfigBuilder":
        """Set the maximum tokens for DOM analysis."""
        self._max_tokens_dom = max_tokens
        return self

    def max_tokens_visual(self, max_tokens: int) -> "AIConfigBuilder":
        """Set the maximum tokens for visual analysis."""
        self._max_tokens_visual = max_tokens
        return self

    def temperature_dom(self, temperature: float) -> "AIConfigBuilder":
        """Set the temperature for DOM analysis."""
        self._temperature_dom = temperature
        return self

    def temperature_visual(self, temperature: float) -> "AIConfigBuilder":
        """Set the temperature for visual analysis."""
        self._temperature_visual = temperature
        return self

    def build(self) -> AIConfig:
        """
        Build and return the AIConfig instance.

        Returns:
            Configured AIConfig instance.
        """
        return AIConfig(
            provider=self._provider,
            model=self._model,
            api_key=self._api_key,
            api_url=self._api_url,
            timeout=self._timeout,
            max_retries=self._max_retries,
            visual_analysis_enabled=self._visual_analysis_enabled,
            max_tokens_dom=self._max_tokens_dom,
            max_tokens_visual=self._max_tokens_visual,
            temperature_dom=self._temperature_dom,
            temperature_visual=self._temperature_visual,
        )


# Helper functions

def _get_property(props: Dict[str, str], key: str, default: Optional[str]) -> Optional[str]:
    """
    Get property value with environment variable substitution.

    Supports ${VAR_NAME:default_value} syntax for environment variable substitution.

    Args:
        props: Properties dictionary.
        key: Property key.
        default: Default value if key not found.

    Returns:
        Property value with environment variables resolved.
    """
    value = props.get(key, default)
    if value and "${" in value:
        return _resolve_environment_variables(value)
    return value


def _resolve_environment_variables(value: str) -> str:
    """
    Resolve environment variables in value.

    Supports ${VAR_NAME:default_value} syntax.

    Args:
        value: Value potentially containing environment variable references.

    Returns:
        Value with environment variables resolved.
    """
    if value.startswith("${") and "}" in value:
        var_part = value[2:-1]
        parts = var_part.split(":", 1)
        var_name = parts[0]
        default_val = parts[1] if len(parts) > 1 else ""

        env_value = os.getenv(var_name)
        return env_value if env_value and env_value.strip() else default_val
    return value


def _get_api_key_for_provider(props: Dict[str, str], provider: AIProvider) -> Optional[str]:
    """
    Get API key for provider from properties or environment.

    Args:
        props: Properties dictionary.
        provider: AI provider.

    Returns:
        API key from properties or environment, or None if not found.
    """
    # First try the generic property
    api_key = _get_property(props, "autoheal.ai.api-key", None)
    if api_key and api_key.strip():
        return api_key.strip()

    # Then try provider-specific environment variable
    env_var = API_KEY_ENV_VARS.get(provider)
    if env_var:
        env_value = os.getenv(env_var)
        if env_value and env_value.strip():
            return env_value.strip()

    return None


def _parse_duration(duration_str: str) -> timedelta:
    """
    Parse duration string to timedelta.

    Supports formats: "30s", "5m", "2h", or plain number (interpreted as seconds).

    Args:
        duration_str: Duration string to parse.

    Returns:
        Parsed timedelta.

    Raises:
        ValueError: If duration format is invalid.
    """
    duration_str = duration_str.strip()

    if duration_str.endswith("s"):
        return timedelta(seconds=int(duration_str[:-1]))
    elif duration_str.endswith("m"):
        return timedelta(minutes=int(duration_str[:-1]))
    elif duration_str.endswith("h"):
        return timedelta(hours=int(duration_str[:-1]))
    else:
        # Assume seconds if no unit
        return timedelta(seconds=int(duration_str))


def _load_properties(filename: str) -> Dict[str, str]:
    """
    Load properties from file.

    Looks for the file in current directory first, then in resources directory.

    Args:
        filename: Name of the properties file to load.

    Returns:
        Dictionary of properties.

    Raises:
        FileNotFoundError: If properties file cannot be found.
    """
    props: Dict[str, str] = {}

    # Try current directory first
    file_path = Path(filename)
    if not file_path.exists():
        # Try resources directory
        resources_path = Path("resources") / filename
        if resources_path.exists():
            file_path = resources_path
        else:
            print(f"Warning: Could not find properties file: {filename}")
            return props

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#') or line.startswith('!'):
                    continue

                # Parse key=value
                if '=' in line:
                    key, value = line.split('=', 1)
                    props[key.strip()] = value.strip()
    except Exception as e:
        print(f"Error loading properties file {filename}: {e}")

    return props
