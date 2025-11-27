# Capstone Proposal v2 - Aegis AI Video Censoring Platform

## 1. Problem Statement

Manually censoring inappropriate content in video and audio for different audiences is a **time-consuming, costly, and inconsistent** process. Parents lack effective, customizable tools to filter content for their children in real-time, while television studios and content creators face significant overhead in producing multiple versions of content for various broadcasting standards. An AI-powered system is required to **automatically detect and censor user-defined improper content** (e.g., profanity, graphic violence) in video streams, providing a reliable, efficient, and customizable solution.

---

## 2. Target Users

### Primary Audience: Parents
- **Goal:** To create a safe viewing environment for their children by filtering inappropriate language, violence, and other mature themes from movies, TV shows, and online videos.
- **Use Case:** Upload a movie clip, activate "Kids Mode" preset, and download a censored version safe for children.

### Secondary Audience: Television Studios & Streaming Services
- **Goal:** To automate the creation of censored versions of content for broadcast television, airline edits, or different regional ratings, thereby reducing manual labor costs and accelerating distribution workflows.
- **Use Case:** Batch process multiple videos with custom profiles for different broadcast standards.

---

## 3. Success Criteria

The success of this project will be measured against the following quantitative and qualitative metrics:

### Technical Metrics

#### Accuracy & Detection Performance
- **Profanity Detection Precision:** >95% (correctly identifying profanity)
- **Profanity Detection Recall:** >90% (not missing instances of profanity)
- **Violence Detection Precision:** >90% (correctly identifying violent scenes)
- **Violence Detection Recall:** >85% (not missing violent scenes)
- **False Positive Rate:** <2% (avoiding over-censorship)
- **Hallucination Rate (STT):** <1% (incorrect transcriptions)

#### Performance & Latency
- **End-to-End Processing (5min video):** P95 latency <90s (target: 60s)
- **Video Upload:** P50 <30s for 10MB file
- **Frame Extraction:** <15s for 5min video (GPU accelerated)
- **AI Detection:** <20s for 5min video (batched API calls)
- **Video Export:** <10s for 5min video (GPU encoding)

#### System Reliability
- **System Uptime:** >99.5% (monthly)
- **API Availability:** >99.9% (weekly)
- **Worker Availability:** >99.0% (average)
- **Queue Availability:** >99.9% (RabbitMQ cluster)

### Product Metrics

#### Task Completion Rate
- **Upload First Video:** >85%
- **Process Video Successfully:** >90%
- **Create Custom Profile:** >40%
- **Export Censored Video:** >75%
- **Activate Kids Mode Preset:** >70%
- **Overall Task Completion:** >80% across all core tasks

#### User Satisfaction
- **System Usability Scale (SUS):** >70 (acceptable usability)
- **CSAT Score:** >4.0/5.0 (80% satisfied)
- **NPS Score:** >30 (industry benchmark)
- **"Would Recommend" Rate:** >60%

### Business Metrics
- **User Activation Rate:** >60% (users who upload + censor first video)
- **Retention (D7):** >30% (users return after 7 days)
- **Paid Conversion:** >5% (upgrade to paid plan)

---

## 4. Technical Architecture

### Architecture Overview

The system is built on a **microservices architecture** with asynchronous processing, designed for scalability, reliability, and performance.

#### Key Architectural Changes Since Week 2

**Week 2 (Initial Proposal):**
- Simple monolithic architecture (single Flask server)
- No authentication (direct API access)
- Synchronous processing (blocking operations)
- Direct AI API calls (no batching)
- No observability (basic logging only)
- Single worker model (no scalability)

**Week 4 (Current Architecture):**
- **Microservices:** Separated frontend (React), API (Flask), workers (Celery), and queue (RabbitMQ)
- **Authentication:** JWT-based auth with Lovable Cloud/Auth0 integration
- **Asynchronous Processing:** RabbitMQ queue with Celery workers for parallel processing
- **Batched AI Calls:** Google Vision API batching (10 frames/request) to reduce latency by 90%
- **Circuit Breaker Pattern:** Fallback to local NSFW model (NudeNet) when Google Vision fails
- **Observability:** CloudWatch/Datadog metrics, structured logging, distributed tracing
- **Auto-scaling:** Kubernetes HPA or AWS ECS Fargate for worker scaling
- **Security Hardening:** Rate limiting, file validation, pre-signed S3 URLs, RBAC

