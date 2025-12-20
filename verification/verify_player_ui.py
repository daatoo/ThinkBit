from playwright.sync_api import sync_playwright
import time

def verify_player_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 1200})
        page = context.new_page()

        # Navigate to home (where we injected the player)
        try:
            page.goto("http://localhost:3000/", timeout=10000)
        except Exception as e:
            print(f"Navigation failed: {e}")
            # Try once more
            page.goto("http://localhost:3000/")

        page.wait_for_selector("body")
        time.sleep(2) # Allow components to mount

        # Screenshot
        page.screenshot(path="verification/verification_player.png")
        print("Screenshot taken at verification/verification_player.png")

        browser.close()

if __name__ == "__main__":
    verify_player_ui()
