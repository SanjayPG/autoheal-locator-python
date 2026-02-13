"""
End-to-end tests for AutoHeal selector healing using saucedemo.com.

These tests navigate to a live website and use INTENTIONALLY BROKEN selectors
to verify that the AutoHeal framework can heal them using the local AI model
(DeepSeek via Cloudflare tunnel). Each test demonstrates the core value
proposition: broken selectors are automatically fixed via DOM analysis.

Prerequisites:
- Local model endpoint must be reachable (Cloudflare tunnel active)
- Chrome/Chromium must be installed for Selenium WebDriver
"""

import logging
import pytest
from datetime import timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from autoheal import AutoHealLocator, AutoHealConfiguration
from autoheal.impl.adapter import SeleniumWebAutomationAdapter
from autoheal.config.ai_config import AIConfig
from autoheal.config.performance_config import PerformanceConfig
from autoheal.models.enums import AIProvider, ExecutionStrategy

from tests.conftest import (
    LOCAL_MODEL_URL,
    LOCAL_MODEL_NAME,
    requires_local_model,
)

logger = logging.getLogger(__name__)

SAUCEDEMO_URL = "https://www.saucedemo.com"
SAUCEDEMO_USER = "standard_user"
SAUCEDEMO_PASS = "secret_sauce"


@pytest.fixture(scope="function")
def chrome_driver():
    """Create a headless Chrome driver for each test."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5)
    yield driver
    driver.quit()


@pytest.fixture(scope="function")
def autoheal_locator(chrome_driver):
    """Create AutoHealLocator configured for local LLM with DOM_ONLY strategy."""
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
        .visual_analysis_enabled(False)
        .build()
    )

    perf_config = (
        PerformanceConfig.builder()
        .execution_strategy(ExecutionStrategy.DOM_ONLY)
        .build()
    )

    config = (
        AutoHealConfiguration.builder()
        .ai(ai_config)
        .performance(perf_config)
        .build()
    )

    adapter = SeleniumWebAutomationAdapter(chrome_driver)
    locator = (
        AutoHealLocator.builder()
        .with_web_adapter(adapter)
        .with_configuration(config)
        .build()
    )

    return locator, chrome_driver


@requires_local_model
class TestSaucedemoHealing:
    """End-to-end healing tests using saucedemo.com with broken selectors."""

    def test_heal_login_username(self, autoheal_locator):
        """
        Verify AI heals a broken username field selector.

        Broken selector: '#user-name-broken' (does not exist)
        Expected heal to: '#user-name' or equivalent
        """
        locator, driver = autoheal_locator
        driver.get(SAUCEDEMO_URL)

        username_field = locator.find_element(
            "#user-name-broken",
            "Username input field for login"
        )

        username_field.send_keys(SAUCEDEMO_USER)

        actual_value = username_field.get_attribute("value")
        assert actual_value == SAUCEDEMO_USER, (
            f"Expected username field to contain '{SAUCEDEMO_USER}', got '{actual_value}'"
        )
        logger.info("Successfully healed username selector and typed value")

    def test_heal_login_password(self, autoheal_locator):
        """
        Verify AI heals a broken password field selector.

        Broken selector: '#password-broken' (does not exist)
        Expected heal to: '#password' or equivalent
        """
        locator, driver = autoheal_locator
        driver.get(SAUCEDEMO_URL)

        password_field = locator.find_element(
            "#password-broken",
            "Password input field for login"
        )

        password_field.send_keys(SAUCEDEMO_PASS)

        actual_value = password_field.get_attribute("value")
        assert actual_value == SAUCEDEMO_PASS, (
            f"Expected password field to contain '{SAUCEDEMO_PASS}', got '{actual_value}'"
        )
        logger.info("Successfully healed password selector and typed value")

    def test_heal_login_button(self, autoheal_locator):
        """
        Verify AI heals a broken login button selector.

        Broken selector: '#login-btn' (does not exist)
        Expected heal to: '#login-button' or equivalent
        """
        locator, driver = autoheal_locator
        driver.get(SAUCEDEMO_URL)

        # Fill credentials with standard Selenium to isolate the button healing
        driver.find_element(By.ID, "user-name").send_keys(SAUCEDEMO_USER)
        driver.find_element(By.ID, "password").send_keys(SAUCEDEMO_PASS)

        # Use broken selector for the login button
        login_button = locator.find_element(
            "#login-btn",
            "Login submit button"
        )

        login_button.click()

        assert "inventory" in driver.current_url, (
            f"Expected to be on inventory page, but URL is: {driver.current_url}"
        )
        logger.info("Successfully healed login button selector and logged in")

    def test_full_login_flow_with_healing(self, autoheal_locator):
        """
        Complete login flow using ALL broken selectors.

        Every element is found via a broken selector that must be healed by the AI.
        """
        locator, driver = autoheal_locator
        driver.get(SAUCEDEMO_URL)

        # Step 1: Find and fill username with broken selector
        username_field = locator.find_element(
            "#user-name-broken",
            "Username input field for login"
        )
        username_field.send_keys(SAUCEDEMO_USER)
        logger.info("Step 1: Username field healed and filled")

        # Step 2: Find and fill password with broken selector
        password_field = locator.find_element(
            "#password-broken",
            "Password input field for login"
        )
        password_field.send_keys(SAUCEDEMO_PASS)
        logger.info("Step 2: Password field healed and filled")

        # Step 3: Find and click login button with broken selector
        login_button = locator.find_element(
            "#login-btn",
            "Login submit button"
        )
        login_button.click()
        logger.info("Step 3: Login button healed and clicked")

        # Step 4: Verify successful login
        assert "inventory" in driver.current_url, (
            f"Expected inventory page, got: {driver.current_url}"
        )

        # Log metrics
        metrics = locator.get_metrics()
        logger.info(
            "Healing metrics: %d/%d successful (%.0f%% success rate)",
            metrics.successful_requests,
            metrics.total_requests,
            metrics.get_success_rate() * 100,
        )
