"""
Integration tests for AutoHeal with a local AI model endpoint.

These tests validate the full AI pipeline against a real local model
served via OpenAI-compatible API at a Cloudflare tunnel.

Tests cover:
- OllamaProvider (OpenAI-compatible mode) DOM analysis
- OllamaProvider disambiguation
- OpenAI provider pointed at local endpoint
- ResilientAIService full flow
- ResponseParser with real AI output
- Playwright-format prompts
"""

import json
import logging
import pytest
import aiohttp
from datetime import timedelta

from autoheal.impl.ai.providers.ollama_provider import OllamaProvider
from autoheal.impl.ai.providers.openai_provider import OpenAIProvider
from autoheal.impl.ai.providers.response_parser import ResponseParser
from autoheal.impl.ai.resilient_ai_service import ResilientAIService
from autoheal.config.ai_config import AIConfig
from autoheal.config.resilience_config import ResilienceConfig
from autoheal.models.enums import AIProvider, AutomationFramework
from autoheal.models.ai_analysis_result import AIAnalysisResult
from autoheal.models.disambiguation_result import DisambiguationResult

from tests.conftest import (
    LOCAL_MODEL_URL,
    LOCAL_MODEL_HEALTH_URL,
    LOCAL_MODEL_NAME,
    SAMPLE_HTML_LOGIN,
    SAMPLE_HTML_TABLE,
    SAMPLE_HTML_NAVIGATION,
    requires_local_model,
)

logger = logging.getLogger(__name__)


# ==================== Health Check ====================

@requires_local_model
class TestHealthCheck:
    """Verify the local model endpoint is reachable."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(LOCAL_MODEL_HEALTH_URL) as resp:
                assert resp.status == 200
                data = await resp.json()
                assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_chat_completions_endpoint(self):
        """Verify the /v1/chat/completions endpoint responds."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                LOCAL_MODEL_URL,
                json={
                    "model": LOCAL_MODEL_NAME,
                    "messages": [{"role": "user", "content": "Reply with: ok"}],
                    "max_tokens": 5,
                },
                headers={"Content-Type": "application/json"},
            ) as resp:
                assert resp.status == 200
                data = await resp.json()
                assert "choices" in data
                assert len(data["choices"]) > 0
                assert "message" in data["choices"][0]


# ==================== OllamaProvider Tests ====================

