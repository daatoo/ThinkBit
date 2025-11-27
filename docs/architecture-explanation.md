# Architecture Explanation

> **Note:** The architecture diagram is available in `docs/architecture-diagram-v2.md` as a Mermaid diagram. To generate `architecture-v2.png`, use:
> - Mermaid Live Editor: https://mermaid.live/ (paste the diagram code and export as PNG)
> - mermaid-cli: `mmdc -i docs/architecture-diagram-v2.md -o docs/architecture-v2.png`
> - Or use any Mermaid renderer tool

## What Changed Since Week 2

### Week 2 (Initial Proposal)
- **Simple monolithic architecture:** Single Flask server handling all processing
- **No authentication:** Direct API access without security
- **Synchronous processing:** Blocking operations, no queue system
- **Direct AI API calls:** No batching or fallback mechanisms
- **No observability:** Basic logging only
- **Single worker model:** No scalability considerations

### Week 4 (Current Architecture)
- **Microservices architecture:** Separated frontend (React), API (Flask), workers (Celery), and queue (RabbitMQ)
- **Authentication layer:** JWT-based auth with Lovable Cloud/Auth0 integration
- **Asynchronous processing:** RabbitMQ queue with Celery workers for parallel processing
- **Batched AI calls:** Google Vision API batching (10 frames/request) to reduce latency by 90%
- **Circuit breaker pattern:** Fallback to local NSFW model (NudeNet) when Google Vision fails
- **Observability:** CloudWatch/Datadog metrics, structured logging, distributed tracing
- **Auto-scaling:** Kubernetes HPA or AWS ECS Fargate for worker scaling
- **Security hardening:** Rate limiting, file validation, pre-signed S3 URLs, RBAC
- **Data retention policies:** S3 lifecycle policies, GDPR compliance features

---

## Tech Choices & Tradeoffs

### Frontend: React + Vite (Lovable Hosted)
**Choice:** React 18+ with Vite build tool, hosted on Lovable Cloud  
**Why:** Fast development, hot reload, modern tooling, easy deployment  
**Tradeoff:** 
- ✅ Fast iteration, great DX
- ❌ Vendor lock-in to Lovable platform (consider migration path later)

### Backend: Flask REST API (Python 3.11+)
**Choice:** Flask over FastAPI  
**Why:** Team familiarity, simpler learning curve, sufficient for REST endpoints  
**Tradeoff:**
- ✅ Easier onboarding for team
- ❌ FastAPI has better async support and auto-docs (not critical for MVP)

### Queue: RabbitMQ Cluster (3 nodes)
**Choice:** RabbitMQ over AWS SQS  
**Why:** Better control, no vendor lock-in, durable queues with DLQ  
**Tradeoff:**
- ✅ Full control, no per-message costs
- ❌ Operational overhead (manage cluster) vs SQS (fully managed)

### Workers: Celery 5.3+ with Redis Broker
**Choice:** Celery for distributed task processing  
**Why:** Mature Python task queue, good RabbitMQ integration  
**Tradeoff:**
- ✅ Battle-tested, extensive docs
- ❌ Requires Redis for result backend (additional dependency)

### Video Processing: FFmpeg 6.0+ with GPU Acceleration
**Choice:** FFmpeg with CUDA/NVENC hardware acceleration  
**Why:** Industry standard, supports hardware encoding/decoding  
**Tradeoff:**
- ✅ Fast processing with GPU
- ❌ Requires GPU instances (AWS EC2 P3/g4dn = $0.50-1.50/hr)

### AI Detection: Google Vision API (Primary) + NudeNet (Fallback)
**Choice:** External API over self-hosted model  
**Why:** Higher accuracy, no model training overhead, pay-per-use  
**Tradeoff:**
- ✅ Better accuracy, no GPU costs for inference
- ❌ Rate limits (1800 req/min free tier), per-request costs ($1.50/1k after free tier)
- **Fallback:** Local NudeNet model for NSFW detection when API fails

### Database: PostgreSQL 15+ with pgvector Extension
**Choice:** PostgreSQL over MongoDB  
**Why:** ACID compliance, relational data (users, videos, profiles), vector search support  
**Tradeoff:**
- ✅ Single database for relational + vector search
- ❌ More complex scaling vs NoSQL (mitigated with read replicas)

### Cache: Redis 7.0+ (Session + Queue Broker)
**Choice:** Redis for caching and Celery broker  
**Why:** Fast in-memory cache, dual-purpose (cache + queue backend)  
**Tradeoff:**
- ✅ Reduces DB load, improves latency
- ❌ Memory cost (monitor eviction policies)

