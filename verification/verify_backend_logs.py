from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the backend logs page
        print("Navigating to http://localhost:3000/backend")
        page.goto("http://localhost:3000/backend")

        # Wait for logs to load (they might say "Loading..." initially or show logs)
        # We wait for the specific header "System Logs"
        page.wait_for_selector("h1:has-text('System Logs')")

        # Take a screenshot
        page.screenshot(path="verification/backend_logs.png")
        print("Screenshot saved to verification/backend_logs.png")

        browser.close()

if __name__ == "__main__":
    run()
