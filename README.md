# AutoHeal Locator — Python Edition

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Selenium](https://img.shields.io/badge/Selenium-4.x-green.svg)](https://www.selenium.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Async](https://img.shields.io/badge/async-native-green.svg)](https://docs.python.org/3/library/asyncio.html)

**AI-powered test automation library that automatically heals broken locators for both Selenium and Playwright.** When your element locators break due to UI changes, AutoHeal intelligently finds the elements using DOM analysis, visual recognition, and smart fallback strategies.

> **Python port** of the original [Java AutoHeal Locator](https://github.com/SanjayPG/autoheal-locator). All features have been re-implemented in idiomatic Python with async/await support.

---

## Table of Contents

- [Framework Comparison](#framework-comparison)
- [How It Works](#how-it-works)
- [Key Features](#key-features)
- [Installation](#installation)
- [Selenium Quick Start](#selenium-quick-start)
- [Playwright Quick Start](#playwright-quick-start)
- [AI Provider Configuration](#ai-provider-configuration)
- [Execution Strategies](#execution-strategies)
- [Cache Configuration](#cache-configuration)
- [Performance Configuration](#performance-configuration)
- [Reporting](#reporting)
- [pytest Integration](#pytest-integration)
- [Full Configuration Reference](#full-configuration-reference)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Framework Comparison

| Feature | Selenium | Playwright |
|---------|----------|-----------|
| **Locator Types** | CSS, XPath, ID, Name, Class, Tag, Link Text | `get_by_role`, `get_by_text`, `get_by_placeholder`, CSS, XPath |
| **AutoHeal Support** | Full | Coming Soon |
| **Filter Support** | N/A | `has_text`, `has_not_text`, `has`, `has_not` |
| **Native Objects** | `WebElement` | `Locator` |
| **Zero-Rewrite** | Requires wrapper | Native locators work directly |
| **Visual Analysis** | Supported | Supported |
| **DOM Analysis** | Supported | Framework-aware |
| **Caching** | Unified cache | Unified cache |
| **Async API** | `find_element_async()` | `find_async()` |

---

## How It Works

When a test calls `find_element()`, AutoHeal follows this sequence:

```
Test calls find_element("#selector", "description")
         │
         ▼
┌─────────────────────┐
│  1. Try Original    │──── Found ────► Return element
│     Selector        │
└─────────────────────┘
         │ Not found (quick timeout)
         ▼
┌─────────────────────┐
│  2. Check Cache     │──── Cache hit ► Try cached selector ──► Return element
│                     │
└─────────────────────┘
         │ Cache miss
         ▼
┌─────────────────────┐
│  3. AI Healing      │
│  (per strategy)     │
│  · DOM Analysis     │──── Found ────► Cache result ──► Return element
│  · Visual Analysis  │
└─────────────────────┘
         │ All failed
         ▼
    ElementNotFoundException
```

1. **Try Original** — attempts the selector with a short timeout (default 500ms)
2. **Check Cache** — looks up previously healed selectors to avoid repeat AI calls
3. **AI Healing** — DOM analysis reads the page HTML; Visual analysis reads a screenshot
4. **Cache Result** — stores the healed selector so future runs skip the AI step

---

## Key Features

- **AI-Powered Healing** — Uses DOM analysis and visual recognition to find relocated elements
- **Multiple AI Providers** — Groq (free), Gemini, OpenAI, Anthropic, DeepSeek, Grok, Local (Ollama/LM Studio)
- **Flexible Strategies** — SMART_SEQUENTIAL, DOM_ONLY, VISUAL_FIRST, SEQUENTIAL, PARALLEL
- **Smart Caching** — Persistent file, in-memory, Redis, or no cache
- **Both Sync and Async APIs** — `find_element()` and `find_element_async()`
- **Selenium Support** — Full support for CSS, XPath, ID, Name, Class, Tag selectors
- **Playwright Support** — Coming soon
- **HTML / JSON Reports** — Detailed healing reports per test session
- **pytest-Ready** — Drop-in fixture pattern, no test rewrites needed

---

## Installation

```bash
# Basic
pip install autoheal-locator

# With Selenium support
pip install autoheal-locator[selenium]

# With Redis cache support
pip install autoheal-locator[redis]

# Everything
pip install autoheal-locator[all]
```

### From Source

```bash
git clone https://github.com/SanjayPG/autoheal-locator-python.git
cd autoheal-locator-python
pip install -e .
```

---

## Selenium Quick Start

### 1. Set Your API Key

Use a `.env` file in your project root. AutoHeal detects which provider to use based on which key is set — **configure only one**.

```bash
# .env — Groq is FREE and the fastest option
GROQ_API_KEY=gsk_your_api_key_here
```

> Get a free key at [console.groq.com](https://console.groq.com) — no credit card required.

Load it in your tests with `python-dotenv`:

```python
from dotenv import load_dotenv
load_dotenv()  # reads .env from project root
```

### 2. Replace Your WebDriver Code

**Before AutoHeal** — standard Selenium that breaks when the UI changes:

```python
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://example.com/login")

# Hard-coded selector — breaks if the developer renames the element
button = driver.find_element(By.ID, "submit-btn")
button.click()
```

**After AutoHeal** — same test, now self-healing:

```python
from selenium import webdriver
from autoheal import AutoHealLocator
from autoheal.impl.adapter import SeleniumWebAutomationAdapter

driver = webdriver.Chrome()
adapter = SeleniumWebAutomationAdapter(driver)
locator = AutoHealLocator.builder() \
    .with_web_adapter(adapter) \
    .build()

driver.get("https://example.com/login")

# AutoHeal auto-detects the locator type and heals if the selector breaks
button = locator.find_element("submit-btn", "Submit button")        # ID
# OR
button = locator.find_element("#submit-btn", "Submit button")       # CSS
# OR
button = locator.find_element("//button[@id='submit-btn']", "Submit button")  # XPath

button.click()
```

### 3. All Supported Locator Types

AutoHeal automatically detects the locator type from the string format — no `By.ID` / `By.CSS_SELECTOR` needed:

```python
# --- CSS Selectors ---
locator.find_element("#submit-btn", "Submit button")             # ID shorthand
locator.find_element(".btn-primary", "Primary button")           # class shorthand
locator.find_element("button[type='submit']", "Submit button")   # attribute
locator.find_element("form > input.email", "Email input")        # compound

# --- XPath ---
locator.find_element("//button[@id='submit']", "Submit button")
locator.find_element("//input[@placeholder='Username']", "Username field")
locator.find_element("//a[contains(text(),'Login')]", "Login link")

# --- ID / Name / Class (bare strings) ---
locator.find_element("submit-btn", "Submit button")              # ID
locator.find_element("username", "Username field")               # Name attribute
locator.find_element("btn-primary", "Primary button")            # Class name

# --- Link Text ---
locator.find_element("Forgot password?", "Forgot password link")

# --- Multiple elements ---
items = locator.find_elements(".product-card", "Product cards")
print(f"Found {len(items)} products")

# --- Presence check (no exception thrown) ---
if locator.is_element_present("#promo-banner", "Promo banner"):
    banner = locator.find_element("#promo-banner", "Promo banner")
    banner.click()
```

### 4. Full Selenium Example (Login Test)

```python
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from autoheal import AutoHealLocator
from autoheal.impl.adapter import SeleniumWebAutomationAdapter
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def driver():
    options = Options()
    options.add_argument("--start-maximized")
    d = webdriver.Chrome(options=options)
    d.implicitly_wait(10)
    yield d
    d.quit()


@pytest.fixture
def autoheal(driver):
    adapter = SeleniumWebAutomationAdapter(driver)
    return AutoHealLocator.builder().with_web_adapter(adapter).build()


def test_login(driver, autoheal):
    driver.get("https://www.saucedemo.com")

    # These selectors will be auto-healed if they ever break
    username = autoheal.find_element("#user-name", "Username input field")
    password = autoheal.find_element("#password", "Password input field")
    submit   = autoheal.find_element("#login-button", "Login submit button")

    username.send_keys("standard_user")
    password.send_keys("secret_sauce")
    submit.click()

    assert "/inventory.html" in driver.current_url


def test_login_with_broken_selectors(driver, autoheal):
    """Demonstrates AutoHeal healing intentionally broken selectors."""
    driver.get("https://www.saucedemo.com")

    # Deliberately wrong selectors — AutoHeal will find the real elements
    username = autoheal.find_element("#user-name-wrong", "Username input field")
    password = autoheal.find_element("#password-wrong", "Password input field")
    submit   = autoheal.find_element("#login-button-wrong", "Login submit button")

    username.send_keys("standard_user")
    password.send_keys("secret_sauce")
    submit.click()

    assert "/inventory.html" in driver.current_url  # still passes!
```

### 5. Async Selenium API

For parallel tests or better performance, use the async API:

```python
import asyncio
from selenium import webdriver
from autoheal import AutoHealLocator
from autoheal.impl.adapter import SeleniumWebAutomationAdapter

async def test_login_async():
    driver = webdriver.Chrome()
    adapter = SeleniumWebAutomationAdapter(driver)
    locator = AutoHealLocator.builder().with_web_adapter(adapter).build()

    try:
        driver.get("https://example.com/login")

        username = await locator.find_element_async("#username", "Username field")
        password = await locator.find_element_async("#password", "Password field")
        submit   = await locator.find_element_async("button[type='submit']", "Submit button")

        username.send_keys("admin")
        password.send_keys("secret")
        submit.click()

        logged_in = await locator.is_element_present_async(".dashboard", "Dashboard")
        assert logged_in

    finally:
        driver.quit()
        await locator.shutdown()

asyncio.run(test_login_async())
```

---

## Playwright Quick Start

> **Status: Coming Soon.** Playwright support is under active development. The API design below reflects the planned interface — it mirrors the Selenium API so migration will be straightforward.

### Why Playwright with AutoHeal?

Playwright's native locators (`get_by_role`, `get_by_text`, `get_by_placeholder`) are already more resilient than CSS/XPath. AutoHeal adds another layer — if even the semantic locator fails, the AI heals it.

**Playwright also offers zero-rewrite migration**: you pass native `Locator` objects directly to AutoHeal without changing how you write selectors.

### Planned API — Native Playwright Locators

```python
from playwright.sync_api import sync_playwright
from autoheal import AutoHealLocator
from autoheal.impl.adapter import PlaywrightWebAutomationAdapter  # coming soon

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    adapter = PlaywrightWebAutomationAdapter(page)
    locator = AutoHealLocator.builder().with_web_adapter(adapter).build()

    page.goto("https://example.com/login")

    # Pass native Playwright locators directly — AutoHeal wraps them
    username = locator.find(page.get_by_placeholder("Username"), "Username field")
    password = locator.find(page.get_by_placeholder("Password"), "Password field")
    submit   = locator.find(page.get_by_role("button", name="Login"), "Login button")

    username.fill("standard_user")
    password.fill("secret_sauce")
    submit.click()
```

### Planned API — Semantic Locator Types

```python
# Role-based (most resilient)
locator.find(page.get_by_role("button", name="Submit"), "Submit button")
locator.find(page.get_by_role("textbox", name="Username"), "Username field")
locator.find(page.get_by_role("link", name="Forgot password?"), "Forgot password link")

# Text-based
locator.find(page.get_by_text("Welcome back"), "Welcome message")
locator.find(page.get_by_text("Add to cart", exact=True), "Add to cart button")

# Placeholder
locator.find(page.get_by_placeholder("Email address"), "Email input")

# Test ID
locator.find(page.get_by_test_id("submit-btn"), "Submit button")

# Label
locator.find(page.get_by_label("Email"), "Email input")

# CSS / XPath still work
locator.find(page.locator("#submit-btn"), "Submit button")
locator.find(page.locator("//button[@type='submit']"), "Submit button")
```

### Planned API — Filtered Locators

Playwright's filter chaining is fully supported:

```python
# Find a specific product's "Add to cart" button
product_btn = locator.find(
    page.get_by_role("listitem")
        .filter(has_text="Sauce Labs Backpack")
        .get_by_role("button"),
    "Add to cart button for Sauce Labs Backpack"
)
product_btn.click()

# Filter with multiple conditions
in_stock_item = locator.find(
    page.get_by_role("listitem")
        .filter(has_text="In stock")
        .filter(has_not_text="Out of stock"),
    "In stock product item"
)
```

### Planned API — Async Playwright

```python
import asyncio
from playwright.async_api import async_playwright

async def test_login_playwright():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        adapter = PlaywrightWebAutomationAdapter(page)
        locator = AutoHealLocator.builder().with_web_adapter(adapter).build()

        await page.goto("https://example.com/login")

        username = await locator.find_async(
            page.get_by_placeholder("Username"), "Username field"
        )
        await username.fill("admin")

        submit = await locator.find_async(
            page.get_by_role("button", name="Login"), "Login button"
        )
        await submit.click()

        await browser.close()

asyncio.run(test_login_playwright())
```

---

## AI Provider Configuration

Configure **one provider only**. AutoHeal auto-detects which one is active based on which environment variable is set.

### Option 1 — Groq (Free, Fastest)

```bash
# .env
GROQ_API_KEY=gsk_your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile    # optional, this is the default
```

Get a free key at [console.groq.com](https://console.groq.com) — no credit card required.

**Visual analysis models for Groq:**
```bash
GROQ_MODEL=llama-3.2-11b-vision-preview   # use for VISUAL_FIRST strategy
```

### Option 2 — Google Gemini

```bash
# .env
GEMINI_API_KEY=AIza_your_api_key_here
GEMINI_MODEL=gemini-2.0-flash              # optional
```

Get a key at [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey).

> **Note:** Gemini free tier has rate limits that may cause 429 errors during rapid visual analysis. Use `SMART_SEQUENTIAL` or `DOM_ONLY` strategy to reduce API calls.

### Option 3 — OpenAI

```bash
# .env
OPENAI_API_KEY=sk-proj-your_api_key_here
OPENAI_MODEL=gpt-4o                        # optional, gpt-4o-mini is cheaper
```

Get a key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

Models with visual analysis support: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`.

### Option 4 — Anthropic Claude

```bash
# .env — use via OpenAI-compatible proxy (e.g. LiteLLM)
AUTOHEAL_API_URL=http://localhost:4000/v1/chat/completions
AUTOHEAL_MODEL=claude-3-5-sonnet-20241022
AUTOHEAL_API_KEY=your_litellm_key
```

Get a key at [console.anthropic.com](https://console.anthropic.com).

> Claude does not have a native OpenAI-compatible endpoint. Use [LiteLLM](https://docs.litellm.ai/) as a proxy.

### Option 5 — DeepSeek

```bash
# .env
AUTOHEAL_API_URL=https://api.deepseek.com/v1/chat/completions
AUTOHEAL_MODEL=deepseek-chat
AUTOHEAL_API_KEY=your_deepseek_api_key
```

Get a key at [platform.deepseek.com](https://platform.deepseek.com).

### Option 6 — Local LLM (Ollama / LM Studio)

No API key needed — completely free and private.

```bash
# .env — Ollama (https://ollama.ai)
# First pull a model: ollama pull deepseek-coder-v2:16b
AUTOHEAL_API_URL=http://localhost:11434/v1/chat/completions
AUTOHEAL_MODEL=deepseek-coder-v2:16b
AUTOHEAL_API_KEY=not-needed

# .env — LM Studio (https://lmstudio.ai)
AUTOHEAL_API_URL=http://localhost:1234/v1/chat/completions
AUTOHEAL_MODEL=your-loaded-model-name
AUTOHEAL_API_KEY=not-needed

# .env — Cloudflare tunnel (remote Ollama)
AUTOHEAL_API_URL=https://your-tunnel.trycloudflare.com/v1/chat/completions
AUTOHEAL_MODEL=deepseek-coder-v2:16b
AUTOHEAL_API_KEY=not-needed
```

### Provider Comparison

| Provider | Visual | Cost | Speed | Notes |
|----------|--------|------|-------|-------|
| **Groq** | Yes | Free | Fastest | Best for getting started |
| **Gemini** | Yes | Low | Fast | Free tier has rate limits |
| **OpenAI** | Yes | Medium | Fast | gpt-4o-mini is cost-effective |
| **Anthropic** | Yes | Medium | Medium | Requires proxy |
| **DeepSeek** | No | Low | Fast | Great for DOM-only use |
| **Local (Ollama)** | Depends | Free | Varies | Private, no data sent to cloud |

### Programmatic Configuration

```python
from autoheal.config import AIConfig
from autoheal.models.enums import AIProvider

ai_config = AIConfig.builder() \
    .provider(AIProvider.GROQ) \
    .api_key(os.getenv("GROQ_API_KEY")) \
    .model("llama-3.3-70b-versatile") \
    .temperature_dom(0.1) \
    .build()
```

---

## Execution Strategies

The execution strategy controls how AutoHeal heals a broken selector. Set via `.env` or in code.

```bash
# .env
AUTOHEAL_EXECUTION_STRATEGY=SMART_SEQUENTIAL
```

### SMART_SEQUENTIAL (Recommended — Default)

Tries DOM analysis first (cheap). Only uses visual if DOM fails.

```python
.execution_strategy(ExecutionStrategy.SMART_SEQUENTIAL)
```

**Cost:** Low | **Speed:** Medium | **Best for:** Production, CI/CD

### DOM_ONLY

Skips visual entirely. Fastest and cheapest.

```python
.execution_strategy(ExecutionStrategy.DOM_ONLY)
```

**Cost:** Lowest | **Speed:** Fastest | **Best for:** Simple UIs, cost-sensitive pipelines

### VISUAL_FIRST

Takes a screenshot and asks the AI to identify the element visually. Falls back to DOM if visual fails.

```python
.execution_strategy(ExecutionStrategy.VISUAL_FIRST)
```

**Cost:** High | **Speed:** Medium | **Best for:** Complex UIs where DOM structure is unreliable

> **Important:** Visual analysis is only as accurate as what the AI can infer from the screenshot. It cannot see actual HTML attribute values (e.g. it may guess `#username` when the real ID is `#user-name`). DOM analysis is more precise for attribute-based selectors.

### SEQUENTIAL

Tries each registered locator strategy in order until one succeeds.

```python
.execution_strategy(ExecutionStrategy.SEQUENTIAL)
```

**Cost:** Medium | **Speed:** Medium | **Best for:** Debugging, understanding which strategy works

### PARALLEL

Runs DOM and visual simultaneously. Uses the first successful result.

```python
.execution_strategy(ExecutionStrategy.PARALLEL)
```

**Cost:** Highest | **Speed:** Fastest healing | **Best for:** Time-critical scenarios

---

## Cache Configuration

Caching avoids repeat AI calls for selectors that have already been healed. Once healed, the fixed selector is cached and reused on subsequent runs.

### PERSISTENT_FILE (Default)

Saves to disk. Survives test restarts. File-locked for parallel safety.

```python
from autoheal.config import CacheConfig
from autoheal.config.cache_config import CacheType
from datetime import timedelta

cache_config = CacheConfig.builder() \
    .cache_type(CacheType.PERSISTENT_FILE) \
    .maximum_size(500) \
    .expire_after_write(timedelta(hours=24)) \
    .build()
```

**Best for:** Up to 10 parallel workers, local development, pipelines where healing results should persist.

### CAFFEINE (In-Memory)

Pure in-memory cache. Fastest. Lost when the process ends.

```python
cache_config = CacheConfig.builder() \
    .cache_type(CacheType.CAFFEINE) \
    .maximum_size(1000) \
    .expire_after_write(timedelta(hours=24)) \
    .build()
```

**Best for:** More than 10 parallel workers, single CI runs, throwaway environments.

### REDIS (Distributed)

Shared across all workers and machines. Requires a Redis server.

```python
cache_config = CacheConfig.builder() \
    .cache_type(CacheType.REDIS) \
    .redis_host("localhost") \
    .redis_port(6379) \
    .redis_password(None)  # set if auth required
    .maximum_size(10000) \
    .expire_after_write(timedelta(days=7)) \
    .build()
```

**Best for:** 50+ parallel workers, distributed test grids, shared CI infrastructure.

### Cache Management API

```python
# Clear all cached selectors
locator.clear_cache()

# Remove one specific entry
locator.remove_cached_selector("#old-btn", "Submit button")

# Check how many entries are cached
print(locator.get_cache_size())

# Inspect hit/miss statistics
metrics = locator.get_cache_metrics()
print(f"Hit rate  : {metrics.total_hits / (metrics.total_hits + metrics.total_misses):.0%}")
print(f"Total hits: {metrics.total_hits}")
print(f"Misses    : {metrics.total_misses}")
```

### Cache Strategy via YAML

If you prefer file-based config, create `config/cache_strategy.yaml`:

```yaml
cache:
  # Options: PERSISTENT_FILE, CAFFEINE, REDIS
  type: PERSISTENT_FILE
  maximum_size: 500
  expire_after_hours: 24

  # Redis-only settings
  redis:
    host: localhost
    port: 6379
    password: null
```

---

## Performance Configuration

```bash
# .env
AUTOHEAL_QUICK_TIMEOUT_MS=500     # How long to try original selector before checking cache
AUTOHEAL_ELEMENT_TIMEOUT_SEC=10   # Max time to spend finding an element
AUTOHEAL_IMPLICIT_WAIT_SEC=10     # Selenium implicit wait (should match your WebDriver setting)
```

```python
from autoheal.config import PerformanceConfig
from autoheal.models.enums import ExecutionStrategy
from datetime import timedelta

perf_config = PerformanceConfig.builder() \
    .execution_strategy(ExecutionStrategy.SMART_SEQUENTIAL) \
    .quick_check_timeout(timedelta(milliseconds=500)) \
    .element_timeout(timedelta(seconds=10)) \
    .build()
```

---

## Reporting

AutoHeal generates HTML, JSON, and text reports at the end of each test session.

```python
from autoheal.config import ReportingConfig

reporting_config = ReportingConfig.builder() \
    .enabled(True) \
    .generate_html(True) \
    .generate_json(True) \
    .generate_text(True) \
    .output_directory("./autoheal-reports") \
    .report_name_prefix("MyProject_AutoHeal") \
    .console_logging(True) \
    .build()
```

**Report contents:**
- Healing history (original selector → healed selector)
- Success and failure counts per element
- Token usage per AI call
- Cache hit/miss statistics
- Per-strategy breakdown (DOM Healed, Visual, Cached)

### Healing Status in Console

```
[SUCCESS] [DOM]    [1250ms] [820 tokens]  #user-name-wrong  ->  #user-name
[SUCCESS] [VISUAL] [3400ms] [1200 tokens] #btn-wrong        ->  .btn-login
[SUCCESS] [CACHED] [2ms]                  #password-wrong   ->  #password
[FAILED]  [FAIL]   [350ms]                #nonexistent      ->  FAILED
```

---

## pytest Integration

### conftest.py Setup

```python
import pytest
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

from autoheal import AutoHealLocator
from autoheal.impl.adapter import SeleniumWebAutomationAdapter
from autoheal.reporting.reporting_autoheal_locator import ReportingAutoHealLocator
from config.autoheal_config import get_autoheal_config

load_dotenv(Path(__file__).parent / ".env")


@pytest.fixture(scope="function")
def driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    d = webdriver.Chrome(service=service, options=options)
    d.implicitly_wait(10)
    yield d
    d.quit()


@pytest.fixture(scope="function")
def autoheal(driver):
    config = get_autoheal_config()
    adapter = SeleniumWebAutomationAdapter(driver)
    locator = ReportingAutoHealLocator(adapter, config)
    yield locator

    metrics = locator.autoheal.get_metrics()
    cache_metrics = locator.autoheal.get_cache_metrics()
    print(f"\nAutoHeal: {metrics.successful_requests}/{metrics.total_requests} healed")
    print(f"Cache   : {cache_metrics.total_hits} hits, {cache_metrics.total_misses} misses")
```

### config/autoheal_config.py

Centralise your configuration here so all tests share the same setup:

```python
import os
from datetime import timedelta
from autoheal import AutoHealConfiguration
from autoheal.config import AIConfig, CacheConfig, PerformanceConfig, ResilienceConfig, ReportingConfig
from autoheal.config.cache_config import CacheType
from autoheal.models.enums import AIProvider, ExecutionStrategy


def get_ai_config() -> AIConfig:
    """
    Auto-detect the configured AI provider from environment variables.
    Only ONE provider should be configured at a time.
    """
    if os.getenv("GROQ_API_KEY"):
        return AIConfig.builder() \
            .provider(AIProvider.GROQ) \
            .api_key(os.getenv("GROQ_API_KEY")) \
            .api_url("https://api.groq.com/openai/v1/chat/completions") \
            .model(os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")) \
            .temperature_dom(0.1) \
            .build()

    if os.getenv("GEMINI_API_KEY"):
        return AIConfig.builder() \
            .provider(AIProvider.GOOGLE_GEMINI) \
            .api_key(os.getenv("GEMINI_API_KEY")) \
            .model(os.getenv("GEMINI_MODEL", "gemini-2.0-flash")) \
            .temperature_dom(0.1) \
            .build()

    if os.getenv("OPENAI_API_KEY"):
        return AIConfig.builder() \
            .provider(AIProvider.OPENAI) \
            .api_key(os.getenv("OPENAI_API_KEY")) \
            .api_url("https://api.openai.com/v1/chat/completions") \
            .model(os.getenv("OPENAI_MODEL", "gpt-4o-mini")) \
            .temperature_dom(0.1) \
            .build()

    if os.getenv("AUTOHEAL_API_URL"):
        return AIConfig.builder() \
            .provider(AIProvider.OPENAI) \
            .api_key(os.getenv("AUTOHEAL_API_KEY", "not-needed")) \
            .api_url(os.getenv("AUTOHEAL_API_URL")) \
            .model(os.getenv("AUTOHEAL_MODEL", "deepseek-coder-v2:16b")) \
            .temperature_dom(0.1) \
            .build()

    raise ValueError(
        "No AI provider configured. Set one of: GROQ_API_KEY, GEMINI_API_KEY, "
        "OPENAI_API_KEY, or AUTOHEAL_API_URL in your .env file."
    )


def get_autoheal_config() -> AutoHealConfiguration:
    strategy_map = {
        "SMART_SEQUENTIAL": ExecutionStrategy.SMART_SEQUENTIAL,
        "DOM_ONLY":         ExecutionStrategy.DOM_ONLY,
        "VISUAL_FIRST":     ExecutionStrategy.VISUAL_FIRST,
        "SEQUENTIAL":       ExecutionStrategy.SEQUENTIAL,
        "PARALLEL":         ExecutionStrategy.PARALLEL,
    }
    strategy = strategy_map.get(
        os.getenv("AUTOHEAL_EXECUTION_STRATEGY", "SMART_SEQUENTIAL").upper(),
        ExecutionStrategy.SMART_SEQUENTIAL
    )

    return AutoHealConfiguration.builder() \
        .ai(get_ai_config()) \
        .cache(
            CacheConfig.builder()
                .cache_type(CacheType.PERSISTENT_FILE)
                .maximum_size(int(os.getenv("AUTOHEAL_CACHE_MAX_SIZE", "500")))
                .expire_after_write(timedelta(hours=24))
                .build()
        ) \
        .performance(
            PerformanceConfig.builder()
                .execution_strategy(strategy)
                .quick_check_timeout(timedelta(
                    milliseconds=int(os.getenv("AUTOHEAL_QUICK_TIMEOUT_MS", "500"))
                ))
                .element_timeout(timedelta(
                    seconds=int(os.getenv("AUTOHEAL_ELEMENT_TIMEOUT_SEC", "10"))
                ))
                .build()
        ) \
        .resilience(ResilienceConfig.builder().retry_max_attempts(3).build()) \
        .reporting(
            ReportingConfig.builder()
                .enabled(True)
                .generate_html(True)
                .generate_json(True)
                .generate_text(True)
                .output_directory("./autoheal-reports")
                .report_name_prefix("AutoHeal")
                .console_logging(True)
                .build()
        ) \
        .build()
```

### Writing Tests

```python
def test_login(driver, autoheal):
    driver.get("https://www.saucedemo.com")

    # Use correct selectors — AutoHeal heals them if they break
    username = autoheal.find_element("#user-name", "Username field")
    password = autoheal.find_element("#password", "Password field")
    submit   = autoheal.find_element("#login-button", "Login button")

    username.send_keys("standard_user")
    password.send_keys("secret_sauce")
    submit.click()

    assert "/inventory.html" in driver.current_url


def test_login_healed(driver, autoheal):
    driver.get("https://www.saucedemo.com")

    # Intentionally wrong selectors — AutoHeal will find the right elements
    username = autoheal.find_element("#user-name-wrong", "Username field")
    password = autoheal.find_element("#password-wrong", "Password field")
    submit   = autoheal.find_element("#login-button-wrong", "Login button")

    username.send_keys("standard_user")
    password.send_keys("secret_sauce")
    submit.click()

    assert "/inventory.html" in driver.current_url
```

---

## Full Configuration Reference

### .env File

```bash
# =============================================================================
# AI Provider — configure ONLY ONE
# =============================================================================

# Groq (free)
GROQ_API_KEY=gsk_your_key
GROQ_MODEL=llama-3.3-70b-versatile

# Google Gemini
# GEMINI_API_KEY=AIza_your_key
# GEMINI_MODEL=gemini-2.0-flash

# OpenAI
# OPENAI_API_KEY=sk-proj-your_key
# OPENAI_MODEL=gpt-4o-mini

# Local / Custom (Ollama, LM Studio, DeepSeek, etc.)
# AUTOHEAL_API_URL=http://localhost:11434/v1/chat/completions
# AUTOHEAL_MODEL=deepseek-coder-v2:16b
# AUTOHEAL_API_KEY=not-needed

# =============================================================================
# Execution Strategy
# =============================================================================
# Options: SMART_SEQUENTIAL | DOM_ONLY | VISUAL_FIRST | SEQUENTIAL | PARALLEL
AUTOHEAL_EXECUTION_STRATEGY=SMART_SEQUENTIAL

# =============================================================================
# Performance
# =============================================================================
AUTOHEAL_QUICK_TIMEOUT_MS=500      # ms — timeout for original selector check
AUTOHEAL_ELEMENT_TIMEOUT_SEC=10    # s  — max time per element lookup
AUTOHEAL_IMPLICIT_WAIT_SEC=10      # s  — should match driver.implicitly_wait()

# =============================================================================
# Cache (settings in config/cache_strategy.yaml)
# =============================================================================
AUTOHEAL_CACHE_MAX_SIZE=500        # max number of cached entries

# =============================================================================
# Debug
# =============================================================================
# AUTOHEAL_DEBUG=true
```

### AutoHealConfiguration Builder Methods

| Method | Accepts | Purpose |
|--------|---------|---------|
| `.ai(config)` | `AIConfig` | Set AI provider and model |
| `.cache(config)` | `CacheConfig` | Set cache backend and TTL |
| `.performance(config)` | `PerformanceConfig` | Set strategy and timeouts |
| `.resilience(config)` | `ResilienceConfig` | Set retry attempts |
| `.reporting(config)` | `ReportingConfig` | Set report output options |
| `.build()` | — | Build the configuration |

### AIConfig Builder Methods

| Method | Default | Purpose |
|--------|---------|---------|
| `.provider(AIProvider.X)` | — | Required. Which AI provider to use |
| `.api_key(str)` | — | API authentication key |
| `.api_url(str)` | Provider default | Override API endpoint |
| `.model(str)` | Provider default | Model name |
| `.temperature_dom(float)` | `0.1` | Temperature for DOM analysis |
| `.temperature_visual(float)` | `0.0` | Temperature for visual analysis |
| `.timeout(int)` | `30` | Request timeout in seconds |

### PerformanceConfig Builder Methods

| Method | Default | Purpose |
|--------|---------|---------|
| `.execution_strategy(ExecutionStrategy.X)` | `SMART_SEQUENTIAL` | Healing strategy |
| `.quick_check_timeout(timedelta)` | `500ms` | Timeout for original selector |
| `.element_timeout(timedelta)` | `10s` | Full element lookup timeout |

### CacheConfig Builder Methods

| Method | Default | Purpose |
|--------|---------|---------|
| `.cache_type(CacheType.X)` | `PERSISTENT_FILE` | Cache backend |
| `.maximum_size(int)` | `500` | Max cached entries |
| `.expire_after_write(timedelta)` | `24h` | TTL after write |
| `.redis_host(str)` | `localhost` | Redis host (REDIS only) |
| `.redis_port(int)` | `6379` | Redis port (REDIS only) |
| `.redis_password(str)` | `None` | Redis password (REDIS only) |

---

## API Reference

### AutoHealLocator Methods

#### Finding Elements

```python
# Find a single element (sync)
element = locator.find_element(selector, description)

# Find a single element (async)
element = await locator.find_element_async(selector, description)

# Find element and return detailed result
result = locator.find_element_with_result(selector, description)
print(result.healing_type)   # "DOM", "VISUAL", "CACHED", "ORIGINAL"
print(result.healed_selector)
print(result.confidence)

# Find multiple elements
elements = locator.find_elements(selector, description)

# Check element presence without raising an exception
if locator.is_element_present(selector, description):
    print("Element is on the page")
```

#### Cache Management

```python
locator.clear_cache()                              # clear all entries
locator.remove_cached_selector(selector, desc)     # remove one entry
locator.get_cache_size()                           # count of entries
locator.cleanup_expired_cache()                    # evict stale entries
```

#### Metrics and Health

```python
metrics = locator.get_metrics()
print(metrics.total_requests)
print(metrics.successful_requests)

cache = locator.get_cache_metrics()
print(cache.total_hits)
print(cache.total_misses)

health = locator.get_health_status()
print(health["overall"])       # True = healthy
print(health["success_rate"])
print(health["cache_hit_rate"])
```

#### Lifecycle

```python
# Graceful shutdown — flush cache, close connections
locator.shutdown()

# Or async
await locator.shutdown()
```

---

## Best Practices

### 1. Always Use Descriptive Element Names

The description is passed to the AI when healing is needed. The more specific it is, the better the AI's suggestion will be.

```python
# Too vague — AI has nothing to work with
locator.find_element("#btn-1", "button")

# Clear and specific — AI understands the context
locator.find_element("#btn-1", "Submit payment button on checkout page")
```

### 2. Match Strategy to Use Case

```python
# CI/CD — cost-effective, fast
AUTOHEAL_EXECUTION_STRATEGY=SMART_SEQUENTIAL

# Local development — skip AI entirely for green tests
AUTOHEAL_EXECUTION_STRATEGY=DOM_ONLY

# Highly visual UIs — screenshots help more than raw HTML
AUTOHEAL_EXECUTION_STRATEGY=VISUAL_FIRST
```

### 3. Use Cache in Long-Running Suites

Enable `PERSISTENT_FILE` cache so healed selectors are reused across runs. This eliminates redundant AI calls for the same broken selectors.

### 4. Use Async for Parallel Tests

```python
import asyncio

async def test_login_async(driver, autoheal):
    driver.get("https://example.com")
    username = await autoheal.find_element_async("#user", "Username field")
    password = await autoheal.find_element_async("#pass", "Password field")
    username.send_keys("admin")
    password.send_keys("secret")
```

### 5. Scope the Driver Fixture to `function`

Each test should get its own driver and autoheal instance. Sharing state between tests leads to unexpected cache collisions.

```python
@pytest.fixture(scope="function")   # not "session" or "module"
def driver():
    ...
```

---

## Troubleshooting

### No AI provider configured

```
AIProviderConfigError: No AI provider configured.
```

Set exactly one API key in your `.env` file. See [AI Provider Configuration](#ai-provider-configuration).

### Multiple AI providers configured

```
AIProviderConfigError: Multiple AI providers configured: GEMINI, OPENAI.
```

Comment out all but one provider block in your `.env` file.

### Gemini returns 404

If using Gemini and seeing `Gemini API call failed: 404`, the `ai_config.py` default URL may include a trailing `/models` which the provider already appends. The correct default base URL is:

```
https://generativelanguage.googleapis.com/v1
```

Not:
```
https://generativelanguage.googleapis.com/v1/models   ← wrong, causes /models/models/
```

### Gemini returns 429 (rate limited)

The free Gemini tier throttles visual analysis because screenshots are large. Switch to `DOM_ONLY` or `SMART_SEQUENTIAL` to reduce API call frequency.

### Visual analysis succeeds but returns wrong selectors

Visual AI infers selectors from what it *sees* in the screenshot — it cannot read actual HTML attributes. It may guess `#username` when the real ID is `#user-name`. DOM analysis reads the real HTML and is more reliable for attribute-based selectors.

Use `SMART_SEQUENTIAL` so DOM is tried first, with visual as fallback.

### Element not found after healing

```python
# Enable debug logging to trace every step
import logging
logging.basicConfig(level=logging.DEBUG)

# Check health
health = locator.get_health_status()
print(health)
```

### Cache not persisting between runs

Check that `AUTOHEAL_CACHE_TYPE=PERSISTENT_FILE` (or your `cache_strategy.yaml` sets `type: PERSISTENT_FILE`). The default cache directory is `~/.autoheal/cache/`.

---

## Project Structure

```
autoheal/
├── autoheal_locator.py          # Main AutoHealLocator class
├── __init__.py                  # Public exports
├── config/                      # AIConfig, CacheConfig, PerformanceConfig, etc.
├── impl/
│   ├── adapter/                 # SeleniumWebAutomationAdapter
│   ├── ai/
│   │   └── providers/           # GeminiProvider, OpenAIProvider, GroqProvider, ...
│   ├── cache/                   # FileSelectorCache, RedisCache, CachetoolsCache
│   └── locator/                 # DOMElementLocator, VisualElementLocator,
│                                #   CostOptimizedHybridElementLocator
├── models/
│   └── enums.py                 # AIProvider, ExecutionStrategy, CacheType
├── reporting/                   # ReportingAutoHealLocator, HTML/JSON/text reporters
└── utils/                       # Locator type detection, helpers
```

---

## License

MIT License. See [LICENSE](LICENSE).

---

## Acknowledgements

- Original Java implementation: [autoheal-locator](https://github.com/SanjayPG/autoheal-locator)
- Built with Python, asyncio, aiohttp, and Pydantic
