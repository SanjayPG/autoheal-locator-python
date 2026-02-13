"""
Cached Selector model.

This module provides the CachedSelector class for representing cached
selectors with usage statistics and success tracking.
"""

import threading
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, PrivateAttr

from autoheal.models.element_fingerprint import ElementFingerprint


class CachedSelector(BaseModel):
    """
    Represents a cached selector with usage statistics and success tracking.

    Tracks selector usage, success rate, and timing information for cache management.

    Attributes:
        selector: The cached CSS/XPath selector.
        success_rate: Initial success rate (typically 1.0 for new entries).
        usage_count: Number of times this selector has been used.
        last_used: Timestamp of last usage.
        created_at: Timestamp when this cache entry was created.
        fingerprint: Element fingerprint for validation.
        successes: Number of successful uses.
        attempts: Total number of attempts.

    Examples:
        >>> from autoheal.models.element_fingerprint import ElementFingerprint
        >>> fingerprint = ElementFingerprint(parent_chain="html>body>div", text_content="Login")
        >>> cached = CachedSelector(selector="#login-btn", fingerprint=fingerprint)

        >>> # Record usage
        >>> cached.record_usage(success=True)
        >>> print(f"Success rate: {cached.get_current_success_rate():.2f}")
    """

    selector: str
    success_rate: float = Field(default=1.0)
    usage_count: int = Field(default=0)
    last_used: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    fingerprint: Optional[ElementFingerprint] = None
    successes: int = Field(default=1)
    attempts: int = Field(default=1)

    # Thread-safe counters (not serialized) - use PrivateAttr for Pydantic v2
    _lock: threading.Lock = PrivateAttr(default_factory=threading.Lock)

    class Config:
        """Pydantic model configuration."""
        validate_assignment = True
        arbitrary_types_allowed = True

    def record_usage(self, success: bool) -> None:
        """
        Record a usage attempt and whether it was successful.

        Thread-safe method to update usage statistics.

        Args:
            success: True if the selector worked, False otherwise.

        Examples:
            >>> cached = CachedSelector(selector="#submit", fingerprint=None)
            >>> cached.record_usage(success=True)
            >>> cached.record_usage(success=False)
            >>> print(f"Success rate: {cached.get_current_success_rate()}")
        """
        with self._lock:
            self.usage_count += 1
            self.attempts += 1
            if success:
                self.successes += 1
            self.last_used = datetime.now(timezone.utc)

    def get_current_success_rate(self) -> float:
        """
        Calculate the current success rate based on recorded attempts.

        Returns:
            Success rate between 0.0 and 1.0.

        Examples:
            >>> cached = CachedSelector(selector="#test", fingerprint=None)
            >>> cached.record_usage(True)
            >>> cached.record_usage(True)
            >>> cached.record_usage(False)
            >>> rate = cached.get_current_success_rate()
            >>> assert 0.6 < rate < 0.7  # 3 successes out of 4 total
        """
        with self._lock:
            if self.attempts > 0:
                return self.successes / self.attempts
            return 0.0

    @property
    def current_success_rate(self) -> float:
        """
        Property alias for get_current_success_rate().

        Returns:
            Success rate between 0.0 and 1.0.
        """
        return self.get_current_success_rate()

    def __str__(self) -> str:
        """String representation of the cached selector."""
        return (
            f"CachedSelector(selector='{self.selector}', "
            f"success_rate={self.get_current_success_rate():.2f}, "
            f"usage_count={self.usage_count})"
        )
