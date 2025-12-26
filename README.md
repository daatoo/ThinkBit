# AegisAI
<img width="2080" height="2048" alt="Gemini_Generated_Image_xe47osxe47osxe47" src="https://github.com/user-attachments/assets/3e50e635-d531-4c52-8d35-f4e6e1e94a1e" />

## Various Links

* Talking Head Demo: [https://drive.google.com/file/d/1jWHam4yYNegbHlylAU9U7OhFNFKQYu8E/view?usp=sharing](https://drive.google.com/file/d/1jWHam4yYNegbHlylAU9U7OhFNFKQYu8E/view?usp=drive_link)
* Corpo AD: [(https://drive.google.com/file/d/1rqE_tggE8wSom52_TNcpWHyJgDgX9ET8/view?usp=sharing](https://drive.google.com/file/d/1rqE_tggE8wSom52_TNcpWHyJgDgX9ET8/view?usp=drive_link)
* Presentation Slides: https://docs.google.com/presentation/d/15p_5xFzWq16Kmwi1_kcNPC2Wq4vW8rqwfkKQqdYZwyo/edit?usp=sharing


## Problem Statement
Manually censoring inappropriate content in video and audio for different audiences is a time-consuming, costly, and inconsistent process. Parents lack effective, customizable tools to filter content for their children in real-time, while television studios and content creators face significant overhead in producing multiple versions of content for various broadcasting standards. An AI-powered system is required to automatically detect and censor user-defined improper content (e.g., profanity, graphic violence) in video streams, providing a reliable, efficient, and customizable solution.


## Team
| Name | Role | Email | GitHub |
|------|------|--------|--------|
| Davit Cheishvili | Documentation & QA Lead | Cheishvili.Davit@kiu.edu.ge | [@daatoo](https://github.com/daatoo) |
| Nikoloz Modebadze | Project Manager / Coordinator | Modebadze.Nikoloz@kiu.edu.ge | [@NW0RK](https://github.com/NW0RK) |
| Juli Chaphidze | Frontend Developer | Chaphidze.Juli@kiu.edu.ge | [@Juliieett](https://github.com/Juliieett)|
| Sandro Iobidze | Backend Developer | Iobidze.Sandro@kiu.edu.ge | [@P4ndro](https://github.com/P4ndro) |

## Overview
The project, **AegisAI**, is an **AI-powered video censoring platform** designed to automatically detect and filter inappropriate content (like profanity and graphic violence) in video streams.

AI is used to achieve the efficiency, speed, and customization that manual censorship lacks. Specifically, the system utilizes:
* **Speech-to-Text (STT) models** (e.g., OpenAI's Whisper) to transcribe audio and detect profane language with precise timestamps for muting.
* **Computer Vision (CV) models** (e.g., Google Vision API) to analyze video frames and identify prohibited visual content like graphic violence or nudity for subsequent blurring or pixelation.

## Tech Stack
- **Frontend:** React (Next.js)
- **Backend:** FastAPI
- **AI:** OpenAI GPT-4o API
- **Database:** PostgreSQL + pgvector
- **Deployment:** Render / Vercel
- **Computer Vision:** Google Cloud Vision SafeSearch for frame triage

## Computer Vision Modules
- `aegisai.vision.safe_search.GoogleSafeSearchClient` wraps the Vision API for SafeSearch detection. Inject raw frame bytes or a `gs://` URI and it returns normalized likelihood scores across adult, spoof, medical, violence, and racy categories. Consumers can call `SafeSearchCategoryScores.exceeds(...)` to gate downstream censoring flows.

## Optimization Notes (Lab 9)

### Text Moderation Optimization
- **Top-k blocklist selection:** Reduces blocklist from 200+ words to top-20 relevant words per transcript
- **Blocklist deduplication:** Removes near-duplicate profanity variants
- **Prompt reduction:** System prompt reduced from 80 → 15 tokens
- **Results:** 80.19% cost reduction, precision/recall maintained at 95.3%/97.6%
- **Implementation:** See `src/aegisai/moderation/optimization.py`
- **Evaluation:** Run `python scripts/optimization_eval.py` for metrics

### Planned Optimizations (Week 11+)
- **Google Vision API batching:** Batch 10 frames per request (90% cost/latency reduction)
- **Frame result caching:** Cache identical frames (12-15% additional savings)
- **See:** `optimization-report.md` for full details

### Cost/Latency Tracking
- Cost and latency metrics are logged during processing
- Evaluation script tracks: tokens/request, cost, p95 latency, precision, recall
- See `scripts/optimization_eval.py` for example implementation

## Setup
See [`docs/setup.md`](./docs/setup.md)

### Quick Start
To set up the environment and run both backend and frontend:
```bash
./start_app.sh
```
This script will:
- Check for `ffmpeg`
- Create a python virtual environment and install dependencies
- Start the backend server
- Install frontend dependencies and start the frontend development server

## Frontend
- https://github.com/NW0RK/safestream-ui
- https://prototype-aegis-ai.lovable.app
## Marketing

<img width="320px" alt="AEGIS st george" src="https://github.com/user-attachments/assets/138c781f-cd42-41ee-8634-bd18bd0f5aab" />
<img width="320px" alt="King witnessing the revelation" src="https://github.com/user-attachments/assets/5e5a0c84-9f56-4cce-a8df-a0c1df54d0b1" />
<img width="320px" alt="Pirosmani Aegis" src="https://github.com/user-attachments/assets/a5bbd66b-638a-4442-a6b6-3cde6b2c4204" />
<img width="320px" alt="Gemini_Generated_Image_bl6nxqbl6nxqbl6n" src="https://github.com/user-attachments/assets/35f60afa-4d1a-40fe-92ac-31c8ae1ef9a5" />
<img width="320px" alt="Gemini_Generated_Image_bl6nxqbl6nxqbl6n" src="https://github.com/user-attachments/assets/e6d641b4-4bde-49b0-a134-1c16bff21be1" />
<img width="320px" alt="Gemini_Generated_Image_bl6nxqbl6nxqbl6n" src="https://github.com/user-attachments/assets/946bced7-7fac-4883-8329-6569e0eda6b1" />