### Storage: AWS S3 with Lifecycle Policies
**Choice:** S3 over local storage  
**Why:** Scalable, durable, integrates with CDN (CloudFront)  
**Tradeoff:**
- ✅ Unlimited scale, automatic backups
- ❌ Egress costs ($0.09/GB after free tier)

---

## Bottlenecks + Mitigations

### 🔴 Critical Bottleneck #1: Google Vision API Rate Limits
**Problem:** 1800 requests/minute free tier → 300 frames = 300 API calls = 10 seconds at max rate  
**Current Latency:** 45 seconds (300 calls × 150ms each)  
**Mitigation:**
- ✅ **Batch 10 frames per request** → 30 API calls → 4.5 seconds
- ✅ **Parallel workers (5 concurrent)** → 6 seconds total
- ✅ **Upgrade to paid tier** ($1.50/1k requests) for higher limits
- ✅ **Circuit breaker** switches to local NudeNet model if API errors > 5 in 60s

### 🔴 Critical Bottleneck #2: FFmpeg CPU Processing
**Problem:** Frame extraction at 1 FPS blocks CPU, no parallelism  
**Current Latency:** 30 seconds for 300 frames  
**Mitigation:**
- ✅ **GPU acceleration** (`-hwaccel cuda`) → 10-15 seconds
- ✅ **Reduce sampling rate** to 0.5 FPS → 15 seconds (acceptable for violence detection)
- ✅ **Dedicated GPU instances** (AWS EC2 g4dn.xlarge) for video workers

### 🟠 Medium Bottleneck #3: Single RabbitMQ Instance
**Problem:** SPOF (Single Point of Failure), memory limits at scale  
**Current Impact:** Queue backup if >1000 messages  
**Mitigation:**
- ✅ **RabbitMQ cluster** (3 nodes, mirrored queues)
- ✅ **DLQ (Dead Letter Queue)** for failed jobs (retry 3x with backoff)
- ✅ **Auto-scaling workers** based on queue depth (Kubernetes HPA)
- 🔄 **Alternative:** Migrate to AWS SQS (unlimited scale, fully managed)

### 🟠 Medium Bottleneck #4: Database Write Contention
**Problem:** PostgreSQL connection pool exhaustion during high load  
**Current Impact:** 500 errors if >20 concurrent uploads  
**Mitigation:**
- ✅ **Connection pooling** (pgBouncer: 20 → 50 connections)
- ✅ **Read replicas** for SELECT queries (status checks, profiles)
- ✅ **Write batching** (bulk inserts for detection metadata)

### 🟡 Minor Bottleneck #5: S3 Upload Latency
**Problem:** Large video files (10MB+) upload slowly  
**Current Latency:** 15 seconds @ 1MB/s  
**Mitigation:**
- ✅ **Pre-signed POST URLs** (direct client → S3, bypasses API)
- ✅ **Multipart upload** (parallel chunks)
- ✅ **Resume on failure** (retry logic)

---

## Latency Targets

| Stage | Target | Current (Before Optimization) | Optimized | Status |
|-------|--------|-------------------------------|-----------|--------|
| **Upload (client → S3)** | 10s | 15s | 8s (pre-signed URLs) | ✅ On track |
| **Frame Extraction** | 15s | 30s | 12s (GPU + 0.5 FPS) | ✅ On track |
| **AI Detection** | 20s | 45s | 6s (batching + parallel) | ✅ On track |
| **Video Reconstruction** | 10s | 20s | 8s (GPU encoding) | ✅ On track |
| **Export (S3 upload)** | 5s | 8s | 5s (multipart) | ✅ On track |
| **Total (5min video)** | **60s** | **118s** | **39s** | ✅ **Exceeds target** |

**Note:** For 30-second demo clips, total processing time: **<10 seconds** ✅

---

## Security Boundaries

### Authentication & Authorization
- **Auth Layer:** Lovable Cloud / Auth0
  - JWT tokens (15min expiry) + refresh tokens (7 days)
  - Roles: `free_user`, `pro_user`, `admin`
- **API Middleware:**
  - JWT validation on every request
  - Rate limiting: 10 req/min (free), 100 req/min (pro)
  - File validation: Max 500MB, MP4/WebM only
  - CORS: Only `lovable.app` domain

### Data Encryption
- **At Rest:**
  - S3 buckets: Server-side encryption (SSE-S3)
  - PostgreSQL: TDE (Transparent Data Encryption) for sensitive columns
  - Redis: AUTH password protection
