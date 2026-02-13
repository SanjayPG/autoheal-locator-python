# AutoHeal Locator Python - Documentation

Welcome to the AutoHeal Locator Python documentation!

## 📚 Documentation Index

### Getting Started

- **[Quick Start Guide](quick-start.md)** - Get up and running in minutes
- **[Installation Guide](installation.md)** - Complete installation instructions
- **[Groq Setup Guide](../GROQ_SETUP.md)** - FREE Groq API setup

### User Guides

- **[Selenium Usage Guide](selenium-usage-guide.md)** - Complete Selenium integration guide
- **[AI Configuration](ai-configuration.md)** - Configure AI providers (Groq, OpenAI, Claude, etc.)

### Reference

- **[API Reference](../README.md#-api-reference)** - Complete API documentation
- **[Configuration Options](ai-configuration.md#configuration-options)** - All configuration options
- **[Examples](../examples/README.md)** - Code examples and use cases

## 🚀 Quick Links

### I want to...

- **Get started quickly** → [Quick Start Guide](quick-start.md)
- **Install AutoHeal** → [Installation Guide](installation.md)
- **Use with Selenium** → [Selenium Usage Guide](selenium-usage-guide.md)
- **Configure AI provider** → [AI Configuration](ai-configuration.md)
- **Use FREE AI** → [Groq Setup Guide](../GROQ_SETUP.md)
- **See examples** → [Examples Directory](../examples/README.md)
- **Troubleshoot issues** → [Quick Start - Troubleshooting](quick-start.md#troubleshooting)

## 📖 Documentation by Topic

### Installation

1. [Prerequisites](installation.md#prerequisites)
2. [Basic Installation](installation.md#basic-installation)
3. [Installation Options](installation.md#installation-options)
4. [Platform-Specific](installation.md#platform-specific-instructions)
5. [Docker Setup](installation.md#docker)
6. [Virtual Environments](installation.md#virtual-environment-setup)

### Configuration

1. [AI Providers](ai-configuration.md)
   - [Groq (FREE)](ai-configuration.md#groq-recommended---free)
   - [OpenAI](ai-configuration.md#openai)
   - [Anthropic Claude](ai-configuration.md#anthropic-claude)
   - [Google Gemini](ai-configuration.md#google-gemini)
   - [Ollama (Local)](ai-configuration.md#ollama-local)

2. [Cache Configuration](quick-start.md#caching-configuration)
   - In-Memory Cache
   - Redis Cache
   - File-Based Cache

3. [Performance Tuning](quick-start.md#execution-strategies)
   - Execution Strategies
   - Timeouts
   - Optimization

### Usage

1. [Basic Usage](selenium-usage-guide.md#basic-usage)
   - Finding Elements
   - Finding Multiple Elements
   - Checking Presence

2. [Advanced Features](selenium-usage-guide.md#advanced-features)
   - Async/Await API
   - Custom Options
   - Page Object Model

3. [Best Practices](selenium-usage-guide.md#best-practices)
   - Naming Conventions
   - Caching Strategies
   - Monitoring

## 🎯 Common Tasks

### Setup a New Project

```bash
# 1. Install AutoHeal
pip install autoheal-locator[all]

# 2. Get FREE Groq API key
# Visit https://console.groq.com

# 3. Set environment variable
export GROQ_API_KEY='gsk-your-key'

# 4. Create your first test
# See Quick Start Guide
```

### Migrate from Standard Selenium

```python
# Before
from selenium import webdriver
driver = webdriver.Chrome()
element = driver.find_element("id", "submit")

# After
from autoheal import AutoHealLocator
from autoheal.impl.adapter import SeleniumWebAutomationAdapter

driver = webdriver.Chrome()
adapter = SeleniumWebAutomationAdapter(driver)
locator = AutoHealLocator.builder().with_web_adapter(adapter).build()
element = locator.find_element("submit", "Submit button")
```

### Configure Different AI Providers

See [AI Configuration Guide](ai-configuration.md) for complete details.

### Enable Caching

```python
from autoheal.config import CacheConfig
from autoheal.models.enums import CacheType

cache_config = CacheConfig.builder() \
    .cache_type(CacheType.REDIS) \
    .redis_host("localhost") \
    .build()
```

### Monitor Performance

```python
# Get metrics
metrics = locator.get_metrics()
cache_metrics = locator.get_cache_metrics()

print(f"Success rate: {metrics.get_success_rate():.2%}")
print(f"Cache hit rate: {cache_metrics.get_hit_rate():.2%}")
```

## 💡 Tips & Tricks

### Use FREE Groq for Development

Groq is completely FREE and 10x faster than other providers!

```python
from autoheal.models.enums import AIProvider

ai_config = AIConfig.builder() \
    .provider(AIProvider.GROQ) \
    .api_key(os.getenv("GROQ_API_KEY")) \
    .model("llama-3.3-70b-versatile") \
    .build()
```

[**Full Groq Setup Guide →**](../GROQ_SETUP.md)

### Save Costs with Caching

Enable caching to reduce AI API calls by 80%+:

```python
cache_config = CacheConfig.builder() \
    .cache_type(CacheType.CAFFEINE) \
    .maximum_size(1000) \
    .expire_after_write(timedelta(days=1)) \
    .build()
```

### Use Async API for Speed

```python
import asyncio

async def test():
    element = await locator.find_element_async("#id", "Description")
    # Much faster for multiple elements!

asyncio.run(test())
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Error**
   ```bash
   pip install autoheal-locator[all]
   ```

2. **API Key Not Found**
   ```bash
   export GROQ_API_KEY='gsk-your-key'
   ```

3. **Element Not Found**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

See [Quick Start - Troubleshooting](quick-start.md#troubleshooting) for more.

## 📚 Additional Resources

### Examples

- [Basic Examples](../examples/README.md)
- [Selenium Examples](../examples/selenium_basic.py)
- [Advanced Examples](../examples/selenium_advanced.py)
- [Pytest Examples](../examples/test_with_pytest.py)

### GitHub

- [Repository](https://github.com/SanjayPG/autoheal-locator-python)
- [Issues](https://github.com/SanjayPG/autoheal-locator-python/issues)
- [Discussions](https://github.com/SanjayPG/autoheal-locator-python/discussions)

### Original Java Project

- [Java AutoHeal Locator](https://github.com/SanjayPG/autoheal-locator)

## 📞 Support

- **🐛 Bug Reports**: [GitHub Issues](https://github.com/SanjayPG/autoheal-locator-python/issues)
- **💡 Feature Requests**: [GitHub Discussions](https://github.com/SanjayPG/autoheal-locator-python/discussions)
- **📧 Email**: support@autoheal-locator.dev

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](../CONTRIBUTING.md) for details.

---

**Happy Testing with AutoHeal! 🤖✨**
