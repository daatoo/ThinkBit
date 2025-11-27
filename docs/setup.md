# Setup Instructions

## Prerequisites
- Python 3.11+
- Node.js 18+
- Git
- FFmpeg 6.x (must be available on the system PATH)

### Installing FFmpeg

- **macOS (Homebrew):** `brew install ffmpeg`
- **Ubuntu/Debian:** `sudo apt-get install ffmpeg`
- **Windows:** Download the latest release from [ffmpeg.org](https://ffmpeg.org/download.html), extract it, and add the `bin` directory to the `PATH`.

### Google Cloud Vision (SafeSearch)

1. Enable the **Vision API** in your Google Cloud project.
2. Create a service account with the `roles/vision.user` permission and download its JSON key.
3. Store the key somewhere secure (e.g., `infra/keys/aegisai-vision.json`) and set `GOOGLE_APPLICATION_CREDENTIALS` to that path before running the backend:
   ```powershell
   setx GOOGLE_APPLICATION_CREDENTIALS "C:\path\to\aegisai-vision.json"
   ```
   On macOS/Linux use `export GOOGLE_APPLICATION_CREDENTIALS=/path/to/aegisai-vision.json`.

## Installation
```bash
git clone https://github.com/team-name/project-name
cd project-name
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cd src/frontend && npm install