### System Components

#### Frontend Layer
- **Technology:** React 18+ with Vite build tool
- **Hosting:** Lovable Cloud (managed deployment)
- **Features:** Video upload, player, timeline, profile management, export

#### API Layer
- **Technology:** Flask 2.3+ (Python 3.11+)
- **Deployment:** Multiple instances behind load balancer (auto-scaling)
- **Features:** REST API endpoints, JWT authentication, rate limiting, file validation

#### Queue Layer
- **Technology:** RabbitMQ 3.12+ cluster (3 nodes for high availability)
- **Features:** Priority queues (realtime, batch, export), Dead-letter exchange (DLQ), mirrored queues

#### Worker Layer
- **Technology:** Celery 5.3+ with Redis broker
- **Worker Types:**
  - **Frame Extractor:** FFmpeg GPU acceleration (AWS EC2 g4dn.xlarge)
  - **AI Detector:** Google Vision API + OpenAI Whisper API (GPU instances)
  - **Video Compositor:** FFmpeg GPU encoding (blur/mute application)
- **Scaling:** Auto-scaling from 2-20 workers based on queue depth

#### Data Layer
- **PostgreSQL 15+:** Relational data (users, videos, profiles, detections) with pgvector extension (for future RAG)
- **Redis 7.0+:** Cache (detection results, profiles) + Celery broker
- **AWS S3:** Video storage with lifecycle policies (delete after 7-30 days)

#### External Services
- **Google Vision API v1:** Violence/NSFW detection (batched: 10 frames/request)
- **OpenAI Whisper API:** Speech-to-text transcription ($0.006/minute)
- **Fallback:** Local NudeNet model (NSFW detection when API fails)

#### Observability
- **Prometheus + Grafana:** Metrics (P50/P95/P99 latency, error rates, queue depth)
- **CloudWatch Logs:** Structured JSON logging with trace IDs
- **OpenTelemetry:** Distributed tracing across Flask → Celery → Workers

### Processing Pipeline

**5-minute video processing flow:**

1. **Upload (8s):** Client → Pre-signed S3 URL → Direct upload to S3
2. **Job Queue (1s):** API → RabbitMQ → Celery worker picks up job
3. **Frame Extraction (12s):** FFmpeg GPU → Extract 150 frames @ 0.5 FPS → S3
4. **AI Detection (6s):** 
   - Batch 10 frames/request → Google Vision API (15 parallel batches)
   - OpenAI Whisper API → Transcribe audio → Profanity detection
5. **Video Reconstruction (8s):** Download frames → Apply blur/mute → GPU encoding → S3
6. **Export (5s):** Multipart upload to S3 → CloudFront CDN → User download

**Total: ~40s (Target: 60s) ✅**

### Tech Stack Summary

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Frontend** | React + Vite | 18+ / 5+ | Web UI |
| **Backend API** | Flask | 2.3+ | REST API |
| **Workers** | Celery | 5.3+ | Async processing |
| **Queue** | RabbitMQ | 3.12+ | Message broker |
| **Database** | PostgreSQL | 15+ | Relational data + pgvector |
| **Cache** | Redis | 7.0+ | Cache + broker |
| **Storage** | AWS S3 | Standard | Video storage |
| **Video Processing** | FFmpeg | 6.0+ | Frame extraction, encoding |
| **AI Detection** | Google Vision API | v1 | Violence/NSFW detection |
| **STT** | OpenAI Whisper | API v1 | Speech-to-text |
| **Monitoring** | Prometheus + Grafana | Latest | Metrics & dashboards |

---

## 5. Architecture Diagram

See `docs/architecture-diagram-v2.md` for detailed Mermaid diagram showing:
- Client layer (React + Vite)
- Ingress & security (Load balancer, WAF, Auth)
- API layer (Flask instances)
- Queue layer (RabbitMQ cluster)
- Worker layer (Celery workers)
- External services (Google Vision, Whisper, S3)
- Data layer (PostgreSQL, Redis)
- Observability (CloudWatch, Prometheus, OpenTelemetry)

---

## 6. Risk Assessment

### Top 5 Critical Risks

#### Risk #1: Google Vision API Rate Limits / Downtime
**Risk Score:** 30 (L: 5, I: 6)

