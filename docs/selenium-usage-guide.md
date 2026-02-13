# Selenium Usage Guide

Complete guide for using AutoHeal Locator with Selenium WebDriver in Python.

## Table of Contents

- [Getting Started](#getting-started)
- [Basic Usage](#basic-usage)
- [Advanced Features](#advanced-features)
- [Configuration](#configuration)
- [Best Practices](#best-practices)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

```bash
# Install AutoHeal with Selenium support
pip install autoheal-locator[selenium]

# Or install Selenium separately
pip install selenium>=4.0.0
```

### Basic Setup

```python
from selenium import webdriver
from autoheal import AutoHealLocator
from autoheal.impl.adapter import SeleniumWebAutomationAdapter

# Create WebDriver
driver = webdriver.Chrome()

# Create adapter
adapter = SeleniumWebAutomationAdapter(driver)

# Create AutoHeal locator
locator = AutoHealLocator.builder() \
    .with_web_adapter(adapter) \
    .build()

# Use it!
driver.get("https://example.com")
element = locator.find_element("#submit", "Submit button")
element.click()

# Cleanup
driver.quit()
```

## Basic Usage

### Finding Single Elements

AutoHeal automatically detects the locator type:

```python
# CSS Selector (starts with # or .)
element = locator.find_element("#username", "Username field")
element = locator.find_element(".btn-primary", "Primary button")

# XPath (starts with // or /)
element = locator.find_element("//input[@name='email']", "Email input")

# ID (no special prefix)
element = locator.find_element("submit-btn", "Submit button")

# All standard Selenium locator types are supported
```

### Finding Multiple Elements

```python
# Find all matching elements
products = locator.find_elements(".product-card", "Product cards")

# Iterate over elements
for product in products:
    title = product.find_element("h3", "Product title")
    print(title.text)

# Get count
print(f"Found {len(products)} products")
```

### Checking Element Presence

```python
# Check if element exists (returns bool, no exception)
if locator.is_element_present("#promo-banner", "Promotional banner"):
    print("Banner is visible")
else:
    print("No banner found")

# Useful for optional elements
has_error = locator.is_element_present(".error-message", "Error message")
if has_error:
    error_elem = locator.find_element(".error-message", "Error message")
    print(f"Error: {error_elem.text}")
```

## Advanced Features

### Async/Await API

For better performance, use the async API:

```python
import asyncio
from selenium import webdriver
from autoheal import AutoHealLocator
from autoheal.impl.adapter import SeleniumWebAutomationAdapter

async def test_login():
    driver = webdriver.Chrome()
    adapter = SeleniumWebAutomationAdapter(driver)
    locator = AutoHealLocator.builder().with_web_adapter(adapter).build()

    try:
        driver.get("https://example.com/login")

        # Use async methods
        username = await locator.find_element_async("#username", "Username field")
        password = await locator.find_element_async("#password", "Password field")
        submit = await locator.find_element_async("button[type='submit']", "Submit")

        # Interact with elements (still synchronous Selenium calls)
        username.send_keys("testuser")
        password.send_keys("password123")
        submit.click()

        # Check result
        is_logged_in = await locator.is_element_present_async(
            ".dashboard",
            "Dashboard"
        )
        print(f"Login successful: {is_logged_in}")

        # Always shutdown gracefully
        await locator.shutdown()

    finally:
        driver.quit()

# Run async function
asyncio.run(test_login())
```

### Custom Locator Options

Fine-tune behavior for specific elements:

```python
from autoheal.config import LocatorOptions
from datetime import timedelta

# Create custom options
options = LocatorOptions.builder() \
    .enable_caching(True) \
    .enable_dom_analysis(True) \
    .enable_visual_analysis(False) \
    .timeout(timedelta(seconds=15)) \
    .build()

# Use with find_element
element = locator.find_element(
    "#dynamic-content",
    "Dynamic content area",
    options=options
)
```

### Working with Frames/iframes

```python
# Switch to iframe
driver.switch_to.frame("iframe-id")

# Use AutoHeal inside iframe
element = locator.find_element("#iframe-button", "Button inside iframe")
element.click()

# Switch back
driver.switch_to.default_content()
```

### Multiple Windows/Tabs

```python
# Store original window
main_window = driver.current_window_handle

# Click link that opens new window
link = locator.find_element("#open-new-window", "Open new window link")
link.click()

# Switch to new window
for window in driver.window_handles:
    if window != main_window:
        driver.switch_to.window(window)
        break

# Use AutoHeal in new window
element = locator.find_element("#new-window-content", "Content in new window")

# Switch back
driver.switch_to.window(main_window)
```

### Shadow DOM Support

```python
from selenium.webdriver.common.by import By

# Navigate to shadow root
shadow_host = driver.find_element(By.CSS_SELECTOR, "#shadow-host")
shadow_root = shadow_host.shadow_root

# AutoHeal doesn't directly support shadow DOM yet
# Use standard Selenium for shadow DOM elements
shadow_element = shadow_root.find_element(By.CSS_SELECTOR, "#shadow-element")
```

## Configuration

### Full Configuration Example

```python
from autoheal import AutoHealConfiguration
from autoheal.config import (
    AIConfig,
    CacheConfig,
    PerformanceConfig,
    ResilienceConfig
)
from autoheal.models.enums import (
    AIProvider,
    CacheType,
    ExecutionStrategy
)
from datetime import timedelta

# AI Configuration (Groq - FREE!)
ai_config = AIConfig.builder() \
    .provider(AIProvider.GROQ) \
    .api_key("gsk-your-api-key") \
    .model("llama-3.3-70b-versatile") \
    .temperature(0.1) \
    .max_tokens(2000) \
    .timeout(timedelta(seconds=30)) \
    .build()

# Cache Configuration
cache_config = CacheConfig.builder() \
    .cache_type(CacheType.CAFFEINE) \
    .maximum_size(1000) \
    .expire_after_write(timedelta(days=1)) \
    .build()

# Performance Configuration
perf_config = PerformanceConfig.builder() \
    .execution_strategy(ExecutionStrategy.SMART_SEQUENTIAL) \
    .element_timeout(timedelta(seconds=10)) \
    .build()

# Resilience Configuration
resilience_config = ResilienceConfig.builder() \
    .max_retries(3) \
    .retry_delay(timedelta(seconds=1)) \
    .circuit_breaker_threshold(5) \
    .circuit_breaker_timeout(timedelta(minutes=1)) \
    .build()

# Combine all
config = AutoHealConfiguration.builder() \
    .ai_config(ai_config) \
    .cache_config(cache_config) \
    .performance_config(perf_config) \
    .resilience_config(resilience_config) \
    .build()

# Create locator with full configuration
locator = AutoHealLocator.builder() \
    .with_web_adapter(adapter) \
    .with_configuration(config) \
    .build()
```

### Browser-Specific Configuration

#### Chrome

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Create driver with options
driver = webdriver.Chrome(options=chrome_options)
adapter = SeleniumWebAutomationAdapter(driver)
locator = AutoHealLocator.builder().with_web_adapter(adapter).build()
```

#### Firefox

```python
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

# Firefox options
firefox_options = Options()
firefox_options.add_argument("--headless")

# Create driver
driver = webdriver.Firefox(options=firefox_options)
adapter = SeleniumWebAutomationAdapter(driver)
locator = AutoHealLocator.builder().with_web_adapter(adapter).build()
```

#### Edge

```python
from selenium import webdriver
from selenium.webdriver.edge.options import Options

# Edge options
edge_options = Options()
edge_options.add_argument("--headless")

# Create driver
driver = webdriver.Edge(options=edge_options)
adapter = SeleniumWebAutomationAdapter(driver)
locator = AutoHealLocator.builder().with_web_adapter(adapter).build()
```

## Best Practices

### 1. Always Provide Descriptive Names

```python
# ❌ Bad - vague
element = locator.find_element("#btn", "button")

# ✅ Good - specific and descriptive
element = locator.find_element(
    "#btn",
    "Submit order button on checkout page"
)
```

### 2. Use Caching for Repeated Elements

```python
# Enable caching (default is enabled)
config = AutoHealConfiguration.builder() \
    .cache_config(
        CacheConfig.builder()
            .cache_type(CacheType.CAFFEINE)
            .maximum_size(1000)
            .build()
    ) \
    .build()

# AutoHeal will cache successful heals
# Subsequent calls will be faster
for i in range(100):
    element = locator.find_element("#same-element", "Same element")
    # First call may heal, rest use cache
```

### 3. Handle Dynamic Content Properly

```python
# For dynamic content, use appropriate timeouts
options = LocatorOptions.builder() \
    .timeout(timedelta(seconds=20)) \
    .build()

element = locator.find_element(
    "#ajax-content",
    "Content loaded via AJAX",
    options=options
)
```

### 4. Organize with Page Object Model

```python
from selenium import webdriver
from autoheal import AutoHealLocator
from autoheal.impl.adapter import SeleniumWebAutomationAdapter

class LoginPage:
    """Page Object for Login Page"""

    def __init__(self, driver: webdriver.Chrome, locator: AutoHealLocator):
        self.driver = driver
        self.locator = locator

    def navigate(self):
        self.driver.get("https://example.com/login")

    def enter_username(self, username: str):
        elem = self.locator.find_element("#username", "Username input field")
        elem.send_keys(username)

    def enter_password(self, password: str):
        elem = self.locator.find_element("#password", "Password input field")
        elem.send_keys(password)

    def click_login(self):
        elem = self.locator.find_element(
            "button[type='submit']",
            "Login submit button"
        )
        elem.click()

    def is_error_displayed(self) -> bool:
        return self.locator.is_element_present(
            ".error-message",
            "Login error message"
        )

# Usage
driver = webdriver.Chrome()
adapter = SeleniumWebAutomationAdapter(driver)
locator = AutoHealLocator.builder().with_web_adapter(adapter).build()

login_page = LoginPage(driver, locator)
login_page.navigate()
login_page.enter_username("testuser")
login_page.enter_password("password123")
login_page.click_login()

if login_page.is_error_displayed():
    print("Login failed!")
```

### 5. Monitor Metrics

```python
# Check metrics periodically
metrics = locator.get_metrics()
cache_metrics = locator.get_cache_metrics()

print(f"Success rate: {metrics.get_success_rate():.2%}")
print(f"Cache hit rate: {cache_metrics.get_hit_rate():.2%}")
print(f"Total requests: {metrics.total_requests}")
print(f"Cache size: {locator.get_cache_size()}")

# Alert if success rate drops
if metrics.get_success_rate() < 0.9:
    print("WARNING: Success rate below 90%!")
```

## Examples

### Complete Login Test

```python
import os
from selenium import webdriver
from autoheal import AutoHealLocator
from autoheal.impl.adapter import SeleniumWebAutomationAdapter

def test_login():
    # Setup
    driver = webdriver.Chrome()
    adapter = SeleniumWebAutomationAdapter(driver)
    locator = AutoHealLocator.builder().with_web_adapter(adapter).build()

    try:
        # Navigate
        driver.get("https://example.com/login")

        # Find and interact with elements
        username = locator.find_element("#username", "Username field")
        username.send_keys("testuser")

        password = locator.find_element("#password", "Password field")
        password.send_keys("password123")

        submit = locator.find_element("button[type='submit']", "Submit button")
        submit.click()

        # Verify login
        assert locator.is_element_present(".dashboard", "Dashboard")
        print("Login successful!")

    finally:
        driver.quit()

if __name__ == "__main__":
    test_login()
```

### Shopping Cart Test

```python
def test_add_to_cart():
    driver = webdriver.Chrome()
    adapter = SeleniumWebAutomationAdapter(driver)
    locator = AutoHealLocator.builder().with_web_adapter(adapter).build()

    try:
        # Navigate to products page
        driver.get("https://example.com/products")

        # Find all products
        products = locator.find_elements(".product-card", "Product cards")
        print(f"Found {len(products)} products")

        # Click first product's "Add to Cart" button
        first_product = products[0]
        add_button = first_product.find_element_by_css_selector(".add-to-cart")
        add_button.click()

        # Verify cart count increased
        cart_badge = locator.find_element(".cart-badge", "Cart item count badge")
        assert cart_badge.text == "1"

        print("Product added to cart successfully!")

    finally:
        driver.quit()
```

### Form Filling Test

```python
def test_registration_form():
    driver = webdriver.Chrome()
    adapter = SeleniumWebAutomationAdapter(driver)
    locator = AutoHealLocator.builder().with_web_adapter(adapter).build()

    try:
        driver.get("https://example.com/register")

        # Fill form fields
        locator.find_element("#first-name", "First name").send_keys("John")
        locator.find_element("#last-name", "Last name").send_keys("Doe")
        locator.find_element("#email", "Email").send_keys("john@example.com")
        locator.find_element("#password", "Password").send_keys("SecurePass123")
        locator.find_element("#confirm-password", "Confirm password").send_keys("SecurePass123")

        # Check terms checkbox
        terms = locator.find_element("#terms", "Terms and conditions checkbox")
        if not terms.is_selected():
            terms.click()

        # Submit form
        locator.find_element("button[type='submit']", "Register button").click()

        # Verify success
        assert locator.is_element_present(".success-message", "Success message")
        print("Registration successful!")

    finally:
        driver.quit()
```

## Troubleshooting

### Element Not Found Even After Healing

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check if element actually exists
driver.get("https://example.com")
print(driver.page_source)  # Inspect HTML

# Try with longer timeout
options = LocatorOptions.builder() \
    .timeout(timedelta(seconds=30)) \
    .build()

element = locator.find_element("#element", "Element", options=options)
```

### Stale Element Reference

```python
# If element becomes stale, just re-find it
element = locator.find_element("#dynamic", "Dynamic element")

# ... some time passes, element may become stale ...

# Re-find instead of storing reference
element = locator.find_element("#dynamic", "Dynamic element")
element.click()
```

### Cache Issues

```python
# Clear cache if you suspect stale entries
locator.clear_cache()

# Or remove specific entry
locator.remove_cached_selector("#old-selector", "Description")

# Check cache health
cache_metrics = locator.get_cache_metrics()
print(f"Hit rate: {cache_metrics.get_hit_rate():.2%}")
```

### Performance Issues

```python
# Use DOM-only strategy for better performance
from autoheal.models.enums import ExecutionStrategy

config = AutoHealConfiguration.builder() \
    .performance_config(
        PerformanceConfig.builder()
            .execution_strategy(ExecutionStrategy.DOM_ONLY)
            .build()
    ) \
    .build()

# Monitor performance
metrics = locator.get_metrics()
print(f"Average latency: {metrics.get_average_latency():.0f}ms")
```

## Next Steps

- **[AI Configuration](ai-configuration.md)** - Configure different AI providers
- **[Quick Start](quick-start.md)** - Quick start guide
- **[Installation](installation.md)** - Installation options
- **[Groq Setup](../GROQ_SETUP.md)** - FREE Groq API setup
- **[Examples](../examples/README.md)** - More examples

## Support

- **GitHub Issues**: [Report Issues](https://github.com/SanjayPG/autoheal-locator-python/issues)
- **Discussions**: [Ask Questions](https://github.com/SanjayPG/autoheal-locator-python/discussions)
