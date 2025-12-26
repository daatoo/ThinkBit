from playwright.sync_api import sync_playwright, expect
import json
import time

def test_seekbar_segments_audio():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Create a new context with a larger viewport for better screenshots
        context = browser.new_context(viewport={"width": 1280, "height": 1024})
        page = context.new_page()

        # Mock Media Object - AUDIO TYPE
        mock_media = {
            "id": 124,
            "input_path": "test_audio.mp3",
            "output_path": "test_audio_censored.mp3",
            "input_type": "audio",
            "filter_audio": True,
            "filter_video": False,
            "status": "done",
            "progress": 100,
            "current_activity": "Done",
            "logs": [],
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:01:00Z",
            "segments": [
                {
                    "id": 1,
                    "start_ms": 10000,
                    "end_ms": 20000,
                    "action_type": "mute",
                    "reason": "Profanity"
                },
                {
                    "id": 2,
                    "start_ms": 30000,
                    "end_ms": 40000,
                    "action_type": "blur", # Should be ignored in audio mode
                    "reason": "Visual"
                }
            ]
        }

        # 1. Mock API Responses
        page.route("**/*.{png,jpg,jpeg,svg,woff,woff2}", lambda route: route.abort())
        page.route("**/api/process?*", lambda route: route.fulfill(
             status=200, content_type="application/json", body=json.dumps(mock_media)
        ))
        page.route("**/api/media/124", lambda route: route.fulfill(
             status=200, content_type="application/json", body=json.dumps(mock_media)
        ))
        page.route("**/api/media?*", lambda route: route.fulfill(
             status=200, content_type="application/json", body=json.dumps({"items": [], "total": 0, "skip": 0, "limit": 10})
        ))
        page.route("**/api/outputs/files", lambda route: route.fulfill(
             status=200, content_type="application/json", body=json.dumps([])
        ))
        page.route("**/api/download/**", lambda route: route.fulfill(
             status=200, content_type="audio/mpeg", body=b""
        ))

        # 2. Go to page
        print("Navigating...")
        page.goto("http://localhost:3000")

        # 3. Open Dialog
        print("Opening upload dialog...")
        # Click "Audio" select mode button (first one)
        buttons = page.get_by_role("button", name="Select Mode").all()
        if len(buttons) >= 1:
             print("Clicking Audio select mode button...")
             buttons[0].click()
        else:
             print("Buttons not found")
             return

        # 4. Click "Audio File → Clean Audio"
        print("Selecting Audio Filter...")
        page.get_by_text("Audio File → Clean Audio").click()

        # Dialog should be open.
        expect(page.locator("text=Upload Content")).to_be_visible()

        # 5. Upload a File
        print("Uploading file...")
        page.set_input_files('input[type="file"]', {
            "name": "test_audio.mp3",
            "mimeType": "audio/mpeg",
            "buffer": b"fake audio content"
        })

        # 6. Click "Start Processing"
        print("Starting processing...")
        page.get_by_text("Start Processing").click()

        # 7. Wait for "Processing Complete"
        print("Waiting for preview...")
        expect(page.locator("p.font-semibold.text-foreground", has_text="Processing Complete")).to_be_visible(timeout=10000)

        # 8. Check Player
        print("Checking player...")
        # In Audio mode, CustomPlayer renders a div with a visualizer and an <audio> tag.
        # The <audio> tag might be hidden or just present.
        # Use state="attached" to find it regardless of visibility, or search for the visualizer container.

        page.wait_for_selector("audio", state="attached", timeout=5000)

        # Inject metadata
        page.evaluate("""
            const a = document.querySelector('audio');
            if(a) {
                Object.defineProperty(a, 'duration', { get: () => 60 });
                a.dispatchEvent(new Event('loadedmetadata'));
                a.dispatchEvent(new Event('timeupdate'));
            }
        """)

        time.sleep(1)

        print("Taking screenshot...")
        custom_player = page.locator(".relative.group.overflow-hidden.rounded-xl.bg-black")
        custom_player.screenshot(path="verification/seekbar_segments_audio_upload.png")

        browser.close()
        print("Done.")

if __name__ == "__main__":
    test_seekbar_segments_audio()
