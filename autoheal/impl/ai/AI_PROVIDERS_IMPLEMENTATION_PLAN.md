# AI Providers Implementation Plan

This document outlines the plan for implementing the full ResilientAIService with all AI providers.

## Overview

The Java `ResilientAIService` is a monolithic ~2300-line file that contains all AI provider implementations embedded within it. The Python conversion should use a more modular architecture.

## Architecture

### Current Status
- ✅ MockAIService implemented (fully functional for testing)
- ⏳ ResilientAIService (foundation created, providers pending)

### Proposed Modular Structure

```
autoheal/impl/ai/
├── __init__.py
├── mock_ai_service.py  (✅ COMPLETE)
├── resilient_ai_service.py  (⏳ IN PROGRESS - foundation only)
├── providers/
│   ├── __init__.py
│   ├── base_provider.py  (Abstract base class for all providers)
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   ├── gemini_provider.py
│   ├── deepseek_provider.py
│   ├── grok_provider.py
│   └── ollama_provider.py
```

## Provider Implementation Details

### Base Provider Interface

Each provider should implement:

```python
class AIProvider(ABC):
    @abstractmethod
    async def analyze_dom(
        self,
        prompt: str,
        framework: AutomationFramework
    ) -> AIAnalysisResult:
        """Perform DOM analysis using provider's API."""
        pass

    @abstractmethod
    async def analyze_visual(
        self,
        prompt: str,
        screenshot: bytes
    ) -> AIAnalysisResult:
        """Perform visual analysis (if supported)."""
        pass

    @abstractmethod
    async def disambiguate(
        self,
        prompt: str
    ) -> int:
        """Select best element from multiple candidates."""
        pass

    @abstractmethod
    def supports_visual_analysis(self) -> bool:
        """Check if provider supports visual/image analysis."""
        pass
```

### OpenAI Provider

**API Details:**
- Endpoint: `https://api.openai.com/v1/chat/completions`
- Headers: `Authorization: Bearer {api_key}`
- Models: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`
- Visual support: ✅ Yes (GPT-4 Vision)

**Key Features:**
- DOM analysis with JSON-mode responses
- Visual analysis using base64-encoded images
- Streaming support (optional)
- Token usage tracking for cost metrics

**Request Format:**
```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "system", "content": "System prompt..."},
    {"role": "user", "content": "User prompt..."}
  ],
  "max_tokens": 2000,
  "temperature": 0.7
}
```

### Anthropic Claude Provider

**API Details:**
- Endpoint: `https://api.anthropic.com/v1/messages`
- Headers:
  - `x-api-key: {api_key}`
  - `anthropic-version: 2023-06-01`
- Models: `claude-3-5-sonnet-20241022`, `claude-3-opus`, `claude-3-haiku`
- Visual support: ✅ Yes (Claude 3 models)

**Key Features:**
- Excellent at structured JSON responses
- Strong reasoning capabilities
- System prompts separate from messages
- Image analysis with base64

**Request Format:**
```json
{
  "model": "claude-3-5-sonnet-20241022",
  "max_tokens": 2000,
  "messages": [
    {"role": "user", "content": "Prompt..."}
  ]
}
```

### Google Gemini Provider

**API Details:**
- Endpoint: `https://generativelanguage.googleapis.com/v1/models/{model}:generateContent`
- Headers:
  - `x-goog-api-key: {api_key}`
- Models: `gemini-1.5-pro`, `gemini-1.5-flash`
- Visual support: ✅ Yes (multimodal models)

**Key Features:**
- Multimodal (text + image) input
- Large context window
- Cost-effective pricing
- Different request/response format

**Request Format:**
```json
{
  "contents": [
    {
      "parts": [
        {"text": "Prompt..."}
      ]
    }
  ],
  "generationConfig": {
    "temperature": 0.7,
    "maxOutputTokens": 2000
  }
}
```

### DeepSeek Provider

**API Details:**
- Endpoint: `https://api.deepseek.com/v1/chat/completions`
- Headers: `Authorization: Bearer {api_key}`
- Models: `deepseek-chat`, `deepseek-coder`
- Visual support: ❌ No
- **OpenAI-compatible API** (can reuse OpenAI request/response parsing)

### Grok Provider

**API Details:**
- Endpoint: `https://api.x.ai/v1/chat/completions`
- Models: `grok-beta`
- Visual support: ❌ No
- **OpenAI-compatible API** (can reuse OpenAI request/response parsing)

### Ollama Provider (Local)

**API Details:**
- Endpoint: `http://localhost:11434/api/chat` (default)
- Models: User-installed (e.g., `llama2`, `mistral`, `codellama`)
- Visual support: ⚠️ Depends on model (llava, bakllava)
- **Streaming JSON responses** (different parsing logic)

**Key Features:**
- Local deployment (no API key required)
- Privacy-focused
- Streaming responses
- Free to use

