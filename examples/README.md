# AutoHeal Locator Examples

This directory contains practical examples demonstrating how to use AutoHeal Locator with different test automation frameworks and configurations.

## 📁 Available Examples

### 🆓 Groq Quickstart (Start Here!)

**groq_quickstart.py** - The easiest way to get started with FREE Groq AI!

```bash
# Get your free API key from https://console.groq.com
export GROQ_API_KEY='gsk-your-key'

cd examples
python groq_quickstart.py
```

This is the recommended starting point - uses completely FREE Groq AI with no credit card required!

**See also:** [GROQ_SETUP.md](../GROQ_SETUP.md) for detailed Groq setup instructions.

---

### Selenium Examples

#### 1. **selenium_basic.py** - Basic Selenium Usage
Simple example showing fundamental AutoHeal features:
- Setting up AutoHeal with Selenium
- Finding elements with auto-healing
- Basic error handling
- Viewing metrics

**Run it:**
```bash
cd examples
python selenium_basic.py
```

**What it demonstrates:**
- Default configuration setup
- Element location with `find_element()`
- Presence checks with `is_element_present()`
- Basic metrics reporting

---

#### 2. **selenium_advanced.py** - Advanced Configuration
Comprehensive example with full configuration:
- Custom AI provider setup (OpenAI GPT-4)
- Cache configuration with TTL
- Performance tuning (SMART_SEQUENTIAL strategy)
- Resilience configuration (retries, circuit breaker)
- Custom locator options
- Comprehensive metrics and health reporting

**Run it:**
```bash
# Set your Groq API key first (FREE!)
export GROQ_API_KEY='gsk-your-api-key-here'  # Linux/Mac
# Get free key from: https://console.groq.com
# OR
set GROQ_API_KEY=gsk-your-api-key-here      # Windows

cd examples
python selenium_advanced.py
```

**What it demonstrates:**
- Full configuration with all options (using FREE Groq AI)
- E-commerce test scenario
- Cost optimization with custom options
- Cache management
- Detailed metrics analysis

---

### Playwright Examples

#### 3. **playwright_basic.py** - Basic Playwright Usage
Async Playwright example with AutoHeal:
- Setting up AutoHeal with Playwright
- Async element location
- Error handling in async context
- Metrics reporting

**Run it:**
```bash
cd examples
python playwright_basic.py
```

**Requirements:**
```bash
pip install playwright
playwright install chromium
```

**What it demonstrates:**
- Playwright async API integration
- `find_element_async()` usage
- Async/await patterns with AutoHeal

---

#### 4. **playwright_advanced.py** - Advanced Playwright Configuration
Full-featured async Playwright example:
- Complete AutoHeal configuration
- Async test scenarios
- Custom options for cost optimization
- Comprehensive async metrics

**Run it:**
```bash
# Set your Groq API key first (FREE!)
export GROQ_API_KEY='gsk-your-api-key-here'
# Get free key from: https://console.groq.com

cd examples
python playwright_advanced.py
```

**What it demonstrates:**
- Advanced async patterns
- Full configuration in Playwright context (using FREE Groq AI)
- Cost-optimized element location
- Health monitoring in async environment

---

### Pytest Integration

#### 5. **test_with_pytest.py** - Pytest Integration
Complete pytest test suite demonstrating:
- Pytest fixtures for AutoHeal setup
- Parameterized tests with different strategies
- Both Selenium and Playwright tests
- Metrics collection in tests
- Test organization best practices

**Run it:**
```bash
cd examples

# Run all tests
pytest test_with_pytest.py -v

# Run only Selenium tests
pytest test_with_pytest.py::TestLoginWithSelenium -v

# Run only Playwright tests
pytest test_with_pytest.py::TestLoginWithPlaywright -v

# Run with coverage
pytest test_with_pytest.py --cov=autoheal -v
```

**What it demonstrates:**
- Session and function-scoped fixtures
- Async pytest tests (`@pytest.mark.asyncio`)
- Parameterized tests with different execution strategies
- Metrics reporting in test teardown
- Test organization patterns

---

## 🚀 Quick Start

### 1. Install Dependencies

**For Selenium examples:**
```bash
pip install autoheal-locator[selenium]
```

**For Playwright examples:**
```bash
pip install autoheal-locator[playwright]
playwright install chromium
```

**For pytest integration:**
```bash
pip install autoheal-locator[selenium,playwright]
pip install pytest pytest-asyncio pytest-cov
playwright install chromium
```

**For all examples with AI support:**
```bash
pip install autoheal-locator[all]
playwright install chromium
```

### 2. Set Up API Keys (Optional for Basic Examples)

The basic examples work without API keys using default configuration. For advanced examples with AI healing:

```bash
# Groq (RECOMMENDED - FREE!)
# Get your free API key from: https://console.groq.com
export GROQ_API_KEY='gsk-your-api-key-here'

# Or use other providers:
# OpenAI
export OPENAI_API_KEY='sk-your-api-key-here'

# Anthropic
export ANTHROPIC_API_KEY='your-api-key-here'

# Google Gemini
export GOOGLE_API_KEY='your-api-key-here'
```

### 3. Run an Example

```bash
cd examples
python selenium_basic.py
```

---

## 📊 Example Output

When you run an example, you'll see output like:

```
==================================================
AutoHeal Locator - Basic Selenium Example
==================================================

AutoHeal Locator initialized successfully!
Navigated to login page
✓ Found and filled username field
✓ Found and filled password field
✓ Found and clicked login button
✓ Login successful!
✓ Logged out successfully

==================================================
AutoHeal Metrics:
==================================================
Total requests: 7
Successful requests: 7
Success rate: 100.00%

Cache hits: 2
Cache misses: 5
Cache hit rate: 28.57%

Overall health: ✓ OK

Browser closed
```

