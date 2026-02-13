"""
Main AutoHeal Configuration.

This module provides the main configuration class that aggregates all
sub-configurations for the AutoHeal locator system.
"""

from typing import Optional

from pydantic import BaseModel, Field

from autoheal.config.ai_config import AIConfig
from autoheal.config.cache_config import CacheConfig
from autoheal.config.performance_config import PerformanceConfig
from autoheal.config.resilience_config import ResilienceConfig
from autoheal.config.reporting_config import ReportingConfig


class AutoHealConfiguration(BaseModel):
    """
    Main configuration class for AutoHeal locator system.

    Aggregates all sub-configurations into a single configuration object.

    Attributes:
        cache_config: Configuration for caching behavior.
        ai_config: Configuration for AI service integration.
        performance_config: Configuration for performance tuning.
        resilience_config: Configuration for resilience patterns.
        reporting_config: Configuration for reporting functionality.

    Examples:
        >>> # Create with all defaults
        >>> config = AutoHealConfiguration()

        >>> # Create with custom AI config
        >>> config = AutoHealConfiguration(
        ...     ai_config=AIConfig(provider=AIProvider.ANTHROPIC_CLAUDE)
        ... )

        >>> # Use builder pattern
        >>> config = (AutoHealConfiguration.builder()
        ...     .cache(CacheConfig(maximum_size=20000))
        ...     .ai(AIConfig.from_properties())
        ...     .performance(PerformanceConfig(thread_pool_size=16))
        ...     .build())

        >>> # Load AI config from properties file
        >>> config = AutoHealConfiguration()
        >>> # AI config will be automatically loaded from properties if not explicitly set
    """

    cache_config: CacheConfig = Field(default_factory=CacheConfig)
    ai_config: Optional[AIConfig] = Field(default=None)
    performance_config: PerformanceConfig = Field(default_factory=PerformanceConfig)
    resilience_config: ResilienceConfig = Field(default_factory=ResilienceConfig)
    reporting_config: ReportingConfig = Field(default_factory=ReportingConfig)

    class Config:
        """Pydantic model configuration."""
        validate_assignment = True

    def model_post_init(self, __context) -> None:
        """
        Post-initialization hook to apply lazy initialization.

        Loads AI config from properties if not explicitly set.
        """
        if self.ai_config is None:
            # Lazy initialization - only load from properties if not explicitly set
            try:
                self.ai_config = AIConfig.from_properties()
            except Exception as e:
                # If loading fails, use defaults
                print(f"Warning: Could not load AI config from properties: {e}")
                self.ai_config = AIConfig()

    @classmethod
    def builder(cls) -> "AutoHealConfigurationBuilder":
        """
        Create a builder for fluent API construction.

        Returns:
            AutoHealConfigurationBuilder instance for method chaining.

        Examples:
            >>> config = (AutoHealConfiguration.builder()
            ...     .cache(CacheConfig(maximum_size=15000))
            ...     .ai(AIConfig(provider=AIProvider.OPENAI))
            ...     .build())
        """
        return AutoHealConfigurationBuilder()

    def __str__(self) -> str:
        """String representation of the configuration."""
        return (
            f"AutoHealConfiguration(\n"
            f"  cache={self.cache_config},\n"
            f"  ai={self.ai_config},\n"
            f"  performance={self.performance_config},\n"
            f"  resilience={self.resilience_config},\n"
            f"  reporting={self.reporting_config}\n"
            f")"
        )


class AutoHealConfigurationBuilder:
    """
    Builder class for fluent AutoHealConfiguration construction.

    Provides a chainable API for building AutoHealConfiguration instances.

    Examples:
        >>> config = (AutoHealConfiguration.builder()
        ...     .cache(CacheConfig(maximum_size=20000))
        ...     .ai(AIConfig(provider=AIProvider.OPENAI))
        ...     .performance(PerformanceConfig(thread_pool_size=16))
        ...     .resilience(ResilienceConfig(retry_max_attempts=5))
        ...     .reporting(ReportingConfig.enabled_with_defaults())
        ...     .build())
    """

    def __init__(self):
        """Initialize builder with default values."""
        self._cache_config: Optional[CacheConfig] = None
        self._ai_config: Optional[AIConfig] = None
        self._performance_config: Optional[PerformanceConfig] = None
        self._resilience_config: Optional[ResilienceConfig] = None
        self._reporting_config: Optional[ReportingConfig] = None

    def cache(self, cache_config: CacheConfig) -> "AutoHealConfigurationBuilder":
        """Set the cache configuration."""
        self._cache_config = cache_config
        return self

    def ai(self, ai_config: AIConfig) -> "AutoHealConfigurationBuilder":
        """Set the AI configuration."""
        self._ai_config = ai_config
        return self

    def performance(self, performance_config: PerformanceConfig) -> "AutoHealConfigurationBuilder":
        """Set the performance configuration."""
        self._performance_config = performance_config
        return self

    def resilience(self, resilience_config: ResilienceConfig) -> "AutoHealConfigurationBuilder":
        """Set the resilience configuration."""
        self._resilience_config = resilience_config
        return self

    def reporting(self, reporting_config: ReportingConfig) -> "AutoHealConfigurationBuilder":
        """Set the reporting configuration."""
        self._reporting_config = reporting_config
        return self

    def build(self) -> AutoHealConfiguration:
        """
        Build and return the AutoHealConfiguration instance.

        Returns:
            Configured AutoHealConfiguration instance.
        """
        config_dict = {}

        if self._cache_config is not None:
            config_dict['cache_config'] = self._cache_config
        if self._ai_config is not None:
            config_dict['ai_config'] = self._ai_config
        if self._performance_config is not None:
            config_dict['performance_config'] = self._performance_config
        if self._resilience_config is not None:
            config_dict['resilience_config'] = self._resilience_config
        if self._reporting_config is not None:
            config_dict['reporting_config'] = self._reporting_config

        return AutoHealConfiguration(**config_dict)
