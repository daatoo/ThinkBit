# Prioritized Backlog v2 - Dependency-Aware

## Overview

This backlog contains prioritized issues for Aegis AI Video Censoring Platform MVP, organized by priority with explicit dependency chains, infrastructure items, evaluation infrastructure, and risk-reduction spikes.

**Target:** Week 15 MVP launch  
**Total Issues:** 28 (15 P1, 9 P2, 4 P3)

**Dependency Legend:**
- `→` = Depends on
- `⇒` = Blocks
- `🔄` = Risk spike / Technical validation

---

## Dependency Graph

```
Infrastructure Layer (Foundation):
#INF-1 (DB Schema) → #INF-2 (Auth) → #INF-3 (Logging) → #INF-4 (Monitoring)
                          ↓
                    All User Features

Core Processing Pipeline:
#1 (Upload) → #2 (Player) → #4 (Timeline)
#1 (Upload) → #3 (Profanity) → #4 (Timeline) → #8 (Export)
#1 (Upload) → #6 (Violence) → #4 (Timeline) → #8 (Export)

User Features:
#5 (Kids Mode) → #11 (Profiles) → #12 (Custom Keywords)
#9 (Queue UI) → #8 (Export)
```

---

## P1: Critical Path / MVP (Weeks 4-12)

### Infrastructure Layer (Foundation)

#### Issue #INF-1: Database Schema & Migrations
**Priority:** P1 (Week 4, Days 1-2)

**User Story:** As a developer, I want a proper database schema so that user data, videos, and profiles are stored correctly.

**Acceptance Criteria:**
- ✅ PostgreSQL schema with tables: users, videos, profiles, detections, jobs, feedback
- ✅ Alembic migrations setup with version control
- ✅ Indexes on foreign keys (user_id, video_id, job_id) and created_at columns
- ✅ Row-Level Security (RLS) policies enabled on all tables
- ✅ Schema ERD documentation in README

**Technical Requirements:**
- Database: PostgreSQL 15+ with pgvector extension (for future RAG)
- ORM: SQLAlchemy models for all entities
- Migrations: Alembic for schema versioning (up/down migrations)
- Indexes: B-tree indexes on user_id, video_id, job_id, created_at
- RLS: Policies: `SELECT WHERE user_id = current_user_id()`

**Effort Estimate:** M (16 hours)
- Schema design: 4 hours
- Models & migrations: 8 hours
- RLS policies: 2 hours
- Documentation: 2 hours

**Assigned To:** Backend Developer

**Dependencies:** None (foundation)

**Blocks:** ALL features (every feature needs DB)

**Definition of Done:**
- ✅ Alembic migrations tested (up/down both work)
- ✅ Indexes verified via EXPLAIN ANALYZE (query time <100ms)
- ✅ RLS policies tested (cross-user access blocked via test suite)
- ✅ Schema ERD diagram in docs/database-schema.png
- ✅ Migration guide in docs/migrations.md

