"""
Element locator strategy implementations.

This module provides different element locator strategies including
DOM-based, visual-based, and hybrid approaches.
"""

from autoheal.impl.locator.dom_element_locator import DOMElementLocator
from autoheal.impl.locator.visual_element_locator import VisualElementLocator
from autoheal.impl.locator.hybrid_element_locator import HybridElementLocator
from autoheal.impl.locator.cost_optimized_hybrid_element_locator import CostOptimizedHybridElementLocator

__all__ = [
    "DOMElementLocator",
    "VisualElementLocator",
    "HybridElementLocator",
    "CostOptimizedHybridElementLocator",
]
