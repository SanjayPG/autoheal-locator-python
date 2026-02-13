"""
Reporting Configuration for AutoHeal framework.

This module provides configuration for AutoHeal reporting functionality
including output formats, directories, and console logging.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class ReportingConfig(BaseModel):
    """
    Configuration for AutoHeal reporting functionality.

    Controls report generation, output formats, and logging behavior.

    Attributes:
        enabled: Whether reporting is enabled.
        generate_html: Whether to generate HTML reports.
        generate_json: Whether to generate JSON reports.
        generate_text: Whether to generate text reports.
        console_logging: Whether to log to console.
        output_directory: Directory for report output.
        report_name_prefix: Prefix for report file names.

    Examples:
        >>> # Create with defaults (disabled)
        >>> config = ReportingConfig()

        >>> # Create enabled with defaults
        >>> config = ReportingConfig.enabled_with_defaults()

        >>> # Create with custom settings
        >>> config = ReportingConfig(
        ...     enabled=True,
        ...     generate_html=True,
        ...     output_directory="/var/reports"
        ... )

        >>> # Use builder pattern
        >>> config = (ReportingConfig.builder()
        ...     .enabled(True)
        ...     .generate_html(True)
        ...     .generate_json(True)
        ...     .output_directory("./reports")
        ...     .build())
    """

    enabled: bool = Field(default=False)
    generate_html: bool = Field(default=True)
    generate_json: bool = Field(default=True)
    generate_text: bool = Field(default=True)
    console_logging: bool = Field(default=True)
    output_directory: str = Field(default_factory=lambda: os.getcwd())
    report_name_prefix: str = Field(default="AutoHeal_Report")

    class Config:
        """Pydantic model configuration."""
        validate_assignment = True

    @classmethod
    def disabled(cls) -> "ReportingConfig":
        """
        Create a disabled reporting configuration.

        Returns:
            ReportingConfig with reporting disabled.

        Examples:
            >>> config = ReportingConfig.disabled()
            >>> assert config.enabled == False
        """
        return cls(enabled=False)

    @classmethod
    def enabled_with_defaults(cls) -> "ReportingConfig":
        """
        Create an enabled reporting configuration with defaults.

        Returns:
            ReportingConfig with reporting enabled and default settings.

        Examples:
            >>> config = ReportingConfig.enabled_with_defaults()
            >>> assert config.enabled == True
            >>> assert config.generate_html == True
        """
        return cls(enabled=True)

    @classmethod
    def builder(cls) -> "ReportingConfigBuilder":
        """
        Create a builder for fluent API construction.

        Returns:
            ReportingConfigBuilder instance for method chaining.

        Examples:
            >>> config = (ReportingConfig.builder()
            ...     .enabled(True)
            ...     .generate_html(True)
            ...     .output_directory("./reports")
            ...     .build())
        """
        return ReportingConfigBuilder()

    def __str__(self) -> str:
        """String representation of the configuration."""
        formats = []
        if self.generate_html:
            formats.append("HTML")
        if self.generate_json:
            formats.append("JSON")
        if self.generate_text:
            formats.append("TEXT")

        return (
            f"ReportingConfig(enabled={self.enabled}, "
            f"formats={formats}, output_directory='{self.output_directory}')"
        )


class ReportingConfigBuilder:
    """
    Builder class for fluent ReportingConfig construction.

    Provides a chainable API for building ReportingConfig instances.

    Examples:
        >>> config = (ReportingConfig.builder()
        ...     .enabled(True)
        ...     .generate_html(True)
        ...     .generate_json(True)
        ...     .generate_text(False)
        ...     .console_logging(True)
        ...     .output_directory("./test-reports")
        ...     .report_name_prefix("TestReport")
        ...     .build())
    """

    def __init__(self):
        """Initialize builder with default values."""
        self._enabled = False
        self._generate_html = True
        self._generate_json = True
        self._generate_text = True
        self._console_logging = True
        self._output_directory = os.getcwd()
        self._report_name_prefix = "AutoHeal_Report"

    def enabled(self, enabled: bool) -> "ReportingConfigBuilder":
        """Set whether reporting is enabled."""
        self._enabled = enabled
        return self

    def generate_html(self, generate: bool) -> "ReportingConfigBuilder":
        """Set whether to generate HTML reports."""
        self._generate_html = generate
        return self

    def generate_json(self, generate: bool) -> "ReportingConfigBuilder":
        """Set whether to generate JSON reports."""
        self._generate_json = generate
        return self

    def generate_text(self, generate: bool) -> "ReportingConfigBuilder":
        """Set whether to generate text reports."""
        self._generate_text = generate
        return self

    def console_logging(self, enabled: bool) -> "ReportingConfigBuilder":
        """Set whether to enable console logging."""
        self._console_logging = enabled
        return self

    def output_directory(self, directory: str) -> "ReportingConfigBuilder":
        """Set the output directory."""
        self._output_directory = directory
        return self

    def report_name_prefix(self, prefix: str) -> "ReportingConfigBuilder":
        """Set the report name prefix."""
        self._report_name_prefix = prefix
        return self

    def build(self) -> ReportingConfig:
        """
        Build and return the ReportingConfig instance.

        Returns:
            Configured ReportingConfig instance.
        """
        return ReportingConfig(
            enabled=self._enabled,
            generate_html=self._generate_html,
            generate_json=self._generate_json,
            generate_text=self._generate_text,
            console_logging=self._console_logging,
            output_directory=self._output_directory,
            report_name_prefix=self._report_name_prefix,
        )