@requires_local_model
class TestOllamaProviderDomAnalysis:
    """Test OllamaProvider in OpenAI-compatible mode."""

    def _make_provider(self) -> OllamaProvider:
        return OllamaProvider(
            api_url=LOCAL_MODEL_URL,
            model=LOCAL_MODEL_NAME,
            timeout=120,
        )

    @pytest.mark.asyncio
    async def test_detect_openai_compatible(self):
        provider = self._make_provider()
        assert provider._openai_compat is True
        assert provider._get_chat_endpoint() == LOCAL_MODEL_URL

    @pytest.mark.asyncio
    async def test_detect_ollama_native(self):
        provider = OllamaProvider(
            api_url="http://localhost:11434",
            model="llama2",
        )
        assert provider._openai_compat is False
        assert provider._get_chat_endpoint() == "http://localhost:11434/api/chat"

    @pytest.mark.asyncio
    async def test_dom_analysis_selenium_login_button(self):
        """Find the login button using Selenium CSS selector."""
        provider = self._make_provider()

        prompt = (
            'Find the best CSS selector for: "Login button"\n\n'
            f'HTML:\n{SAMPLE_HTML_LOGIN}\n\n'
            'Respond with valid JSON only:\n'
            '{"selector": "css-selector-here", "confidence": 0.95, '
            '"reasoning": "brief explanation", "alternatives": ["alt1", "alt2"]}'
        )

        result = await provider.analyze_dom(
            prompt=prompt,
            framework=AutomationFramework.SELENIUM,
            max_tokens=500,
            temperature=0.1,
        )

        assert isinstance(result, AIAnalysisResult)
        assert result.recommended_selector is not None
        assert len(result.recommended_selector) > 0
        assert result.confidence > 0.0
        assert result.reasoning is not None
        assert result.tokens_used > 0
        logger.info(
            "Login button selector: %s (confidence: %.2f)",
            result.recommended_selector, result.confidence
        )

    @pytest.mark.asyncio
    async def test_dom_analysis_selenium_username_input(self):
        """Find the username input field."""
        provider = self._make_provider()

        prompt = (
            'Find the best CSS selector for: "Username input field"\n\n'
            f'HTML:\n{SAMPLE_HTML_LOGIN}\n\n'
            'Respond with valid JSON only:\n'
            '{"selector": "css-selector-here", "confidence": 0.95, '
            '"reasoning": "brief explanation", "alternatives": ["alt1", "alt2"]}'
        )

        result = await provider.analyze_dom(
            prompt=prompt,
            framework=AutomationFramework.SELENIUM,
            max_tokens=500,
            temperature=0.1,
        )

        assert isinstance(result, AIAnalysisResult)
        assert result.recommended_selector is not None
        assert result.confidence > 0.0
        assert result.tokens_used > 0
        logger.info(
            "Username input selector: %s (confidence: %.2f)",
            result.recommended_selector, result.confidence
        )

    @pytest.mark.asyncio
    async def test_dom_analysis_selenium_table_edit_button(self):
        """Find the edit button for a specific user in a table."""
        provider = self._make_provider()

        prompt = (
            'Find the best CSS selector for: "Edit button for the first user (John Doe)"\n\n'
            f'HTML:\n{SAMPLE_HTML_TABLE}\n\n'
            'Respond with valid JSON only:\n'
            '{"selector": "css-selector-here", "confidence": 0.95, '
            '"reasoning": "brief explanation", "alternatives": ["alt1", "alt2"]}'
        )

        result = await provider.analyze_dom(
            prompt=prompt,
            framework=AutomationFramework.SELENIUM,
            max_tokens=500,
            temperature=0.1,
        )

        assert isinstance(result, AIAnalysisResult)
        assert result.recommended_selector is not None
        assert result.confidence > 0.0
        logger.info(
            "Table edit button selector: %s (confidence: %.2f)",
            result.recommended_selector, result.confidence
        )

    @pytest.mark.asyncio
    async def test_dom_analysis_playwright_login_button(self):
        """Find the login button using Playwright semantic locators."""
        provider = self._make_provider()

        prompt = (
            'You are a Playwright automation expert. Find the best user-facing locator for: '
            '"Login button"\n\n'
            f'HTML:\n{SAMPLE_HTML_LOGIN}\n\n'
            'PRIORITY ORDER:\n'
            '1. getByRole() - ARIA role with accessible name\n'
            '2. getByLabel() - Form label text\n'
            '3. getByText() - Visible text content\n'
            '4. CSS Selector - FALLBACK ONLY\n\n'
            'Respond with valid JSON only:\n'
            '{"locatorType": "getByRole", "value": "button", '
            '"options": {"name": "Login"}, "confidence": 0.95, '
            '"reasoning": "brief explanation", '
            '"alternatives": [{"type": "css", "value": "#login-btn"}]}'
        )

        result = await provider.analyze_dom(
            prompt=prompt,
            framework=AutomationFramework.PLAYWRIGHT,
            max_tokens=500,
            temperature=0.1,
        )

        assert isinstance(result, AIAnalysisResult)
        # Playwright responses may have either a playwright_locator or recommended_selector
        has_locator = result.playwright_locator is not None
        has_selector = result.recommended_selector is not None
        assert has_locator or has_selector, (
            f"Expected playwright_locator or recommended_selector, got neither. "
            f"Result: {result}"
        )
        assert result.confidence > 0.0
        assert result.tokens_used > 0
        logger.info(
            "Playwright login button: locator=%s, selector=%s (confidence: %.2f)",
            result.playwright_locator, result.recommended_selector, result.confidence
        )

    @pytest.mark.asyncio
    async def test_dom_analysis_navigation_link(self):
        """Find a navigation link in semantic HTML."""
        provider = self._make_provider()

        prompt = (
            'Find the best CSS selector for: "Products navigation link"\n\n'
            f'HTML:\n{SAMPLE_HTML_NAVIGATION}\n\n'
            'Respond with valid JSON only:\n'
            '{"selector": "css-selector-here", "confidence": 0.95, '
            '"reasoning": "brief explanation", "alternatives": ["alt1", "alt2"]}'
        )

        result = await provider.analyze_dom(
            prompt=prompt,
            framework=AutomationFramework.SELENIUM,
            max_tokens=500,
            temperature=0.1,
        )

        assert isinstance(result, AIAnalysisResult)
        assert result.recommended_selector is not None
        assert result.confidence > 0.0
        logger.info(
            "Navigation link selector: %s (confidence: %.2f)",
            result.recommended_selector, result.confidence
        )


