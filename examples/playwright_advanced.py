"""
Advanced Playwright Example with Full Configuration

This example demonstrates advanced features of AutoHeal Locator:
- Custom AI provider configuration
- Cache configuration with Redis
- Performance tuning with execution strategies
- Resilience configuration
- Custom locator options
- Comprehensive error handling
"""

import os
import asyncio
from datetime import timedelta
from playwright.async_api import async_playwright

from autoheal import AutoHealLocator, AutoHealConfiguration
from autoheal.impl.adapter import PlaywrightWebAutomationAdapter
from autoheal.config import (
    AIConfig,
    CacheConfig,
    PerformanceConfig,
    ResilienceConfig,
    LocatorOptions
)
from autoheal.models.enums import (
    AIProvider,
    ExecutionStrategy,
    CacheType
)


def create_configuration():
    """Create a fully configured AutoHeal configuration."""

    # AI Configuration - Using Groq (FREE!)
    # Get your free API key from https://console.groq.com
    ai_config = AIConfig.builder() \
        .provider(AIProvider.GROQ) \
        .api_key(os.getenv("GROQ_API_KEY", "gsk-your-api-key-here")) \
        .model("llama-3.3-70b-versatile") \
        .temperature(0.1) \
        .max_tokens(2000) \
        .timeout(timedelta(seconds=30)) \
        .build()

    # Cache Configuration - Using in-memory cache
    # For production, consider using Redis for distributed caching
    cache_config = CacheConfig.builder() \
        .cache_type(CacheType.CAFFEINE) \
        .maximum_size(500) \
        .expire_after_write(timedelta(hours=24)) \
        .expire_after_access(timedelta(hours=12)) \
        .record_stats(True) \
        .build()

    # Performance Configuration
    # SMART_SEQUENTIAL: Try DOM first (cheap), then visual if needed
    perf_config = PerformanceConfig.builder() \
        .execution_strategy(ExecutionStrategy.SMART_SEQUENTIAL) \
        .element_timeout(timedelta(seconds=10)) \
        .screenshot_quality(85) \
        .build()

    # Resilience Configuration
    # Configure retry logic and circuit breaker
    resilience_config = ResilienceConfig.builder() \
        .max_retries(3) \
        .retry_delay(timedelta(seconds=1)) \
        .circuit_breaker_threshold(5) \
        .circuit_breaker_timeout(timedelta(minutes=1)) \
        .build()

    # Combine all configurations
    config = AutoHealConfiguration.builder() \
        .ai_config(ai_config) \
        .cache_config(cache_config) \
        .performance_config(perf_config) \
        .resilience_config(resilience_config) \
        .build()

    return config


async def run_test_scenario(locator, page):
    """Run a comprehensive test scenario."""

    print("\n" + "="*60)
    print("Test Scenario: E-commerce Product Search")
    print("="*60)

    # Navigate to demo site
    await page.goto("https://www.saucedemo.com/")
    print("✓ Navigated to demo site")

    # Login
    username = await locator.find_element_async(
        "#user-name",
        "Username input field"
    )
    await username.fill("standard_user")

    password = await locator.find_element_async(
        "#password",
        "Password input field"
    )
    await password.fill("secret_sauce")

    login_btn = await locator.find_element_async(
        "#login-button",
        "Login button"
    )
    await login_btn.click()
    print("✓ Logged in successfully")

    # Find products
    products = await locator.find_elements_async(
        ".inventory_item",
        "Product items in the catalog"
    )
    print(f"✓ Found {len(products)} products")

    # Add first product to cart
    add_to_cart_btn = await locator.find_element_async(
        ".btn_inventory",
        "Add to cart button for first product"
    )
    await add_to_cart_btn.click()
    print("✓ Added product to cart")

    # Go to cart
    cart_icon = await locator.find_element_async(
        ".shopping_cart_link",
        "Shopping cart icon"
    )
    await cart_icon.click()
    print("✓ Navigated to cart")

    # Verify cart has items
    if await locator.is_element_present_async(".cart_item", "Cart item"):
        print("✓ Cart contains items")
    else:
        print("✗ Cart is empty")

    # Checkout
    checkout_btn = await locator.find_element_async(
        "#checkout",
        "Checkout button"
    )
    await checkout_btn.click()
    print("✓ Started checkout process")