**Mitigation:**
- Request batching (10 frames/request) reduces API calls by 90%
- Circuit breaker pattern (switch to fallback after 5 errors in 60s)
- Fallback to local NudeNet model
- Upgrade to paid tier for higher limits

**Early Warning:** API error rate >5%, queue depth >500 jobs

#### Risk #2: High Latency Exceeding Targets
**Risk Score:** 24 (L: 4, I: 6)

**Mitigation:**
- GPU acceleration for frame extraction (30s → 12s)
- Batched API calls (45s → 6s)
- GPU encoding for video export (20s → 8s)
- Progress indicators and email notifications

**Early Warning:** P95 latency >90s, task completion rate <75%

#### Risk #3: AI Model Accuracy Issues
**Risk Score:** 30 (L: 5, I: 6)

**Mitigation:**
- State-of-the-art models (Whisper, Google Vision)
- Confidence thresholds (adjustable per profile)
- User feedback loop ("Mark as False Positive")
- Continuous retraining with user feedback

**Early Warning:** False positive rate >2%, precision <95%, recall <90%

#### Risk #4: Scalability Bottleneck
**Risk Score:** 20 (L: 4, I: 5)

**Mitigation:**
- RabbitMQ cluster (3 nodes, mirrored queues)
- Auto-scaling workers (Kubernetes HPA: 2-20 instances)
- Alternative: Migrate to AWS SQS if needed

**Early Warning:** Queue depth >500 jobs, worker availability <95%

#### Risk #5: Child Safety Failure
**Risk Score:** 24 (L: 4, I: 6)

**Mitigation:**
- Target recall >90% (profanity), >85% (violence)
- Multiple detection passes (STT + keyword + NLP)
- User custom keywords
- Transparency: Show confidence scores, warning messages

**Early Warning:** Recall <90%, user reports of missed content

See `docs/risk-assessment.md` for complete risk analysis (12 risks total).

---

## 7. Research Plan

### Phase 1: Infrastructure Foundation (Weeks 4-5)
**Duration:** 2 weeks

**Key Activities:**
- Database schema & migrations (PostgreSQL + pgvector)
- Authentication & authorization (JWT, RBAC)
- Structured logging infrastructure (CloudWatch, trace IDs)
- Monitoring & metrics (Prometheus, Grafana, OpenTelemetry)
- RabbitMQ queue infrastructure (cluster setup, DLQ)

**Deliverables:**
- Database schema with RLS policies
- Auth middleware with JWT validation
- Logging pipeline with trace correlation
- Metrics dashboard (8 core metrics)
- RabbitMQ cluster with mirrored queues

### Phase 2: Core Processing Pipeline (Weeks 6-8)
**Duration:** 3 weeks

**Key Activities:**
- Video upload with drag-and-drop (pre-signed S3 URLs)
- HTML5 video player with custom controls
- Profanity detection pipeline (Whisper API + keyword matching)
- Visual violence detection pipeline (Google Vision API + batching)
- Timeline with censored markers
- Kids Mode preset (one-click activation)
- Export censored video (GPU encoding)

**Deliverables:**
- Functional upload → process → export pipeline
- Profanity detection with >95% precision, >90% recall
- Violence detection with >90% precision, >85% recall
- End-to-end latency <90s (P95) for 5min video

### Phase 3: User Features & Profiles (Weeks 9-10)
**Duration:** 2 weeks

**Key Activities:**
- Profile management (CRUD interface)
- Custom keyword blocklist editor
- Processing queue UI with status indicators
- False positive override button

**Deliverables:**
- Profile CRUD API + UI
- Custom keyword management
- Real-time queue status updates
- Feedback collection system

### Phase 4: Optimization & Polish (Weeks 11-12)
**Duration:** 2 weeks

**Key Activities:**
- Performance optimization (GPU acceleration, API batching)
- Circuit breaker implementation (fallback to NudeNet)
- Caching strategy (Redis cache for transcripts/frames)
- Rate limiting & security hardening
- GDPR compliance (data retention, right to erasure)

**Deliverables:**
- Optimized processing pipeline (<60s target)
- Circuit breaker with fallback
- Cache hit rate >25% (transcripts), >12% (frames)
- Security audit passed (OWASP Top 10)
- GDPR compliance features

### Phase 5: User Study & Finalization (Weeks 13-15)
**Duration:** 3 weeks

