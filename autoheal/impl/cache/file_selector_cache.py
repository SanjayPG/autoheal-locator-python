"""
File-based persistent cache implementation for AutoHeal selectors.

This module provides a persistent storage cache that survives application restarts
using JSON files, with an in-memory cache layer for performance.
"""

import atexit
import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from cachetools import TTLCache
from filelock import FileLock

from autoheal.config.cache_config import CacheConfig
from autoheal.core.selector_cache import SelectorCache
from autoheal.metrics.cache_metrics import CacheMetrics
from autoheal.models.cached_selector import CachedSelector
from autoheal.models.element_context import ElementContext
from autoheal.models.element_fingerprint import ElementFingerprint
from autoheal.models.position import Position

logger = logging.getLogger(__name__)


@dataclass
class FileCacheMetrics:
    """
    File-based cache metrics for persistence.

    Attributes:
        attempts: Total number of usage attempts.
        successes: Number of successful usages.
        last_used: Timestamp of last usage.
        last_access_time: Unix timestamp in milliseconds.
    """
    attempts: int = 0
    successes: int = 0
    last_used: datetime = field(default_factory=datetime.now)
    last_access_time: float = field(default_factory=lambda: time.time() * 1000)

    def get_success_rate(self) -> float:
        """Calculate success rate."""
        return self.successes / self.attempts if self.attempts > 0 else 0.0

    def is_expired(self, expire_after_access: timedelta) -> bool:
        """Check if metrics are expired based on access time."""
        current_time_ms = time.time() * 1000
        return current_time_ms - self.last_access_time > expire_after_access.total_seconds() * 1000

    def record_usage(self, success: bool) -> None:
        """
        Record a usage attempt.

        Args:
            success: Whether the usage was successful.
        """
        self.attempts += 1
        if success:
            self.successes += 1
        self.last_used = datetime.now()
        self.last_access_time = time.time() * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "attempts": self.attempts,
            "successes": self.successes,
            "last_used": self.last_used.isoformat(),
            "last_access_time": self.last_access_time
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileCacheMetrics":
        """Create from dictionary after JSON deserialization."""
        return cls(
            attempts=data.get("attempts", 0),
            successes=data.get("successes", 0),
            last_used=datetime.fromisoformat(data["last_used"]) if "last_used" in data else datetime.now(),
            last_access_time=data.get("last_access_time", time.time() * 1000)
        )


@dataclass
class FileCacheEntry:
    """
    Serializable cache entry for file persistence.

    Attributes:
        selector: The cached selector string.
        success_rate: Current success rate.
        usage_count: Number of times used.
        last_used: Timestamp of last usage.
        created_at: Timestamp of creation.
        last_access_time: Unix timestamp in milliseconds.
    """
    selector: str
    success_rate: float = 0.0
    usage_count: int = 0
    last_used: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    last_access_time: float = field(default_factory=lambda: time.time() * 1000)

    @classmethod
    def from_cached_selector(cls, cached: CachedSelector) -> "FileCacheEntry":
        """
        Create FileCacheEntry from CachedSelector.

        Args:
            cached: The cached selector to convert.

        Returns:
            FileCacheEntry instance.
        """
        return cls(
            selector=cached.selector,
            success_rate=cached.current_success_rate,
            usage_count=cached.usage_count,
            last_used=cached.last_used,
            created_at=cached.created_at,
            last_access_time=time.time() * 1000
        )

    def to_cached_selector(self) -> CachedSelector:
        """
        Convert to CachedSelector.

        Creates a dummy ElementFingerprint since we only store the selector.
        In future, this could be enhanced to store and restore the full fingerprint.

        Returns:
            CachedSelector instance.
        """
        # Create a dummy ElementFingerprint
        dummy_position = Position(x=0, y=0, width=0, height=0)
        dummy_fingerprint = ElementFingerprint(
            tag_name="",
            position=dummy_position,
            attributes={},
            text_content="",
            child_elements=[],
            parent_info=""
        )

        cached = CachedSelector(
            selector=self.selector,
            fingerprint=dummy_fingerprint
        )

        # Simulate usage history by recording attempts
        # This approximates the success rate without storing full history
        if self.usage_count > 0:
            successful_count = int(self.usage_count * self.success_rate)
            for i in range(self.usage_count):
                cached.record_usage(i < successful_count)

        return cached

    def is_expired(self, expire_after_write: timedelta, expire_after_access: timedelta) -> bool:
        """
        Check if entry is expired.

        Args:
            expire_after_write: Time to expire after creation.
            expire_after_access: Time to expire after last access.

        Returns:
            True if expired, False otherwise.
        """
        # Use timezone-aware or naive to match created_at
        now = datetime.now(self.created_at.tzinfo)

        # Check write expiry
        if now - self.created_at > expire_after_write:
            return True

        # Check access expiry
        current_time_ms = time.time() * 1000
        if current_time_ms - self.last_access_time > expire_after_access.total_seconds() * 1000:
            return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "selector": self.selector,
            "success_rate": self.success_rate,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat(),
            "created_at": self.created_at.isoformat(),
            "last_access_time": self.last_access_time
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileCacheEntry":
        """Create from dictionary after JSON deserialization."""
        return cls(
            selector=data["selector"],
            success_rate=data.get("success_rate", 0.0),
            usage_count=data.get("usage_count", 0),
            last_used=datetime.fromisoformat(data["last_used"]) if "last_used" in data else datetime.now(),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            last_access_time=data.get("last_access_time", time.time() * 1000)
        )


