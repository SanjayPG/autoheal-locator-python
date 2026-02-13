"""
Basic Playwright Example with AutoHeal Locator

This example demonstrates the basic usage of AutoHeal Locator with Playwright.
It shows how to:
- Set up AutoHeal with Playwright
- Find elements with auto-healing
- Handle element location failures gracefully
"""

import asyncio
from playwright.async_api import async_playwright
from autoheal import AutoHealLocator
from autoheal.impl.adapter import PlaywrightWebAutomationAdapter


async def main():
    """Run a basic Playwright test with AutoHeal."""

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        try:
            # Create AutoHeal adapter
            adapter = PlaywrightWebAutomationAdapter(page)

            # Create AutoHeal locator with default configuration
            locator = AutoHealLocator.builder() \
                .with_web_adapter(adapter) \
                .build()

            print("AutoHeal Locator initialized successfully!")

            # Navigate to a test page
            await page.goto("https://the-internet.herokuapp.com/login")
            print("Navigated to login page")

            # Find username field with auto-healing
            # If the selector breaks, AutoHeal will automatically fix it!
            username = await locator.find_element_async(
                "#username",
                "Username input field on login page"
            )
            await username.fill("tomsmith")
            print("✓ Found and filled username field")

            # Find password field
            password = await locator.find_element_async(
                "#password",
                "Password input field on login page"
            )
            await password.fill("SuperSecretPassword!")
            print("✓ Found and filled password field")

            # Find login button
            login_button = await locator.find_element_async(
                "button[type='submit']",
                "Login submit button"
            )
            await login_button.click()
            print("✓ Found and clicked login button")

            # Verify login success
            if await locator.is_element_present_async(".flash.success", "Success message"):
                print("✓ Login successful!")
            else:
                print("✗ Login failed")

            # Find logout button (demonstrates finding elements after page change)
            logout_button = await locator.find_element_async(
                ".button.secondary",
                "Logout button in header"
            )
            await logout_button.click()
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
            await browser.close()
            print("\nBrowser closed")


if __name__ == "__main__":
    print("="*50)
    print("AutoHeal Locator - Basic Playwright Example")
    print("="*50)
    print()

    asyncio.run(main())