**Resources:**
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [PostgreSQL RLS](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

---

#### Issue #INF-2: Authentication & Authorization Infrastructure
**Priority:** P1 (Week 4, Days 3-5)

**User Story:** As a system, I want secure authentication so that only authorized users can access their videos.

**Acceptance Criteria:**
- ✅ JWT-based authentication via Lovable Cloud / Auth0
- ✅ JWT tokens with 15-minute expiry + refresh tokens (7 days)
- ✅ Role-based access control: free_user, pro_user, admin
- ✅ Flask middleware: `@require_auth` decorator for protected endpoints
- ✅ All API endpoints require JWT validation (except public endpoints)

**Technical Requirements:**
- Auth Provider: Lovable Cloud or Auth0 integration
- Backend: Flask-JWT-Extended for token validation
- Middleware: Custom decorator `@require_auth` checks JWT + roles
- Database: User table with user_id, email, role, created_at
- Security: Token rotation, secure cookie storage

**Effort Estimate:** M (24 hours)
- Auth provider setup: 4 hours
- JWT middleware: 8 hours
- Role-based access: 4 hours
- Integration tests: 6 hours
- Documentation: 2 hours

**Assigned To:** Backend Developer

**Dependencies:** Depends on #INF-1 (database schema)

**Blocks:** ALL user-facing features (every feature needs auth)

**Definition of Done:**
- ✅ Unit tests: JWT validation logic (coverage >90%)
- ✅ Integration tests: Auth flow (login → token → API access → refresh)
- ✅ Security tests: Unauthorized access blocked (401/403 status codes)
- ✅ Load tests: Auth middleware overhead <50ms per request
- ✅ Documentation: Authentication API docs in docs/auth.md

**Resources:**
- [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/)
- [Auth0 Python SDK](https://auth0.com/docs/quickstart/backend/python)
- **Risk Spike:** 🔄 #SPIKE-1 (Validate Auth0 vs Lovable Cloud choice)

---

#### Issue #INF-3: Structured Logging Infrastructure
**Priority:** P1 (Week 4, Days 6-7)

**User Story:** As a developer, I want structured logging so that I can debug issues and track system behavior.

**Acceptance Criteria:**
- ✅ JSON structured logging (Python structlog or loguru)
- ✅ Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- ✅ Trace IDs for request correlation across services
- ✅ Log aggregation: CloudWatch Logs or Datadog
- ✅ Log retention: 30 days for INFO, 90 days for ERROR+

**Technical Requirements:**
- Logging Library: Python structlog or loguru
- Format: JSON output with fields: timestamp, level, service, trace_id, user_id, message
- Integration: CloudWatch Logs Insights or Datadog Logs
- Context: Add trace_id to Flask request context

**Effort Estimate:** S (12 hours)
- Logging setup: 4 hours
- Trace ID middleware: 3 hours
- CloudWatch integration: 3 hours
- Documentation: 2 hours

**Assigned To:** Backend Developer

**Dependencies:** Depends on #INF-2 (auth - for user_id in logs)

**Blocks:** All features (needed for debugging)

**Definition of Done:**
- ✅ Structured logs verified (JSON format, all fields present)
- ✅ Trace IDs work across Flask → Celery → Workers
- ✅ CloudWatch Logs ingestion working (logs visible in CloudWatch)
- ✅ Log query examples in docs/logging.md
- ✅ Performance: Logging overhead <5ms per request

**Resources:**
- [Python Structlog](https://www.structlog.org/)
- [CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/)

---

#### Issue #INF-4: Monitoring & Metrics Infrastructure
**Priority:** P1 (Week 5, Days 1-3)

**User Story:** As a developer, I want monitoring and metrics so that I can track system health and catch issues early.

**Acceptance Criteria:**
- ✅ Prometheus metrics: Latency (P50/P95/P99), error rates, queue depth
- ✅ Grafana dashboard: Real-time visualization of key metrics
- ✅ CloudWatch alarms: P95 latency >90s, API error rate >5%, queue depth >500
- ✅ Alerting: PagerDuty or Slack notifications for critical alerts
- ✅ Distributed tracing: OpenTelemetry traces across Flask → Celery → Workers

**Technical Requirements:**
- Metrics: Prometheus client library (prometheus-client)
- Dashboard: Grafana with Prometheus data source
- Tracing: OpenTelemetry Python SDK with AWS X-Ray or Datadog APM
- Alerts: CloudWatch alarms → SNS → PagerDuty/Slack

**Effort Estimate:** M (20 hours)
- Prometheus setup: 6 hours
- Grafana dashboard: 6 hours
- OpenTelemetry tracing: 4 hours
- Alerting configuration: 2 hours
- Documentation: 2 hours

**Assigned To:** DevOps Engineer

**Dependencies:** Depends on #INF-3 (logging - for trace correlation)

**Blocks:** All features (needed for production readiness)

**Definition of Done:**
- ✅ Metrics dashboard: All 8 core metrics tracked (see evaluation plan)
- ✅ Alerts: Critical alerts configured and tested (manual trigger)
- ✅ Tracing: End-to-end traces visible (upload → process → export)
- ✅ Runbook: docs/monitoring-runbook.md with alert response procedures
- ✅ Performance: Metrics collection overhead <10ms per request

**Resources:**
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Grafana Documentation](https://grafana.com/docs/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- **Metric Link:** All metrics (Metric #1-8)

---

### Core Features

#### Issue #1: Video Upload with Drag-and-Drop
**Priority:** P1 (Week 5, Days 4-6)

**User Story:** As a parent, I want to upload video files easily so that I can quickly censor content for my children.

**Acceptance Criteria:**
- ✅ Drag-and-drop interface accepts MP4 and WebM files
- ✅ File validation: Max 500MB, MP4/WebM only (server-side)
- ✅ Upload progress indicator shows 0-100%
- ✅ Pre-signed S3 POST URLs for direct client upload (bypasses API)
- ✅ Upload success rate >95% for files <100MB
- ✅ Upload time <30s for 10MB file (P50)

**Technical Requirements:**
- Frontend: React file upload component (react-dropzone)
- Backend: Flask endpoint `/api/v1/upload` returns pre-signed S3 POST URL
- S3: Private bucket, pre-signed URLs with 1-hour expiry
- Validation: Server-side MIME type check (python-magic), file size validation
- Database: Store video metadata (video_id, user_id, s3_key, status, created_at)

**Effort Estimate:** M (16 hours)
- Frontend component: 6 hours
- Backend endpoint: 4 hours
- S3 integration: 3 hours
- Testing: 3 hours

**Assigned To:** Full-Stack Developer

**Dependencies:** Depends on #INF-1 (database), #INF-2 (auth)

**Blocks:** #2, #3, #6, #8 (all features need upload)

**Definition of Done:**
- ✅ Unit tests: File upload component (coverage >80%)
- ✅ Integration tests: Upload → S3 → Database flow (end-to-end)
- ✅ Security tests: Malicious file uploads rejected (ZIP bombs, scripts)
- ✅ Performance: Upload latency <30s (P50) for 10MB file
- ✅ Documentation: Upload API endpoint docs in docs/api.md

**Resources:**
- [AWS S3 Pre-signed POST URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedPostUpload.html)
- [React Dropzone](https://react-dropzone.js.org/)
- **Metric Link:** Task Completion Rate (Metric #3), Upload success rate

---

#### Issue #2: HTML5 Video Player with Custom Controls
**Priority:** P1 (Week 5-6, Days 1-4)

**User Story:** As a user, I want to play and review censored videos so that I can verify the censorship before exporting.

**Acceptance Criteria:**
- ✅ Play/pause controls with keyboard shortcuts (spacebar)
- ✅ Timeline scrubber with seek functionality
- ✅ Volume control and mute toggle
- ✅ Fullscreen mode toggle
- ✅ Loading/buffering states during processing
- ✅ Video playback error rate <2%

**Technical Requirements:**
- Frontend: React video player component (react-player or custom HTML5)
- Controls: Custom control bar with play/pause/seek/volume
- Keyboard shortcuts: Space (play/pause), Arrow keys (seek ±5s)
- Responsive: Works on desktop (1920x1080) and mobile (375x667)

**Effort Estimate:** M (20 hours)
- Player component: 8 hours
- Controls & keyboard: 4 hours
- Responsive design: 4 hours
- Testing: 4 hours

**Assigned To:** Frontend Developer

**Dependencies:** Depends on #1 (video upload), #INF-2 (auth)

**Blocks:** #4 (timeline), #8 (export)

**Definition of Done:**
- ✅ Unit tests: Player component (coverage >80%)
- ✅ E2E tests: Play/pause/seek functionality (Playwright)
- ✅ Accessibility: Keyboard navigation works (WCAG 2.1 AA)
- ✅ Performance: Player load time <2s, no memory leaks
- ✅ Documentation: Player controls docs in docs/frontend.md

**Resources:**
- [React Player](https://github.com/CookPete/react-player)
- **Metric Link:** Task Completion Rate (Metric #3), Video playback error rate

---

#### Issue #3: Profanity Detection Pipeline (Audio Transcription)
**Priority:** P1 (Week 6, Days 1-5)

**User Story:** As a parent, I want profanity automatically detected and muted so that inappropriate language is removed from videos.

**Acceptance Criteria:**
- ✅ Speech-to-text transcription using OpenAI Whisper API
- ✅ Profanity keyword matching against 100+ word blocklist
- ✅ Timestamp detection for profane words (±0.2s accuracy)
- ✅ Auto-mute logic: Silence audio segments (0.5-2s duration)
- ✅ Profanity detection precision >95%, recall >90% (Golden Set)
- ✅ False positive rate <2%

**Technical Requirements:**
- Backend: Celery worker for audio processing
- STT: OpenAI Whisper API integration ($0.006/minute)
- Profanity DB: PostgreSQL table with 100+ common words (word, category, severity)
- Muting: FFmpeg audio filter (`afade`) to mute detected segments
- Queue: RabbitMQ job queue (priority: realtime)
- Database: Store detections (video_id, timestamp_start, timestamp_end, word, confidence)

**Effort Estimate:** L (40 hours)
- Whisper API integration: 8 hours
- Profanity matching logic: 8 hours
- FFmpeg audio muting: 8 hours
- Celery worker setup: 6 hours
- Testing & validation: 10 hours

**Assigned To:** Backend Developer / ML Engineer

**Dependencies:** Depends on #1 (upload), #INF-1 (database), #INF-3 (logging)

**Blocks:** #4 (timeline), #8 (export), #5 (Kids Mode)

**Definition of Done:**
- ✅ Unit tests: Profanity detection logic (coverage >85%)
- ✅ Integration tests: STT → Detection → Muting pipeline (end-to-end)
- ✅ Golden Set validation: Precision >95%, Recall >90% on 15 test cases
- ✅ Performance: Processing time <20s for 5min video (P95)
- ✅ Documentation: Profanity detection API docs in docs/api.md

**Resources:**
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [FFmpeg Audio Filters](https://ffmpeg.org/ffmpeg-filters.html)
- **Metric Link:** Profanity Detection Accuracy (Metric #2), False Positive Override Rate (Metric #7)

---

#### Issue #4: Timeline with Censored Markers
**Priority:** P1 (Week 6, Days 6-7)

**User Story:** As a user, I want to see where content was censored on the timeline so that I can review and navigate to specific sections.

**Acceptance Criteria:**
- ✅ Timeline scrubber shows red bars for profanity detections
- ✅ Timeline scrubber shows ⚠️ markers for violence detections
- ✅ Click on marker to seek to that timestamp
- ✅ Hover tooltip shows detection type and timestamp
- ✅ Timeline loads markers in <1s for 10min video

**Technical Requirements:**
- Frontend: Custom timeline component with SVG markers
- Data: Detection timestamps from backend API (`GET /api/v1/videos/{video_id}/detections`)
- Visualization: Red bars for audio (profanity), ⚠️ icons for video (violence)
- Performance: Render markers efficiently (thousands of markers via canvas or SVG)

**Effort Estimate:** M (16 hours)
- Timeline component: 8 hours
- Marker rendering: 4 hours
- Testing: 4 hours

**Assigned To:** Frontend Developer

**Dependencies:** Depends on #2 (player), #3 (profanity detection), #6 (violence detection)

**Blocks:** #8 (export), #11 (profiles)

**Definition of Done:**
- ✅ Unit tests: Timeline component (coverage >80%)
- ✅ E2E tests: Marker display and click functionality
- ✅ Performance: Timeline load time <1s for 10min video (1000+ markers)
- ✅ Documentation: Timeline component docs in docs/frontend.md

**Resources:**
- [SVG Timeline Visualization](https://developer.mozilla.org/en-US/docs/Web/SVG)
- **Metric Link:** Task Completion Rate (Metric #3), Time on Task

---

#### Issue #5: Kids Mode Preset (One-Click Activation)
**Priority:** P1 (Week 7, Days 1-2)

**User Story:** As a parent, I want to activate strict censorship with one click so that I can quickly censor videos for young children.

**Acceptance Criteria:**
- ✅ One-click "Kids Mode" button in player UI
- ✅ Preset applies strict blocklist (100+ words, zero tolerance)
- ✅ Preset activates within 3 seconds
- ✅ Reprocessing applies stricter settings automatically
- ✅ Activation rate >70% of users try it (Week 7 user testing)

**Technical Requirements:**
- Frontend: Preset selector dropdown or prominent button
- Backend: Preset configuration stored in PostgreSQL (preset_id, name, blocklist, sensitivity)
- Blocklist: Pre-defined strict word list (100+ words) seeded in database
- Reprocessing: Automatically triggers re-processing with new preset

**Effort Estimate:** S (12 hours)
- Frontend UI: 4 hours
- Backend preset logic: 4 hours
- Reprocessing trigger: 2 hours
- Testing: 2 hours

**Assigned To:** Full-Stack Developer

**Dependencies:** Depends on #3 (profanity detection), #INF-1 (database)

**Blocks:** #11 (profiles), #12 (custom keywords)

**Definition of Done:**
- ✅ Unit tests: Preset activation logic (coverage >80%)
- ✅ E2E tests: Preset activation → Reprocessing flow
- ✅ User testing: Activation rate >70% (Week 7)
- ✅ Documentation: Preset configuration docs in docs/api.md

**Resources:**
- **Metric Link:** User Activation Rate (Metric #6), Task Completion Rate (Metric #3)

---

#### Issue #6: Visual Violence Detection Pipeline
**Priority:** P1 (Week 7, Days 3-7)

**User Story:** As a parent, I want violent scenes automatically detected and blurred so that my children don't see graphic content.

**Acceptance Criteria:**
- ✅ Frame extraction at 0.5 FPS using FFmpeg GPU acceleration
- ✅ Google Vision API integration for violence detection (batch 10 frames/request)
- ✅ Blur effect applied to flagged frames (intensity ≥70%)
- ✅ Violence detection precision >90%, recall >85% (Golden Set)
- ✅ Processing time <15s for 5min video (frame extraction)

**Technical Requirements:**
- Backend: Celery worker for video frame extraction
- FFmpeg: GPU acceleration (`-hwaccel cuda`) for frame extraction
- Google Vision API: Batch 10 frames per request, circuit breaker fallback
- Blur: FFmpeg blur filter (`boxblur=10`) applied to detected frames
- Fallback: Local NudeNet model if API fails (circuit breaker)
- Database: Store violence detections (video_id, frame_number, timestamp, confidence)

**Effort Estimate:** L (48 hours)
- Frame extraction: 12 hours
- Google Vision API integration: 12 hours
- Blur application: 8 hours
- Circuit breaker & fallback: 8 hours
- Testing & validation: 8 hours

**Assigned To:** Backend Developer / ML Engineer

**Dependencies:** Depends on #1 (upload), #INF-1 (database), #INF-3 (logging)

**Blocks:** #4 (timeline), #8 (export)

**Definition of Done:**
- ✅ Unit tests: Violence detection logic (coverage >85%)
- ✅ Integration tests: Frame extraction → Detection → Blur pipeline
- ✅ Golden Set validation: Precision >90%, Recall >85% on 10 test cases
- ✅ Performance: Frame extraction <15s for 5min video (P95)
- ✅ Documentation: Violence detection API docs in docs/api.md

**Resources:**
- [Google Vision API](https://cloud.google.com/vision/docs)
- [FFmpeg GPU Acceleration](https://trac.ffmpeg.org/wiki/HWAccelIntro)
- [NudeNet (Fallback)](https://github.com/notAI-tech/NudeNet)
- **Metric Link:** Profanity Detection Accuracy (Metric #2), End-to-End Latency (Metric #1)
- **Risk Spike:** 🔄 #SPIKE-2 (Validate Google Vision API batching performance)

---

#### Issue #7: RabbitMQ Queue Infrastructure
**Priority:** P1 (Week 5, Days 7-8)

**User Story:** As a system, I want a message queue so that video processing jobs can be handled asynchronously.

**Acceptance Criteria:**
- ✅ RabbitMQ cluster setup (3 nodes for high availability)
- ✅ Priority queues: realtime, batch, export
- ✅ Dead-letter exchange (DLQ) for failed jobs
- ✅ Celery workers configured to consume from queues
- ✅ Queue depth monitoring <1000 jobs (alert if exceeded)

**Technical Requirements:**
- Infrastructure: RabbitMQ 3.12+ cluster (CloudAMQP or self-hosted)
- Queues: `realtime` (priority 10), `batch` (priority 5), `export` (priority 1)
- DLQ: Failed jobs after 3 retries go to DLQ
- Celery: Configured with RabbitMQ broker
- Monitoring: CloudWatch metrics for queue depth

**Effort Estimate:** M (16 hours)
- RabbitMQ setup: 6 hours
- Queue configuration: 4 hours
- Celery integration: 4 hours
- Monitoring: 2 hours

**Assigned To:** DevOps Engineer

**Dependencies:** Depends on #INF-3 (logging)

**Blocks:** #3, #6, #8, #9 (all processing features)

**Definition of Done:**
- ✅ RabbitMQ cluster healthy (all 3 nodes running)
- ✅ Queue configuration tested (jobs route correctly)
- ✅ DLQ working (failed jobs appear in DLQ)
- ✅ Monitoring: Queue depth metrics visible in CloudWatch
- ✅ Documentation: Queue setup guide in docs/infrastructure.md

**Resources:**
- [RabbitMQ Clustering](https://www.rabbitmq.com/clustering.html)
- [Celery RabbitMQ Broker](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/rabbitmq.html)

---

#### Issue #8: Export Censored Video (MP4 Download)
**Priority:** P1 (Week 8, Days 1-4)

**User Story:** As a user, I want to download the censored video so that I can save it for offline viewing.

**Acceptance Criteria:**
- ✅ Export button in player UI
- ✅ Export process completes in <60s for 5min video
- ✅ Export success rate >90%
- ✅ Download button appears when export completes
- ✅ Downloaded file is playable MP4 with censored content

**Technical Requirements:**
- Backend: Celery worker for video export (FFmpeg composition)
- FFmpeg: GPU encoding (`-c:v h264_nvenc`) for faster export
- S3: Multipart upload for large files
- CDN: CloudFront signed URLs for download (1-hour expiry)
- Database: Update video status to "exported", store S3 key

**Effort Estimate:** M (24 hours)
- Export worker: 8 hours
- FFmpeg composition: 6 hours
- S3/CloudFront integration: 6 hours
- Testing: 4 hours

**Assigned To:** Backend Developer

**Dependencies:** Depends on #3 (profanity), #6 (violence), #2 (player), #7 (queue)

**Blocks:** None

**Definition of Done:**
- ✅ Unit tests: Export logic (coverage >80%)
- ✅ Integration tests: Export → Download flow (end-to-end)
- ✅ Performance: Export time <60s for 5min video (P95)
- ✅ Security: Pre-signed URLs expire after 1 hour
- ✅ Documentation: Export API docs in docs/api.md

**Resources:**
- [FFmpeg GPU Encoding](https://trac.ffmpeg.org/wiki/HWAccelIntro)
- [S3 Multipart Upload](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html)
- **Metric Link:** Task Completion Rate (Metric #3), End-to-End Latency (Metric #1)

---

#### Issue #9: Processing Queue UI with Status Indicators
**Priority:** P1 (Week 8, Days 5-7)

**User Story:** As a user, I want to see processing progress so that I know when my video will be ready.

**Acceptance Criteria:**
- ✅ Processing queue UI shows job status (queued, processing, completed, failed)
- ✅ Progress bar shows 0-100% completion
- ✅ Estimated time remaining displayed
- ✅ Queue depth indicator (if >10 jobs, show warning)
- ✅ Real-time updates via polling (every 2s)

**Technical Requirements:**
- Frontend: Queue UI component with status badges
- Backend: RabbitMQ job status API endpoint (`GET /api/v1/jobs/{job_id}`)
- Redis: Cache job status for fast lookups (1-minute TTL)
- Polling: Frontend polls every 2s for status updates

**Effort Estimate:** M (20 hours)
- Queue UI component: 8 hours
- Status API endpoint: 6 hours
- Redis caching: 3 hours
- Testing: 3 hours

**Assigned To:** Full-Stack Developer

**Dependencies:** Depends on #1 (upload), #3 (profanity detection), #7 (queue)

**Blocks:** None

**Definition of Done:**
- ✅ Unit tests: Queue UI component (coverage >80%)
- ✅ Integration tests: Queue status updates (polling works)
- ✅ Performance: Status updates <500ms latency
- ✅ UX: Progress bar updates smoothly (no jank)
- ✅ Documentation: Queue API docs in docs/api.md

**Resources:**
- [RabbitMQ Management API](https://www.rabbitmq.com/management.html)
- **Metric Link:** Task Completion Rate (Metric #3), System Uptime (Metric #5)

---

#### Issue #10: Profile Management (CRUD)
**Priority:** P1 (Week 9, Days 1-3)

**User Story:** As a user, I want to create and manage custom censorship profiles so that I can customize what content is filtered.

**Acceptance Criteria:**
- ✅ Create profile interface (name, description, blocklist)
- ✅ Edit profile (update blocklist, sensitivity settings)
- ✅ Delete profile (with confirmation)
- ✅ Profile selector dropdown in player UI
- ✅ Profile switching without page reload
- ✅ Profile creation rate >40% (Week 7 user testing)

**Technical Requirements:**
- Frontend: Profile CRUD forms and UI
- Backend: Flask API endpoints (`POST /api/v1/profiles`, `PUT /api/v1/profiles/{id}`, `DELETE /api/v1/profiles/{id}`)
- Database: Profiles table with user_id foreign key, blocklist JSONB
- Caching: Redis cache for active profiles (1-hour TTL)

**Effort Estimate:** M (20 hours)
- Frontend forms: 6 hours
- Backend API: 8 hours
- Redis caching: 3 hours
- Testing: 3 hours

**Assigned To:** Full-Stack Developer

**Dependencies:** Depends on #INF-2 (auth), #INF-1 (database), #5 (Kids Mode)

**Blocks:** #12 (custom keywords)

**Definition of Done:**
- ✅ Unit tests: Profile CRUD logic (coverage >85%)
- ✅ Integration tests: Create → Edit → Delete flow
- ✅ User testing: Profile creation rate >40% (Week 7)
- ✅ Performance: Profile load time <200ms (from cache)
- ✅ Documentation: Profile API docs in docs/api.md

**Resources:**
- **Metric Link:** User Activation Rate (Metric #6), Task Completion Rate (Metric #3)

---

#### Issue #11: Custom Keyword Blocklist Editor
**Priority:** P1 (Week 9, Days 4-5)

**User Story:** As a user, I want to add custom words to my blocklist so that I can censor words specific to my needs.

**Acceptance Criteria:**
- ✅ Add keyword interface (input field + "Add" button)
- ✅ Keyword validation (alphanumeric, max 50 chars)
- ✅ Save keywords to profile blocklist
- ✅ Reprocessing detects and censors custom keywords
- ✅ Timeline shows new censored segments
- ✅ Task completion >60% (add keyword task in Week 7 user testing)

**Technical Requirements:**
- Frontend: Keyword input component with validation
- Backend: Profile blocklist update API endpoint (`PUT /api/v1/profiles/{id}/blocklist`)
- Database: Profile blocklist stored as JSONB array (update triggers reprocessing)
- Reprocessing: Trigger re-processing when blocklist updated

**Effort Estimate:** M (16 hours)
- Frontend component: 6 hours
- Backend API: 6 hours
- Reprocessing trigger: 2 hours
- Testing: 2 hours

**Assigned To:** Full-Stack Developer

**Dependencies:** Depends on #11 (profile management), #3 (profanity detection)

**Blocks:** None

**Definition of Done:**
- ✅ Unit tests: Keyword validation logic (coverage >90%)
- ✅ Integration tests: Add keyword → Reprocessing flow
- ✅ User testing: Task completion >60% (Week 7)
- ✅ Security: SQL injection prevention (parameterized queries)
- ✅ Documentation: Keyword API docs in docs/api.md

**Resources:**
- **Metric Link:** Task Completion Rate (Metric #3), User Activation Rate (Metric #6)

---

### Evaluation Infrastructure

#### Issue #EVAL-1: Golden Set Test Suite Setup
**Priority:** P1 (Week 6, Days 6-7)

**User Story:** As a developer, I want automated test cases so that I can validate model accuracy continuously.

**Acceptance Criteria:**
- ✅ Golden Set test suite with 50+ test cases (typical/edge/adversarial)
- ✅ Automated test execution (pytest) runs nightly
- ✅ Test cases stored in PostgreSQL (test_id, video_url, ground_truth, expected_detections)
- ✅ Accuracy metrics calculated automatically (precision, recall, false positive rate)
- ✅ Test results dashboard (Grafana or custom)

**Technical Requirements:**
- Test Framework: pytest with custom fixtures
- Test Data: 50+ curated videos stored in S3 (private bucket)
- Ground Truth: JSON annotations (timestamps, words, categories)
- Automation: CI/CD pipeline runs tests nightly
- Reporting: Test results stored in PostgreSQL, visualized in Grafana

**Effort Estimate:** M (24 hours)
- Test suite setup: 8 hours
- Golden Set curation: 8 hours
- Automation: 4 hours
- Reporting: 4 hours

**Assigned To:** ML Engineer / QA Engineer

**Dependencies:** Depends on #3 (profanity detection), #6 (violence detection)

**Blocks:** None (evaluation)

**Definition of Done:**
- ✅ 50+ test cases defined (15 typical, 10 edge, 5 adversarial)
- ✅ Automated tests run successfully (pytest passes)
- ✅ Accuracy metrics calculated correctly (precision, recall)
- ✅ Test results dashboard visible in Grafana
- ✅ Documentation: Golden Set guide in docs/evaluation.md

**Resources:**
- [Pytest Documentation](https://docs.pytest.org/)
- [Evaluation Plan](docs/evaluation-plan-v2.md)
- **Metric Link:** Profanity Detection Accuracy (Metric #2)

---

#### Issue #EVAL-2: Metrics Collection Infrastructure
**Priority:** P1 (Week 7, Days 1-2)

**User Story:** As a developer, I want metrics collection so that I can track all 8 core metrics automatically.

**Acceptance Criteria:**
- ✅ All 8 core metrics tracked (latency, accuracy, completion rate, SUS, uptime, activation, false positives, CSAT)
- ✅ Metrics stored in Prometheus (time-series database)
- ✅ Grafana dashboard shows all metrics (real-time)
- ✅ Metrics exported to evaluation reports (weekly)
- ✅ Alerting: Metrics outside targets trigger alerts

**Technical Requirements:**
- Prometheus: Custom metrics exported via prometheus-client
- Metrics: Counter, Histogram, Gauge metrics for all 8 core metrics
- Grafana: Dashboard with 8 panels (one per metric)
- Export: Weekly CSV export for evaluation reports

**Effort Estimate:** M (20 hours)
- Metrics instrumentation: 8 hours
- Grafana dashboard: 6 hours
- Export pipeline: 4 hours
- Documentation: 2 hours

**Assigned To:** DevOps Engineer

**Dependencies:** Depends on #INF-4 (monitoring infrastructure)

**Blocks:** None (evaluation)

**Definition of Done:**
- ✅ All 8 metrics tracked (verified in Prometheus)
- ✅ Grafana dashboard shows all metrics (real-time updates)
- ✅ Weekly export works (CSV files generated)
- ✅ Alerting configured (alerts trigger for out-of-target metrics)
- ✅ Documentation: Metrics collection guide in docs/evaluation.md

**Resources:**
- [Prometheus Client Python](https://github.com/prometheus/client_python)
- [Evaluation Plan](docs/comprehensive-evaluation-plan.md)
- **Metric Link:** All metrics (Metric #1-8)

---

### Risk Reduction Spikes

#### Issue #SPIKE-1: Auth Provider Validation Spike
**Priority:** P1 (Week 4, Day 1)

**User Story:** As a developer, I want to validate the auth provider choice so that I can make an informed decision.

**Acceptance Criteria:**
- ✅ Proof-of-concept: Auth0 vs Lovable Cloud integration
- ✅ Performance comparison: Auth latency (Auth0 vs Lovable)
- ✅ Cost comparison: Monthly costs for 1000 users
- ✅ Feature comparison: JWT, refresh tokens, RBAC support
- ✅ Recommendation: Choose one provider with justification

**Technical Requirements:**
- Auth0: Free tier (7000 MAU), Python SDK integration
- Lovable Cloud: Built-in auth, JWT support
- Testing: Load test both (100 concurrent requests)
- Documentation: Spike report with recommendation

**Effort Estimate:** S (8 hours)
- Auth0 PoC: 3 hours
- Lovable PoC: 2 hours
- Comparison: 2 hours
- Report: 1 hour

**Assigned To:** Backend Developer

**Dependencies:** None (spike)

**Blocks:** #INF-2 (auth infrastructure - needs decision)

**Definition of Done:**
- ✅ Both providers tested (PoC working)
- ✅ Performance data collected (latency, throughput)
- ✅ Cost analysis complete (monthly costs)
- ✅ Recommendation documented in docs/spikes/auth-provider.md

**Resources:**
- [Auth0 Python SDK](https://auth0.com/docs/quickstart/backend/python)
- [Lovable Cloud Auth](https://docs.lovable.dev/)

---

#### Issue #SPIKE-2: Google Vision API Batching Performance Spike
**Priority:** P1 (Week 6, Day 1)

**User Story:** As a developer, I want to validate API batching performance so that I can ensure latency targets are met.

**Acceptance Criteria:**
- ✅ Proof-of-concept: Batch 10 frames per request
- ✅ Performance test: Latency comparison (single vs batch)
- ✅ Rate limit test: Verify 1800 req/min limit handling
- ✅ Cost analysis: API costs with batching vs without
- ✅ Recommendation: Batch size and parallel worker count

**Technical Requirements:**
- Google Vision API: Batch request implementation
- Testing: Load test with 100 frames (10 batches vs 100 single requests)
- Monitoring: Track latency, error rate, cost
- Documentation: Spike report with batching strategy

**Effort Estimate:** S (8 hours)
- Batch PoC: 4 hours
- Performance testing: 2 hours
- Analysis: 1 hour
- Report: 1 hour

**Assigned To:** Backend Developer

**Dependencies:** None (spike)

**Blocks:** #6 (violence detection - needs batching strategy)

**Definition of Done:**
- ✅ Batch PoC working (10 frames per request)
- ✅ Performance data collected (latency, throughput)
- ✅ Rate limit handling verified (no quota exceeded errors)
- ✅ Recommendation documented in docs/spikes/api-batching.md

**Resources:**
- [Google Vision API Batching](https://cloud.google.com/vision/docs/batch)
- **Metric Link:** End-to-End Latency (Metric #1)

---

## P2: High Value (Weeks 9-14)

### Issue #13: False Positive Override Button
**Priority:** P2 (Week 10, Days 1-3)

**User Story:** As a user, I want to mark false positives so that I can correct incorrect detections and improve the system.

**Acceptance Criteria:**
- ✅ "Mark as False Positive" button in player UI
- ✅ Override removes mute/blur from timeline
- ✅ Override stored in database for model retraining
- ✅ False positive override rate <5% (indicates model accuracy)
- ✅ User can undo override (re-apply censorship)

**Technical Requirements:**
- Frontend: Override button component in player
- Backend: Override API endpoint (`POST /api/v1/detections/{id}/override`)
- Database: False_positive_feedback table (user_id, detection_id, timestamp, comment)
- Model training: Export feedback to CSV for retraining

**Effort Estimate:** M (16 hours)

**Assigned To:** Full-Stack Developer

**Dependencies:** Depends on #4 (timeline markers), #3 (profanity detection)

**Blocks:** #19 (feedback loop)

**Definition of Done:**
- ✅ Unit tests: Override logic (coverage >85%)
- ✅ Integration tests: Override → Database → Export flow
- ✅ User testing: Override rate <5% (indicates accuracy)
- ✅ Documentation: Override API docs in docs/api.md

**Resources:**
- **Metric Link:** False Positive Override Rate (Metric #7), Profanity Detection Accuracy (Metric #2)

---

### Issue #14: Performance Optimization (GPU Acceleration)
**Priority:** P2 (Week 10, Days 4-7)

**User Story:** As a user, I want fast video processing so that I don't wait too long for results.

**Acceptance Criteria:**
- ✅ GPU acceleration for frame extraction (FFmpeg CUDA)
- ✅ GPU encoding for video export (h264_nvenc)
- ✅ Frame extraction time <15s for 5min video (vs. 30s baseline)
- ✅ Video export time <10s for 5min video (vs. 20s baseline)
- ✅ P95 latency <90s for 5min video (meets target)

**Technical Requirements:**
- Infrastructure: AWS EC2 g4dn.xlarge GPU instances for workers
- FFmpeg: GPU acceleration (`-hwaccel cuda`) for frame extraction
- FFmpeg: GPU encoding (`-c:v h264_nvenc`) for video export
- Monitoring: Track GPU utilization and processing times

**Effort Estimate:** L (32 hours)

**Assigned To:** DevOps Engineer / Backend Developer

**Dependencies:** Depends on #3 (profanity), #6 (violence), #8 (export)

**Blocks:** None

**Definition of Done:**
- ✅ Performance tests: P95 latency <90s (meets target)
- ✅ GPU utilization monitoring (CloudWatch metrics)
- ✅ Cost analysis: GPU instance costs vs. processing time savings
- ✅ Documentation: GPU setup guide in docs/infrastructure.md

**Resources:**
- [AWS EC2 GPU Instances](https://aws.amazon.com/ec2/instance-types/g4/)
- [FFmpeg GPU Acceleration](https://trac.ffmpeg.org/wiki/HWAccelIntro)
- **Metric Link:** End-to-End Latency (Metric #1), System Uptime (Metric #5)

---

### Issue #15: API Batching & Circuit Breaker
**Priority:** P2 (Week 11, Days 1-4)

**User Story:** As a system, I want to batch API calls and handle failures gracefully so that I can reduce costs and maintain reliability.

**Acceptance Criteria:**
- ✅ Google Vision API batching (10 frames/request) reduces calls by 90%
- ✅ Circuit breaker activates after 5 errors in 60s
- ✅ Fallback to local NudeNet model when API fails
- ✅ API error rate <5% (from monitoring)
- ✅ Processing latency reduced by 90% (45s → 6s for AI detection)

**Technical Requirements:**
- Backend: Batch API request logic (10 frames per request)
- Circuit breaker: Implemented with exponential backoff (pybreaker library)
- Fallback: Local NudeNet model deployment
- Monitoring: Track API error rates and circuit breaker activations

**Effort Estimate:** M (24 hours)

**Assigned To:** Backend Developer

**Dependencies:** Depends on #6 (violence detection), #SPIKE-2 (batching validation)

**Blocks:** None

**Definition of Done:**
- ✅ Unit tests: Batching logic (coverage >90%)
- ✅ Integration tests: Circuit breaker → Fallback flow
- ✅ Performance: AI detection latency <20s (target)
- ✅ Monitoring: API error rate dashboard

**Resources:**
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Google Vision API Batching](https://cloud.google.com/vision/docs/batch)
- **Metric Link:** End-to-End Latency (Metric #1), System Uptime (Metric #5)

---

### Issue #16: Caching Strategy (Transcript & Frame Cache)
**Priority:** P2 (Week 11, Days 5-7)

**User Story:** As a system, I want to cache detection results so that I can reduce API costs and improve performance.

**Acceptance Criteria:**
- ✅ Transcript cache: 25% hit rate (users re-process same videos)
- ✅ Frame cache: 12% hit rate (same frames in multiple videos)
- ✅ Redis cache with 24-hour TTL
- ✅ Cache reduces API calls by 25% (transcript) + 12% (frame)
- ✅ Cost savings: $504/month at scale (10k videos/month)

**Technical Requirements:**
- Infrastructure: Redis cache (AWS ElastiCache)
- Backend: Cache lookup before API calls
- Hashing: SHA-256 hash of transcript/frame for cache key
- Monitoring: Track cache hit rates and cost savings

**Effort Estimate:** M (20 hours)

**Assigned To:** Backend Developer

**Dependencies:** Depends on #3 (profanity), #6 (violence)

**Blocks:** None

**Definition of Done:**
- ✅ Unit tests: Cache logic (coverage >85%)
- ✅ Integration tests: Cache hit/miss scenarios
- ✅ Performance: Cache hit rate >25% (transcript), >12% (frame)
- ✅ Cost analysis: Monthly cost savings report

**Resources:**
- [Redis Caching](https://redis.io/docs/manual/patterns/cache/)
- [Token Cost Optimization](docs/token-cost-optimization.md)
- **Metric Link:** End-to-End Latency (Metric #1), Cost optimization

---

### Issue #17: Rate Limiting & Security Hardening
**Priority:** P2 (Week 12, Days 1-3)

**User Story:** As a system, I want rate limiting and security controls so that I can prevent abuse and protect user data.

**Acceptance Criteria:**
- ✅ Rate limiting: 10 req/min (free users), 100 req/min (pro users)
- ✅ File validation: MIME type check, max 500MB
- ✅ CORS: Only lovable.app domain allowed
- ✅ API key security: Environment variables, monthly rotation
- ✅ Security scan: No OWASP Top 10 vulnerabilities

**Technical Requirements:**
- Backend: Redis-based rate limiter middleware (flask-limiter)
- File validation: Server-side MIME type check (python-magic)
- CORS: Flask-CORS configuration
- Security: Regular security audits (OWASP ZAP)

**Effort Estimate:** M (16 hours)

**Assigned To:** Backend Developer / Security Engineer

**Dependencies:** Depends on #INF-2 (auth)

**Blocks:** None

**Definition of Done:**
- ✅ Unit tests: Rate limiting logic (coverage >90%)
- ✅ Integration tests: Rate limit enforcement
- ✅ Security scan: OWASP ZAP scan passes
- ✅ Documentation: Security best practices guide

**Resources:**
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Rate Limiting](https://flask-limiter.readthedocs.io/)
- **Metric Link:** System Uptime (Metric #5), Security regression tests

---

### Issue #18: Redis Cache Infrastructure
**Priority:** P2 (Week 9, Days 1-2)

**User Story:** As a system, I want Redis caching so that I can improve performance and reduce database load.

**Acceptance Criteria:**
- ✅ Redis cluster setup (AWS ElastiCache or self-hosted)
- ✅ Cache configuration: 24-hour TTL for detection results
- ✅ Cache warming: Pre-load popular profiles and blocklists
- ✅ Cache monitoring: Hit rate >70% for profiles, >25% for transcripts

**Technical Requirements:**
- Infrastructure: Redis 7.0+ (AWS ElastiCache t3.micro)
- Backend: Redis Python client (redis-py)
- Configuration: TTL policies, eviction policies (LRU)
- Monitoring: CloudWatch metrics for cache hit rate

**Effort Estimate:** M (12 hours)

**Assigned To:** DevOps Engineer

**Dependencies:** Depends on #INF-4 (monitoring)

**Blocks:** #16 (caching strategy), #11 (profile caching)

**Definition of Done:**
- ✅ Redis cluster healthy (all nodes running)
- ✅ Cache configuration tested (TTL, eviction work correctly)
- ✅ Monitoring: Cache hit rate metrics visible in CloudWatch
- ✅ Documentation: Redis setup guide in docs/infrastructure.md

**Resources:**
- [Redis Documentation](https://redis.io/docs/)
- [AWS ElastiCache](https://aws.amazon.com/elasticache/)

---

### Issue #19: User Feedback Loop for Model Retraining
**Priority:** P2 (Week 13, Days 1-5)

**User Story:** As a system, I want to collect user feedback so that I can improve model accuracy over time.

**Acceptance Criteria:**
- ✅ Export user feedback to CSV for model training
- ✅ Admin dashboard to review feedback (approve/reject)
- ✅ Feedback integrated into retraining pipeline
- ✅ Model retrained monthly with new feedback data
- ✅ Accuracy improvements tracked (precision/recall trends)

**Technical Requirements:**
- Backend: Feedback export API endpoint (CSV format)
- Admin UI: Feedback review dashboard
- ML Pipeline: Retraining script with feedback data
- Monitoring: Track accuracy improvements over time

**Effort Estimate:** L (40 hours)

**Assigned To:** ML Engineer / Backend Developer

**Dependencies:** Depends on #13 (false positive override)

**Blocks:** None

**Definition of Done:**
- ✅ Unit tests: Feedback export logic (coverage >85%)
- ✅ Integration tests: Feedback → Export → Retraining flow
- ✅ Model validation: Accuracy improvements measured
- ✅ Documentation: Feedback collection and retraining guide

**Resources:**
- **Metric Link:** Profanity Detection Accuracy (Metric #2), False Positive Override Rate (Metric #7)

---

### Issue #20: S3 Lifecycle Policies & GDPR Compliance
**Priority:** P2 (Week 12, Days 4-7)

**User Story:** As a system, I want data retention policies so that I can comply with GDPR and reduce storage costs.

**Acceptance Criteria:**
- ✅ S3 lifecycle policy: Delete original videos after 7 days
- ✅ Processed videos: Delete after 30 days (free), 1 year (pro)
- ✅ GDPR: "Delete Account" feature (soft delete + hard delete after 30 days)
- ✅ Data export: "Export My Data" endpoint (ZIP file)
- ✅ Audit log: Track all data deletions

**Technical Requirements:**
- S3: Lifecycle policies configured (transition to Glacier, delete)
- Backend: GDPR endpoints (`DELETE /api/v1/user/data`, `GET /api/v1/user/data-export`)
- Database: Soft delete flag on videos (deleted_at timestamp)
- Audit: Audit log table (action, user_id, timestamp, ip_address)

**Effort Estimate:** M (20 hours)

**Assigned To:** Backend Developer

**Dependencies:** Depends on #INF-1 (database), #1 (upload)

**Blocks:** None

**Definition of Done:**
- ✅ S3 lifecycle policies tested (files deleted after retention period)
- ✅ GDPR endpoints tested (delete account, export data)
- ✅ Audit log verified (all deletions logged)
- ✅ Documentation: GDPR compliance guide in docs/compliance.md

**Resources:**
- [AWS S3 Lifecycle Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [GDPR Compliance](https://gdpr.eu/)

---

## P3: Nice to Have (Weeks 13-15)

### Issue #21: Playback Speed Controls & Confidence Scores
**Priority:** P3 (Week 14, Days 1-3)

**User Story:** As a user, I want playback speed controls and confidence scores so that I can review videos more efficiently and understand detection certainty.

**Acceptance Criteria:**
- ✅ Playback speed controls (0.5x, 1x, 1.5x, 2x)
- ✅ Confidence score display (0-100%) for each detection
- ✅ Tooltip shows detection confidence on hover
- ✅ Usage rate >15% (playback speed) from analytics

**Technical Requirements:**
- Frontend: Playback speed selector component
- Frontend: Confidence score display in timeline markers
- Backend: Return confidence scores in detection API
- Analytics: Track feature usage rates

**Effort Estimate:** S (12 hours)

**Assigned To:** Frontend Developer

**Dependencies:** Depends on #2 (player), #4 (timeline)

**Blocks:** None

**Definition of Done:**
- ✅ Unit tests: Playback speed logic (coverage >80%)
- ✅ E2E tests: Speed controls and confidence display
- ✅ Analytics: Usage rate >15% (playback speed)
- ✅ Documentation: Feature documentation

**Resources:**
- **Metric Link:** User Activation Rate (Metric #6), CSAT Score (Metric #8)

---

### Issue #22: Batch Video Upload Interface
**Priority:** P3 (Week 14, Days 4-7)

**User Story:** As a studio user, I want to upload multiple videos at once so that I can process them in batch.

**Acceptance Criteria:**
- ✅ Drag-and-drop multiple files (up to 10 videos)
- ✅ Batch processing queue shows all videos
- ✅ Progress indicator per video (0-100%)
- ✅ Email notification when batch completes
- ✅ Batch export: Download all videos as ZIP

**Technical Requirements:**
- Frontend: Multi-file upload component
- Backend: Batch processing API endpoint
- Queue: Batch jobs processed in parallel (5 concurrent)
- Email: SendGrid or AWS SES for notifications

**Effort Estimate:** M (24 hours)

**Assigned To:** Full-Stack Developer

**Dependencies:** Depends on #1 (upload), #9 (queue UI)

**Blocks:** None

**Definition of Done:**
- ✅ Unit tests: Batch upload component (coverage >80%)
- ✅ Integration tests: Batch processing flow
- ✅ Performance: Batch of 10 videos processes in <10 minutes
- ✅ Documentation: Batch processing guide

**Resources:**
- **Metric Link:** Task Completion Rate (Metric #3), CSAT Score (Metric #8)

---

### Issue #23: Advanced Timeline Editor (Trim/Cut/Merge)
**Priority:** P3 (Week 15, Days 1-4)

**User Story:** As a studio user, I want to trim and edit videos so that I can create custom cuts.

**Acceptance Criteria:**
- ✅ Timeline editor with trim handles (start/end markers)
- ✅ Cut video segments (remove middle section)
- ✅ Merge multiple videos (concatenate)
- ✅ Preview changes before applying
- ✅ Export edited video

**Technical Requirements:**
- Frontend: Timeline editor component with trim handles
- Backend: Video editing API (FFmpeg trim/cut/merge)
- FFmpeg: Segment extraction and concatenation
- Database: Store edit metadata (trim points, cuts)

**Effort Estimate:** L (40 hours)

**Assigned To:** Full-Stack Developer

**Dependencies:** Depends on #4 (timeline), #8 (export)

**Blocks:** None

**Definition of Done:**
- ✅ Unit tests: Timeline editor logic (coverage >80%)
- ✅ Integration tests: Trim → Cut → Merge flow
- ✅ Performance: Edit operations complete in <30s
- ✅ Documentation: Timeline editor guide

**Resources:**
- **Metric Link:** CSAT Score (Metric #8), User Activation Rate (Metric #6)

---

### Issue #24: Censoring Stats Summary Dashboard
**Priority:** P3 (Week 15, Days 5-7)

**User Story:** As a user, I want to see censoring statistics so that I can understand what content was filtered.

**Acceptance Criteria:**
- ✅ Stats summary: # profanities muted, # violent scenes blurred
- ✅ Per-video stats: Show stats for each processed video
- ✅ Aggregate stats: Total videos processed, total detections
- ✅ Stats visualization: Charts/graphs (bar charts, pie charts)
- ✅ Export stats: Download stats as CSV

**Technical Requirements:**
- Frontend: Stats dashboard component
- Backend: Stats API endpoint (`GET /api/v1/stats`)
- Database: Aggregate stats from detections table
- Visualization: Chart.js or Recharts for graphs

**Effort Estimate:** M (16 hours)

**Assigned To:** Full-Stack Developer

**Dependencies:** Depends on #3 (profanity), #6 (violence), #INF-1 (database)

**Blocks:** None

**Definition of Done:**
- ✅ Unit tests: Stats calculation logic (coverage >80%)
- ✅ Integration tests: Stats API endpoint
- ✅ UX: Stats dashboard loads in <2s
- ✅ Documentation: Stats dashboard guide

**Resources:**
- **Metric Link:** User Activation Rate (Metric #6), CSAT Score (Metric #8)

---

## Backlog Summary

### Priority Distribution
- **P1 (Critical Path):** 15 issues (Weeks 4-12)
  - Infrastructure: 4 issues
  - Core Features: 7 issues
  - Evaluation: 2 issues
  - Risk Spikes: 2 issues
- **P2 (High Value):** 9 issues (Weeks 9-14)
- **P3 (Nice to Have):** 4 issues (Weeks 13-15)

### Effort Estimate Summary
- **P1 Total:** ~340 hours (~8.5 weeks @ 40hrs/week)
- **P2 Total:** ~220 hours (~5.5 weeks @ 40hrs/week)
- **P3 Total:** ~92 hours (~2.3 weeks @ 40hrs/week)
- **Grand Total:** ~652 hours (~16.3 weeks @ 40hrs/week)

### Critical Path Dependencies
```
Infrastructure (Foundation):
#INF-1 (DB) → #INF-2 (Auth) → #INF-3 (Logging) → #INF-4 (Monitoring)
                    ↓
              All User Features

Core Processing:
#1 (Upload) → #2 (Player) → #4 (Timeline) → #8 (Export)
#1 (Upload) → #3 (Profanity) → #4 (Timeline) → #8 (Export)
#1 (Upload) → #6 (Violence) → #4 (Timeline) → #8 (Export)
#7 (Queue) → #3, #6, #8 (All processing)

User Features:
#5 (Kids Mode) → #11 (Profiles) → #12 (Custom Keywords)
```

### Risk Spikes
- **#SPIKE-1:** Auth provider validation (Week 4) → Blocks #INF-2
- **#SPIKE-2:** API batching validation (Week 6) → Blocks #6

### Metric Coverage
All 8 core metrics from evaluation plan are covered:
- ✅ Metric #1: End-to-End Latency (Issues #8, #14, #15)
- ✅ Metric #2: Profanity Detection Accuracy (Issues #3, #13, #19, #EVAL-1)
- ✅ Metric #3: Task Completion Rate (Issues #1, #2, #4, #8, #11, #12)
- ✅ Metric #4: SUS Score (All P1 issues, #EVAL-2)
- ✅ Metric #5: System Uptime (Issues #INF-4, #17, #18)
- ✅ Metric #6: User Activation Rate (Issues #5, #11, #12)
- ✅ Metric #7: False Positive Override Rate (Issue #13)
- ✅ Metric #8: CSAT Score (All user-facing issues, #EVAL-2)