@requires_local_model
class TestOllamaProviderDisambiguation:
    """Test OllamaProvider's disambiguation capability."""

    @pytest.mark.asyncio
    async def test_disambiguate_edit_buttons(self):
        """AI should pick the correct edit button based on description."""
        provider = OllamaProvider(
            api_url=LOCAL_MODEL_URL,
            model=LOCAL_MODEL_NAME,
            timeout=120,
        )

        prompt = (
            'Multiple elements match the selector. Select the best match for: '
            '"Edit button for Jane Smith"\n\n'
            'Element 1:\n'
            '  Tag: button\n'
            '  Text: Edit\n'
            '  Class: btn btn-edit\n'
            '  Data-action: edit\n'
            '  Data-user-id: 1\n'
            '  (Row context: John Doe, john@example.com, Admin)\n\n'
            'Element 2:\n'
            '  Tag: button\n'
            '  Text: Edit\n'
            '  Class: btn btn-edit\n'
            '  Data-action: edit\n'
            '  Data-user-id: 2\n'
            '  (Row context: Jane Smith, jane@example.com, User)\n\n'
            'Respond with only the number (1 or 2) of the element that best '
            'matches the description.'
        )

        result = await provider.disambiguate(prompt=prompt, max_tokens=10)

        assert isinstance(result, DisambiguationResult)
        assert result.selected_index == 2, (
            f"Expected element 2 (Jane Smith), got {result.selected_index}"
        )
        logger.info(
            "Disambiguation selected element %d (tokens: %d)",
            result.selected_index, result.tokens_used
        )

    @pytest.mark.asyncio
    async def test_disambiguate_navigation_links(self):
        """AI should pick the correct navigation link."""
        provider = OllamaProvider(
            api_url=LOCAL_MODEL_URL,
            model=LOCAL_MODEL_NAME,
            timeout=120,
        )

        prompt = (
            'Multiple elements match the selector. Select the best match for: '
            '"About Us page link"\n\n'
            'Element 1:\n  Tag: a\n  Text: Home\n  Href: /\n\n'
            'Element 2:\n  Tag: a\n  Text: Products\n  Href: /products\n\n'
            'Element 3:\n  Tag: a\n  Text: About Us\n  Href: /about\n\n'
            'Element 4:\n  Tag: a\n  Text: Contact\n  Href: /contact\n\n'
            'Respond with only the number of the best match.'
        )

        result = await provider.disambiguate(prompt=prompt, max_tokens=10)

        assert isinstance(result, DisambiguationResult)
        assert result.selected_index == 3, (
            f"Expected element 3 (About Us), got {result.selected_index}"
        )


# ==================== OpenAI Provider with Local Endpoint ====================

@requires_local_model
class TestOpenAIProviderWithLocalEndpoint:
    """Test that OpenAI provider works when pointed at a local endpoint."""

    @pytest.mark.asyncio
    async def test_openai_provider_dom_analysis(self):
        """OpenAI provider should work with any OpenAI-compatible endpoint."""
        provider = OpenAIProvider(
            api_key="not-needed",
            api_url=LOCAL_MODEL_URL,
            model=LOCAL_MODEL_NAME,
            timeout=120,
        )

        prompt = (
            'Find the best CSS selector for: "Login button"\n\n'
            f'HTML:\n{SAMPLE_HTML_LOGIN}\n\n'
            'Respond with valid JSON only:\n'
            '{"selector": "css-selector-here", "confidence": 0.95, '
            '"reasoning": "brief explanation", "alternatives": ["alt1", "alt2"]}'
        )

        result = await provider.analyze_dom(
            prompt=prompt,
            framework=AutomationFramework.SELENIUM,
            max_tokens=500,
            temperature=0.1,
        )

        assert isinstance(result, AIAnalysisResult)
        assert result.recommended_selector is not None
        assert result.confidence > 0.0
        assert result.tokens_used > 0
        logger.info(
            "OpenAI provider (local): %s (confidence: %.2f, tokens: %d)",
            result.recommended_selector, result.confidence, result.tokens_used
        )


# ==================== ResilientAIService Tests ====================

