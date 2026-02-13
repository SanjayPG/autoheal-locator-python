"""
Exception classes for AutoHeal locator errors.

This module defines all custom exceptions used throughout the AutoHeal framework,
including a base exception class, error codes, and specific exception types.
"""

from enum import Enum
from datetime import timedelta
from typing import Dict, Any, Optional


class ErrorCode(Enum):
    """Error codes for different types of AutoHeal failures."""

    CONFIGURATION_INVALID = "configuration_invalid"
    """Configuration validation failed"""

    ELEMENT_NOT_FOUND = "element_not_found"
    """Element could not be located using any strategy"""

    AI_SERVICE_UNAVAILABLE = "ai_service_unavailable"
    """AI service is unavailable or failing"""

    TIMEOUT_EXCEEDED = "timeout_exceeded"
    """Operation timed out"""

    CACHE_ERROR = "cache_error"
    """Cache operation failed"""

    ADAPTER_ERROR = "adapter_error"
    """Web automation adapter error"""

    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    """Circuit breaker is open, blocking requests"""

    INVALID_LOCATOR = "invalid_locator"
    """Invalid locator format or unable to parse locator"""


class AutoHealException(Exception):
    """
    Base exception for AutoHeal locator errors.

    This exception includes an error code and optional context information
    to provide detailed error diagnostics.

    Attributes:
        error_code: The ErrorCode indicating the type of error
        context: Additional context information about the error
    """

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize an AutoHealException.

        Args:
            error_code: The ErrorCode indicating the type of error
            message: Human-readable error message
            cause: The underlying exception that caused this error, if any
            context: Additional context information about the error
        """
        super().__init__(message)
        self.error_code = error_code
        self.context = dict(context) if context else {}
        self.__cause__ = cause

    def __str__(self) -> str:
        """Return a string representation of the exception."""
        return (
            f"AutoHealException(error_code={self.error_code.value}, "
            f"message='{str(self.args[0])}', context={self.context})"
        )

    def __repr__(self) -> str:
        """Return a detailed string representation of the exception."""
        return self.__str__()


class ElementNotFoundException(AutoHealException):
    """
    Exception raised when an element cannot be located using any strategy.

    This exception is thrown when all healing strategies have been exhausted
    and the element still cannot be found on the page.
    """

    def __init__(
        self,
        message: str,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize an ElementNotFoundException.

        Args:
            message: Human-readable error message
            cause: The underlying exception that caused this error, if any
            context: Additional context information about the error
        """
        super().__init__(ErrorCode.ELEMENT_NOT_FOUND, message, cause, context)


class AIServiceException(AutoHealException):
    """
    Exception raised when AI service is unavailable or returns an error.

    This exception is thrown when communication with the AI provider fails
    or the AI service returns an unexpected response.
    """

    def __init__(
        self,
        message: str,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize an AIServiceException.

        Args:
            message: Human-readable error message
            cause: The underlying exception that caused this error, if any
            context: Additional context information about the error
        """
        super().__init__(ErrorCode.AI_SERVICE_UNAVAILABLE, message, cause, context)


class ConfigurationException(AutoHealException):
    """
    Exception raised when configuration validation fails.

    This exception is thrown when required configuration is missing or invalid.
    """

    def __init__(
        self,
        message: str,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize a ConfigurationException.

        Args:
            message: Human-readable error message
            cause: The underlying exception that caused this error, if any
            context: Additional context information about the error
        """
        super().__init__(ErrorCode.CONFIGURATION_INVALID, message, cause, context)


class CacheException(AutoHealException):
    """
    Exception raised when a cache operation fails.

    This exception is thrown when reading from or writing to the cache fails.
    """

    def __init__(
        self,
        message: str,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize a CacheException.

        Args:
            message: Human-readable error message
            cause: The underlying exception that caused this error, if any
            context: Additional context information about the error
        """
        super().__init__(ErrorCode.CACHE_ERROR, message, cause, context)


class CircuitBreakerOpenException(AutoHealException):
    """
    Exception thrown when circuit breaker is open and blocking requests.

    This exception indicates that the circuit breaker has tripped due to
    repeated failures and is temporarily blocking requests to protect the system.

    Attributes:
        retry_after: Duration to wait before retrying
    """

    def __init__(
        self,
        message: str,
        retry_after: Optional[timedelta] = None,
    ) -> None:
        """
        Initialize a CircuitBreakerOpenException.

        Args:
            message: Human-readable error message
            retry_after: Duration to wait before retrying (defaults to 5 minutes)
        """
        super().__init__(ErrorCode.CIRCUIT_BREAKER_OPEN, message)
        self.retry_after = retry_after or timedelta(minutes=5)


class PlaywrightLocatorExtractionException(Exception):
    """
    Exception thrown when AutoHeal cannot extract a locator string from a native
    Playwright Locator object.

    This typically occurs when:
    - Complex chained locators are used (e.g., multiple filter() calls)
    - Custom locator implementations that don't expose internal state
    - Reflection fails due to security restrictions or API changes

    Resolution: Use JavaScript-style string format instead:

    Example:
        # Instead of:
        autoheal.find(page, page.locator("...").filter(...).nth(2), "desc")

        # Use:
        autoheal.find(page, "locator('...').filter(...).nth(2)", "desc")
    """

    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        """
        Initialize a PlaywrightLocatorExtractionException.

        Args:
            message: The detail message explaining why extraction failed
            cause: The underlying cause of the extraction failure
        """
        super().__init__(message)
        self.__cause__ = cause


class AdapterException(AutoHealException):
    """
    Exception raised when a web automation adapter encounters an error.

    This exception is thrown when the Selenium or Playwright adapter
    fails to perform an operation.
    """

    def __init__(
        self,
        message: str,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize an AdapterException.

        Args:
            message: Human-readable error message
            cause: The underlying exception that caused this error, if any
            context: Additional context information about the error
        """
        super().__init__(ErrorCode.ADAPTER_ERROR, message, cause, context)


class TimeoutException(AutoHealException):
    """
    Exception raised when an operation times out.

    This exception is thrown when an operation exceeds its configured timeout.
    """

    def __init__(
        self,
        message: str,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize a TimeoutException.

        Args:
            message: Human-readable error message
            cause: The underlying exception that caused this error, if any
            context: Additional context information about the error
        """
        super().__init__(ErrorCode.TIMEOUT_EXCEEDED, message, cause, context)


class InvalidLocatorException(AutoHealException):
    """
    Exception raised when a locator format is invalid or cannot be parsed.

    This exception is thrown when the locator string cannot be parsed
    or has an invalid format.
    """

    def __init__(
        self,
        message: str,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize an InvalidLocatorException.

        Args:
            message: Human-readable error message
            cause: The underlying exception that caused this error, if any
            context: Additional context information about the error
        """
        super().__init__(ErrorCode.INVALID_LOCATOR, message, cause, context)
