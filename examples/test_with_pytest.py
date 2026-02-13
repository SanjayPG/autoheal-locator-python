"""
Pytest Integration Example with AutoHeal Locator

This example demonstrates how to integrate AutoHeal Locator with pytest:
- Pytest fixtures for AutoHeal setup
- Parameterized tests with different configurations
- Test organization and best practices
- Metrics reporting in test results
"""

import os
import pytest
from datetime import timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from playwright.async_api import async_playwright

from autoheal import AutoHealLocator, AutoHealConfiguration
from autoheal.impl.adapter import SeleniumWebAutomationAdapter, PlaywrightWebAutomationAdapter
from autoheal.config import AIConfig, CacheConfig, PerformanceConfig
from autoheal.models.enums import AIProvider, ExecutionStrategy, CacheType


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def autoheal_config():
    """Create AutoHeal configuration for the test session."""
    ai_config = AIConfig.builder() \
        .provider(AIProvider.GROQ) \
        .api_key(os.getenv("GROQ_API_KEY", "gsk-test-key")) \
        .model("llama-3.3-70b-versatile") \
        .temperature(0.1) \
        .build()

    cache_config = CacheConfig.builder() \
        .cache_type(CacheType.CAFFEINE) \
        .maximum_size(100) \
        .expire_after_write(timedelta(hours=1)) \
        .build()

    perf_config = PerformanceConfig.builder() \
        .execution_strategy(ExecutionStrategy.SMART_SEQUENTIAL) \
        .element_timeout(timedelta(seconds=10)) \
        .build()

    return AutoHealConfiguration.builder() \
        .ai_config(ai_config) \
        .cache_config(cache_config) \
        .performance_config(perf_config) \
        .build()


@pytest.fixture(scope="function")
def selenium_driver():
    """Create Selenium WebDriver for each test."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=chrome_options)
    yield driver
    driver.quit()


@pytest.fixture(scope="function")
def autoheal_selenium(selenium_driver, autoheal_config):
    """Create AutoHeal locator with Selenium adapter."""
    adapter = SeleniumWebAutomationAdapter(selenium_driver)
    locator = AutoHealLocator.builder() \
        .with_web_adapter(adapter) \
        .with_configuration(autoheal_config) \
        .build()
    yield locator, selenium_driver

    # Print metrics after each test
    metrics = locator.get_metrics()
    print(f"\n📊 Test Metrics: {metrics.successful_requests}/{metrics.total_requests} successful")


@pytest.fixture(scope="function")
async def playwright_browser():
    """Create Playwright browser for each test."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        yield page
        await browser.close()


@pytest.fixture(scope="function")
async def autoheal_playwright(playwright_browser, autoheal_config):
    """Create AutoHeal locator with Playwright adapter."""
    adapter = PlaywrightWebAutomationAdapter(playwright_browser)
    locator = AutoHealLocator.builder() \
        .with_web_adapter(adapter) \
        .with_configuration(autoheal_config) \
        .build()
    yield locator, playwright_browser

    # Print metrics after each test
    metrics = locator.get_metrics()
    print(f"\n📊 Test Metrics: {metrics.successful_requests}/{metrics.total_requests} successful")


# ============================================================================
# Selenium Tests
# ============================================================================

class TestLoginWithSelenium:
    """Test suite for login functionality using Selenium."""

    def test_successful_login(self, autoheal_selenium):
        """Test successful login flow."""
        locator, driver = autoheal_selenium

        # Navigate to login page
        driver.get("https://the-internet.herokuapp.com/login")

        # Perform login
        username = locator.find_element("#username", "Username field")
        username.send_keys("tomsmith")

        password = locator.find_element("#password", "Password field")
        password.send_keys("SuperSecretPassword!")

        login_btn = locator.find_element("button[type='submit']", "Login button")
        login_btn.click()

        # Verify success
        assert locator.is_element_present(".flash.success", "Success message")

    def test_failed_login(self, autoheal_selenium):
        """Test failed login with wrong credentials."""
        locator, driver = autoheal_selenium

        driver.get("https://the-internet.herokuapp.com/login")

        username = locator.find_element("#username", "Username field")
        username.send_keys("invaliduser")

        password = locator.find_element("#password", "Password field")
        password.send_keys("wrongpassword")

        login_btn = locator.find_element("button[type='submit']", "Login button")
        login_btn.click()

        # Verify error message
        assert locator.is_element_present(".flash.error", "Error message")


class TestDynamicContent:
    """Test suite for dynamic content using Selenium."""

    def test_dynamic_loading(self, autoheal_selenium):
        """Test handling dynamically loaded content."""
        locator, driver = autoheal_selenium

        driver.get("https://the-internet.herokuapp.com/dynamic_loading/1")

        start_btn = locator.find_element("#start button", "Start button")
        start_btn.click()

        # AutoHeal will wait for the element to appear
        result = locator.find_element("#finish", "Finish message")
        assert result is not None


