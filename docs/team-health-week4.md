# Team Health - Week 4

<!-- To be filled in -->

# gaps:
Architecture Analysis: Aegis AI Video Censoring Platform
Current Stack Review
Frontend: React + Vite (Lovable hosted)
Backend: Flask REST API (external hosting needed)
Queue: RabbitMQ + Celery workers
Video Processing: FFmpeg
AI Detection: Google Vision API
Cache: Redis
DB: PostgreSQL
Storage: S3/Cloud Storage
1. SCALABILITY RISKS
Critical Bottlenecks:
Component	Risk	Impact	Fix
FFmpeg Processing	CPU-bound, blocks workers	High	Move to GPU instances (AWS EC2 P3) or dedicated transcoding service (AWS MediaConvert)
Google Vision API	Rate limits (1800 req/min free tier)	Critical	Implement request batching (10 frames/request), upgrade to paid tier, add fallback model
RabbitMQ Single Instance	SPOF, memory limits at scale	High	RabbitMQ cluster (3 nodes min) + durable queues + dead-letter exchanges
Celery Workers	No autoscaling, fixed pool	Medium	Kubernetes HPA based on queue depth or AWS ECS Fargate with target tracking
PostgreSQL	Write contention on metadata tables	Medium	Read replicas + pgBouncer connection pooling
Recommended Architecture Changes:
┌─────────────────────────────────────────────────────────────┐
│ INGRESS (Load Balancer)                                      │
│  ├─ Rate Limiting: 100 req/min per IP                       │
│  ├─ WAF: Block suspicious uploads                           │
│  └─ CloudFront CDN for frontend assets                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ FLASK API (Stateless, 3+ instances)                         │
│  ├─ Upload endpoint → pre-signed S3 URLs (bypass API)       │
│  ├─ Status endpoint → Redis cache (not DB)                  │
│  └─ Results endpoint → CloudFront signed URLs               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ MESSAGE QUEUE (RabbitMQ Cluster OR AWS SQS)                 │
│  ├─ Priority queues: [realtime, batch, export]              │
│  ├─ DLQ for failed jobs (retry 3x with backoff)            │
│  └─ Max message size: 256KB (metadata only, not frames)     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ CELERY WORKERS (Auto-scaling 2-20 instances)                │
│  ├─ Frame Extractor (CPU-optimized, c5.2xlarge)            │
│  ├─ AI Detector (GPU-optional, g4dn.xlarge for local model)│
│  └─ Video Compositor (GPU-required for real-time blur)      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ EXTERNAL SERVICES                                            │
│  ├─ Google Vision API (quota: 10k req/day → $1.50/1k after)│
│  ├─ S3 Storage (lifecycle: delete after 30 days)           │
│  └─ CloudWatch Logs + Datadog APM                           │
└─────────────────────────────────────────────────────────────┘
Tradeoff:

Simpler: Stick with single RabbitMQ + 4 fixed Celery workers → Works for <100 users
Scalable: Kubernetes + AWS SQS + Lambda for frame extraction → Costs $200-500/mo baseline
2. LATENCY BUDGET (60s Target for 5min Video)
Hop	Budget	Current Estimate	Optimization
Upload (client → S3)	10s	15s (10MB @ 1MB/s)	Pre-signed POST URLs, multipart upload, resume on failure
Frame Extraction	15s	30s (FFmpeg @ 1fps = 300 frames)	Use hardware acceleration (-hwaccel cuda), reduce to 0.5fps
AI Detection	20s	45s (300 API calls @ 150ms each)	Batch 10 frames per request (3s), parallel workers (5 concurrent = 6s)
Video Reconstruction	10s	20s (FFmpeg compose with blur filters)	Pre-render blur overlays, use GPU encoding (-c:v h264_nvenc)
Export (S3 upload)	5s	8s	Direct S3 multipart upload from worker, skip API hop
Critical Path: 60s total → Achievable with optimizations above

Failure Mode: If latency >90s, show user progress bar + email notification when done.

