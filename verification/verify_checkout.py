from playwright.sync_api import Page, expect, sync_playwright

def verify_free_trial_and_modals(page: Page):
    # 1. Navigate to the homepage
    print("Navigating to homepage...")
    page.goto("http://localhost:3000")

    # 2. Verify Sign In Modal
    print("Verifying Sign In Modal...")
    page.get_by_role("button", name="Sign In").click()
    expect(page.get_by_role("heading", name="Welcome Back")).to_be_visible()
    # Close modal (clicking outside or escape - but let's just reload or navigate for simplicity if we want to reset state,
    # but here we can just verify content)
    page.keyboard.press("Escape")

    # 3. Verify Get Started (Sign Up) Modal
    print("Verifying Sign Up Modal...")
    page.get_by_role("button", name="Get Started").first.click()
    expect(page.get_by_role("heading", name="Get Started")).to_be_visible()
    page.keyboard.press("Escape")

    # 4. Navigate to Free Trial Page
    print("Navigating to Free Trial Page...")
    page.goto("http://localhost:3000/free-trial")

    # 5. Verify Checkout Page Elements
    print("Verifying Checkout Page Elements...")
    expect(page.get_by_role("heading", name="Start Your Free Trial")).to_be_visible()
    expect(page.get_by_role("heading", name="Checkout Details")).to_be_visible()

    # 6. Fill out the form
    print("Filling out form...")
    page.get_by_label("First Name").fill("Jules")
    page.get_by_label("Last Name").fill("Agent")
    page.get_by_label("Email Address").fill("jules@example.com")

    # 7. Submit
    print("Submitting form...")
    page.get_by_role("button", name="Start Free Trial").click()

    # 8. Wait for Success State
    print("Waiting for success...")
    expect(page.get_by_text("Success!")).to_be_visible(timeout=10000)

    # 9. Screenshot
    print("Taking screenshot...")
    page.screenshot(path="/home/jules/verification/verification.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_free_trial_and_modals(page)
        finally:
            browser.close()
