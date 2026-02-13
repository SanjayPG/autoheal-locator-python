"""
AutoHeal Locator - AI-powered test automation framework for healing broken element locators.

This package provides intelligent element location and healing capabilities for Selenium and
Playwright test automation frameworks using AI-powered analysis.
"""

__version__ = "1.0.5"
__author__ = "SanjayPG"
__license__ = "MIT"

# Main API exports
from autoheal.autoheal_locator import AutoHealLocator
from autoheal.config.autoheal_config import AutoHealConfiguration
from autoheal.config.locator_options import LocatorOptions
from autoheal.models.enums import AIProvider, ExecutionStrategy, LocatorStrategy
from autoheal.exception.exceptions import (
    AutoHealException,
    ElementNotFoundException,
    AIServiceException,
    ConfigurationException,
)

__all__ = [
    # Main class
    "AutoHealLocator",

    # Configuration
    "AutoHealConfiguration",
    "LocatorOptions",
    "ExecutionStrategy",
    "AIProvider",
    "LocatorStrategy",

    # Exceptions
    "AutoHealException",
    "ElementNotFoundException",
    "AIServiceException",
    "ConfigurationException",

    # Version
    "__version__",
]
