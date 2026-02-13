"""
Response parsing utilities for AI provider responses.

This module contains utilities for parsing AI responses into structured
AIAnalysisResult objects for both Selenium and Playwright frameworks.
"""

import json
import logging
from typing import Dict, Any, List

from autoheal.models.ai_analysis_result import AIAnalysisResult
from autoheal.models.element_candidate import ElementCandidate
from autoheal.models.enums import AutomationFramework
from autoheal.models.playwright_locator import PlaywrightLocator

logger = logging.getLogger(__name__)


class ResponseParser:
    """
    Utility class for parsing AI provider responses.

    Handles parsing of both Selenium (CSS/XPath) and Playwright (user-facing locators)
    response formats.
    """

    @staticmethod
    def parse_dom_response(
        content_json: Dict[str, Any],
        framework: AutomationFramework
    ) -> AIAnalysisResult:
        """
        Parse DOM analysis response based on framework.

        Args:
            content_json: Parsed JSON response from AI.
            framework: Target automation framework.

        Returns:
            AIAnalysisResult with appropriate selector format.

        Raises:
            ValueError: If response format is invalid.
        """
        # Detect response format
        if "locatorType" in content_json:
            # Playwright format
            return ResponseParser._parse_playwright_response(content_json)
        else:
            # Selenium format
            return ResponseParser._parse_selenium_response(content_json)

    @staticmethod
    def _parse_selenium_response(ai_response: Dict[str, Any]) -> AIAnalysisResult:
        """
        Parse Selenium-specific DOM analysis response (CSS selectors).

        Args:
            ai_response: Parsed JSON from AI.

        Returns:
            AIAnalysisResult for Selenium.

        Raises:
            ValueError: If required fields are missing.
        """
        try:
            selector = ai_response.get("selector", "")
            if not selector:
                raise ValueError("No selector found in Selenium response")

            confidence = max(0.0, min(1.0, float(ai_response.get("confidence", 0.8))))
            reasoning = ai_response.get("reasoning", "AI-generated selector")

            logger.debug("Parsed Selenium selector: '%s', confidence: %.2f", selector, confidence)

            # Parse alternatives
            alternatives: List[ElementCandidate] = []
            alternatives_node = ai_response.get("alternatives", [])

            if isinstance(alternatives_node, list):
                for alt in alternatives_node:
                    if isinstance(alt, str):
                        alternatives.append(
                            ElementCandidate(
                                selector=alt,
                                confidence=confidence * 0.8,
                                description="Alternative selector",
                                element_fingerprint=None,
                                attributes={}
                            )
                        )

            return AIAnalysisResult.builder() \
                .recommended_selector(selector) \
                .target_framework(AutomationFramework.SELENIUM) \
                .confidence(confidence) \
                .reasoning(reasoning) \
                .alternatives(alternatives) \
                .build()

        except Exception as e:
            logger.error("Failed to parse Selenium DOM content: %s", str(e))
            raise ValueError(f"Failed to parse Selenium DOM content: {e}")

    @staticmethod
    def _parse_playwright_response(ai_response: Dict[str, Any]) -> AIAnalysisResult:
        """
        Parse Playwright-specific DOM analysis response.

        Args:
            ai_response: Parsed JSON from AI.

        Returns:
            AIAnalysisResult for Playwright.

        Raises:
            ValueError: If required fields are missing.
        """
        try:
            locator_type = ai_response.get("locatorType", "")
            value = ai_response.get("value", "")
            confidence = max(0.0, min(1.0, float(ai_response.get("confidence", 0.8))))
            reasoning = ai_response.get("reasoning", "AI-generated Playwright locator")

            if not locator_type or not value:
                raise ValueError("Missing locatorType or value in Playwright response")

            logger.debug(
                "Parsed Playwright locator: type='%s', value='%s', confidence=%.2f",
                locator_type, value, confidence
            )

            # Parse options if present
            options_node = ai_response.get("options", {})
            options: Dict[str, Any] = {}
            if isinstance(options_node, dict):
                options = options_node

            # Build PlaywrightLocator based on type
            locator_builder = PlaywrightLocator.builder()
            playwright_locator = ResponseParser._build_playwright_locator(
                locator_builder,
                locator_type,
                value,
                options
            )

            # Parse alternatives
            alternatives: List[ElementCandidate] = []
            alternatives_node = ai_response.get("alternatives", [])

            if isinstance(alternatives_node, list):
                for alt in alternatives_node:
                    if isinstance(alt, dict):
                        alt_type = alt.get("type", "")
                        alt_value = alt.get("value", "")
                        alt_selector = f"{alt_type}('{alt_value}')"
                        alternatives.append(
                            ElementCandidate(
                                selector=alt_selector,
                                confidence=confidence * 0.8,
                                description="Alternative Playwright locator",
                                element_fingerprint=None,
                                attributes={}
                            )
                        )
                    elif isinstance(alt, str):
                        alternatives.append(
                            ElementCandidate(
                                selector=alt,
                                confidence=confidence * 0.8,
                                description="Alternative selector",
                                element_fingerprint=None,
                                attributes={}
                            )
                        )

            return AIAnalysisResult.builder() \
                .playwright_locator(playwright_locator) \
                .target_framework(AutomationFramework.PLAYWRIGHT) \
                .confidence(confidence) \
                .reasoning(reasoning) \
                .alternatives(alternatives) \
                .build()

        except Exception as e:
            logger.error("Failed to parse Playwright DOM content: %s", str(e))
            raise ValueError(f"Failed to parse Playwright DOM content: {e}")

    @staticmethod
    def _build_playwright_locator(
        builder: Any,  # PlaywrightLocatorBuilder
        locator_type: str,
        value: str,
        options: Dict[str, Any]
    ) -> PlaywrightLocator:
        """
        Build PlaywrightLocator based on locator type.

        Args:
            builder: PlaywrightLocator builder instance.
            locator_type: Type of locator (getByRole, getByLabel, etc.).
            value: Locator value.
            options: Additional options for the locator.

        Returns:
            Built PlaywrightLocator.
        """
        locator_type_lower = locator_type.lower()

        if locator_type_lower == "getbyrole":
            role_name = options.get("name")
            if role_name:
                return builder.by_role(value, role_name).build()
            else:
                return builder.by_role(value).build()

        elif locator_type_lower == "getbylabel":
            return builder.by_label(value).build()

        elif locator_type_lower == "getbyplaceholder":
            return builder.by_placeholder(value).build()

        elif locator_type_lower == "getbytext":
            return builder.by_text(value).build()

        elif locator_type_lower == "getbyalttext":
            return builder.by_alt_text(value).build()

        elif locator_type_lower == "getbytitle":
            return builder.by_title(value).build()

        elif locator_type_lower == "getbytestid":
            return builder.by_test_id(value).build()

        elif locator_type_lower == "css":
            return builder.css_selector(value).build()

        elif locator_type_lower == "xpath":
            return builder.xpath(value).build()

        else:
            logger.warning("Unknown Playwright locator type: %s, falling back to CSS", locator_type)
            return builder.css_selector(value).build()

    @staticmethod
    def parse_disambiguation_response(content: str) -> int:
        """
        Parse disambiguation response to extract element index.

        Args:
            content: Raw response content.

        Returns:
            1-based element index.

        Raises:
            ValueError: If unable to parse valid index.
        """
        content = content.strip()

        # Try to parse as integer directly
        try:
            return int(content)
        except ValueError:
            pass

        # Try to extract number from text
        import re
        numbers = re.findall(r'\d+', content)
        if numbers:
            return int(numbers[0])

        # Default to first element if parsing fails
        logger.warning("Failed to parse disambiguation response: %s, defaulting to 1", content)
        return 1
