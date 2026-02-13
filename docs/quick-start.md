# Quick Start Guide

Get up and running with AutoHeal Locator Python in minutes.

## Prerequisites

- Python 3.9 or higher
- pip package manager
- Selenium WebDriver
- Groq API key (FREE - for AI-powered features)

## Installation

### Using pip (Recommended)

```bash
# Basic installation
pip install autoheal-locator

# With Selenium support
pip install autoheal-locator[selenium]

# With all features
pip install autoheal-locator[all]
```

### From Source

```bash
git clone https://github.com/SanjayPG/autoheal-locator-python.git
cd autoheal-locator-python
pip install -e .
```

## Get Your FREE Groq API Key

1. Visit [console.groq.com](https://console.groq.com)
2. Sign up (no credit card required!)
3. Navigate to **API Keys** section
4. Click **Create API Key**
5. Copy your key (starts with `gsk_...`)

## Basic Example

```python
import os
from selenium import webdriver
from autoheal import AutoHealLocator
from autoheal.impl.adapter import SeleniumWebAutomationAdapter

# Set your Groq API key
os.environ['GROQ_API_KEY'] = 'gsk-your-api-key-here'

# Setup WebDriver
driver = webdriver.Chrome()

# Create AutoHeal locator
adapter = SeleniumWebAutomationAdapter(driver)
locator = AutoHealLocator.builder() \
    .with_web_adapter(adapter) \
    .build()

try:
    # Navigate to your page
    driver.get("https://example.com")

    # Find element with CSS selector and description
    button = locator.find_element("#submit-btn", "Submit button")
    button.click()

    # Find element with XPath selector and description
    email_input = locator.find_element(
        "//input[@type='email']",  # XPath selector
        "Email input field"        # Description for AI healing
    )
    email_input.send_keys("user@example.com")

    # Check if element is present
    if locator.is_element_present(".success-message", "Success message"):
        print("Success!")

finally:
    driver.quit()
```

## Configuration Options

### Using Groq (FREE and Fast)

```python
from autoheal import AutoHealConfiguration
from autoheal.config import AIConfig
from autoheal.models.enums import AIProvider

# Configure Groq (recommended)
ai_config = AIConfig.builder() \
    .provider(AIProvider.GROQ) \
    .api_key(os.getenv("GROQ_API_KEY")) \
    .model("llama-3.3-70b-versatile") \
    .build()

config = AutoHealConfiguration.builder() \
    .ai_config(ai_config) \
    .build()

locator = AutoHealLocator.builder() \
    .with_web_adapter(adapter) \
    .with_configuration(config) \
    .build()
```

### Execution Strategies

```python
from autoheal.config import PerformanceConfig
from autoheal.models.enums import ExecutionStrategy

# Cost-optimized (recommended - default)
perf_config = PerformanceConfig.builder() \
    .execution_strategy(ExecutionStrategy.SMART_SEQUENTIAL) \
    .build()

config = AutoHealConfiguration.builder() \
    .performance_config(perf_config) \
    .build()

# DOM-only (fastest, cheapest)
perf_config = PerformanceConfig.builder() \
    .execution_strategy(ExecutionStrategy.DOM_ONLY) \
    .build()

# Visual-first (most accurate)
perf_config = PerformanceConfig.builder() \
    .execution_strategy(ExecutionStrategy.VISUAL_FIRST) \
    .build()
```

### Caching Configuration

```python
from autoheal.config import CacheConfig
from autoheal.models.enums import CacheType
from datetime import timedelta

# In-memory cache (default)
cache_config = CacheConfig.builder() \
    .cache_type(CacheType.CAFFEINE) \
    .maximum_size(1000) \
    .expire_after_write(timedelta(hours=24)) \
    .build()

# File-based persistent cache
cache_config = CacheConfig.builder() \
    .cache_type(CacheType.PERSISTENT_FILE) \
    .file_path("./cache/autoheal.db") \
    .maximum_size(1000) \
    .build()

# Redis cache (for distributed testing)
cache_config = CacheConfig.builder() \
    .cache_type(CacheType.REDIS) \
    .redis_host("localhost") \
    .redis_port(6379) \
    .maximum_size(10000) \
    .expire_after_write(timedelta(days=7)) \
    .build()

config = AutoHealConfiguration.builder() \
    .cache_config(cache_config) \
    .build()
```

## Async API

For better performance, use the async API:

```python
import asyncio
from selenium import webdriver
from autoheal import AutoHealLocator
from autoheal.impl.adapter import SeleniumWebAutomationAdapter

async def test_login():
    driver = webdriver.Chrome()
    adapter = SeleniumWebAutomationAdapter(driver)

    locator = AutoHealLocator.builder() \
        .with_web_adapter(adapter) \
        .build()

    try:
        driver.get("https://example.com")

        # Use async API
        username = await locator.find_element_async(
            "#username",
            "Username input field"
        )
        password = await locator.find_element_async(
            "#password",
            "Password input field"
        )
        submit = await locator.find_element_async(
            "button[type='submit']",
            "Submit button"
        )

        username.send_keys("testuser")
        password.send_keys("password123")
        submit.click()

        # Check if login succeeded
        is_logged_in = await locator.is_element_present_async(
            ".dashboard",
            "User dashboard"
        )

        if is_logged_in:
            print("Login successful!")

        # Always shutdown gracefully
        await locator.shutdown()

    finally:
        driver.quit()

# Run async function
asyncio.run(test_login())
```

## Using with pytest

```python
import pytest
from selenium import webdriver
from autoheal import AutoHealLocator
from autoheal.impl.adapter import SeleniumWebAutomationAdapter

@pytest.fixture
def autoheal_locator():
    """Fixture to create AutoHeal locator with Selenium"""
    driver = webdriver.Chrome()
    adapter = SeleniumWebAutomationAdapter(driver)

    locator = AutoHealLocator.builder() \
        .with_web_adapter(adapter) \
        .build()

    yield locator

    # Cleanup
    driver.quit()

def test_login_page(autoheal_locator):
    """Test login functionality with auto-healing locators"""
    driver = autoheal_locator.adapter.driver
    driver.get("https://example.com/login")

    # Find elements with auto-healing
    username = autoheal_locator.find_element("#username", "Username field")
    password = autoheal_locator.find_element("#password", "Password field")
    submit = autoheal_locator.find_element("button[type='submit']", "Submit button")

    # Interact with elements
    username.send_keys("testuser")
    password.send_keys("password123")
    submit.click()

    # Verify login success
    assert autoheal_locator.is_element_present(".dashboard", "User dashboard")

def test_product_search(autoheal_locator):
    """Test product search with multiple elements"""
    driver = autoheal_locator.adapter.driver
    driver.get("https://example.com/products")

    # Find search box
    search_box = autoheal_locator.find_element("#search", "Product search box")
    search_box.send_keys("laptop")

    # Find all product cards
    products = autoheal_locator.find_elements(".product-card", "Product cards")

    # Verify search results
    assert len(products) > 0, "Should find at least one product"
```

## Environment Variables

AutoHeal can be configured using environment variables:

```bash
# AI Provider Configuration
export GROQ_API_KEY='gsk-your-api-key'
export AUTOHEAL_AI_PROVIDER='GROQ'
export AUTOHEAL_AI_MODEL='llama-3.3-70b-versatile'

# Cache Configuration
export AUTOHEAL_CACHE_TYPE='REDIS'
export AUTOHEAL_CACHE_REDIS_HOST='localhost'
export AUTOHEAL_CACHE_REDIS_PORT='6379'

# Performance Configuration
export AUTOHEAL_EXECUTION_STRATEGY='SMART_SEQUENTIAL'
```

Then use in your code:

```python
import os
from autoheal import AutoHealConfiguration

# Configuration will automatically load from environment
config = AutoHealConfiguration.from_env()

locator = AutoHealLocator.builder() \
    .with_web_adapter(adapter) \
    .with_configuration(config) \
    .build()
```

## Monitoring and Metrics

```python
# Get locator metrics
metrics = locator.get_metrics()
print(f"Total requests: {metrics.total_requests}")
print(f"Success rate: {metrics.get_success_rate():.2%}")
print(f"Average latency: {metrics.get_average_latency():.0f}ms")

# Get cache metrics
cache_metrics = locator.get_cache_metrics()
print(f"Cache hit rate: {cache_metrics.get_hit_rate():.2%}")
print(f"Total hits: {cache_metrics.total_hits}")
print(f"Total misses: {cache_metrics.total_misses}")

# Check health status
health = locator.get_health_status()
if health['overall']:
    print("System is healthy!")
else:
    print(f"Warning: Success rate is {health['success_rate']:.2%}")
```

## Next Steps

- **[Selenium Usage Guide](selenium-usage-guide.md)** - Detailed Selenium integration
- **[AI Configuration](ai-configuration.md)** - Configure different AI providers
- **[Installation Guide](installation.md)** - Advanced installation options
- **[Groq Setup](../GROQ_SETUP.md)** - Complete Groq configuration guide
- **[Examples](../examples/README.md)** - More comprehensive examples

## Troubleshooting

### Common Issues

**Import Error: No module named 'autoheal'**
```bash
# Make sure you've installed the package
pip install autoheal-locator
```

**API Key Not Found**
```bash
# Set the environment variable
export GROQ_API_KEY='gsk-your-api-key'
# Verify it's set
echo $GROQ_API_KEY
```

**Element Not Found After Healing**
```python
# Enable debug logging to see what's happening
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Cache Not Working**
```python
# Clear the cache and try again
locator.clear_cache()

# Check cache metrics
metrics = locator.get_cache_metrics()
print(f"Hit rate: {metrics.get_hit_rate():.2%}")
```

## Support

- **Documentation**: [docs/](.)
- **Examples**: [examples/](../examples/)
- **Issues**: [GitHub Issues](https://github.com/SanjayPG/autoheal-locator-python/issues)
- **Discussions**: [GitHub Discussions](https://github.com/SanjayPG/autoheal-locator-python/discussions)