async def demonstrate_custom_options(locator, page):
    """Demonstrate using custom locator options."""

    print("\n" + "="*60)
    print("Demonstrating Custom Locator Options")
    print("="*60)

    await page.goto("https://the-internet.herokuapp.com/dynamic_loading/1")

    # Custom options: Disable visual analysis to save costs
    fast_options = LocatorOptions.builder() \
        .enable_caching(True) \
        .enable_dom_analysis(True) \
        .enable_visual_analysis(False) \
        .timeout(timedelta(seconds=15)) \
        .build()

    # Use custom options
    element = await locator.find_element_async(
        "#start button",
        "Start button",
        options=fast_options
    )
    await element.click()
    print("✓ Clicked start button with custom options (DOM only)")


def display_comprehensive_metrics(locator):
    """Display comprehensive metrics and health information."""

    print("\n" + "="*60)
    print("Comprehensive Metrics Report")
    print("="*60)

    # Locator metrics
    metrics = locator.get_metrics()
    print("\n📊 Locator Performance:")
    print(f"  Total requests: {metrics.total_requests}")
    print(f"  Successful: {metrics.successful_requests}")
    print(f"  Failed: {metrics.failed_requests}")
    print(f"  Success rate: {metrics.get_success_rate():.2%}")
    print(f"  Average latency: {metrics.get_average_latency():.0f}ms")

    # Cache metrics
    cache_metrics = locator.get_cache_metrics()
    total_cache_requests = cache_metrics.total_hits + cache_metrics.total_misses

    print("\n💾 Cache Performance:")
    print(f"  Total requests: {total_cache_requests}")
    print(f"  Hits: {cache_metrics.total_hits}")
    print(f"  Misses: {cache_metrics.total_misses}")
    print(f"  Hit rate: {cache_metrics.get_hit_rate():.2%}")
    print(f"  Evictions: {cache_metrics.evictions}")

    if cache_metrics.total_hits > 0:
        print(f"\n💰 Cost Savings:")
        print(f"  Cache saved {cache_metrics.total_hits} AI API calls!")

    # Health status
    health = locator.get_health_status()
    print("\n🏥 Health Status:")
    print(f"  Overall: {'✓ HEALTHY' if health['overall'] else '✗ DEGRADED'}")
    print(f"  Success rate: {health['success_rate']:.2%}")
    print(f"  Cache efficiency: {health['cache_hit_rate']:.2%}")


async def main():
    """Run advanced Playwright example."""

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        try:
            # Create advanced configuration
            print("Creating advanced configuration...")
            config = create_configuration()
            print("✓ Configuration created")

            # Create AutoHeal adapter and locator
            adapter = PlaywrightWebAutomationAdapter(page)
            locator = AutoHealLocator.builder() \
                .with_web_adapter(adapter) \
                .with_configuration(config) \
                .build()

            print("✓ AutoHeal Locator initialized with custom configuration")

            # Run test scenarios
            await run_test_scenario(locator, page)
            await demonstrate_custom_options(locator, page)

            # Display comprehensive metrics
            display_comprehensive_metrics(locator)

            # Cache management demonstration
            print("\n" + "="*60)
            print("Cache Management")
            print("="*60)

            cache_size = locator.get_cache_size()
            print(f"Current cache size: {cache_size} entries")

            # Optionally clear cache
            # locator.clear_cache()
            # print("Cache cleared")

        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Cleanup
            await browser.close()
            print("\n✓ Browser closed")


if __name__ == "__main__":
    print("="*60)
    print("AutoHeal Locator - Advanced Playwright Example")
    print("="*60)
    print()
    print("This example demonstrates:")
    print("  • Custom AI configuration")
    print("  • Cache configuration")
    print("  • Performance tuning")
    print("  • Resilience settings")
    print("  • Custom locator options")
    print("  • Comprehensive metrics")
    print()

    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️  WARNING: GROQ_API_KEY not set!")
        print("   Get your FREE API key from: https://console.groq.com")
        print("   Set it with: export GROQ_API_KEY='gsk-your-key'")
        print("   Continuing with placeholder key...")
        print()

    asyncio.run(main())