@requires_local_model
class TestResilientAIServiceWithLocalModel:
    """Test the full ResilientAIService pipeline with LOCAL_MODEL provider."""

    def _make_service(self) -> ResilientAIService:
        ai_config = (
            AIConfig.builder()
            .provider(AIProvider.LOCAL_MODEL)
            .model(LOCAL_MODEL_NAME)
            .api_url(LOCAL_MODEL_URL)
            .api_key("")
            .timeout(timedelta(seconds=120))
            .max_retries(2)
            .temperature_dom(0.1)
            .max_tokens_dom(500)
            .build()
        )
        resilience_config = ResilienceConfig.builder().build()
        return ResilientAIService(ai_config, resilience_config)

    @pytest.mark.asyncio
    async def test_full_dom_analysis_selenium(self):
        """Full pipeline: config -> ResilientAIService -> OllamaProvider -> parse."""
        service = self._make_service()

        result = await service.analyze_dom(
            html=SAMPLE_HTML_LOGIN,
            description="Login button on the form",
            previous_selector="#old-login-btn",
            framework=AutomationFramework.SELENIUM,
        )

        assert isinstance(result, AIAnalysisResult)
        assert result.recommended_selector is not None
        assert len(result.recommended_selector) > 0
        assert result.confidence > 0.0
        assert result.reasoning is not None
        logger.info(
            "ResilientAIService result: %s (confidence: %.2f)",
            result.recommended_selector, result.confidence
        )

    @pytest.mark.asyncio
    async def test_full_dom_analysis_table(self):
        """Full pipeline with a more complex table HTML."""
        service = self._make_service()

        result = await service.analyze_dom(
            html=SAMPLE_HTML_TABLE,
            description="Delete button for the second user",
            framework=AutomationFramework.SELENIUM,
        )

        assert isinstance(result, AIAnalysisResult)
        assert result.recommended_selector is not None
        assert result.confidence > 0.0
        logger.info(
            "Table delete button: %s (confidence: %.2f)",
            result.recommended_selector, result.confidence
        )

    @pytest.mark.asyncio
    async def test_metrics_after_requests(self):
        """Verify metrics are tracked after requests."""
        service = self._make_service()

        await service.analyze_dom(
            html=SAMPLE_HTML_LOGIN,
            description="Username input",
            framework=AutomationFramework.SELENIUM,
        )

        metrics = service.get_metrics()
        assert metrics.total_requests >= 1
        assert metrics.successful_requests >= 1
        assert service.is_healthy()

    @pytest.mark.asyncio
    async def test_playwright_dom_analysis(self):
        """Full pipeline with Playwright framework."""
        service = self._make_service()

        result = await service.analyze_dom(
            html=SAMPLE_HTML_LOGIN,
            description="Login button",
            framework=AutomationFramework.PLAYWRIGHT,
        )

        assert isinstance(result, AIAnalysisResult)
        # Either playwright_locator or recommended_selector should be set
        has_locator = result.playwright_locator is not None
        has_selector = result.recommended_selector is not None
        assert has_locator or has_selector
        assert result.confidence > 0.0
        logger.info(
            "Playwright result: locator=%s, selector=%s, confidence=%.2f",
            result.playwright_locator, result.recommended_selector, result.confidence
        )


# ==================== ResponseParser Tests with Real Output ====================

