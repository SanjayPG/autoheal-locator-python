"""
AutoHeal exception module.

This module provides all exception classes used throughout the AutoHeal framework.
"""

from autoheal.exception.exceptions import (
    ErrorCode,
    AutoHealException,
    ElementNotFoundException,
    AIServiceException,
    ConfigurationException,
    CacheException,
    CircuitBreakerOpenException,
    PlaywrightLocatorExtractionException,
    AdapterException,
    TimeoutException,
    InvalidLocatorException,
)

__all__ = [
    "ErrorCode",
    "AutoHealException",
    "ElementNotFoundException",
    "AIServiceException",
    "ConfigurationException",
    "CacheException",
    "CircuitBreakerOpenException",
    "PlaywrightLocatorExtractionException",
    "AdapterException",
    "TimeoutException",
    "InvalidLocatorException",
]
