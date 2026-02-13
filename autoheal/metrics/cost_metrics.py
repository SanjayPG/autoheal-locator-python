"""
Cost metrics module for tracking AI service costs and usage.

This module provides metrics collection for AI API costs including token consumption
and estimated expenses for different types of analysis.
"""

import threading
from typing import Dict, Any


class CostMetrics:
    """
    Tracks AI service costs and usage including actual token consumption.

    This class monitors the financial cost of using AI services, tracking both
    DOM and visual analysis requests along with their token consumption.

    All methods are thread-safe.
    """

    # Cost per token for GPT-4o-mini (as of 2024)
    COST_PER_INPUT_TOKEN = 0.00015 / 1000  # $0.15 per 1M input tokens
    COST_PER_OUTPUT_TOKEN = 0.0006 / 1000  # $0.60 per 1M output tokens

    # Fallback cost per request when token info unavailable
    DOM_COST_PER_REQUEST = 0.02  # $0.02 per DOM analysis
    VISUAL_COST_PER_REQUEST = 0.10  # $0.10 per visual analysis

    def __init__(self) -> None:
        """Initialize cost metrics with zero counters."""
        self._lock = threading.Lock()
        self._total_requests = 0
        self._dom_requests = 0
        self._visual_requests = 0
        self._total_cost = 0.0
        self._dom_cost = 0.0
        self._visual_cost = 0.0

        # Token usage tracking
        self._total_tokens_used = 0
        self._dom_tokens_used = 0
        self._visual_tokens_used = 0

    def record_dom_request(self) -> None:
        """Record a DOM analysis request using fallback cost."""
        with self._lock:
            self._dom_requests += 1
            self._total_requests += 1
            self._dom_cost += self.DOM_COST_PER_REQUEST
            self._total_cost += self.DOM_COST_PER_REQUEST

    def record_visual_request(self) -> None:
        """Record a visual analysis request using fallback cost."""
        with self._lock:
            self._visual_requests += 1
            self._total_requests += 1
            self._visual_cost += self.VISUAL_COST_PER_REQUEST
            self._total_cost += self.VISUAL_COST_PER_REQUEST

    def record_dom_request_with_tokens(
        self,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """
        Record DOM request with actual token usage.

        Args:
            input_tokens: Number of input tokens consumed
            output_tokens: Number of output tokens generated
        """
        with self._lock:
            self._dom_requests += 1
            self._total_requests += 1

            total_tokens = input_tokens + output_tokens
            self._dom_tokens_used += total_tokens
            self._total_tokens_used += total_tokens

            request_cost = self._calculate_token_cost(input_tokens, output_tokens)
            self._dom_cost += request_cost
            self._total_cost += request_cost

    def record_visual_request_with_tokens(
        self,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """
        Record visual request with actual token usage.

        Args:
            input_tokens: Number of input tokens consumed
            output_tokens: Number of output tokens generated
        """
        with self._lock:
            self._visual_requests += 1
            self._total_requests += 1

            total_tokens = input_tokens + output_tokens
            self._visual_tokens_used += total_tokens
            self._total_tokens_used += total_tokens

            request_cost = self._calculate_token_cost(input_tokens, output_tokens)
            self._visual_cost += request_cost
            self._total_cost += request_cost

    def _calculate_token_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost based on token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Total cost in USD
        """
        return (input_tokens * self.COST_PER_INPUT_TOKEN) + (
            output_tokens * self.COST_PER_OUTPUT_TOKEN
        )

    # Getters for request counts
    @property
    def total_requests(self) -> int:
        """Get total number of requests."""
        with self._lock:
            return self._total_requests

    @property
    def dom_requests(self) -> int:
        """Get number of DOM analysis requests."""
        with self._lock:
            return self._dom_requests

    @property
    def visual_requests(self) -> int:
        """Get number of visual analysis requests."""
        with self._lock:
            return self._visual_requests

    # Getters for costs
    @property
    def total_cost(self) -> float:
        """Get total cost in USD."""
        with self._lock:
            return self._total_cost

    @property
    def dom_cost(self) -> float:
        """Get DOM analysis cost in USD."""
        with self._lock:
            return self._dom_cost

    @property
    def visual_cost(self) -> float:
        """Get visual analysis cost in USD."""
        with self._lock:
            return self._visual_cost

    # Getters for token usage
    @property
    def total_tokens_used(self) -> int:
        """Get total tokens consumed."""
        with self._lock:
            return self._total_tokens_used

    @property
    def dom_tokens_used(self) -> int:
        """Get tokens consumed by DOM analysis."""
        with self._lock:
            return self._dom_tokens_used

    @property
    def visual_tokens_used(self) -> int:
        """Get tokens consumed by visual analysis."""
        with self._lock:
            return self._visual_tokens_used

    def get_average_cost_per_request(self) -> float:
        """
        Calculate average cost per request.

        Returns:
            Average cost in USD
        """
        with self._lock:
            return self._total_cost / self._total_requests if self._total_requests > 0 else 0.0

    def get_cost_savings_vs_parallel(self) -> float:
        """
        Calculate savings compared to always running both DOM and Visual.

        Returns:
            Cost savings in USD
        """
        with self._lock:
            parallel_cost = self._total_requests * (
                self.DOM_COST_PER_REQUEST + self.VISUAL_COST_PER_REQUEST
            )
            return parallel_cost - self._total_cost

    def reset(self) -> None:
        """Reset all metrics to zero."""
        with self._lock:
            self._total_requests = 0
            self._dom_requests = 0
            self._visual_requests = 0
            self._total_cost = 0.0
            self._dom_cost = 0.0
            self._visual_cost = 0.0
            self._total_tokens_used = 0
            self._dom_tokens_used = 0
            self._visual_tokens_used = 0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metrics to dictionary format.

        Returns:
            Dictionary containing all metrics
        """
        with self._lock:
            return {
                "total_requests": self._total_requests,
                "dom_requests": self._dom_requests,
                "visual_requests": self._visual_requests,
                "total_cost_usd": self._total_cost,
                "dom_cost_usd": self._dom_cost,
                "visual_cost_usd": self._visual_cost,
                "total_tokens_used": self._total_tokens_used,
                "dom_tokens_used": self._dom_tokens_used,
                "visual_tokens_used": self._visual_tokens_used,
                "average_cost_per_request": self.get_average_cost_per_request(),
                "cost_savings_vs_parallel": self.get_cost_savings_vs_parallel(),
            }

    def __str__(self) -> str:
        """Return string representation of metrics."""
        return (
            f"CostMetrics(total_cost=${self.total_cost:.4f}, "
            f"requests={self.total_requests}, "
            f"avg=${self.get_average_cost_per_request():.4f})"
        )
