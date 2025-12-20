from playwright.sync_api import sync_playwright
import time

def verify_player():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # Navigate to home
        page.goto("http://localhost:3000/")

        # Wait for app to load
        page.wait_for_selector("body")

        # We need to find where the player is.
        # It's likely in OutputPreview which shows up after upload/processing.
        # Or maybe there is a demo or FeaturesSection that uses it?
        # Let's check features section or hero.

        # If I can't easily trigger the state, I might need to mock it.
        # However, looking at codebase, HeroSection might have one?
        # Let's check HeroSection.tsx content.

        page.screenshot(path="verification/verification_initial.png")
        browser.close()

if __name__ == "__main__":
    verify_player()
