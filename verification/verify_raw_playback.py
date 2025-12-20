from playwright.sync_api import sync_playwright, expect
import time

def verify_raw_playback():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Navigate to the app
        page.goto("http://localhost:3000")

        # Scroll to Raw Outputs section
        # Wait for the file list to load (polling is 10s, but we expect initial load)
        raw_section = page.locator("#raw-outputs")
        expect(raw_section).to_be_visible(timeout=10000)

        # We need to make sure there is at least one file.
        # If there are no files, we can't test.
        # Ideally, we should have uploaded a file previously or mocked the backend.
        # But let's assume the environment might have some files or we just verify the section structure.

        # Try to find a file item
        file_item = page.locator("#raw-outputs .grid > div").first

        if file_item.count() > 0:
            print("Found file item, clicking...")
            filename = file_item.locator("p").first.text_content()
            print(f"File: {filename}")

            file_item.click()

            # Wait for dialog
            dialog = page.locator("div[role='dialog']")
            expect(dialog).to_be_visible()

            # Check title matches filename
            expect(dialog.locator("h2")).to_contain_text(filename)

            # Check player exists
            # Video or Audio element
            video = dialog.locator("video")
            audio = dialog.locator("audio")

            # One of them should be present (though 'audio' might be wrapped in visualizer)
            # CustomPlayer puts <video> or <audio> in the DOM.

            if video.count() > 0 or audio.count() > 0:
                print("Player element found.")
            else:
                print("Player element NOT found.")
                # Maybe it's inside the visualizer div structure?

            time.sleep(2) # Wait for player to potentially load/render

            page.screenshot(path="/home/jules/verification/raw_playback_modal.png")
            print("Screenshot taken.")

        else:
            print("No raw files found. Cannot verify playback.")
            page.screenshot(path="/home/jules/verification/raw_outputs_empty.png")

        browser.close()

if __name__ == "__main__":
    verify_raw_playback()