**Request Format:**
```json
{
  "model": "llama2",
  "messages": [
    {"role": "system", "content": "System..."},
    {"role": "user", "content": "User..."}
  ]
}
```

## Prompt Engineering

### DOM Analysis Prompts

The system uses different prompts for Selenium vs Playwright:

**Selenium Prompt** (CSS/XPath selectors):
```
You are a web automation expert. Find the best CSS selector for: "{description}"

The selector "{previous_selector}" is broken. Analyze the HTML and find the correct element.

HTML:
{html}

REQUIREMENTS:
- Look for elements with matching id, name, class, or text content
- Prefer ID selectors (#id) when available
- Ensure the selector matches exactly one element
- The selector must be valid CSS syntax

Respond with valid JSON only:
{
    "selector": "css-selector-here",
    "confidence": 0.95,
    "reasoning": "brief explanation",
    "alternatives": ["alt1", "alt2"]
}
```

**Playwright Prompt** (User-facing locators):
```
You are a Playwright automation expert. Find the best user-facing locator for: "{description}"

PRIORITY ORDER:
1. getByRole() - ARIA role with accessible name
2. getByLabel() - Form label text
3. getByPlaceholder() - Input placeholder
4. getByText() - Visible text content
5. getByTestId() - Test ID attribute
6. CSS Selector - FALLBACK ONLY

Respond with valid JSON:
{
    "locatorType": "getByRole|getByLabel|...",
    "value": "button|Username|...",
    "options": {"name": "Submit"},
    "confidence": 0.95,
    "reasoning": "...",
    "alternatives": [...]
}
```

### Visual Analysis Prompts

Enhanced visual analysis with robustness focus:
```
You are an expert web automation engineer. Analyze the provided screenshot to locate an element described as: "{description}"

Generate ROBUST selectors that will survive DOM changes by identifying:
1. Multiple identification strategies (ID, class, attributes, text content)
2. Stable visual landmarks nearby for relative positioning
3. Hierarchical relationships with parent containers
4. Text-based selectors using visible content
5. Semantic attributes like data-testid, aria-label, role

Respond in JSON format:
{
    "primary_selector": "most reliable CSS selector",
    "alternative_selectors": ["fallback option 1", "fallback option 2"],
    "visual_landmarks": ["stable nearby elements"],
    "text_based_selector": "selector using visible text",
    "confidence": 0.85,
    "stability_reasoning": "why these selectors should survive DOM changes"
}
```

## Implementation Priority

1. **Phase 1: Foundation** ✅
   - [x] MockAIService for testing
   - [x] ResilientAIService basic structure
   - [x] Circuit breaker integration

2. **Phase 2: Core Providers** (Next)
   - [ ] OpenAI provider (most common)
   - [ ] Anthropic Claude provider (high quality)
   - [ ] Gemini provider (cost-effective)

3. **Phase 3: Additional Providers**
   - [ ] DeepSeek provider (OpenAI-compatible)
   - [ ] Grok provider (OpenAI-compatible)
   - [ ] Ollama provider (local, different format)

4. **Phase 4: Advanced Features**
   - [ ] Retry logic with exponential backoff
   - [ ] Token usage tracking and cost metrics
   - [ ] Response caching
   - [ ] Streaming support
   - [ ] Failover between providers

## HTTP Client

Use `aiohttp` for async HTTP requests:

```python
import aiohttp
import asyncio

class OpenAIProvider:
    async def _make_request(self, request_body: dict) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request_body,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response.raise_for_status()
                return await response.json()
```

## Testing Strategy

1. **Unit Tests**:
   - Mock HTTP responses for each provider
   - Test request body creation
   - Test response parsing
   - Test error handling

2. **Integration Tests**:
   - Test with actual API keys (optional, CI/CD)
   - Use MockAIService for fast tests
   - Playwright and Selenium integration tests

3. **Performance Tests**:
   - Measure latency for each provider
   - Test circuit breaker behavior
   - Cost tracking accuracy

## Dependencies

Add to `pyproject.toml`:
```toml
[tool.poetry.dependencies]
aiohttp = "^3.9.0"  # Async HTTP client
httpx = "^0.25.0"   # Alternative async HTTP client (optional)
```

## Migration from Java

Key differences:
- Java uses `CompletableFuture` → Python uses `async`/`await`
- Java uses `OkHttpClient` → Python uses `aiohttp` or `httpx`
- Java uses Jackson for JSON → Python uses built-in `json` + Pydantic models
- Java uses thread pools → Python uses `asyncio` event loop

## Next Steps

1. Implement OpenAI provider first (most mature API)
2. Create base provider abstract class
3. Implement ResilientAIService with provider routing
4. Add unit tests for MockAIService
5. Gradually add other providers
6. Implement visual analysis support
7. Add comprehensive integration tests

---

**Status:** Foundation complete, ready for provider implementations
**Est. Effort:** ~20-30 hours for full implementation
**Priority:** High (core functionality)
