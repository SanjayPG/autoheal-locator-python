"""
Basic Selenium Example with AutoHeal Locator

This example demonstrates the basic usage of AutoHeal Locator with Selenium.
It shows how to:
- Set up AutoHeal with Selenium
- Find elements with auto-healing
- Handle element location failures gracefully
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from autoheal import AutoHealLocator
from autoheal.impl.adapter import SeleniumWebAutomationAdapter


def main():
    """Run a basic Selenium test with AutoHeal."""

    # Setup Chrome driver
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Create AutoHeal adapter
        adapter = SeleniumWebAutomationAdapter(driver)

        # Create AutoHeal locator with default configuration
        locator = AutoHealLocator.builder() \
            .with_web_adapter(adapter) \
            .build()

        print("AutoHeal Locator initialized successfully!")

        # Navigate to a test page
        driver.get("https://the-internet.herokuapp.com/login")
        print("Navigated to login page")

        # Find username field with auto-healing
        # If the selector breaks, AutoHeal will automatically fix it!
        username = locator.find_element(
            "#username",
            "Username input field on login page"
        )
        username.send_keys("tomsmith")
        print("✓ Found and filled username field")

        # Find password field
        password = locator.find_element(
            "#password",
            "Password input field on login page"
        )
        password.send_keys("SuperSecretPassword!")
        print("✓ Found and filled password field")

        # Find login button
        login_button = locator.find_element(
            "button[type='submit']",
            "Login submit button"
        )
        login_button.click()
        print("✓ Found and clicked login button")

        # Verify login success
        if locator.is_element_present(".flash.success", "Success message"):
            print("✓ Login successful!")
        else:
            print("✗ Login failed")

        # Find logout button (demonstrates finding elements after page change)
        logout_button = locator.find_element(
            ".button.secondary",
            "Logout button in header"
        )
        logout_button.click()
        print("✓ Logged out successfully")

        # Display metrics
        print("\n" + "="*50)
        print("AutoHeal Metrics:")
        print("="*50)

        metrics = locator.get_metrics()
        print(f"Total requests: {metrics.total_requests}")
        print(f"Successful requests: {metrics.successful_requests}")
        print(f"Success rate: {metrics.get_success_rate():.2%}")

        cache_metrics = locator.get_cache_metrics()
        print(f"\nCache hits: {cache_metrics.total_hits}")
        print(f"Cache misses: {cache_metrics.total_misses}")
        print(f"Cache hit rate: {cache_metrics.get_hit_rate():.2%}")

        health = locator.get_health_status()
        print(f"\nOverall health: {'✓ OK' if health['overall'] else '✗ DEGRADED'}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Always cleanup
        driver.quit()
        print("\nBrowser closed")


if __name__ == "__main__":
    print("="*50)
    print("AutoHeal Locator - Basic Selenium Example")
    print("="*50)
    print()

    main()