3. SECURITY / AUTHN / AUTHZ BOUNDARIES
Current Gaps:
Layer	Risk	Fix
No Authentication	Anyone can upload videos, DoS attack vector	Add JWT-based auth (Lovable Cloud or Auth0)
No Rate Limiting	API abuse, cost explosion	Redis-based rate limiter: 10 uploads/hour per user
Unvalidated Uploads	Malicious file uploads (ZIP bombs, scripts)	Validate MIME type server-side, scan with ClamAV
Public S3 Buckets	Data leaks	Pre-signed URLs with 1-hour expiry, block public access
No RBAC	All users can see all videos	User-scoped queries: WHERE user_id = current_user
API Keys in Code	Google Vision key leak	Store in env vars (GOOGLE_APPLICATION_CREDENTIALS), rotate monthly
Recommended Security Architecture:
┌─────────────────────────────────────────────────────────────┐
│ AUTH LAYER (Lovable Cloud / Auth0)                          │
│  ├─ JWT with 15min expiry                                   │
│  ├─ Refresh tokens (7 days)                                 │
│  └─ Roles: [free_user, pro_user, admin]                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ FLASK API MIDDLEWARE                                         │
│  ├─ JWT validation on every request                         │
│  ├─ Rate limiting: 10 req/min (free), 100 req/min (pro)    │
│  ├─ File validation: Max 500MB, MP4/WebM only              │
│  └─ CORS: Only lovable.app domain                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ DATABASE (PostgreSQL with RLS)                               │
│  ├─ videos table: user_id (indexed), video_url (encrypted) │
│  ├─ RLS policy: SELECT WHERE user_id = current_user_id()   │
│  └─ Audit log: created_at, accessed_at, ip_address          │
└─────────────────────────────────────────────────────────────┘
Tradeoff:

Fast MVP: Skip auth, use API keys hardcoded → Ship in 2 weeks but insecure
Production: Full JWT + RBAC + audit logs → Add 1 week dev time
4. FAILURE MODES + FALLBACKS
Failure	Impact	Detection	Mitigation
Google Vision API down	All detection stops	Health check every 30s	Fallback to local NSFW model (NudeNet), queue jobs for retry
FFmpeg crash (corrupted video)	Worker stuck, queue backup	Celery timeout (60s), worker restart	Validate video with ffprobe before processing, log to DLQ
RabbitMQ out of memory	New jobs rejected	CloudWatch alarm on memory >80%	Auto-scaling (more nodes) or switch to AWS SQS (unlimited)
S3 upload fails	User sees "processing" forever	Check S3 PutObject response	Retry 3x with exponential backoff (2s, 4s, 8s), email user on final failure
DB connection pool exhausted	API returns 500	pgBouncer metrics	Increase pool size (20 → 50), add read replicas
Worker node crash	In-progress jobs lost	Celery acks after job done	Set task_acks_late=True, persist tasks in DB
Circuit Breaker Pattern:


# In Flask API
if google_vision_api_errors > 5 in last_60s:
    return {"status": "degraded", "message": "Using fallback model"}
    celery_task.apply_async(queue="fallback_queue")  # Local NSFW model
5. OBSERVABILITY
Logs (Structured JSON):

{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "INFO",
  "service": "frame-extractor",
  "trace_id": "abc123",
  "user_id": "usr_456",
  "video_id": "vid_789",
  "event": "frame_extraction_complete",
  "duration_ms": 1200,
  "frame_count": 300
}
Tools: CloudWatch Logs Insights or Datadog Logs

Metrics (Prometheus + Grafana):
Throughput: Videos processed per hour
Latency: P50/P95/P99 for each pipeline stage
Queue Depth: RabbitMQ message count (alert if >1000)
Error Rate: Failed jobs per minute
Cost: Google Vision API spend per day
Traces (Distributed Tracing):
Use OpenTelemetry to trace: upload → extract → detect → compose → export
Tools: AWS X-Ray or Datadog APM
Alerting Rules:

alerts:
  - name: HighErrorRate
    condition: error_rate > 5% for 5 minutes
    action: PagerDuty notification
  - name: QueueBacklog
    condition: rabbitmq_messages > 500
    action: Auto-scale Celery workers
  - name: APIQuotaExceeded
    condition: google_vision_quota_remaining < 100
    action: Slack notification + switch to fallback