---

## 🎯 Example Comparison

| Example | Framework | Complexity | AI Required | Best For |
|---------|-----------|------------|-------------|----------|
| selenium_basic.py | Selenium | Basic | No | Learning basics |
| selenium_advanced.py | Selenium | Advanced | Yes | Production setup |
| playwright_basic.py | Playwright | Basic | No | Async learning |
| playwright_advanced.py | Playwright | Advanced | Yes | Async production |
| test_with_pytest.py | Both | Intermediate | Optional | Test integration |

---

## 💡 Common Patterns

### Pattern 1: Basic Setup (No AI)

```python
from selenium import webdriver
from autoheal import AutoHealLocator
from autoheal.impl.adapter import SeleniumWebAutomationAdapter

driver = webdriver.Chrome()
adapter = SeleniumWebAutomationAdapter(driver)

locator = AutoHealLocator.builder() \
    .with_web_adapter(adapter) \
    .build()

element = locator.find_element("#my-id", "My element description")
```

### Pattern 2: With Custom Configuration

```python
from autoheal import AutoHealLocator, AutoHealConfiguration
from autoheal.config import AIConfig, PerformanceConfig
from autoheal.models.enums import AIProvider, ExecutionStrategy

config = AutoHealConfiguration.builder() \
    .ai_config(
        AIConfig.builder()
        .provider(AIProvider.GROQ)  # FREE!
        .api_key(os.getenv("GROQ_API_KEY"))
        .model("llama-3.3-70b-versatile")
        .build()
    ) \
    .performance_config(
        PerformanceConfig.builder()
        .execution_strategy(ExecutionStrategy.SMART_SEQUENTIAL)
        .build()
    ) \
    .build()

locator = AutoHealLocator.builder() \
    .with_web_adapter(adapter) \
    .with_configuration(config) \
    .build()
```

### Pattern 3: Async with Playwright

```python
from playwright.async_api import async_playwright
from autoheal import AutoHealLocator
from autoheal.impl.adapter import PlaywrightWebAutomationAdapter

async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()

    adapter = PlaywrightWebAutomationAdapter(page)
    locator = AutoHealLocator.builder() \
        .with_web_adapter(adapter) \
        .build()

    element = await locator.find_element_async("#my-id", "My element")
```

### Pattern 4: Pytest Fixture

```python
@pytest.fixture(scope="function")
def autoheal_locator(selenium_driver):
    adapter = SeleniumWebAutomationAdapter(selenium_driver)
    locator = AutoHealLocator.builder() \
        .with_web_adapter(adapter) \
        .build()

    yield locator

    # Print metrics after test
    metrics = locator.get_metrics()
    print(f"Metrics: {metrics.successful_requests}/{metrics.total_requests}")

def test_my_feature(autoheal_locator):
    element = autoheal_locator.find_element("#button", "Submit button")
    element.click()
```

---

## 🔧 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'selenium'"
**Solution:** Install Selenium support:
```bash
pip install autoheal-locator[selenium]
```

### Issue: "ModuleNotFoundError: No module named 'playwright'"
**Solution:** Install Playwright and browser binaries:
```bash
pip install autoheal-locator[playwright]
playwright install chromium
```

### Issue: "WARNING: GROQ_API_KEY not set!"
**Solution:** This is just a warning. Examples will still run but won't use AI healing. To enable AI with FREE Groq:
```bash
# Get your free API key from https://console.groq.com
export GROQ_API_KEY='gsk-your-key'
```

### Issue: Playwright tests fail with "Browser not installed"
**Solution:** Install browser binaries:
```bash
playwright install chromium
```

### Issue: pytest tests fail with "async" errors
**Solution:** Install pytest-asyncio:
```bash
pip install pytest-asyncio
```

### Issue: "Element not found" errors
**Possible causes:**
1. Network issues - the demo sites might be temporarily down
2. Page loading too slowly - increase element timeout in configuration
3. Selector changed - AutoHeal should fix this automatically if AI is configured

---

## 📚 Learning Path

**If you're new to AutoHeal:**
1. Start with `selenium_basic.py` - learn the fundamentals
2. Try `playwright_basic.py` - see async patterns
3. Explore `selenium_advanced.py` - understand full configuration
4. Study `test_with_pytest.py` - learn test integration
5. Experiment with `playwright_advanced.py` - master async configuration

**If you're integrating into existing tests:**
1. Review `test_with_pytest.py` for pytest patterns
2. Check `selenium_advanced.py` for configuration options
3. Adapt the fixtures to your test framework
4. Start with DOM_ONLY strategy to avoid AI costs while testing

---

## 🌐 Test Sites Used

These examples use publicly available test websites:

- **https://the-internet.herokuapp.com** - General web automation practice
  - Login page: Username/password forms
  - Dynamic loading: Async content testing

- **https://www.saucedemo.com** - E-commerce demo
  - Credentials: standard_user / secret_sauce
  - Product catalog and cart functionality

---

## 📖 Additional Resources

- **Main README**: See `../README.md` for complete API documentation
- **Configuration Guide**: Check `../README.md#configuration` for all config options
- **API Reference**: See `../README.md#api-reference` for method details
- **Best Practices**: Review `../README.md#best-practices` for optimization tips

---

## 🤝 Contributing Examples

Have a useful example? Contributions are welcome!

1. Create a new example file following the naming convention
2. Add comprehensive comments explaining each step
3. Update this README with your example
4. Ensure it runs successfully
5. Submit a pull request

---

## 📝 Notes

- All examples use headless browser mode for CI/CD compatibility
- Examples are self-contained and can run independently
- No real user data or credentials are required
- Test sites are public and rate-limiting applies
- Cache is cleared between example runs

---

**Happy Testing with AutoHeal! 🚀**
