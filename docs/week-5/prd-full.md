# PRD - Product Requirements Document

<!-- TODO: Complete PRD -->

#  Aegis AI – Video Censoring Platform
**Production-Ready Project Requirements Document (PRD)**  
_Lab 5 | Building AI-Powered Applications | ThinkBit Repository_

---

## 1. Project Goal & Problem Statement
**Goal:**  
Automatically detect, classify, and censor inappropriate video/audio content (profanity, violence, nudity) using AI models and GPU-accelerated media processing.

**Problem Solved:**  
Manual censorship is slow, inconsistent, and expensive. Aegis AI automates this process, enabling parents and studios to instantly create audience-safe versions of media.

---

## 2. MVP Scope & Boundaries

### ✅ In Scope
- Video upload → async job queue → AI detection → censor → export  
- Profanity detection via OpenAI Whisper API  
- Visual violence detection via Google Vision API + fallback NudeNet  
- Preset profiles (Kids / Teen / Studio)  
- Custom keyword blocklist editor  
- Processing queue UI with progress  
- Export to S3 → CloudFront download  

### 🚫 Out of Scope
- Browser extensions  
- Real-time stream filtering  
- Manual annotation workbench  
- RAG content explanation (chat-style interface) — post-MVP  

---

## 3. Target Users
| Segment | Description | Use Case |
|----------|--------------|----------|
| **Parents** | Protect children from explicit media | Upload → Kids Mode → Safe download |
| **Studios / Broadcasters** | Automate compliant regional versions | Batch upload → FCC preset → Export |

---

