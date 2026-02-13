"""
Cache implementations for the AutoHeal framework.

This module provides various cache backend implementations including
in-memory (cachetools), distributed (Redis), and file-based persistent caching.
"""

from autoheal.impl.cache.cachetools_selector_cache import CachetoolsSelectorCache
from autoheal.impl.cache.file_selector_cache import FileSelectorCache

# Redis import requires redis package - uncomment when redis is installed
# from autoheal.impl.cache.redis_selector_cache import RedisSelectorCache

__all__ = [
    "CachetoolsSelectorCache",
    "FileSelectorCache",
    # "RedisSelectorCache",  # Requires redis package
]