- **In Transit:**
  - TLS 1.3 for all API calls (HTTPS)
  - Pre-signed S3 URLs (1-hour expiry)
  - Internal service communication: mTLS (if deployed on Kubernetes)

### Access Control
- **Database:** Row-Level Security (RLS) policies
  - `SELECT WHERE user_id = current_user_id()`
  - Users can only access their own videos/profiles
- **S3 Buckets:** Private buckets, no public access
  - Pre-signed URLs with 1-hour expiry
  - Lifecycle policies: Delete after retention period

### Failure Points & Fallbacks

| Failure Point | Detection | Mitigation | Fallback |
|----------------|-----------|------------|----------|
| **Google Vision API down** | Health check every 30s | Circuit breaker | Local NudeNet model (NSFW detection) |
| **FFmpeg crash** | Celery timeout (60s) | Validate with `ffprobe` before processing | Log to DLQ, retry 3x |
| **RabbitMQ out of memory** | CloudWatch alarm (>80% memory) | Auto-scale RabbitMQ nodes | Switch to AWS SQS |
| **S3 upload fails** | Check PutObject response | Retry 3x (exponential backoff: 2s, 4s, 8s) | Email user notification |
| **DB connection pool exhausted** | pgBouncer metrics | Increase pool (20 → 50), add read replicas | Graceful degradation (queue job) |
| **Worker node crash** | Celery `task_acks_late=True` | Persist tasks in DB | Auto-restart worker, retry job |

---

## External Dependencies

| Service | Version/Provider | Purpose | Cost Estimate |
|---------|------------------|---------|---------------|
| **Google Vision API** | v1 (Cloud Vision API) | Violence/NSFW detection | $1.50/1k requests (after free tier) |
| **OpenAI Whisper** | API v1 (or local model) | Speech-to-text transcription | $0.006/minute (API) or free (local) |
| **Redis** | 7.0+ (AWS ElastiCache) | Cache + Celery broker | ~$15/month (t3.micro) |
| **PostgreSQL** | 15+ (AWS RDS) | Relational data + pgvector | ~$30/month (db.t3.medium) |
| **AWS S3** | Standard tier | Video storage | ~$0.023/GB/month + egress |
| **RabbitMQ** | 3.12+ (CloudAMQP or self-hosted) | Message queue | ~$20/month (CloudAMQP) or free (self-hosted) |
| **CloudFront CDN** | AWS | Frontend asset delivery | ~$0.085/GB (first 10TB) |

**Total Monthly Cost (MVP):** ~$100-150/month (low traffic)  
**Total Monthly Cost (Scale):** ~$500-1000/month (1000+ users)

---

## Open Questions

### Technical
1. **Should we migrate to AWS SQS instead of RabbitMQ?**
   - ✅ Fully managed, unlimited scale
   - ❌ Vendor lock-in, per-message costs
   - **Decision:** Start with RabbitMQ, migrate if queue depth >1000 consistently

2. **Should we use OpenAI Whisper API or local model?**
   - API: Higher accuracy, lower latency, but costs $0.006/min
   - Local: Free, but requires GPU instance
   - **Decision:** Start with API, optimize to local if costs >$50/month

3. **Should we add RAG (Retrieval-Augmented Generation) for custom censorship rules?**
   - Use case: "Censor scenes with [brand logo]" or custom symbols
   - Requires: pgvector + embedding model (OpenAI text-embedding-3-small)
   - **Decision:** Defer to Week 8+ if users request custom rule uploads

4. **Should we support real-time streaming (RTMP) or batch-only?**
   - RTMP: Lower latency (<400ms target), but complex WebRTC setup
   - Batch: Simpler, current architecture supports it
   - **Decision:** MVP = batch only, add RTMP if user demand is high

### Business
5. **Should we offer browser extension for Netflix/YouTube?**
   - High effort (7+ days), requires Chrome Web Store approval
   - **Decision:** Defer to post-MVP (Week 16+)

6. **Should we charge per video or subscription model?**
   - Per video: Pay-as-you-go, but may deter users
   - Subscription: Predictable revenue, better for retention
   - **Decision:** Hybrid: Free (10 videos/month) + Paid ($9.99/month unlimited)

### Operational
7. **How do we handle GDPR "Right to Erasure" requests?**
   - Soft delete videos immediately, hard delete after 30 days
   - Export user data on request (ZIP file)
   - **Decision:** Implement Week 10+ (before public launch)

8. **Should we implement user feedback loop for model retraining?**
   - "Mark as False Positive" button → collect annotations → retrain model
   - **Decision:** Phase 2 feature (post-MVP)