6. DATA RETENTION & PRIVACY
Data Type	Retention	Reason	Implementation
Original Videos	7 days	User re-processing	S3 lifecycle policy: Delete after 7 days
Processed Videos	30 days (free), 1 year (pro)	User downloads	Separate S3 bucket with versioning
Detection Metadata	90 days	Model retraining	PostgreSQL with auto-vacuum
Audit Logs	1 year	Compliance	Append-only table, archived to S3 Glacier
User PII	Forever (GDPR right to delete)	Legal requirement	Encryption at rest + "Delete Account" feature
GDPR Compliance:

Data Minimization: Don't store video frames, only timestamps
Right to Access: API endpoint: GET /user/data-export → ZIP file
Right to Erasure: Soft delete videos, hard delete after 30 days
Consent: Explicit checkbox: "I consent to AI analysis of my videos"
Tradeoff:

Simple: Never delete data → Cheaper storage but legal risk
Compliant: Auto-delete + GDPR features → Add 3 days dev time
7. RAG SPECIFICS (If Adding Knowledge Base for Censorship Rules)
Use Case: Custom Censorship Knowledge Base
Example: "Censor all scenes with [brand logo X]" or "Detect custom gang symbols"

Architecture:
┌─────────────────────────────────────────────────────────────┐
│ DOCUMENT INGESTION PIPELINE                                  │
│  ├─ User uploads PDF (censorship guidelines)                │
│  ├─ Parse with PyPDF2 or Unstructured.io                    │
│  ├─ Chunk: 500 tokens with 50-token overlap                 │
│  └─ Store in PostgreSQL `knowledge_base` table              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ EMBEDDING GENERATION                                         │
│  ├─ Model: OpenAI text-embedding-3-small (1536 dims)       │
│  ├─ Cost: $0.02 per 1M tokens                               │
│  └─ Store embeddings in pgvector extension                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ RETRIEVAL (During Video Processing)                         │
│  1. User query: "Censor scenes with violence"               │
│  2. Embed query with same model                             │
│  3. Cosine similarity search: top-k=5 chunks                │
│  4. Rerank with Cohere Rerank API (optional)                │
│  5. Pass to LLM: "Based on these rules, flag this frame?"   │
└─────────────────────────────────────────────────────────────┘
RAG Configuration:
Parameter	Value	Rationale
Chunk Size	500 tokens	Balance context vs. precision
Overlap	50 tokens	Avoid splitting key sentences
Top-K	5 chunks	Enough context without noise
Similarity Threshold	0.75	Filter irrelevant results
Reranking	Cohere Rerank v3	Improves relevance by 20-30%
Citation Format	[Source: doc_id, page 3]	Transparency for users
Embeddings Storage (pgvector):

CREATE EXTENSION vector;

CREATE TABLE knowledge_chunks (
  id SERIAL PRIMARY KEY,
  user_id UUID,
  content TEXT,
  embedding VECTOR(1536),
  metadata JSONB  -- {doc_name, page_num, upload_date}
);

CREATE INDEX ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops);
Query Example:


SELECT content, metadata
FROM knowledge_chunks
WHERE user_id = 'usr_456'
ORDER BY embedding <=> '[query_embedding_here]'
LIMIT 5;
Tradeoffs:
Simple: Keyword search on censorship rules → Fast but misses context
RAG: Semantic search with embeddings → Better accuracy, adds 5-10ms latency
SUMMARY: TOP 5 CRITICAL FIXES
Priority	Fix	Impact	Effort
🔴 P0	Add authentication (JWT)	Prevents abuse, enables billing	2 days
🔴 P0	Batch Google Vision API calls	Reduces latency by 90%	1 day
🟠 P1	Implement rate limiting	Stops DoS, controls costs	1 day
🟠 P1	Add circuit breaker for API failures	Graceful degradation	1 day
🟡 P2	Set up CloudWatch metrics + alarms	Catch issues before users complain	2 days
Total Time to Production-Ready: ~1-2 weeks