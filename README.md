# AutoHeal Locator — Python

[![PyPI version](https://img.shields.io/pypi/v/autoheal-locator.svg)](https://pypi.org/project/autoheal-locator/)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AI-powered test automation library that automatically heals broken locators for Selenium and Playwright.**

When element selectors break due to UI changes, AutoHeal finds the elements using DOM analysis, visual recognition, and smart fallback strategies — with results cached so AI is called only once per broken selector.

> Python port of the original [Java AutoHeal Locator](https://github.com/SanjayPG/autoheal-locator).

---

## Quick Start

**New here?** See **[START_HERE.md](START_HERE.md)** first — it guides you to the right place based on what you want to do.

```bash
# Selenium project
pip install autoheal-locator

# Playwright project
pip install autoheal-locator[playwright]

# With Redis cache support
pip install autoheal-locator[redis]

# Everything
pip install autoheal-locator[all]
```

### Quickstart Config (Zero Setup)

For the fastest way to get started, use the built-in `get_autoheal_config()`. **No config file needed!**

```python
from autoheal import get_autoheal_config
from autoheal.impl.adapter import PlaywrightWebAutomationAdapter
from autoheal.reporting import ReportingAutoHealLocator

# Auto-detects provider from environment variables
config = get_autoheal_config()
adapter = PlaywrightWebAutomationAdapter(page)
locator = ReportingAutoHealLocator(adapter, config)

# Start healing broken selectors
element = await locator.find_element_async("#broken-selector", "Submit button")
```

Just set **one** environment variable (in `.env` or shell):

```bash
# Option 1: Groq (FREE - recommended)
GROQ_API_KEY=gsk_your_key_here

# Option 2: OpenAI
OPENAI_API_KEY=sk-your_key_here

# Option 3: Google Gemini
GEMINI_API_KEY=AIza_your_key_here

# Option 4: Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-your_key_here

# Option 5: DeepSeek
DEEPSEEK_API_KEY=your_key_here

# Option 6: Local Model (Ollama/LM Studio)
AUTOHEAL_API_URL=http://localhost:11434/v1/chat/completions
AUTOHEAL_MODEL=qwen2.5:7b
```

Optionally override the default model:

```bash
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

### Custom Config (Optional)

Need more control? Create your own `config/autoheal_config.py` to customize:
- Cache settings (type, size, expiry)
- Execution strategy (DOM_ONLY, VISUAL_FIRST, etc.)
- Timeouts and retry settings
- Report output directory

See [Full Configuration Reference](#full-configuration-reference) or copy from the [demo projects](#demo-projects)

---

## Demo Projects

| Project | Framework | Link |
|---|---|---|
| Selenium demo | Selenium + Python | [autoheal-selenium-python-demo](https://github.com/SanjayPG/autoheal-selenium-demo-python) |
| Playwright demo | Playwright + Python | [autoheal-playwright-demo-python](https://github.com/SanjayPG/autoheal-playwright-demo-python) |

Both demos include a `START_HERE.md` with full step-by-step setup instructions.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Key Features](#key-features)
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

## How It Works

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
│  2. Check Cache     │──── Hit ──────► Try cached selector ──► Return element
└─────────────────────┘
         │ Cache miss
         ▼
┌─────────────────────┐
│  3. AI Healing      │
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

- **AI-Powered Healing** — DOM analysis and visual recognition to find relocated elements
- **Multiple AI Providers** — Groq (free), Gemini, OpenAI, Anthropic, DeepSeek, Local (Ollama/LM Studio)
- **Flexible Strategies** — SMART_SEQUENTIAL, DOM_ONLY, VISUAL_FIRST, SEQUENTIAL, PARALLEL
- **Smart Caching** — Persistent file, in-memory, Redis, or no cache
- **Sync and Async APIs** — `find_element()` and `find_element_async()`
- **Selenium Support** — CSS, XPath, ID, Name, Class, Tag selectors
- **Playwright Support** — CSS selectors, XPath, and native Playwright Locators (`get_by_role`, `get_by_text`, etc.)
- **HTML / JSON / Text Reports** — Detailed healing reports per test session
- **pytest-Ready** — Drop-in fixture pattern, no test rewrites needed

---

## Framework Comparison

| Feature | Selenium | Playwright |
|---------|----------|-----------|
| Locator types | CSS, XPath, ID, Name, Class, Tag, Link Text | CSS, XPath, `get_by_role`, `get_by_text`, `get_by_placeholder`, etc. |
| Native objects | `WebElement` | `Locator` |
| Sync API | `find_element()` | — |
| Async API | `find_element_async()` | `find_element_async()`, `find_async()` |
| Visual analysis | Supported | Supported |
| DOM analysis | Supported | Supported |
| Caching | Unified cache | Unified cache |

---

## Selenium Quick Start

### 1. Set Your API Key

```bash
# .env — Groq is FREE and the fastest option to get started
GROQ_API_KEY=gsk_your_api_key_here
```

Get a free key at [console.groq.com](https://console.groq.com) — no credit card required.

### 2. Before and After

**Before AutoHeal** — breaks when UI changes:

```python
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://example.com/login")
button = driver.find_element(By.ID, "submit-btn")  # breaks if renamed
button.click()
```

**After AutoHeal** — self-healing:

```python
from selenium import webdriver
from autoheal import AutoHealLocator
from autoheal.impl.adapter import SeleniumWebAutomationAdapter

driver = webdriver.Chrome()
adapter = SeleniumWebAutomationAdapter(driver)
locator = AutoHealLocator.builder().with_web_adapter(adapter).build()

driver.get("https://example.com/login")
button = locator.find_element("#submit-btn", "Submit button")  # heals automatically
button.click()
```

### 3. All Supported Locator Types

AutoHeal detects the locator type from the string format — no `By.X` needed:

```python
# CSS selectors
locator.find_element("#submit-btn", "Submit button")
locator.find_element(".btn-primary", "Primary button")
locator.find_element("button[type='submit']", "Submit button")
locator.find_element("form > input.email", "Email input")

# XPath
locator.find_element("//button[@id='submit']", "Submit button")
locator.find_element("//input[@placeholder='Username']", "Username field")
locator.find_element("//a[contains(text(),'Login')]", "Login link")

# Bare ID / Name / Class
locator.find_element("submit-btn", "Submit button")
locator.find_element("username", "Username field")

# Multiple elements
items = locator.find_elements(".product-card", "Product cards")

# Presence check — no exception if missing
if locator.is_element_present("#promo-banner", "Promo banner"):
    locator.find_element("#promo-banner", "Promo banner").click()
```

### 4. Full Login Example

```python
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from autoheal import AutoHealLocator
from autoheal.impl.adapter import SeleniumWebAutomationAdapter
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def driver():
    options = Options()
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    d = webdriver.Chrome(service=service, options=options)
    d.implicitly_wait(10)
    yield d
    d.quit()


@pytest.fixture
def autoheal(driver):
    adapter = SeleniumWebAutomationAdapter(driver)
    return AutoHealLocator.builder().with_web_adapter(adapter).build()


def test_login(driver, autoheal):
    driver.get("https://www.saucedemo.com")
    autoheal.find_element("#user-name", "Username field").send_keys("standard_user")
    autoheal.find_element("#password", "Password field").send_keys("secret_sauce")
    autoheal.find_element("#login-button", "Login button").click()
    assert "/inventory.html" in driver.current_url


def test_login_broken_selectors(driver, autoheal):
    """AutoHeal heals intentionally broken selectors."""
    driver.get("https://www.saucedemo.com")
    autoheal.find_element("#user-name-wrong", "Username field").send_keys("standard_user")
    autoheal.find_element("#password-wrong", "Password field").send_keys("secret_sauce")
    autoheal.find_element("#login-button-wrong", "Login button").click()
    assert "/inventory.html" in driver.current_url  # still passes!
```

---

## Playwright Quick Start

### 1. Install with Playwright Extra

```bash
pip install autoheal-locator[playwright]
playwright install chromium
```

### 2. Usage

AutoHeal for Playwright is fully async. It supports both CSS string selectors and native Playwright Locators:

```python
import pytest
from playwright.async_api import async_playwright
from autoheal.impl.adapter import PlaywrightWebAutomationAdapter
from autoheal.reporting.reporting_autoheal_locator import ReportingAutoHealLocator

# Using a broken CSS selector — AI heals it
async def test_heal_broken_selector(page, autoheal_locator):
    await page.goto("https://www.saucedemo.com")

    username = await autoheal_locator.find_element_async(
        "#user-name-BROKEN",
        "Username input field on the SauceDemo login page"
    )
    await username.fill("standard_user")
    assert await username.input_value() == "standard_user"


# Using a broken native Playwright Locator — AI heals it
async def test_heal_broken_native_locator(page, autoheal_locator):
    await page.goto("https://www.saucedemo.com")

    username = await autoheal_locator.find_async(
        page.get_by_role("textbox", name="Username-BROKEN"),
        "Username input field on the SauceDemo login page"
    )
    await username.fill("standard_user")
    assert await username.input_value() == "standard_user"
```

### 3. pytest Fixture

```python
import pytest
from playwright.async_api import async_playwright
from autoheal.impl.adapter import PlaywrightWebAutomationAdapter
from autoheal.reporting.reporting_autoheal_locator import ReportingAutoHealLocator
from config.autoheal_config import get_autoheal_config


@pytest.fixture(scope="function")
async def browser():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture(scope="function")
async def page(browser):
    page = await browser.new_page()
    yield page
    await page.close()


@pytest.fixture(scope="function")
def autoheal_locator(page):
    config = get_autoheal_config()
    adapter = PlaywrightWebAutomationAdapter(page)
    locator = ReportingAutoHealLocator(adapter, config)
    yield locator
    locator.shutdown()  # generates HTML/JSON/text reports
```

### 4. Native Locator Types Supported

```python
# Role-based
await autoheal_locator.find_async(page.get_by_role("button", name="Login"), "Login button")
await autoheal_locator.find_async(page.get_by_role("textbox", name="Username"), "Username field")

# Text-based
await autoheal_locator.find_async(page.get_by_text("Add to cart", exact=True), "Add to cart button")

# Placeholder
await autoheal_locator.find_async(page.get_by_placeholder("Email address"), "Email input")

# CSS / XPath
await autoheal_locator.find_async(page.locator("#submit-btn"), "Submit button")

# CSS string shorthand
await autoheal_locator.find_element_async("#submit-btn", "Submit button")
```

---

## AI Provider Configuration

Configure **one provider only**. AutoHeal detects which one to use based on which environment variable is set.

### Groq — Free, Recommended for Getting Started

```bash
GROQ_API_KEY=gsk_your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile    # optional
```

Get a free key at [console.groq.com](https://console.groq.com).

### Google Gemini

```bash
GEMINI_API_KEY=AIza_your_api_key_here
GEMINI_MODEL=gemini-2.0-flash          # optional
```

> Free tier has rate limits. Use `DOM_ONLY` or `SMART_SEQUENTIAL` strategy to reduce API calls.

### OpenAI

```bash
OPENAI_API_KEY=sk-proj-your_key
OPENAI_MODEL=gpt-4o-mini               # optional — gpt-4o-mini is cheapest
```

### Local LLM — Ollama / LM Studio (Free, Private)

```bash
# Ollama
AUTOHEAL_API_URL=http://localhost:11434/v1/chat/completions
AUTOHEAL_MODEL=deepseek-coder-v2:16b
AUTOHEAL_API_KEY=not-needed

# LM Studio
AUTOHEAL_API_URL=http://localhost:1234/v1/chat/completions
AUTOHEAL_MODEL=your-loaded-model-name
AUTOHEAL_API_KEY=not-needed
```

### Provider Comparison

| Provider | Visual | Cost | Speed | Notes |
|----------|--------|------|-------|-------|
| **Groq** | Yes | Free | Fastest | Best for getting started |
| **Gemini** | Yes | Low | Fast | Free tier has rate limits |
| **OpenAI** | Yes | Medium | Fast | gpt-4o-mini is cost-effective |
| **Anthropic** | Yes | Medium | Medium | Requires LiteLLM proxy |
| **DeepSeek** | No | Low | Fast | Good for DOM-only use |
| **Ollama** | Depends | Free | Varies | Private, no data sent externally |

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

```bash
# .env
AUTOHEAL_EXECUTION_STRATEGY=SMART_SEQUENTIAL
```

| Strategy | Cost | Speed | Best For |
|----------|------|-------|----------|
| `SMART_SEQUENTIAL` | Low | Medium | Default — DOM first, visual fallback |
| `DOM_ONLY` | Lowest | Fastest | CI/CD, cost-sensitive |
| `VISUAL_FIRST` | High | Medium | Complex UIs where DOM structure unreliable |
| `SEQUENTIAL` | Medium | Medium | Debugging |
| `PARALLEL` | Highest | Fastest healing | Speed-critical scenarios |

---

## Cache Configuration

```python
from autoheal.config import CacheConfig
from autoheal.config.cache_config import CacheType
from datetime import timedelta

# Persistent file (default) — survives restarts
cache_config = CacheConfig.builder() \
    .cache_type(CacheType.PERSISTENT_FILE) \
    .maximum_size(500) \
    .expire_after_write(timedelta(hours=24)) \
    .build()

# In-memory — fastest, lost when process ends
cache_config = CacheConfig.builder() \
    .cache_type(CacheType.CAFFEINE) \
    .maximum_size(1000) \
    .build()

# Redis — shared across machines
cache_config = CacheConfig.builder() \
    .cache_type(CacheType.REDIS) \
    .redis_host("localhost") \
    .redis_port(6379) \
    .build()
```

### Cache Strategy via YAML

Create `config/cache_strategy.yaml`:

```yaml
cache:
  type: PERSISTENT_FILE     # PERSISTENT_FILE | CAFFEINE | REDIS
  maximum_size: 500
  expire_after_hours: 24

  # Redis-only settings
  redis:
    host: localhost
    port: 6379
    password: null
```

### Cache Management

```python
locator.clear_cache()
locator.remove_cached_selector("#old-btn", "Submit button")
print(locator.get_cache_size())

metrics = locator.get_cache_metrics()
print(f"Hit rate: {metrics.total_hits / (metrics.total_hits + metrics.total_misses):.0%}")
```

---

## Performance Configuration

```bash
# .env
AUTOHEAL_QUICK_TIMEOUT_MS=500     # timeout to try original selector before healing
AUTOHEAL_ELEMENT_TIMEOUT_SEC=10   # max time per element lookup
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

```python
from autoheal.config import ReportingConfig
from pathlib import Path

reporting_config = ReportingConfig.builder() \
    .enabled(True) \
    .generate_html(True) \
    .generate_json(True) \
    .generate_text(True) \
    .output_directory(str(Path(__file__).parent.parent / "autoheal-reports")) \
    .report_name_prefix("MyProject") \
    .console_logging(True) \
    .build()
```

**Console output during test run:**

```
[SUCCESS] [DOM]    [1250ms] [820 tokens]  #user-name-wrong  ->  #user-name
[SUCCESS] [VISUAL] [3400ms] [1200 tokens] #btn-wrong        ->  .btn-login
[SUCCESS] [CACHED] [2ms]                  #password-wrong   ->  #password
[FAILED]  [FAIL]   [350ms]                #nonexistent      ->  FAILED
```

---

## pytest Integration

### conftest.py — Selenium

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

load_dotenv(Path(__file__).parent / ".env")


@pytest.fixture(scope="function")
def driver():
    options = Options()
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    d = webdriver.Chrome(service=service, options=options)
    d.implicitly_wait(10)
    yield d
    d.quit()


@pytest.fixture(scope="function")
def autoheal(driver):
    from config.autoheal_config import get_autoheal_config
    adapter = SeleniumWebAutomationAdapter(driver)
    locator = ReportingAutoHealLocator(adapter, get_autoheal_config())
    yield locator
    metrics = locator.autoheal.get_metrics()
    print(f"\nAutoHeal: {metrics.successful_requests}/{metrics.total_requests} healed")
```

### conftest.py — Playwright

```python
import pytest
from playwright.async_api import async_playwright
from autoheal.impl.adapter import PlaywrightWebAutomationAdapter
from autoheal.reporting.reporting_autoheal_locator import ReportingAutoHealLocator


@pytest.fixture(scope="function")
async def browser():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture(scope="function")
async def page(browser):
    page = await browser.new_page()
    yield page
    await page.close()


@pytest.fixture(scope="function")
def autoheal_locator(page):
    from config.autoheal_config import get_autoheal_config
    adapter = PlaywrightWebAutomationAdapter(page)
    locator = ReportingAutoHealLocator(adapter, get_autoheal_config())
    yield locator
    locator.shutdown()
```

### config/autoheal_config.py

```python
import os
from pathlib import Path
from datetime import timedelta
from autoheal import AutoHealConfiguration
from autoheal.config import AIConfig, CacheConfig, PerformanceConfig, ResilienceConfig, ReportingConfig
from autoheal.config.cache_config import CacheType
from autoheal.models.enums import AIProvider, ExecutionStrategy


def get_autoheal_config() -> AutoHealConfiguration:
    # Auto-detect AI provider from env vars
    if os.getenv("GROQ_API_KEY"):
        ai = AIConfig.builder() \
            .provider(AIProvider.GROQ) \
            .api_key(os.getenv("GROQ_API_KEY")) \
            .api_url("https://api.groq.com/openai/v1/chat/completions") \
            .model(os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")) \
            .build()
    elif os.getenv("GEMINI_API_KEY"):
        ai = AIConfig.builder() \
            .provider(AIProvider.GOOGLE_GEMINI) \
            .api_key(os.getenv("GEMINI_API_KEY")) \
            .model(os.getenv("GEMINI_MODEL", "gemini-2.0-flash")) \
            .build()
    elif os.getenv("OPENAI_API_KEY"):
        ai = AIConfig.builder() \
            .provider(AIProvider.OPENAI) \
            .api_key(os.getenv("OPENAI_API_KEY")) \
            .api_url("https://api.openai.com/v1/chat/completions") \
            .model(os.getenv("OPENAI_MODEL", "gpt-4o-mini")) \
            .build()
    elif os.getenv("AUTOHEAL_API_URL"):
        ai = AIConfig.builder() \
            .provider(AIProvider.OPENAI) \
            .api_key(os.getenv("AUTOHEAL_API_KEY", "not-needed")) \
            .api_url(os.getenv("AUTOHEAL_API_URL")) \
            .model(os.getenv("AUTOHEAL_MODEL", "deepseek-coder-v2:16b")) \
            .build()
    else:
        raise ValueError("No AI provider configured. Set one of: GROQ_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY")

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

    project_root = Path(__file__).parent.parent

    return AutoHealConfiguration.builder() \
        .ai(ai) \
        .cache(
            CacheConfig.builder()
                .cache_type(CacheType.PERSISTENT_FILE)
                .maximum_size(500)
                .expire_after_write(timedelta(hours=24))
                .build()
        ) \
        .performance(
            PerformanceConfig.builder()
                .execution_strategy(strategy)
                .quick_check_timeout(timedelta(milliseconds=500))
                .element_timeout(timedelta(seconds=10))
                .build()
        ) \
        .resilience(ResilienceConfig.builder().retry_max_attempts(3).build()) \
        .reporting(
            ReportingConfig.builder()
                .enabled(True)
                .generate_html(True)
                .generate_json(True)
                .generate_text(True)
                .output_directory(str(project_root / "autoheal-reports"))
                .report_name_prefix("AutoHeal")
                .console_logging(True)
                .build()
        ) \
        .build()
```

---

## Full Configuration Reference

### .env File

```bash
# AI Provider — configure ONLY ONE
GROQ_API_KEY=gsk_your_key
GROQ_MODEL=llama-3.3-70b-versatile

# GEMINI_API_KEY=AIza_your_key
# GEMINI_MODEL=gemini-2.0-flash

# OPENAI_API_KEY=sk-proj-your_key
# OPENAI_MODEL=gpt-4o-mini

# AUTOHEAL_API_URL=http://localhost:11434/v1/chat/completions
# AUTOHEAL_MODEL=deepseek-coder-v2:16b
# AUTOHEAL_API_KEY=not-needed

# Execution Strategy
# Options: SMART_SEQUENTIAL | DOM_ONLY | VISUAL_FIRST | SEQUENTIAL | PARALLEL
AUTOHEAL_EXECUTION_STRATEGY=SMART_SEQUENTIAL

# Performance
AUTOHEAL_QUICK_TIMEOUT_MS=500
AUTOHEAL_ELEMENT_TIMEOUT_SEC=10
```

### Builder Reference

| Builder | Method | Default | Purpose |
|---------|--------|---------|---------|
| `AIConfig` | `.provider(AIProvider.X)` | — | Required |
| `AIConfig` | `.api_key(str)` | — | Required |
| `AIConfig` | `.model(str)` | Provider default | Model name |
| `AIConfig` | `.temperature_dom(float)` | `0.1` | DOM analysis temperature |
| `CacheConfig` | `.cache_type(CacheType.X)` | `PERSISTENT_FILE` | Cache backend |
| `CacheConfig` | `.maximum_size(int)` | `500` | Max cached entries |
| `CacheConfig` | `.expire_after_write(timedelta)` | `24h` | TTL |
| `PerformanceConfig` | `.execution_strategy(X)` | `SMART_SEQUENTIAL` | Healing strategy |
| `PerformanceConfig` | `.quick_check_timeout(timedelta)` | `500ms` | Original selector timeout |
| `PerformanceConfig` | `.element_timeout(timedelta)` | `10s` | Full lookup timeout |

---

## API Reference

```python
# Find single element (sync)
element = locator.find_element(selector, description)

# Find single element (async)
element = await locator.find_element_async(selector, description)

# Playwright only — pass native Locator
element = await locator.find_async(page.get_by_role("button"), description)

# Find multiple elements
elements = locator.find_elements(selector, description)

# Presence check — no exception if missing
if locator.is_element_present(selector, description):
    ...

# Cache management
locator.clear_cache()
locator.remove_cached_selector(selector, description)
locator.get_cache_size()

# Metrics
metrics = locator.get_metrics()
cache = locator.get_cache_metrics()
health = locator.get_health_status()

# Shutdown — flush cache, close connections, generate reports
locator.shutdown()
await locator.shutdown()  # async version
```

---

## Best Practices

**Use descriptive element names** — the description is sent to the AI when healing is needed:

```python
# Vague — AI has little context
locator.find_element("#btn-1", "button")

# Specific — AI understands exactly what to find
locator.find_element("#btn-1", "Submit payment button on checkout page")
```

**Match strategy to environment:**

```bash
SMART_SEQUENTIAL  # production and CI — cost-effective
DOM_ONLY          # local dev when you want fast runs
VISUAL_FIRST      # highly visual UIs where DOM structure is unreliable
```

**Use absolute paths for reports** so they always land in the project root regardless of where pytest is run from:

```python
.output_directory(str(Path(__file__).parent.parent / "autoheal-reports"))
```

**Scope fixtures to `function`** — each test should get its own driver and locator instance to avoid cache collisions between tests.

---

## Troubleshooting

**`No AI provider configured`**
Set exactly one API key in your `.env`. See [AI Provider Configuration](#ai-provider-configuration).

**`Multiple AI providers configured`**
Comment out all but one provider block in `.env`.

**`Gemini 404`**
The correct Gemini base URL is `https://generativelanguage.googleapis.com/v1` — without a trailing `/models`.

**`Gemini 429 rate limited`**
Switch to `AUTOHEAL_EXECUTION_STRATEGY=DOM_ONLY` or `SMART_SEQUENTIAL` to reduce screenshot-based calls.

**Visual analysis returns wrong selector**
Visual AI infers selectors from screenshots — it cannot read actual HTML attributes. Use `SMART_SEQUENTIAL` so DOM analysis runs first; visual is the fallback.

**Reports landing in wrong folder**
Use `Path(__file__).parent.parent / "autoheal-reports"` instead of `"./autoheal-reports"`. Relative paths depend on where pytest is launched from.

---

## Project Structure

```
autoheal/
├── autoheal_locator.py          # Main AutoHealLocator class
├── __init__.py
├── config/                      # AIConfig, CacheConfig, PerformanceConfig, etc.
├── impl/
│   ├── adapter/                 # SeleniumWebAutomationAdapter, PlaywrightWebAutomationAdapter
│   ├── ai/providers/            # GeminiProvider, OpenAIProvider, GroqProvider, ...
│   ├── cache/                   # FileSelectorCache, RedisCache, CachetoolsCache
│   └── locator/                 # DOMElementLocator, VisualElementLocator, HybridLocator
├── models/
│   └── enums.py                 # AIProvider, ExecutionStrategy, CacheType
├── reporting/                   # ReportingAutoHealLocator, HTML/JSON/text reporters
└── utils/                       # Locator type detection, helpers
```

---

## License

MIT License. See [LICENSE](LICENSE).

---

## Links

- **PyPI**: https://pypi.org/project/autoheal-locator/
- **GitHub**: https://github.com/SanjayPG/autoheal-locator-python
- **Java version**: https://github.com/SanjayPG/autoheal-locator
- **Selenium demo**: https://github.com/SanjayPG/autoheal-selenium-python-demo
- **Playwright demo**: https://github.com/SanjayPG/autoheal-playwright-demo-python
- **Free Groq API key**: https://console.groq.com
