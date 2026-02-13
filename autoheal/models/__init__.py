"""
Models module for AutoHeal framework.

This module provides all data models for the AutoHeal locator system,
including element models, locator models, and result models.
"""

from autoheal.models.ai_analysis_result import AIAnalysisResult, AIAnalysisResultBuilder
from autoheal.models.cached_selector import CachedSelector
from autoheal.models.disambiguation_result import DisambiguationResult
from autoheal.models.element_candidate import ElementCandidate
from autoheal.models.element_context import ElementContext, ElementContextBuilder
from autoheal.models.element_fingerprint import ElementFingerprint, ElementFingerprintBuilder
from autoheal.models.enums import (
    AIProvider,
    AutomationFramework,
    CacheType,
    ExecutionStrategy,
    HealingStrategy,
    LocatorStrategy,
    LocatorType,
    ReportFormat,
)
from autoheal.models.locator_filter import FilterType, LocatorFilter, LocatorFilterBuilder
from autoheal.models.locator_request import LocatorRequest, LocatorRequestBuilder
from autoheal.models.locator_result import LocatorResult, LocatorResultBuilder
from autoheal.models.playwright_locator import (
    PlaywrightLocator,
    PlaywrightLocatorBuilder,
    PlaywrightLocatorType,
)
from autoheal.models.position import Position

__all__ = [
    # Enums
    "AIProvider",
    "AutomationFramework",
    "CacheType",
    "ExecutionStrategy",
    "HealingStrategy",
    "LocatorStrategy",
    "LocatorType",
    "ReportFormat",
    # Position
    "Position",
    # Element models
    "ElementCandidate",
    "ElementContext",
    "ElementContextBuilder",
    "ElementFingerprint",
    "ElementFingerprintBuilder",
    # Cached selector
    "CachedSelector",
    # Locator models
    "LocatorRequest",
    "LocatorRequestBuilder",
    "LocatorResult",
    "LocatorResultBuilder",
    # Playwright models
    "PlaywrightLocator",
    "PlaywrightLocatorBuilder",
    "PlaywrightLocatorType",
    "LocatorFilter",
    "LocatorFilterBuilder",
    "FilterType",
    # AI Analysis
    "AIAnalysisResult",
    "AIAnalysisResultBuilder",
    # Disambiguation
    "DisambiguationResult",
]