@requires_local_model
class TestResponseParserWithRealOutput:
    """Test ResponseParser handles real AI model output correctly."""

    @pytest.mark.asyncio
    async def test_parse_real_selenium_response(self):
        """Get real output from model and verify ResponseParser handles it."""
        provider = OllamaProvider(
            api_url=LOCAL_MODEL_URL,
            model=LOCAL_MODEL_NAME,
            timeout=120,
        )

        prompt = (
            'Find the best CSS selector for: "Password input"\n\n'
            f'HTML:\n{SAMPLE_HTML_LOGIN}\n\n'
            'Respond with valid JSON only:\n'
            '{"selector": "css-selector-here", "confidence": 0.95, '
            '"reasoning": "brief explanation", "alternatives": ["alt1", "alt2"]}'
        )

        # Call the provider and get a result - this validates the full chain
        result = await provider.analyze_dom(
            prompt=prompt,
            framework=AutomationFramework.SELENIUM,
            max_tokens=500,
            temperature=0.1,
        )

        # Verify the result structure
        assert result.target_framework == AutomationFramework.SELENIUM
        assert result.recommended_selector is not None
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0
        assert result.reasoning is not None and len(result.reasoning) > 0

    @pytest.mark.asyncio
    async def test_parse_selenium_json_directly(self):
        """Test ResponseParser with a known-good JSON structure."""
        content_json = {
            "selector": "#login-btn",
            "confidence": 0.95,
            "reasoning": "ID-based selector is unique and stable",
            "alternatives": ["button.btn-primary", ".btn.btn-primary[type='submit']"]
        }

        result = ResponseParser.parse_dom_response(
            content_json, AutomationFramework.SELENIUM
        )

        assert result.recommended_selector == "#login-btn"
        assert result.confidence == 0.95
        assert result.reasoning == "ID-based selector is unique and stable"
        assert len(result.alternatives) == 2

    @pytest.mark.asyncio
    async def test_parse_playwright_json_directly(self):
        """Test ResponseParser with Playwright-format JSON."""
        content_json = {
            "locatorType": "getByRole",
            "value": "button",
            "options": {"name": "Login"},
            "confidence": 0.98,
            "reasoning": "Semantic role-based locator is most resilient",
            "alternatives": [
                {"type": "css", "value": "#login-btn"},
                {"type": "getByText", "value": "Login"}
            ]
        }

        result = ResponseParser.parse_dom_response(
            content_json, AutomationFramework.PLAYWRIGHT
        )

        assert result.playwright_locator is not None
        assert result.target_framework == AutomationFramework.PLAYWRIGHT
        assert result.confidence == 0.98
        assert len(result.alternatives) == 2

    def test_parse_disambiguation_response_number(self):
        """Test disambiguation parsing with plain number."""
        assert ResponseParser.parse_disambiguation_response("2") == 2
        assert ResponseParser.parse_disambiguation_response("  3  ") == 3

    def test_parse_disambiguation_response_with_text(self):
        """Test disambiguation parsing with text around number."""
        assert ResponseParser.parse_disambiguation_response("Element 2") == 2
        assert ResponseParser.parse_disambiguation_response("The best match is 3.") == 3


# ==================== Edge Cases ====================

@requires_local_model
class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_html(self):
        """Provider should still return a result (or fail gracefully) with empty HTML."""
        provider = OllamaProvider(
            api_url=LOCAL_MODEL_URL,
            model=LOCAL_MODEL_NAME,
            timeout=120,
        )

        prompt = (
            'Find the best CSS selector for: "Submit button"\n\n'
            'HTML:\n<div></div>\n\n'
            'Respond with valid JSON only:\n'
            '{"selector": "css-selector-here", "confidence": 0.5, '
            '"reasoning": "brief explanation", "alternatives": []}'
        )

        # Should either succeed with low confidence or raise an exception
        try:
            result = await provider.analyze_dom(
                prompt=prompt,
                framework=AutomationFramework.SELENIUM,
                max_tokens=500,
                temperature=0.1,
            )
            assert isinstance(result, AIAnalysisResult)
            logger.info("Empty HTML result: %s", result.recommended_selector)
        except Exception as e:
            logger.info("Empty HTML raised expected exception: %s", str(e))

    @pytest.mark.asyncio
    async def test_provider_name(self):
        provider = OllamaProvider(
            api_url=LOCAL_MODEL_URL,
            model=LOCAL_MODEL_NAME,
        )
        assert provider.get_provider_name() == "Ollama"

    @pytest.mark.asyncio
    async def test_visual_analysis_not_supported(self):
        """Non-vision models should raise NotImplementedError for visual analysis."""
        provider = OllamaProvider(
            api_url=LOCAL_MODEL_URL,
            model=LOCAL_MODEL_NAME,
        )

        assert provider.supports_visual_analysis() is False

        with pytest.raises(NotImplementedError):
            await provider.analyze_visual(
                prompt="Find button",
                screenshot=b"fake-screenshot-data",
            )

    def test_clean_markdown_json(self):
        """Test _clean_markdown handles various markdown wrappings."""
        provider = OllamaProvider()

        # Standard json code block
        assert provider._clean_markdown('```json\n{"a": 1}\n```') == '{"a": 1}'

        # Plain code block
        assert provider._clean_markdown('```\n{"a": 1}\n```') == '{"a": 1}'

        # No code block
        assert provider._clean_markdown('{"a": 1}') == '{"a": 1}'

        # With whitespace
        assert provider._clean_markdown('  ```json\n{"a": 1}\n```  ') == '{"a": 1}'