**Key Activities:**
- User testing (5 participants, 3-5 tasks)
- Golden Set test suite (50+ test cases)
- Metrics collection (all 8 core metrics)
- Bug fixes and final optimizations
- Final project report

**Deliverables:**
- User testing report (SUS score >70, CSAT >4.0)
- Golden Set validation (accuracy targets met)
- Metrics dashboard (all metrics tracked)
- Final MVP application
- Comprehensive capstone report

---

## 8. User Study Plan

### Objective
To assess the usability, effectiveness, and user satisfaction of Aegis AI with its primary target audience before public launch.

### Participants
- **Target:** 5 participants (3-4 parents, 1-2 content creators/studios)
- **Recruitment Criteria:**
  - Parents: Have children aged 6-16, regularly monitor media consumption
  - Studios: Work with video production/distribution
  - Mix of tech-savvy and tech-novice users

### Methodology
**Duration:** 45-60 minutes per session  
**Location:** Remote (Zoom/Google Meet) or in-person lab

**Session Structure:**
1. **Introduction (5 min):** Explain purpose, obtain informed consent
2. **Task Scenarios (30-40 min):** 3-5 tasks:
   - Task 1: Upload and process first video (core flow)
   - Task 2: Activate Kids Mode preset
   - Task 3: Add custom keyword to blocklist
   - Task 4: Review and export censored video
   - Task 5: Report false positive (optional)
3. **Post-Session Survey (10 min):** SUS questionnaire, CSAT, open-ended questions

### Success Criteria
- **Task Completion Rate:** >70% overall
- **SUS Score:** >70 (acceptable usability)
- **CSAT Score:** >4.0/5.0 (80% satisfied)
- **Time on Task:** Within limits (upload <30s, process <90s, export <10s)

### IRB Considerations
- ✅ **Informed Consent:** Consent form detailing procedures, data handling, right to withdraw
- ✅ **Data Privacy:** All data anonymized, screen recordings deleted after 6 months
- ✅ **Benefit vs Risk:** Minimal risk (brief exposure to inappropriate content), outweighed by benefit
- ✅ **Participant Selection:** Diverse group (age, gender, technical proficiency)

See `docs/evaluation-plan-v2.md` for detailed user testing protocol.

---

## 9. Evaluation Plan

### Golden Set Test Suite
- **Total Test Cases:** 50+ (expand from 10 initial cases)
- **Distribution:**
  - 70% Typical cases (standard use cases)
  - 20% Edge cases (accents, noise, fast speech)
  - 10% Adversarial cases (evasion attempts, quick cuts)

### Core Metrics (8 Total)

1. **End-to-End Latency:** P95 <90s (target: 60s)
2. **Profanity Detection Accuracy:** Precision >95%, Recall >90%
3. **Task Completion Rate:** >80% overall
4. **SUS Score:** >70 (acceptable usability)
5. **System Uptime:** >99.5% (monthly)
6. **User Activation Rate:** >60% (upload + censor first video)
7. **False Positive Override Rate:** <5% (indicates accuracy)
8. **CSAT Score:** >4.0/5.0 (80% satisfied)

### Measurement Methodology
- **In-app Analytics:** Track user interactions (Mixpanel/Amplitude)
- **Backend Metrics:** P95 latency, accuracy rates from processing logs
- **User Surveys:** In-app prompts + email surveys (weekly for first month)
- **External Monitoring:** Uptime monitoring (Pingdom/UptimeRobot)

### Reporting Frequency
- **Daily:** Technical metrics (latency, uptime, error rates)
- **Weekly:** Product metrics (task completion, time on task)
- **Monthly:** Business metrics (CSAT, NPS, recommendation rate)

See `docs/evaluation-plan-v2.md` for complete evaluation plan.

---

## 10. Cost Model

### Monthly Infrastructure Costs (MVP - Low Traffic)

| Service | Provider | Cost Estimate |
|---------|----------|---------------|
| **Google Vision API** | Google Cloud | $1.50/1k requests (after free tier) |
| **OpenAI Whisper API** | OpenAI | $0.006/minute (or free local) |
| **Redis** | AWS ElastiCache | ~$15/month (t3.micro) |
| **PostgreSQL** | AWS RDS | ~$30/month (db.t3.medium) |
| **AWS S3** | AWS | ~$0.023/GB/month + egress |
| **RabbitMQ** | CloudAMQP or self-hosted | ~$20/month (CloudAMQP) or free |
| **CloudFront CDN** | AWS | ~$0.085/GB (first 10TB) |
| **GPU Workers** | AWS EC2 g4dn.xlarge | ~$0.50-1.50/hr (on-demand) |

