# AI Configuration Guide

Complete guide for configuring AI providers with AutoHeal Locator.

## Table of Contents

- [Overview](#overview)
- [Groq (Recommended - FREE)](#groq-recommended---free)
- [OpenAI](#openai)
- [Anthropic Claude](#anthropic-claude)
- [Google Gemini](#google-gemini)
- [DeepSeek](#deepseek)
- [Grok](#grok)
- [Ollama (Local)](#ollama-local)
- [Configuration Options](#configuration-options)
- [Best Practices](#best-practices)

## Overview

AutoHeal supports multiple AI providers for element healing. Each provider has different characteristics:

| Provider | Cost | Speed | Accuracy | Vision Support |
|----------|------|-------|----------|----------------|
| **Groq** | FREE | ⚡⚡⚡ Ultra Fast | High | ✅ Yes |
| **Google Gemini** | Low | ⚡⚡ Fast | High | ✅ Yes |
| **OpenAI** | Medium | ⚡ Medium | Very High | ✅ Yes |
| **Anthropic Claude** | Medium | ⚡ Medium | Very High | ✅ Yes |
| **DeepSeek** | Low | ⚡⚡ Fast | Good | ❌ No |
| **Grok** | Medium | ⚡⚡ Fast | Good | ❌ No |
| **Ollama** | FREE | ⚡ Varies | Varies | ⚡ Model-dependent |

## Groq (Recommended - FREE)

**Best for**: Development, CI/CD, Production (FREE!)

Groq provides ultra-fast, completely FREE AI inference - perfect for AutoHeal!

### Setup

1. Get FREE API key at [console.groq.com](https://console.groq.com)
2. No credit card required
3. 14,400 requests/day free tier

### Configuration

```python
from autoheal import AutoHealConfiguration
from autoheal.config import AIConfig
from autoheal.models.enums import AIProvider

# For DOM analysis (text-based)
ai_config = AIConfig.builder() \
    .provider(AIProvider.GROQ) \
    .api_key("gsk-your-api-key") \
    .model("llama-3.3-70b-versatile") \
    .temperature(0.1) \
    .build()

config = AutoHealConfiguration.builder() \
    .ai_config(ai_config) \
    .build()
```

### Available Models

#### Text Models (DOM Analysis)
- `llama-3.3-70b-versatile` (Recommended) - Fast and accurate
- `llama-3.1-70b-versatile` - Alternative option
- `mixtral-8x7b-32768` - Longer context window

#### Vision Models (Screenshot Analysis)
- `llama-3.2-11b-vision-preview` (Recommended) - Good balance
- `llama-3.2-90b-vision-preview` - Higher accuracy

### Environment Variables

```bash
# Set API key
export GROQ_API_KEY='gsk-your-api-key'
```

Then use:

```python
import os

ai_config = AIConfig.builder() \
    .provider(AIProvider.GROQ) \
    .api_key(os.getenv("GROQ_API_KEY")) \
    .model("llama-3.3-70b-versatile") \
    .build()
```

### Why Groq?

✅ **FREE** - No cost, no credit card
✅ **Fast** - 10x faster than other providers
✅ **Generous Limits** - 14,400 requests/day
✅ **Vision Support** - Screenshot analysis available
✅ **No Vendor Lock-in** - OpenAI-compatible API

**[📖 Full Groq Setup Guide](../GROQ_SETUP.md)**

---

## OpenAI

**Best for**: Production (if budget allows), High accuracy requirements

### Setup

1. Get API key at [platform.openai.com](https://platform.openai.com/api-keys)
2. Credit card required
3. Pay-as-you-go pricing

### Configuration

```python
from autoheal.config import AIConfig
from autoheal.models.enums import AIProvider

ai_config = AIConfig.builder() \
    .provider(AIProvider.OPENAI) \
    .api_key("sk-your-api-key") \
    .model("gpt-4o-mini") \
    .temperature(0.1) \
    .max_tokens(2000) \
    .build()
```

### Available Models

- `gpt-4o` - Most capable (expensive)
- `gpt-4o-mini` (Recommended) - Good balance of cost/performance
- `gpt-4-turbo` - Fast and capable
- `gpt-3.5-turbo` - Cheapest, good for simple cases

### Vision Support

```python
# Use vision model for screenshot analysis
ai_config = AIConfig.builder() \
    .provider(AIProvider.OPENAI) \
    .api_key("sk-your-api-key") \
    .model("gpt-4o")  # Supports vision
    .build()
```

### Cost Optimization

```python
# Use cheaper model for DOM, expensive for visual
from autoheal.models.enums import ExecutionStrategy

config = AutoHealConfiguration.builder() \
    .ai_config(
        AIConfig.builder()
            .provider(AIProvider.OPENAI)
            .api_key("sk-your-api-key")
            .model("gpt-4o-mini")  # Cheaper
            .build()
    ) \
    .performance_config(
        PerformanceConfig.builder()
            .execution_strategy(ExecutionStrategy.DOM_ONLY)  # Skip visual
            .build()
    ) \
    .build()
```

---

## Anthropic Claude

**Best for**: Complex DOM analysis, High accuracy

### Setup

1. Get API key at [console.anthropic.com](https://console.anthropic.com/)
2. Credit card required
3. Pay-as-you-go pricing

### Configuration

```python
from autoheal.config import AIConfig
from autoheal.models.enums import AIProvider

ai_config = AIConfig.builder() \
    .provider(AIProvider.ANTHROPIC_CLAUDE) \
    .api_key("sk-ant-your-api-key") \
    .model("claude-3-5-sonnet-20241022") \
    .temperature(0.1) \
    .max_tokens(4000) \
    .build()
```

### Available Models

- `claude-3-5-sonnet-20241022` (Recommended) - Best balance
- `claude-3-opus-20240229` - Most capable (expensive)
- `claude-3-haiku-20240307` - Fast and cheap

### Vision Support

All Claude 3 models support vision:

```python
ai_config = AIConfig.builder() \
    .provider(AIProvider.ANTHROPIC_CLAUDE) \
    .api_key("sk-ant-your-api-key") \
    .model("claude-3-5-sonnet-20241022")  # Has vision
    .build()
```

---

## Google Gemini

**Best for**: Good balance of cost and performance

### Setup

1. Get API key at [makersuite.google.com](https://makersuite.google.com/app/apikey)
2. Free tier available
3. Pay-as-you-go for production

### Configuration

```python
from autoheal.config import AIConfig
from autoheal.models.enums import AIProvider

ai_config = AIConfig.builder() \
    .provider(AIProvider.GEMINI) \
    .api_key("your-gemini-api-key") \
    .model("gemini-2.0-flash") \
    .temperature(0.1) \
    .build()
```

### Available Models

- `gemini-2.0-flash` (Recommended) - Fast and efficient
- `gemini-1.5-pro` - Most capable
- `gemini-1.5-flash` - Fast and cheap

### Vision Support

```python
ai_config = AIConfig.builder() \
    .provider(AIProvider.GEMINI) \
    .api_key("your-gemini-api-key") \
    .model("gemini-2.0-flash")  # Supports vision
    .build()
```

---

## DeepSeek

**Best for**: Low-cost alternative to OpenAI

### Setup

1. Get API key at [platform.deepseek.com](https://platform.deepseek.com/)
2. Very affordable pricing

### Configuration

```python
from autoheal.config import AIConfig
from autoheal.models.enums import AIProvider

ai_config = AIConfig.builder() \
    .provider(AIProvider.DEEPSEEK) \
    .api_key("your-deepseek-key") \
    .base_url("https://api.deepseek.com") \
    .model("deepseek-chat") \
    .build()
```

### Available Models

- `deepseek-chat` - General purpose
- `deepseek-coder` - Better for technical content

**Note**: DeepSeek currently doesn't support vision analysis.

---

## Grok

**Best for**: X.AI ecosystem users

### Setup

1. Get API key at [console.x.ai](https://console.x.ai/)
2. Pay-as-you-go pricing

### Configuration

```python
from autoheal.config import AIConfig
from autoheal.models.enums import AIProvider

ai_config = AIConfig.builder() \
    .provider(AIProvider.GROK) \
    .api_key("your-grok-api-key") \
    .base_url("https://api.x.ai/v1") \
    .model("grok-beta") \
    .build()
```

**Note**: Grok currently doesn't support vision analysis.

---

## Ollama (Local)

**Best for**: Privacy, No internet, Development

### Setup

1. Install Ollama: [ollama.ai](https://ollama.ai)
2. Pull a model: `ollama pull llama3.2`
3. Start Ollama: `ollama serve`

### Configuration

```python
from autoheal.config import AIConfig
from autoheal.models.enums import AIProvider

ai_config = AIConfig.builder() \
    .provider(AIProvider.OLLAMA) \
    .base_url("http://localhost:11434") \
    .model("llama3.2") \
    .build()
```

### Available Models

Download with `ollama pull <model>`:

- `llama3.2` - Good general purpose
- `llama3.2-vision` - Vision support
- `codellama` - Better for HTML/code
- `mixtral` - Large context window

### Vision Support

```python
# Use vision model
ai_config = AIConfig.builder() \
    .provider(AIProvider.OLLAMA) \
    .base_url("http://localhost:11434") \
    .model("llama3.2-vision") \
    .build()
```

### Benefits

✅ **FREE** - Completely free to run locally
✅ **Privacy** - Data stays on your machine
✅ **No Internet** - Works offline
✅ **No Rate Limits** - Use as much as you want

### Drawbacks

⚠️ **Slower** - Depends on your hardware
⚠️ **Less Accurate** - Smaller models may be less accurate
⚠️ **Resource Intensive** - Requires GPU for good performance

---

## Configuration Options

### Common Configuration

All providers support these options:

```python
ai_config = AIConfig.builder() \
    .provider(AIProvider.GROQ) \
    .api_key("your-api-key") \
    .model("model-name") \
    .temperature(0.1) \          # Lower = more consistent (0.0-2.0)
    .max_tokens(2000) \           # Max response length
    .timeout(timedelta(seconds=30)) \  # Request timeout
    .build()
```

### Temperature

Controls randomness of responses:

```python
# More deterministic (recommended for AutoHeal)
.temperature(0.0)

# Balanced
.temperature(0.1)

# More creative
.temperature(0.7)
```

### Token Limits

```python
# Conservative (cheaper)
.max_tokens(1000)

# Balanced (recommended)
.max_tokens(2000)

# Generous (for complex pages)
.max_tokens(4000)
```

### Timeouts

```python
from datetime import timedelta

# Quick timeout
.timeout(timedelta(seconds=15))

# Standard timeout (recommended)
.timeout(timedelta(seconds=30))

# Long timeout (for slow providers)
.timeout(timedelta(seconds=60))
```

### Custom Base URL

For providers with custom endpoints:

```python
ai_config = AIConfig.builder() \
    .provider(AIProvider.OPENAI) \
    .api_key("your-key") \
    .base_url("https://your-custom-endpoint.com/v1") \
    .model("model-name") \
    .build()
```

---

## Best Practices

### 1. Use Groq for Development

```python
# Development configuration (FREE!)
dev_config = AIConfig.builder() \
    .provider(AIProvider.GROQ) \
    .api_key(os.getenv("GROQ_API_KEY")) \
    .model("llama-3.3-70b-versatile") \
    .build()
```

### 2. Switch Providers Based on Environment

```python
import os

def get_ai_config():
    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        # Use OpenAI for production
        return AIConfig.builder() \
            .provider(AIProvider.OPENAI) \
            .api_key(os.getenv("OPENAI_API_KEY")) \
            .model("gpt-4o-mini") \
            .build()
    else:
        # Use FREE Groq for dev/test
        return AIConfig.builder() \
            .provider(AIProvider.GROQ) \
            .api_key(os.getenv("GROQ_API_KEY")) \
            .model("llama-3.3-70b-versatile") \
            .build()
```

### 3. Monitor Usage and Costs

```python
# Track AI usage
metrics = locator.get_metrics()
print(f"Total AI calls: {metrics.total_ai_calls}")
print(f"Cache saved: {metrics.cache_hits} calls")

# Estimate costs (for paid providers)
if ai_config.provider == AIProvider.OPENAI:
    cost_per_call = 0.01  # Approximate
    total_cost = metrics.total_ai_calls * cost_per_call
    print(f"Estimated cost: ${total_cost:.2f}")
```

### 4. Use Caching to Reduce Costs

```python
# Enable aggressive caching
cache_config = CacheConfig.builder() \
    .cache_type(CacheType.REDIS) \
    .maximum_size(10000) \
    .expire_after_write(timedelta(days=7)) \
    .build()

config = AutoHealConfiguration.builder() \
    .ai_config(ai_config) \
    .cache_config(cache_config) \
    .build()

# Cache can reduce AI calls by 80%+!
```

### 5. Choose Right Strategy for Provider

```python
# For FREE providers (Groq, Ollama), use PARALLEL for speed
config_groq = AutoHealConfiguration.builder() \
    .ai_config(groq_ai_config) \
    .performance_config(
        PerformanceConfig.builder()
            .execution_strategy(ExecutionStrategy.PARALLEL)
            .build()
    ) \
    .build()

# For PAID providers, use SMART_SEQUENTIAL to minimize costs
config_openai = AutoHealConfiguration.builder() \
    .ai_config(openai_ai_config) \
    .performance_config(
        PerformanceConfig.builder()
            .execution_strategy(ExecutionStrategy.SMART_SEQUENTIAL)
            .build()
    ) \
    .build()
```

---

## Next Steps

- **[Quick Start](quick-start.md)** - Get started quickly
- **[Selenium Guide](selenium-usage-guide.md)** - Selenium integration
- **[Groq Setup](../GROQ_SETUP.md)** - FREE Groq detailed setup
- **[Examples](../examples/README.md)** - Configuration examples

## Support

- **GitHub Issues**: [Report Issues](https://github.com/SanjayPG/autoheal-locator-python/issues)
- **Discussions**: [Ask Questions](https://github.com/SanjayPG/autoheal-locator-python/discussions)
