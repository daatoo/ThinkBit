# AegisAI

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

## Setup
See [`docs/setup.md`](./docs/setup.md)

## Frontend
https://github.com/NW0RK/safestream-ui

## Marketing

<img width="320px" alt="AEGIS st george" src="https://github.com/user-attachments/assets/138c781f-cd42-41ee-8634-bd18bd0f5aab" />
<img width="320px" alt="King witnessing the revelation" src="https://github.com/user-attachments/assets/5e5a0c84-9f56-4cce-a8df-a0c1df54d0b1" />
<img width="320px" alt="Pirosmani Aegis" src="https://github.com/user-attachments/assets/a5bbd66b-638a-4442-a6b6-3cde6b2c4204" />