# ============================================================================
# Playwright Tests (Async)
# ============================================================================

class TestLoginWithPlaywright:
    """Test suite for login functionality using Playwright."""

    @pytest.mark.asyncio
    async def test_successful_login(self, autoheal_playwright):
        """Test successful login flow."""
        locator, page = autoheal_playwright

        # Navigate to login page
        await page.goto("https://the-internet.herokuapp.com/login")

        # Perform login
        username = await locator.find_element_async("#username", "Username field")
        await username.fill("tomsmith")

        password = await locator.find_element_async("#password", "Password field")
        await password.fill("SuperSecretPassword!")

        login_btn = await locator.find_element_async("button[type='submit']", "Login button")
        await login_btn.click()

        # Verify success
        assert await locator.is_element_present_async(".flash.success", "Success message")

    @pytest.mark.asyncio
    async def test_logout_flow(self, autoheal_playwright):
        """Test complete login-logout flow."""
        locator, page = autoheal_playwright

        await page.goto("https://the-internet.herokuapp.com/login")

        # Login
        username = await locator.find_element_async("#username", "Username field")
        await username.fill("tomsmith")

        password = await locator.find_element_async("#password", "Password field")
        await password.fill("SuperSecretPassword!")

        login_btn = await locator.find_element_async("button[type='submit']", "Login button")
        await login_btn.click()

        # Logout
        logout_btn = await locator.find_element_async(".button.secondary", "Logout button")
        await logout_btn.click()

        # Verify back at login page
        assert await locator.is_element_present_async("#username", "Username field")


# ============================================================================
# Parameterized Tests
# ============================================================================

class TestWithDifferentStrategies:
    """Test with different execution strategies."""

    @pytest.mark.parametrize("strategy", [
        ExecutionStrategy.DOM_ONLY,
        ExecutionStrategy.SMART_SEQUENTIAL,
    ])
    def test_with_strategy(self, selenium_driver, strategy):
        """Test element location with different strategies."""
        # Create config with specific strategy
        config = AutoHealConfiguration.builder() \
            .performance_config(
                PerformanceConfig.builder()
                .execution_strategy(strategy)
                .build()
            ) \
            .build()

        adapter = SeleniumWebAutomationAdapter(selenium_driver)
        locator = AutoHealLocator.builder() \
            .with_web_adapter(adapter) \
            .with_configuration(config) \
            .build()

        selenium_driver.get("https://the-internet.herokuapp.com/login")

        # Find element should work regardless of strategy
        username = locator.find_element("#username", "Username field")
        assert username is not None

        print(f"\n✓ Strategy {strategy.name} succeeded")


# ============================================================================
# Metrics and Reporting
# ============================================================================

class TestMetricsReporting:
    """Test suite for metrics and health reporting."""

    def test_metrics_collection(self, autoheal_selenium):
        """Verify metrics are collected correctly."""
        locator, driver = autoheal_selenium

        driver.get("https://the-internet.herokuapp.com/login")

        # Perform some operations
        locator.find_element("#username", "Username field")
        locator.find_element("#password", "Password field")
        locator.is_element_present("button[type='submit']", "Login button")

        # Check metrics
        metrics = locator.get_metrics()
        assert metrics.total_requests >= 3
        assert metrics.successful_requests >= 3
        assert metrics.get_success_rate() > 0

    def test_cache_metrics(self, autoheal_selenium):
        """Verify cache metrics are tracked."""
        locator, driver = autoheal_selenium

        driver.get("https://the-internet.herokuapp.com/login")

        # Find same element twice - second should be cached
        locator.find_element("#username", "Username field")
        locator.find_element("#username", "Username field")

        cache_metrics = locator.get_cache_metrics()
        # At least one request should have been made
        total_requests = cache_metrics.total_hits + cache_metrics.total_misses
        assert total_requests > 0

    def test_health_status(self, autoheal_selenium):
        """Verify health status reporting."""
        locator, driver = autoheal_selenium

        driver.get("https://the-internet.herokuapp.com/login")

        # Perform successful operations
        locator.find_element("#username", "Username field")

        health = locator.get_health_status()
        assert 'overall' in health
        assert 'success_rate' in health
        assert 'cache_hit_rate' in health


# ============================================================================
# Test Configuration
# ============================================================================

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([
        __file__,
        "-v",  # Verbose output
        "-s",  # Show print statements
        "--tb=short",  # Short traceback format
        "--maxfail=3",  # Stop after 3 failures
    ])
