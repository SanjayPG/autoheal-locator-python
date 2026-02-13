"""
Enumerations used throughout the AutoHeal framework.

This module defines all enum types used for configuration and operation
of the AutoHeal locator system.
"""

from enum import Enum
from typing import List


class AIProvider(Enum):
    """
    Enumeration of supported AI service providers with capability information.

    Each provider has different capabilities for text and visual analysis.
    """

    OPENAI = "openai"
    """OpenAI's GPT models - supports text and visual analysis"""

    GOOGLE_GEMINI = "google_gemini"
    """Google's Gemini models - supports text and visual analysis"""

    ANTHROPIC_CLAUDE = "anthropic_claude"
    """Anthropic's Claude models - supports text analysis only"""

    DEEPSEEK = "deepseek"
    """DeepSeek AI models - supports text analysis only"""

    GROK = "grok"
    """Grok AI models (X.AI) - supports text analysis only"""

    GROQ = "groq"
    """Groq inference engine - fast, free inference for open-source models"""

    LOCAL_MODEL = "local_model"
    """Local AI model deployment via Ollama"""

    MOCK = "mock"
    """Mock implementation for testing"""

    def get_default_model(self) -> str:
        """Get the default model name for this provider."""
        defaults = {
            AIProvider.OPENAI: "gpt-4o-mini",
            AIProvider.GOOGLE_GEMINI: "gemini-2.0-flash",
            AIProvider.ANTHROPIC_CLAUDE: "claude-3-5-sonnet-20241022",
            AIProvider.DEEPSEEK: "deepseek-chat",
            AIProvider.GROK: "grok-beta",
            AIProvider.GROQ: "llama-3.3-70b-versatile",
            AIProvider.LOCAL_MODEL: "llama2",
            AIProvider.MOCK: "mock-model",
        }
        return defaults[self]

    def supports_text_analysis(self) -> bool:
        """Check if this provider supports text-based DOM analysis."""
        return True  # All providers support text analysis

    def supports_visual_analysis(self) -> bool:
        """Check if this provider supports visual screenshot analysis."""
        visual_capable = {
            AIProvider.OPENAI,
            AIProvider.GOOGLE_GEMINI,
            AIProvider.GROQ,
            AIProvider.MOCK,
        }
        return self in visual_capable

    @classmethod
    def get_visual_analysis_capable_providers(cls) -> List["AIProvider"]:
        """Get list of providers that support visual analysis."""
        return [
            cls.OPENAI,
            cls.GOOGLE_GEMINI,
            cls.GROQ,
            cls.MOCK,
        ]


class LocatorStrategy(Enum):
    """Enumeration of available element location strategies."""

    ORIGINAL_SELECTOR = "original_selector"
    """Use the original selector without any AI assistance"""

    DOM_ANALYSIS = "dom_analysis"
    """Use AI to analyze DOM structure and find alternative selectors"""

    VISUAL_ANALYSIS = "visual_analysis"
    """Use AI to analyze visual screenshots and locate elements"""

    HYBRID = "hybrid"
    """Combine multiple strategies to find the best result"""

    CACHED = "cached"
    """Retrieve selector from cache based on previous successful attempts"""

    AI_DISAMBIGUATION = "ai_disambiguation"
    """Use AI to select the correct element when multiple elements match"""


class ExecutionStrategy(Enum):
    """
    Execution strategy for healing locators to optimize cost and performance.

    Different strategies provide trade-offs between cost, speed, and reliability.
    """

    SEQUENTIAL = "sequential"
    """
    Run locators sequentially, stopping at first success.
    Cost: Lowest (only pays for successful strategy)
    Speed: Slower (sequential execution)
    """

    PARALLEL = "parallel"
    """
    Run all locators in parallel, select best result.
    Cost: Highest (pays for all strategies)
    Speed: Fastest (parallel execution)
    """

    SMART_SEQUENTIAL = "smart_sequential"
    """
    Smart strategy: Try DOM first, then Visual if DOM fails.
    Cost: Medium (DOM is cheaper, Visual only if needed)
    Speed: Medium (optimized sequential)
    """

    DOM_ONLY = "dom_only"
    """
    Cost-optimized: Only use DOM analysis, skip visual.
    Cost: Lowest (DOM only)
    Speed: Fast (single strategy)
    """

    VISUAL_FIRST = "visual_first"
    """
    Visual-first: Try visual first, then DOM if visual fails.
    Cost: High (Visual is expensive)
    Speed: Medium (visual analysis first)
    """


class AutomationFramework(Enum):
    """Supported web automation frameworks."""

    SELENIUM = "selenium"
    """Selenium WebDriver framework"""

    PLAYWRIGHT = "playwright"
    """Microsoft Playwright framework"""


class LocatorType(Enum):
    """Types of locators supported by the framework."""

    # Selenium locator types
    CSS = "css"
    """CSS selector"""

    XPATH = "xpath"
    """XPath expression"""

    ID = "id"
    """Element ID"""

    NAME = "name"
    """Element name attribute"""

    CLASS_NAME = "class_name"
    """Element class name"""

    TAG_NAME = "tag_name"
    """HTML tag name"""

    LINK_TEXT = "link_text"
    """Link text (exact match)"""

    PARTIAL_LINK_TEXT = "partial_link_text"
    """Link text (partial match)"""

    # Playwright semantic locators
    GET_BY_ROLE = "get_by_role"
    """Playwright getByRole locator"""

    GET_BY_TEXT = "get_by_text"
    """Playwright getByText locator"""

    GET_BY_LABEL = "get_by_label"
    """Playwright getByLabel locator"""

    GET_BY_PLACEHOLDER = "get_by_placeholder"
    """Playwright getByPlaceholder locator"""

    GET_BY_ALT_TEXT = "get_by_alt_text"
    """Playwright getByAltText locator"""

    GET_BY_TITLE = "get_by_title"
    """Playwright getByTitle locator"""

    GET_BY_TEST_ID = "get_by_test_id"
    """Playwright getByTestId locator"""

    PLAYWRIGHT_LOCATOR = "playwright_locator"
    """Generic Playwright locator() method"""


class CacheType(Enum):
    """Types of cache implementations available."""

    IN_MEMORY = "in_memory"
    """In-memory cache using cachetools (like Java's Caffeine)"""

    REDIS = "redis"
    """Distributed Redis cache"""

    FILE = "file"
    """File-based persistent cache using diskcache"""

    NONE = "none"
    """No caching"""


class ReportFormat(Enum):
    """Output formats for healing reports."""

    HTML = "html"
    """HTML format with interactive visualizations"""

    JSON = "json"
    """JSON format for programmatic processing"""

    TEXT = "text"
    """Plain text format"""


# Alias for backwards compatibility (matching Java naming)
HealingStrategy = ExecutionStrategy
