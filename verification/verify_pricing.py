from playwright.sync_api import sync_playwright

def verify_pricing(page):
    page.goto("http://localhost:3000")

    # Wait for page to load
    page.wait_for_selector('footer')

    # Test Pricing Link
    page.click('a[href="#pricing"]')
    page.wait_for_timeout(1000)
    pricing_section = page.locator('#pricing')
    if pricing_section.is_visible():
        print("Pricing section is visible")
        page.screenshot(path="verification/pricing_section.png", full_page=True)
    else:
        print("Pricing section not visible")

    # Test API Link
    page.click('a[href="#api"]')
    page.wait_for_timeout(1000)
    api_section = page.locator('#api')
    if api_section.is_visible():
        print("API section is visible")
        api_section.scroll_into_view_if_needed()
        page.screenshot(path="verification/api_section.png")
    else:
        print("API section not visible")

    # Test Features Link
    page.click('a[href="#features"]')
    page.wait_for_timeout(1000)
    features_section = page.locator('#features')
    if features_section.is_visible():
        print("Features section is visible")
        features_section.scroll_into_view_if_needed()
        page.screenshot(path="verification/features_section.png")
    else:
        print("Features section not visible")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_pricing(page)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()