**Total Monthly Cost (MVP):** ~$100-150/month (low traffic)  
**Total Monthly Cost (Scale):** ~$500-1000/month (1000+ users)

### Cost Optimization Strategies
- **API Batching:** Reduce Google Vision API calls by 90% (10 frames/request)
- **Caching:** Redis cache for transcripts (25% hit rate) and frames (12% hit rate)
- **GPU Optimization:** GPU acceleration reduces processing time (lower worker costs)
- **S3 Lifecycle:** Delete videos after retention period (reduce storage costs)

See `docs/cost-model-v2.md` for detailed cost breakdown.

---

## 11. Timeline Summary

| Phase | Duration | Key Deliverables | Status |
|-------|----------|------------------|--------|
| **Phase 1: Infrastructure** | Weeks 4-5 | Database, Auth, Logging, Monitoring, Queue | ✅ In Progress |
| **Phase 2: Core Pipeline** | Weeks 6-8 | Upload, Player, Profanity/Violence Detection, Export | 🔄 Next |
| **Phase 3: User Features** | Weeks 9-10 | Profiles, Custom Keywords, Queue UI | ⏳ Planned |
| **Phase 4: Optimization** | Weeks 11-12 | Performance, Security, GDPR Compliance | ⏳ Planned |
| **Phase 5: User Study** | Weeks 13-15 | Testing, Metrics, Final Report | ⏳ Planned |

**Target MVP Launch:** Week 15  
**Demo Day:** Week 15

---

## 12. Key Differences from v1 Proposal

### Architecture Evolution
- **Monolithic → Microservices:** Separated concerns for scalability
- **Synchronous → Asynchronous:** Queue-based processing for performance
- **Direct API Calls → Batched:** Reduced API calls by 90%
- **No Fallback → Circuit Breaker:** Improved reliability with fallback models

### Technology Updates
- **Flask (not FastAPI):** Team familiarity, sufficient for REST endpoints
- **RabbitMQ (not AWS SQS):** Better control, no vendor lock-in
- **PostgreSQL + pgvector:** Single database for relational + vector search (future RAG)
- **GPU Acceleration:** Dedicated GPU instances for video processing

### Success Criteria Refinement
- **More Granular Metrics:** P50/P95/P99 latency, precision/recall, false positive rate
- **Business Metrics:** CSAT, NPS, activation rate, retention
- **System Reliability:** Uptime, availability, queue depth monitoring

### Risk Mitigation Enhancements
- **API Rate Limits:** Batching + circuit breaker + fallback
- **Latency:** GPU acceleration + parallel workers + caching
- **Accuracy:** User feedback loop + continuous retraining
- **Scalability:** Auto-scaling workers + RabbitMQ cluster

---

## 13. Next Steps

### Immediate (Week 5)
1. Complete infrastructure setup (database, auth, logging, monitoring)
2. Set up RabbitMQ cluster and Celery workers
3. Begin core processing pipeline development

### Short-term (Weeks 6-8)
1. Implement video upload and player
2. Integrate profanity detection (Whisper API)
3. Integrate violence detection (Google Vision API)
4. Build timeline and export functionality

### Medium-term (Weeks 9-12)
1. Add user features (profiles, custom keywords)
2. Optimize performance (GPU, batching, caching)
3. Implement security and GDPR compliance
4. Conduct user testing

### Long-term (Weeks 13-15)
1. Finalize MVP features
2. Complete user study and metrics collection
3. Bug fixes and optimizations
4. Prepare final capstone report

---

## 14. References

- **Architecture Diagram:** `docs/architecture-diagram-v2.md`
- **Architecture Explanation:** `docs/architecture-explanation.md`
- **Backlog:** `docs/backlog-v2.md`
- **Evaluation Plan:** `docs/evaluation-plan-v2.md`
- **Risk Assessment:** `docs/risk-assessment.md`
- **Cost Model:** `docs/cost-model-v2.md`
- **Feature Roadmap:** `docs/feature-roadmap.md`

---

**Last Updated:** Week 4  
**Next Review:** Week 6
