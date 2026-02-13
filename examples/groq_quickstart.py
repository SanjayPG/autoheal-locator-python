"""
Groq Quickstart Example

This example shows the simplest way to get started with AutoHeal Locator using
the FREE Groq AI provider. Perfect for trying out AutoHeal without spending money!

Steps:
1. Get your FREE API key from: https://console.groq.com
2. Set the environment variable: export GROQ_API_KEY='gsk-your-key'
3. Run this script!
"""

import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from autoheal import AutoHealLocator, AutoHealConfiguration
from autoheal.impl.adapter import SeleniumWebAutomationAdapter
from autoheal.config import AIConfig
from autoheal.models.enums import AIProvider


def main():
    """Simple example using FREE Groq AI."""

    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        print("="*60)
        print("⚠️  GROQ_API_KEY not set!")
        print("="*60)
        print()
        print("Get your FREE API key:")
        print("1. Visit: https://console.groq.com")
        print("2. Sign up (it's free!)")
        print("3. Create an API key")
        print("4. Set it:")
        print("   export GROQ_API_KEY='gsk-your-key'")
        print()
        print("Continuing with demo mode (no AI healing)...")
        print("="*60)
        print()
        api_key = "demo-key"
    else:
        api_key = os.getenv("GROQ_API_KEY")
        print("✅ Groq API key found!")

    # Setup Chrome driver
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Create AutoHeal configuration with Groq
        ai_config = AIConfig.builder() \
            .provider(AIProvider.GROQ) \
            .api_key(api_key) \
            .model("llama-3.3-70b-versatile") \
            .build()

        config = AutoHealConfiguration.builder() \
            .ai_config(ai_config) \
            .build()

        # Create adapter and locator
        adapter = SeleniumWebAutomationAdapter(driver)
        locator = AutoHealLocator.builder() \
            .with_web_adapter(adapter) \
            .with_configuration(config) \
            .build()

        print("\n✅ AutoHeal Locator initialized with Groq!")
        print("   Model: llama-3.3-70b-versatile (FREE)")
        print()

        # Simple test
        print("Running a simple test...")
        driver.get("https://the-internet.herokuapp.com/login")

        # Find and interact with elements
        username = locator.find_element("#username", "Username field")
        username.send_keys("tomsmith")
        print("✓ Found username field")

        password = locator.find_element("#password", "Password field")
        password.send_keys("SuperSecretPassword!")
        print("✓ Found password field")

        login_btn = locator.find_element("button[type='submit']", "Login button")
        login_btn.click()
        print("✓ Clicked login button")

        # Check if login was successful
        if locator.is_element_present(".flash.success", "Success message"):
            print("✓ Login successful!")

        # Show metrics
        print("\n" + "="*60)
        print("Metrics Summary")
        print("="*60)
        metrics = locator.get_metrics()
        print(f"Total requests: {metrics.total_requests}")
        print(f"Successful: {metrics.successful_requests}")
        print(f"Success rate: {metrics.get_success_rate():.1%}")

        cache_metrics = locator.get_cache_metrics()
        print(f"Cache hits: {cache_metrics.total_hits}")
        print(f"Cache misses: {cache_metrics.total_misses}")

        if cache_metrics.total_hits > 0:
            print(f"\n💰 Saved {cache_metrics.total_hits} AI API calls with caching!")

        print("\n✅ All done! AutoHeal Locator works with FREE Groq AI!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()
        print("\n🔒 Browser closed")


if __name__ == "__main__":
    print("="*60)
    print("AutoHeal Locator - Groq Quickstart")
    print("="*60)
    print()
    print("Using FREE Groq AI for element healing!")
    print("No costs, no limits - perfect for development")
    print()

    main()
