"""
Quick Start Configuration for AutoHeal Locator.

Copy this file to your project's config/ directory and use it as-is.
Just set your API key as an environment variable and you're ready to go!

Usage:
    from config.quickstart_config import get_autoheal_config

    config = get_autoheal_config()
    locator = ReportingAutoHealLocator(adapter, config)

Supported environment variables:
    GROQ_API_KEY      - Groq API key (FREE, recommended for getting started)
    OPENAI_API_KEY    - OpenAI API key
    GEMINI_API_KEY    - Google Gemini API key
    ANTHROPIC_API_KEY - Anthropic Claude API key
    DEEPSEEK_API_KEY  - DeepSeek API key

    For local models (Ollama/LM Studio):
        AUTOHEAL_API_URL  - API endpoint URL
        AUTOHEAL_MODEL    - Model name
"""

import os
from pathlib import Path
from datetime import timedelta

from autoheal import AutoHealConfiguration
from autoheal.config import (
    AIConfig,
    CacheConfig,
    PerformanceConfig,
    ResilienceConfig,
    ReportingConfig,
)
from autoheal.config.cache_config import CacheType
from autoheal.models.enums import AIProvider, ExecutionStrategy


def get_autoheal_config() -> AutoHealConfiguration:
    """
    Build AutoHeal configuration from environment variables.

    Automatically detects which AI provider to use based on which
    API key environment variable is set.

    Returns:
        AutoHealConfiguration ready to use with AutoHealLocator

    Raises:
        ValueError: If no AI provider is configured
    """
    ai_config = _build_ai_config()

    return AutoHealConfiguration.builder() \
        .ai(ai_config) \
        .cache(_build_cache_config()) \
        .performance(_build_performance_config()) \
        .resilience(_build_resilience_config()) \
        .reporting(_build_reporting_config()) \
        .build()


def _build_ai_config() -> AIConfig:
    """Auto-detect and configure AI provider from environment variables."""

    # Groq - FREE and fastest, recommended for getting started
    if os.getenv("GROQ_API_KEY"):
        return AIConfig.builder() \
            .provider(AIProvider.GROQ) \
            .api_key(os.getenv("GROQ_API_KEY")) \
            .model(os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")) \
            .build()

    # OpenAI
    if os.getenv("OPENAI_API_KEY"):
        return AIConfig.builder() \
            .provider(AIProvider.OPENAI) \
            .api_key(os.getenv("OPENAI_API_KEY")) \
            .model(os.getenv("OPENAI_MODEL", "gpt-4o-mini")) \
            .build()

    # Google Gemini
    if os.getenv("GEMINI_API_KEY"):
        return AIConfig.builder() \
            .provider(AIProvider.GOOGLE_GEMINI) \
            .api_key(os.getenv("GEMINI_API_KEY")) \
            .model(os.getenv("GEMINI_MODEL", "gemini-2.0-flash")) \
            .build()

    # Anthropic Claude
    if os.getenv("ANTHROPIC_API_KEY"):
        return AIConfig.builder() \
            .provider(AIProvider.ANTHROPIC_CLAUDE) \
            .api_key(os.getenv("ANTHROPIC_API_KEY")) \
            .model(os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")) \
            .build()

    # DeepSeek
    if os.getenv("DEEPSEEK_API_KEY"):
        return AIConfig.builder() \
            .provider(AIProvider.DEEPSEEK) \
            .api_key(os.getenv("DEEPSEEK_API_KEY")) \
            .model(os.getenv("DEEPSEEK_MODEL", "deepseek-chat")) \
            .build()

    # Local model (Ollama / LM Studio)
    if os.getenv("AUTOHEAL_API_URL"):
        return AIConfig.builder() \
            .provider(AIProvider.LOCAL_MODEL) \
            .api_url(os.getenv("AUTOHEAL_API_URL")) \
            .model(os.getenv("AUTOHEAL_MODEL", "llama2")) \
            .build()

    raise ValueError(
        "No AI provider configured. Set one of these environment variables:\n"
        "  - GROQ_API_KEY (FREE - get key at https://console.groq.com)\n"
        "  - OPENAI_API_KEY\n"
        "  - GEMINI_API_KEY\n"
        "  - ANTHROPIC_API_KEY\n"
        "  - DEEPSEEK_API_KEY\n"
        "  - AUTOHEAL_API_URL (for local models like Ollama)"
    )


def _build_cache_config() -> CacheConfig:
    """Configure caching - persistent file cache by default."""
    return CacheConfig.builder() \
        .cache_type(CacheType.PERSISTENT_FILE) \
        .maximum_size(500) \
        .expire_after_write(timedelta(hours=24)) \
        .build()


def _build_performance_config() -> PerformanceConfig:
    """Configure performance settings."""
    strategy_name = os.getenv("AUTOHEAL_EXECUTION_STRATEGY", "SMART_SEQUENTIAL").upper()
    strategy_map = {
        "SMART_SEQUENTIAL": ExecutionStrategy.SMART_SEQUENTIAL,
        "DOM_ONLY": ExecutionStrategy.DOM_ONLY,
        "VISUAL_FIRST": ExecutionStrategy.VISUAL_FIRST,
        "SEQUENTIAL": ExecutionStrategy.SEQUENTIAL,
        "PARALLEL": ExecutionStrategy.PARALLEL,
    }
    strategy = strategy_map.get(strategy_name, ExecutionStrategy.SMART_SEQUENTIAL)

    return PerformanceConfig.builder() \
        .execution_strategy(strategy) \
        .quick_check_timeout(timedelta(milliseconds=500)) \
        .element_timeout(timedelta(seconds=10)) \
        .build()


def _build_resilience_config() -> ResilienceConfig:
    """Configure retry and circuit breaker settings."""
    return ResilienceConfig.builder() \
        .retry_max_attempts(3) \
        .retry_delay(timedelta(seconds=1)) \
        .build()


def _build_reporting_config() -> ReportingConfig:
    """Configure HTML/JSON/text report generation."""
    # Default to ./autoheal-reports in current working directory
    output_dir = os.getenv(
        "AUTOHEAL_REPORT_DIR",
        str(Path.cwd() / "autoheal-reports")
    )

    return ReportingConfig.builder() \
        .enabled(True) \
        .generate_html(True) \
        .generate_json(True) \
        .generate_text(True) \
        .output_directory(output_dir) \
        .console_logging(True) \
        .build()
