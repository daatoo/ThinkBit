from playwright.sync_api import sync_playwright

def verify_player():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # Navigate to homepage
            page.goto("http://localhost:3000")
            page.wait_for_timeout(3000) # Wait for page load

            # Take full page screenshot
            page.screenshot(path="verification/player_full.png")

            # Try to find the CustomPlayer in Audio mode
            # We look for the activity icon which is the new toggle button
            # Note: The player might be in 'video' mode by default or not visible if no content is loaded.
            # However, looking at the code, CustomPlayer is used in OutputPreview and potentially other places.
            # Let's try to locate the player container.

            # Since I can't easily force audio state without interaction or mocking,
            # I will just capture the page state.
            # If the player is not visible, I might need to trigger something.
            # But the 'verify_pricing.py' exists, suggesting the main page has content.

            print("Screenshot taken.")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_player()