class FileSelectorCache(SelectorCache):
    """
    File-based persistent cache implementation.

    This cache provides persistent storage that survives application restarts
    using JSON files, with an in-memory TTLCache layer for performance.

    Features:
        - Persistent storage in JSON files
        - In-memory cache for fast access
        - Automatic save on shutdown
        - Background async saves
        - Thread-safe operations
        - Expiration based on write and access time

    Attributes:
        config: Cache configuration.
        metrics: Cache performance metrics.

    Examples:
        >>> from autoheal.config import CacheConfig
        >>> from datetime import timedelta
        >>>
        >>> config = CacheConfig(
        ...     maximum_size=10000,
        ...     expire_after_write=timedelta(hours=24),
        ...     expire_after_access=timedelta(hours=12)
        ... )
        >>> cache = FileSelectorCache(config)
        >>>
        >>> # Cache persists across restarts
        >>> selector = CachedSelector(...)
        >>> cache.put("my-key", selector)
        >>> # ... application restart ...
        >>> cached = cache.get("my-key")  # Still available!
    """

    DEFAULT_CACHE_DIR = os.path.join(Path.home(), ".autoheal", "cache")
    CACHE_FILE = "selector-cache.json"
    METRICS_FILE = "cache-metrics.json"

    def __init__(self, config: CacheConfig, cache_directory: Optional[str] = None) -> None:
        """
        Create a new file-based selector cache.

        Args:
            config: Cache configuration settings.
            cache_directory: Optional custom cache directory path.
        """
        self._config = config
        self._metrics = CacheMetrics()
        self._lock = threading.RLock()

        # Setup cache directory
        self._cache_directory = cache_directory or self.DEFAULT_CACHE_DIR
        self._cache_file_path = os.path.join(self._cache_directory, self.CACHE_FILE)
        self._metrics_file_path = os.path.join(self._cache_directory, self.METRICS_FILE)

        # In-memory metrics backup
        self._file_metrics: Dict[str, FileCacheMetrics] = {}

        # Create in-memory cache for performance
        ttl_seconds = min(
            config.expire_after_write.total_seconds(),
            config.expire_after_access.total_seconds()
        )

        self._memory_cache: TTLCache[str, CachedSelector] = TTLCache(
            maxsize=config.maximum_size,
            ttl=ttl_seconds
        )

        # Track access times for expire_after_access support
        self._access_times: Dict[str, float] = {}

        # Initialize cache
        self._create_cache_directory()
        self._load_cache_from_file()
        self._setup_shutdown_hook()

        logger.info("Initialized persistent file cache at: %s", self._cache_directory)
        logger.info(
            "FileSelectorCache initialized. Directory: %s, Loaded entries: %d",
            self._cache_directory,
            len(self._memory_cache)
        )

    def get(self, key: str) -> Optional[CachedSelector]:
        """
        Retrieve a cached selector by key.

        Args:
            key: Cache key.

        Returns:
            CachedSelector if found, None otherwise.
        """
        start_time = time.time()

        with self._lock:
            # First try memory cache
            result = self._memory_cache.get(key)

            if result is not None:
                # Update access time for file cache
                self._update_file_metrics(key, True)
                self._access_times[key] = time.time()
                self._metrics.record_hit()
                logger.debug("Cache HIT: %s", key)
                logger.debug("Memory cache hit for key: %s", key)
                return result
            else:
                self._metrics.record_miss()
                logger.debug("Cache MISS: %s", key)
                logger.debug("Cache miss for key: %s", key)
                return None

    def put(self, key: str, selector: CachedSelector) -> None:
        """
        Store a selector in the cache.

        Args:
            key: Cache key.
            selector: Selector to cache.
        """
        start_time = time.time()

        with self._lock:
            # Store in memory cache
            self._memory_cache[key] = selector
            self._access_times[key] = time.time()

            # Update file metrics
            self._update_file_metrics(key, True)

            # Async save to file to avoid blocking
            self._save_to_file_async()

            elapsed_ms = (time.time() - start_time) * 1000
            self._metrics.record_load(int(elapsed_ms))

            expire_hours = self._config.expire_after_write.total_seconds() / 3600
            logger.debug("Cache STORED: %s (expires in %.1f hours)", key, expire_hours)
            logger.debug("Cached selector for key: %s", key)

    def update_success(self, key: str, success: bool) -> None:
        """
        Update success rate for a cached selector.

        Args:
            key: Cache key.
            success: Whether the selector usage was successful.
        """
        with self._lock:
            cached = self._memory_cache.get(key)
            if cached is not None:
                cached.record_usage(success)
                self._update_file_metrics(key, success)
                logger.debug("Updated success rate for key: %s (success: %s)", key, success)

    def get_metrics(self) -> CacheMetrics:
        """
        Get cache performance metrics.

        Returns:
            Current cache metrics.
        """
        return self._metrics

    def evict_expired(self) -> None:
        """
        Evict expired cache entries.

        TTLCache handles TTL automatically, but this also cleans up file metrics.
        """
        with self._lock:
            self._cleanup_expired_file_metrics()
            logger.debug("Evicted expired cache entries")

    def clear_all(self) -> None:
        """
        Clear all cache entries.
        """
        with self._lock:
            size_before = len(self._memory_cache)
            self._memory_cache.clear()
            self._access_times.clear()
            self._file_metrics.clear()

            # Clear file cache
            self._clear_file_cache()

            self._metrics.record_eviction()
            logger.info("Cache cleared: %d entries removed", size_before)
            logger.info("Cache cleared completely: %d entries removed", size_before)

    def remove(self, key: str) -> bool:
        """
        Remove a specific cache entry.

        Args:
            key: Cache key to remove.

        Returns:
            True if entry was removed, False if not found.
        """
        with self._lock:
            if key in self._memory_cache:
                del self._memory_cache[key]
                self._access_times.pop(key, None)
                self._file_metrics.pop(key, None)
                self._metrics.record_eviction()

                logger.debug("Cache entry removed: %s", key)
                logger.debug("Cache entry removed: %s", key)

                # Save updated cache to file
                self._save_to_file_async()
                return True

            logger.debug("Attempted to remove non-existent cache entry: %s", key)
            return False

    def size(self) -> int:
        """
        Get current cache size.

        Returns:
            Number of entries in cache.
        """
        with self._lock:
            return len(self._memory_cache)

    def generate_contextual_key(
        self,
        original_selector: str,
        description: str,
        context: Optional[ElementContext] = None
    ) -> str:
        """
        Generate a contextual cache key that includes element context.

        Args:
            original_selector: The original CSS selector.
            description: Human-readable element description.
            context: Element context information.

        Returns:
            Contextual cache key.
        """
        key_parts = [original_selector, description]

        if context is not None:
            if context.parent_container:
                key_parts.append(f"parent:{context.parent_container}")

            if context.relative_position:
                pos = context.relative_position
                key_parts.append(f"pos:{pos.x},{pos.y}")

            if context.sibling_elements:
                siblings_str = ",".join(context.sibling_elements)
                key_parts.append(f"siblings:{siblings_str}")

        return "|".join(key_parts)

    def get_cache_file_path(self) -> str:
        """
        Get cache file path for debugging.

        Returns:
            Path to cache file.
        """
        return self._cache_file_path

    def force_save(self) -> None:
        """
        Force save cache to file (for testing).
        """
        self._save_cache_to_file()

    # Private methods

    def _create_cache_directory(self) -> None:
        """Create cache directory if it doesn't exist."""
        try:
            Path(self._cache_directory).mkdir(parents=True, exist_ok=True)
            logger.debug("Created cache directory: %s", self._cache_directory)
        except Exception as e:
            logger.error("Failed to create cache directory: %s", self._cache_directory, exc_info=e)

    def _load_cache_from_file(self) -> None:
        """Load cache from file on startup."""
        self._load_cache_entries()
        self._load_file_metrics()

    def _load_cache_entries(self) -> None:
        """Load cache entries from file with file-level locking."""
        cache_file = Path(self._cache_file_path)
        lock_file = str(cache_file) + '.lock'

        if cache_file.exists():
            try:
                with FileLock(lock_file, timeout=10):  # Cross-process file lock
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        loaded_data = json.load(f)

                loaded_count = 0
                expired_count = 0

                for key, entry_data in loaded_data.items():
                    entry = FileCacheEntry.from_dict(entry_data)

                    # Check if entry is expired
                    if not entry.is_expired(
                        self._config.expire_after_write,
                        self._config.expire_after_access
                    ):
                        cached_selector = entry.to_cached_selector()
                        self._memory_cache[key] = cached_selector
                        self._access_times[key] = time.time()
                        loaded_count += 1
                    else:
                        expired_count += 1

                logger.info(
                    "Loaded %d entries from cache file, %d expired entries skipped",
                    loaded_count, expired_count
                )
                logger.info(
                    "Loaded %d cache entries from file, %d expired entries skipped",
                    loaded_count,
                    expired_count
                )
            except Exception as e:
                logger.error("Failed to load cache from file: %s", self._cache_file_path, exc_info=e)
        else:
            logger.debug("Cache file does not exist, starting with empty cache: %s", self._cache_file_path)

    def _load_file_metrics(self) -> None:
        """Load file metrics from file with file-level locking."""
        metrics_file = Path(self._metrics_file_path)
        lock_file = str(metrics_file) + '.lock'

        if metrics_file.exists():
            try:
                with FileLock(lock_file, timeout=10):  # Cross-process file lock
                    with open(metrics_file, 'r', encoding='utf-8') as f:
                        loaded_data = json.load(f)

                # Filter out expired metrics
                for key, metrics_data in loaded_data.items():
                    metrics = FileCacheMetrics.from_dict(metrics_data)
                    if not metrics.is_expired(self._config.expire_after_access):
                        self._file_metrics[key] = metrics

                logger.info("Loaded %d file metrics from cache", len(self._file_metrics))
            except Exception as e:
                logger.error("Failed to load file metrics: %s", self._metrics_file_path, exc_info=e)

    def _save_to_file_async(self) -> None:
        """Save cache to file asynchronously."""
        # Use a separate thread to avoid blocking
        save_thread = threading.Thread(target=self._save_cache_to_file, daemon=True)
        save_thread.start()

    def _save_cache_to_file(self) -> None:
        """Save cache to file with file-level locking for parallel safety."""
        lock_file = self._cache_file_path + '.lock'
        try:
            with FileLock(lock_file, timeout=10):  # Cross-process file lock
                with self._lock:  # Thread lock within same process
                    # Save cache entries
                    entries_to_save = {}
                    for key, cached_selector in self._memory_cache.items():
                        entry = FileCacheEntry.from_cached_selector(cached_selector)
                        entries_to_save[key] = entry.to_dict()

                    # Write cache entries
                    with open(self._cache_file_path, 'w', encoding='utf-8') as f:
                        json.dump(entries_to_save, f, indent=2, ensure_ascii=False)

                    # Save file metrics
                    metrics_to_save = {
                        key: metrics.to_dict()
                        for key, metrics in self._file_metrics.items()
                    }

                    with open(self._metrics_file_path, 'w', encoding='utf-8') as f:
                        json.dump(metrics_to_save, f, indent=2, ensure_ascii=False)

                logger.debug(
                    "Cache saved to files: %d entries, %d metrics",
                    len(entries_to_save),
                    len(metrics_to_save)
                )
        except Exception as e:
            logger.error("Failed to save cache to file", exc_info=e)

    def _clear_file_cache(self) -> None:
        """Clear file cache."""
        try:
            cache_file = Path(self._cache_file_path)
            metrics_file = Path(self._metrics_file_path)

            if cache_file.exists():
                cache_file.unlink()
            if metrics_file.exists():
                metrics_file.unlink()

            logger.debug("Cache files cleared")
        except Exception as e:
            logger.error("Failed to clear cache files", exc_info=e)

    def _update_file_metrics(self, key: str, success: bool) -> None:
        """
        Update file metrics.

        Args:
            key: Cache key.
            success: Whether the operation was successful.
        """
        if key not in self._file_metrics:
            self._file_metrics[key] = FileCacheMetrics()
        self._file_metrics[key].record_usage(success)

    def _cleanup_expired_file_metrics(self) -> None:
        """Clean up expired file metrics."""
        expired_keys = [
            key for key, metrics in self._file_metrics.items()
            if metrics.is_expired(self._config.expire_after_access)
        ]

        for key in expired_keys:
            del self._file_metrics[key]

    def _setup_shutdown_hook(self) -> None:
        """Setup shutdown hook to save cache."""
        def shutdown_handler():
            logger.info("Saving cache before shutdown...")
            logger.info("Saving cache to file before shutdown...")
            self._save_cache_to_file()

        atexit.register(shutdown_handler)