## 4. Technology Stack
| Category | Technology | Version | Notes |
|-----------|-------------|----------|--------|
| Language | Python | 3.11.4 | Backend core |
| Backend Framework | Flask | 2.3.2 | REST API |
| Workers | Celery | 5.3.6 | Async orchestration |
| Queue | RabbitMQ | 3.12+ | Message broker |
| Database | PostgreSQL | 15.3 | pgvector enabled |
| Cache | Redis | 7.0 | Caching + Celery backend |
| Frontend Framework | React + Vite | React 18.2.0 / Vite 5.2.0 | SPA frontend |
| UI Library | TailwindCSS | 3.3.3 | Consistent styling |
| Storage | AWS S3 | N/A | Video & asset storage |
| CDN | CloudFront | N/A | Global delivery |
| AI APIs | Google Vision, OpenAI Whisper | Latest | Detection & STT |
| Video Processing | FFmpeg | 6.0 | GPU acceleration |
| Monitoring | Prometheus + Grafana + CloudWatch | Latest | Observability stack |
| Deployment | AWS ECS | N/A | Containerized deployment |
| Testing (Unit) | pytest | 7.4.4 | Backend tests |
| Testing (E2E) | Cypress | 12.17.0 | UI tests |
| Version Control | Git + GitHub | N/A | Repo: [ThinkBit](https://github.com/Juliieett/ThinkBit) |

---

## 5. Architecture
**Pattern:** Microservices + asynchronous queue-based processing.  
**Style:** REST API with async workers; observability via OpenTelemetry.

```mermaid
flowchart TD
    A[User (Web App)] -->|Upload Video| B[Frontend (React + Vite)]
    B -->|REST API| C[Flask API Server]
    C -->|Auth + Task Enqueue| D[(RabbitMQ Cluster)]
    D --> E1[Celery Worker - Frame Extractor]
    D --> E2[Celery Worker - AI Detector]
    D --> E3[Celery Worker - Video Compositor]
    E2 -->|Vision API + Whisper| F[External AI Services]
    E3 -->|GPU Encode| G[S3 Video Storage]
    C --> H[(PostgreSQL DB)]
    C --> I[(Redis Cache)]
    G --> J[User Download (CloudFront CDN)]
    C --> K[(Prometheus + Grafana + CloudWatch)] ```
#
6. Core Modules
Module	Description	Key Interfaces
Frontend (React)	Uploads videos, shows timeline, manages profiles	/upload, /process/:id
API (Flask)	Auth, validation, enqueue jobs	POST /api/jobs, GET /api/status/:id
Workers (Celery)	Frame extraction, AI calls, censor rebuild	tasks.extract_frames, tasks.detect, tasks.compose
Queue (RabbitMQ)	Priority routing, DLQ	jobs.*
Data (PostgreSQL)	Users, profiles, detections	/migrations/schema.sql
Cache (Redis)	Detection cache, rate limit	cache:frames:*
Storage (S3)	Video files	Pre-signed URLs
Observability	Metrics + logs	Prometheus dashboards
7. RAG / Knowledge Retrieval Strategy

Sources: embeddings of detections, user feedback, keyword sets

Store: PostgreSQL pgvector column (vector(768))

Retriever: cosine similarity > 0.8

Purpose: dynamic threshold tuning + context recall for AI calls

8. Core AI Functions (Structured Outputs)
🧠 Function 1 — detect_profanity_audio

Transcribe video audio and timestamp profane words.

Input Model

class AudioDetectionInput(BaseModel):
    video_url: HttpUrl
    language: str = "en"
    custom_keywords: list[str] = []


Output Model

class AudioDetectionOutput(BaseModel):
    detections: list[dict]
    profanity_score: float


JSON Schema

{
  "name": "detect_profanity_audio",
  "description": "Transcribe video audio and locate profane words with timestamps",
  "parameters": {
    "type": "object",
    "properties": {
      "video_url": {"type": "string", "format": "uri"},
      "language": {"type": "string"},
      "custom_keywords": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["video_url"]
  }
}

🧩 Function 2 — detect_violence_frames

Detect violent or graphic scenes in frames.

Input

class VisualDetectionInput(BaseModel):
    frame_urls: list[HttpUrl]
    threshold: float = 0.7


Output

class VisualDetectionOutput(BaseModel):
    flagged_frames: list[int]
    avg_confidence: float

⚙️ Function 3 — compose_censored_video

Merge original video with mute/blur operations.

Input

class VideoComposeInput(BaseModel):
    source_video: HttpUrl
    mutes: list[tuple[float, float]]
    blurs: list[tuple[float, float]]
    blur_strength: int = 15


Output

class VideoComposeOutput(BaseModel):
    output_url: HttpUrl
    processing_time: float
    size_mb: float

9. UI / UX Standards

Minimal, distraction-free layout

Timeline color codes: 🔇 red = mute, ⚠️ yellow = blur

Responsive ≤ 1280 px

Accessible contrast (WCAG AA)

Visible progress + ETA

10. Coding & Quality Requirements

Lint: Ruff + ESLint

Format: Black + Prettier

CI Checks: MyPy + Bandit + pytest

Docstrings: required for all functions

Quality Focus: Reliability • Testability • Security • Maintainability • Performance

Reliability Targets:

Uptime ≥ 99.5 %

Precision ≥ 95 %

Recall ≥ 90 %

11. Testing Plan
Level	Tool	Goal	Coverage
Unit	pytest	Module correctness	≥ 80 %
Integration	pytest + Redis mock	API flow	✅
UI E2E	Cypress	Upload → Export	✅
Performance	Locust	P95 latency	✅

CI: GitHub Actions → run tests before merge.

12. Setup & Installation
git clone https://github.com/Juliieett/ThinkBit
cd ThinkBit
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # add API keys
cd frontend
npm install && npm run dev
docker-compose up -d    # local services

13. Architectural Decisions
Decision	Rationale
Flask > FastAPI	Familiarity, plugin ecosystem
RabbitMQ > SQS	Full control, priority queues
PostgreSQL + pgvector	Relational + vector search
Google Vision + Whisper	Accuracy + fallback models
Circuit Breaker pattern	API-failure resilience
14. Documentation Structure
/docs
 ├─ prd-full.md
 ├─ api.md
 ├─ architecture-diagram-v2.md
 ├─ development.md
 ├─ user-guide.md
 ├─ risk-assessment.md
 ├─ evaluation-plan-v2.md
 └─ cost-model-v2.md

15. Repository

🔗 https://github.com/Juliieett/ThinkBit

16. Dependencies & External Services
Service	Purpose	Keys / Limits
Google Vision API	Violence, nudity detection	Key · 1800 req/min
OpenAI Whisper	Profanity STT	Key · $0.006 / min
AWS S3 / CloudFront	Storage & CDN	IAM · $0.023 / GB
Redis (ElastiCache)	Cache	~$15 / month
RabbitMQ	Queue	Self-hosted
Prometheus + Grafana + CloudWatch	Monitoring	Free tier

.env keys:
OPENAI_KEY, GOOGLE_VISION_KEY, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

17. Security Model

Auth: JWT (Auth0 / Lovable Cloud)

RBAC: user / pro_user / admin

Protection: AES-256 S3, TLS 1.3, RLS in Postgres

Mitigation: file validation, rate limit, param queries

Risks: XSS, CSRF, SQL Injection, Prompt Injection

Compliance: GDPR (delete, export, consent)

18. Deployment & DevOps
Stage	Stack	Actions
Dev	Docker Compose	Local test
Staging	AWS ECS dev cluster	Auto-deploy on dev
Prod	AWS ECS + CloudFront	Manual approval
CI/CD	GitHub Actions	lint → test → build → deploy
Monitoring	Prometheus + Grafana + CloudWatch	Alerts
Backup	RDS snapshots + S3 Glacier	Nightly
Disaster Recovery	DLQ replay + Multi-AZ	< 1 h RTO
-->
