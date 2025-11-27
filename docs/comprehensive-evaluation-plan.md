# Comprehensive Evaluation Plan - MVP

## Executive Summary

This document outlines the complete evaluation strategy for Aegis AI Video Censoring Platform MVP, covering core metrics, test suites, user testing protocols, regression testing, and a measurement timeline from Weeks 4-15.

**Product:** AI-powered video censoring platform for parents and studios  
**MVP Features:** Video upload, profanity detection, violence detection, custom profiles, presets, export  
**Target Users:** Parents (primary), TV studios/content creators (secondary)

---

## 1. Core Metrics (5-8 Metrics with Targets)

### Metric 1: End-to-End Processing Latency (P95)
**Category:** Technical Performance  
**Definition:** 95th percentile latency from video upload to censored video ready for download  
**Target:** <90 seconds for 5-minute video (P95)  
**Current Baseline:** ~118 seconds  
**Measurement:** 
- Track: Upload time + Processing time + Export time
- Source: Backend metrics (CloudWatch/Grafana)
- Frequency: Continuous (real-time monitoring)

**Success Criteria:**
- ✅ P50 (median): <60 seconds
- ✅ P95: <90 seconds
- ✅ P99: <120 seconds

---

### Metric 2: Profanity Detection Accuracy (Precision & Recall)
**Category:** AI Model Performance  
**Definition:** 
- **Precision:** % of detected profanity that is actually profanity
- **Recall:** % of actual profanity that is detected

**Targets:**
- Precision: >95%
- Recall: >90%
- False Positive Rate: <2%

**Measurement:**
- Test Set: Golden Set (50+ curated videos with ground truth)
- Frequency: Weekly automated tests + manual review
- Source: Model evaluation pipeline

**Success Criteria:**
- ✅ Precision >95% AND Recall >90% on Golden Set
- ✅ False positive rate <2% (user-reported overrides)
- ✅ No critical misses (child safety incidents)

---

### Metric 3: Task Completion Rate (Core User Flow)
**Category:** Product Usability  
**Definition:** Percentage of users who successfully complete the critical path: Upload → Process → Export  
**Target:** >75% completion rate  
**Measurement:**
- Track: `(users who export video) / (users who upload video)`
- Source: Frontend analytics (Mixpanel/Amplitude)
- Frequency: Daily aggregation

**Success Criteria:**
- ✅ Upload → Process: >85%
- ✅ Process → Export: >75%
- ✅ End-to-end completion: >75%

---

### Metric 4: System Usability Scale (SUS) Score
**Category:** User Satisfaction  
**Definition:** Standard SUS questionnaire score (0-100 scale)  
**Target:** >70 (acceptable usability)  
**Measurement:**
- Method: Post-session survey (10-item SUS questionnaire)
- Frequency: Week 7 user testing + Week 15 final testing
- Sample Size: Minimum 5 users (Week 7), 15 users (Week 15)

**Success Criteria:**
- ✅ Week 7: >65 (acceptable threshold)
- ✅ Week 15: >70 (target for MVP launch)
- ✅ Consistent improvement from Week 7 → Week 15

---

### Metric 5: System Uptime & Availability
**Category:** Technical Reliability  
**Definition:** Percentage of time system is operational and serving requests  
**Target:** >99.5% monthly uptime  
**Measurement:**
- Track: `(Total Time - Downtime) / Total Time`
- Source: Uptime monitoring (Pingdom/CloudWatch)
- Frequency: Continuous, reported monthly

**Success Criteria:**
- ✅ Monthly uptime: >99.5%
- ✅ API availability: >99.9%
- ✅ No critical downtime events (>30 minutes)

---

### Metric 6: User Activation Rate
**Category:** Product Adoption  
**Definition:** Percentage of users who complete first video upload and processing  
**Target:** >60% activation rate  
**Measurement:**
- Track: `(users who process first video) / (users who sign up)`
- Source: User analytics (Mixpanel/Amplitude)
- Frequency: Weekly aggregation

**Success Criteria:**
- ✅ First upload: >70% of sign-ups
- ✅ First processing: >60% of sign-ups
- ✅ Week 1 retention: >30% return within 7 days

---

### Metric 7: False Positive Override Rate
**Category:** Model Quality / User Experience  
**Definition:** Percentage of detections that users mark as false positives  
**Target:** <5% override rate  
**Measurement:**
- Track: `(user-reported false positives) / (total detections)`
- Source: User feedback ("Mark as False Positive" button)
- Frequency: Real-time tracking, weekly aggregation

**Success Criteria:**
- ✅ Override rate: <5% (indicates model accuracy)
- ✅ User complaints: <2% of users report false positives
- ✅ Trend: Decreasing over time (model improvement)

---

### Metric 8: CSAT Score (Customer Satisfaction)
**Category:** Business Metrics  
**Definition:** Average satisfaction score (1-5 scale) after completing video processing  
**Target:** >4.0/5.0 (80% satisfied)  
**Measurement:**
- Method: In-app survey after video export
- Questions: 5 satisfaction questions (profanity accuracy, violence accuracy, ease of use, speed, overall)
- Frequency: Continuous (after each export), reported weekly

**Success Criteria:**
- ✅ CSAT score: >4.0/5.0
- ✅ Satisfaction rate: >75% rate 4 or 5 (Satisfied/Very Satisfied)
- ✅ Trend: Improving over time

---

## 2. Golden Set Plan (Structured Test Suite)

### Test Case Distribution

| Category | Percentage | Count (50 total) | Purpose |
|----------|-----------|------------------|---------|
| **Typical** | 70% | ~35 cases | Validate standard use cases with clear, unambiguous content |
| **Edge** | 20% | ~10 cases | Test model robustness (accents, noise, edge cases) |
| **Adversarial** | 10% | ~5 cases | Test evasion attempts and adversarial scenarios |

### Typical Cases (70% - 35 test cases)

**Focus Areas:**
- Explicit profanity in clear speech (American English)
- Graphic violence scenes (blood, weapons, fighting)
- Clean family content (false positive control)
- Mixed content (profanity + violence combined)
- PG-13 content (mild profanity, implied violence)
- Various video formats (MP4, WebM, different resolutions)
- Different video lengths (30s, 2min, 5min, 10min)

**Sample Test Cases:**
1. **TC-TYP-001:** 3-minute movie clip with 5-7 explicit profanity instances (f-words, s-words)
2. **TC-TYP-002:** 2-minute action movie clip with visible blood, weapons, fighting
3. **TC-TYP-003:** 4-minute educational video (kids' show) - zero false positives
4. **TC-TYP-004:** 5-minute movie clip with both profanity (8 instances) and violence (2 scenes)
5. **TC-TYP-005:** 6-minute PG-13 clip with mild profanity (damn, hell, crap)

**Success Criteria per Typical Case:**
- Profanity detection: Precision ≥95%, Recall ≥90%
- Violence detection: Precision ≥90%, Recall ≥85%
- False positive rate: <2%
- Processing time: <90s (P95) for 5min video

### Edge Cases (20% - 10 test cases)

**Focus Areas:**
- Heavy accents (British English, regional dialects)
- Background noise and music
- Fast speech / rapid dialogue
- Ambiguous content (martial arts, sports vs. violence)
- Multiple speakers overlapping
- Low quality / compressed video
- Different audio qualities (mono, stereo, surround)

**Sample Test Cases:**
1. **TC-EDG-001:** British English accent with 4 profanity instances
2. **TC-EDG-002:** Loud background music with 3 profanity instances
3. **TC-EDG-003:** Rapid-fire dialogue with 5 profanity instances
4. **TC-EDG-004:** Martial arts training video (sports context, not violence)
5. **TC-EDG-005:** Multiple speakers overlapping, 2 profanity instances

**Success Criteria per Edge Case:**
- Acceptable degradation: Recall ≥75% (vs. 90% typical)
- No false positives from edge conditions
- Processing completes successfully (no crashes)
- Graceful handling of edge cases

### Adversarial Cases (10% - 5 test cases)

**Focus Areas:**
- Intentional misspelling / phonetic evasion
- Quick cuts / flash frames (<0.5s)
- Pre-censored content (already beeped/blurred)
- Foreign language mixed with English
- Low quality / heavily compressed video

**Sample Test Cases:**
1. **TC-ADV-001:** Intentional mispronunciation ("fudge" instead of profanity)
2. **TC-ADV-002:** Rapid cuts with brief violent frames (4 instances)
3. **TC-ADV-003:** TV broadcast version (already censored)
4. **TC-ADV-004:** Bilingual dialogue (English + Spanish)
5. **TC-ADV-005:** 480p compressed video with 3 profanity instances

**Success Criteria per Adversarial Case:**
- System handles gracefully (no crashes)
- Detection rate ≥50% (lower threshold for adversarial)
- No false positives from adversarial techniques
- User can add custom keywords if needed

### Golden Set Execution Plan

**Week 4-5:** Create initial 15 test cases (10 typical, 3 edge, 2 adversarial)  
**Week 6:** Expand to 50+ test cases, establish automated test suite  
**Week 7-15:** Run weekly automated tests, add new cases based on user feedback

**Test Execution:**
- **Automated:** Run nightly on CI/CD pipeline
- **Manual Review:** Weekly review of failures, edge cases
- **Reporting:** Weekly accuracy report (precision, recall, false positive rate)

**Test Data Management:**
- Store test videos in S3 (private bucket)
- Ground truth annotations in PostgreSQL
- Version control for test cases (Git)
- Automated comparison: Expected vs. Actual detections

---

## 3. Week 7 User Testing Protocol

### Overview
**Timeline:** Week 7 (early MVP validation)  
**Duration:** 45-60 minutes per session  
**Participants:** 5 users (minimum 3, recommended 5)  
**Location:** Remote (Zoom/Google Meet) or in-person lab

### Participant Profile

**Target:** Primary users (Parents)
- Have children aged 6-16
- Regularly monitor children's media consumption
- Use video streaming platforms (Netflix, YouTube)
- Mix of tech-savvy and tech-novice users

**Recruitment:**
- Screener: "Do you have children who watch videos/movies?" (Yes)
- Diversity: Age 25-50, balanced gender, varied technical proficiency

### Testing Tasks (4 Core Tasks)

#### Task 1: Upload and Process First Video
**Objective:** Test core workflow - upload → process → review  
**Scenario:** "You want to censor a 2-minute movie clip so your child can watch it safely."

**Steps:**
1. Navigate to upload page
2. Select video file (provided: `test-clip-1.mp4` - 2min, contains profanity)
3. Upload video
4. Wait for processing to complete
5. Review censored video in player

**Success Criteria:**
- ✅ Uploads video without errors
- ✅ Processing completes within 90 seconds
- ✅ Can view censored video in player
- ✅ Timeline shows red bars indicating censored segments

**Time Limit:** 5 minutes  
**Expected Completion:** >85%

**Data Captured:**
- Upload time (seconds)
- Processing time (seconds)
- Errors encountered
- Task completion (Yes/No)

---

#### Task 2: Activate Kids Mode Preset
**Objective:** Test preset activation and verify stricter censorship  
**Scenario:** "You want to use the 'Kids Mode' preset for stricter censorship."

**Steps:**
1. Navigate to presets page (or find preset selector)
2. Select "Kids Mode" preset
3. Reprocess video (if needed)
4. Review changes in censored content

**Success Criteria:**
- ✅ Finds preset selector within 30 seconds
- ✅ Successfully activates Kids Mode
- ✅ Reprocessing completes successfully
- ✅ Censored content reflects stricter settings

**Time Limit:** 3 minutes  
**Expected Completion:** >70%

**Data Captured:**
- Time to find preset (seconds)
- Time to activate (seconds)
- User confusion points (observer notes)
- Task completion (Yes/No)

---

#### Task 3: Add Custom Keyword to Blocklist
**Objective:** Test custom keyword management  
**Scenario:** "The word 'darn' is not on the default blocklist, but you want to censor it."

**Steps:**
1. Navigate to keyword management interface
2. Add "darn" to custom blocklist
3. Save profile
4. Reprocess video (or verify it's applied)
5. Verify "darn" is now censored

**Success Criteria:**
- ✅ Finds keyword interface within 1 minute
- ✅ Successfully adds "darn" to blocklist
- ✅ Reprocessing detects and censors "darn"
- ✅ Timeline shows new censored segment

**Time Limit:** 4 minutes  
**Expected Completion:** >60%

**Data Captured:**
- Time to find interface (seconds)
- Time to add keyword (seconds)
- Number of incorrect attempts
- Task completion (Yes/No)

---

#### Task 4: Export Censored Video
**Objective:** Test export functionality  
**Scenario:** "You're satisfied with the censored video. Export it so you can download it."

**Steps:**
1. Review censored video (play/pause to verify)
2. Locate export button
3. Initiate export
4. Wait for export to complete
5. Download exported video

**Success Criteria:**
- ✅ Can play/pause video and verify censoring
- ✅ Finds export button within 30 seconds
- ✅ Export completes within 60 seconds
- ✅ Successfully downloads exported video file

**Time Limit:** 3 minutes  
**Expected Completion:** >75%

**Data Captured:**
- Time to find export button (seconds)
- Export completion time (seconds)
- Download success (Yes/No)
- Task completion (Yes/No)

---

### Data Collection Instruments

#### Quantitative Metrics
1. **Task Completion Rate:** % of tasks completed successfully
2. **Time on Task:** Average time per task (seconds)
3. **Error Count:** Number of errors per task
4. **SUS Score:** System Usability Scale (10-item questionnaire, 0-100 scale)
5. **CSAT Score:** Customer Satisfaction (5 questions, 1-5 scale)

#### Qualitative Data
1. **Think-Aloud Protocol:** Participants verbalize thoughts while using system
2. **Post-Task Interviews:** 5-minute discussion after each task
3. **Post-Session Survey:** Comprehensive feedback form
4. **Screen Recording:** Record entire session for later analysis
5. **Observer Notes:** Researcher notes on confusion points, errors, workarounds

#### Tools
- **Screen Recording:** OBS Studio, Zoom recording, or Loom
- **Survey Tools:** Google Forms, Typeform, or Qualtrics
- **Analytics:** Mixpanel/Amplitude for in-app behavior tracking
- **Note-Taking:** Shared Google Doc or Notion for observer notes

### Consent & Privacy

**Informed Consent Required:**
- Study purpose: Testing video censoring tool usability
- Procedure: 4 tasks, 45-60 minutes
- Risks: Brief exposure to uncensored inappropriate content
- Benefits: Improve tool for parents and content creators
- Confidentiality: All data anonymized, recordings deleted after 6 months
- Right to withdraw: Can stop at any time

**Privacy Protections:**
- Use pseudo-IDs (P001, P002, etc.)
- No personal info in recordings
- Test videos only (not participant's personal videos)
- Encrypted storage, delete after 6 months

---

## 4. Regression Testing Outline

### Purpose
Ensure new features and bug fixes don't break existing functionality.

### Test Categories

#### Category 1: Core Functionality Regression
**Frequency:** Before every release  
**Scope:** Critical path features

**Test Cases:**
1. **Video Upload:** Upload MP4 file (5MB, 2min) → Verify success
2. **Profanity Detection:** Process video with 5 profanity instances → Verify all detected
3. **Violence Detection:** Process video with 2 violent scenes → Verify both detected
4. **Profile Creation:** Create custom profile → Verify saved and activated
5. **Preset Activation:** Activate Kids Mode → Verify stricter censorship applied
6. **Export:** Export censored video → Verify download successful

**Success Criteria:** All 6 test cases pass (100% pass rate)

---

#### Category 2: API Endpoint Regression
**Frequency:** Before every backend release  
**Scope:** All API endpoints

**Test Cases:**
1. **POST /api/v1/upload:** Upload video → Verify 200 OK, job ID returned
2. **GET /api/v1/status/{job_id}:** Check status → Verify status updates correctly
3. **GET /api/v1/result/{job_id}:** Get result → Verify censored video URL
4. **POST /api/v1/profiles:** Create profile → Verify profile saved
5. **GET /api/v1/profiles:** List profiles → Verify user's profiles returned
6. **POST /api/v1/export:** Export video → Verify export job created

**Success Criteria:** All endpoints return expected status codes and data

---

#### Category 3: Performance Regression
**Frequency:** Weekly  
**Scope:** Latency and throughput

**Test Cases:**
1. **Latency Test:** Process 5-minute video → Verify P95 <90s
2. **Concurrent Users:** 10 simultaneous uploads → Verify all process successfully
3. **Queue Depth:** Process 50 videos → Verify queue doesn't exceed 1000 jobs
4. **API Response Time:** 100 API calls → Verify P95 <500ms

**Success Criteria:** All performance metrics meet targets

---

#### Category 4: Model Accuracy Regression
**Frequency:** Before model updates  
**Scope:** AI detection accuracy

**Test Cases:**
1. **Golden Set:** Run 50 test cases → Verify precision/recall maintained
2. **False Positive Rate:** Process 10 clean videos → Verify <2% false positives
3. **False Negative Rate:** Process 10 videos with profanity → Verify >90% recall

**Success Criteria:** Accuracy metrics don't degrade >2% from baseline

---

#### Category 5: Security Regression
**Frequency:** Before every release  
**Scope:** Authentication and authorization

**Test Cases:**
1. **Unauthenticated Access:** Access API without JWT → Verify 401 Unauthorized
2. **Cross-User Access:** User A tries to access User B's videos → Verify 403 Forbidden
3. **Rate Limiting:** 100 requests/minute → Verify 429 Too Many Requests
4. **File Validation:** Upload malicious file → Verify rejection

**Success Criteria:** All security tests pass (100% pass rate)

---

### Regression Test Execution

**Automation:**
- **Unit Tests:** pytest (Python), Jest (React) - Run on every commit
- **Integration Tests:** API tests with pytest - Run on every PR
- **E2E Tests:** Playwright/Cypress - Run nightly
- **Performance Tests:** Load testing with Locust - Run weekly

**Manual Testing:**
- **Smoke Tests:** Before every release (15 minutes)
- **Full Regression:** Before major releases (2 hours)

**Test Reporting:**
- **Daily:** Automated test results (CI/CD dashboard)
- **Weekly:** Test summary report (pass/fail rates)
- **Before Release:** Full regression test report

---

## 5. Measurement Timeline (Weeks 4-15)

### Week 4-5: Foundation & Baseline
**Activities:**
- ✅ Set up monitoring infrastructure (CloudWatch, Grafana, Prometheus)
- ✅ Implement core metrics tracking (latency, accuracy, uptime)
- ✅ Create initial Golden Set (15 test cases)
- ✅ Establish baseline measurements

**Deliverables:**
- Monitoring dashboard (real-time metrics)
- Baseline metrics report (current performance)
- Initial Golden Set test cases

**Metrics Tracked:**
- P95 latency (baseline: ~118s)
- Profanity detection accuracy (baseline: ~85% estimated)
- System uptime (baseline: N/A, not deployed)

---

### Week 6: Golden Set Expansion & Automation
**Activities:**
- ✅ Expand Golden Set to 50+ test cases
- ✅ Set up automated test suite (CI/CD integration)
- ✅ Implement regression testing framework
- ✅ Establish weekly test execution schedule

**Deliverables:**
- Complete Golden Set (50+ test cases)
- Automated test suite (runs nightly)
- Regression testing framework

**Metrics Tracked:**
- Golden Set accuracy (precision, recall, false positive rate)
- Automated test pass rate (target: >95%)

---

### Week 7: User Testing Round 1
**Activities:**
- ✅ Recruit 5 participants (parents)
- ✅ Conduct usability testing sessions (4 tasks)
- ✅ Collect quantitative data (SUS, CSAT, task completion)
- ✅ Analyze findings and identify top 5 UX issues

**Deliverables:**
- User testing report (findings, metrics, recommendations)
- Prioritized UX issues list
- SUS score (target: >65)
- CSAT score (target: >3.5/5.0)

**Metrics Tracked:**
- Task completion rate (target: >70%)
- SUS score (target: >65)
- CSAT score (target: >3.5/5.0)
- Time on task (baseline)

---

### Week 8-9: UX Improvements & Optimization
**Activities:**
- ✅ Fix top 5 UX issues from Week 7 testing
- ✅ Optimize processing latency (GPU acceleration, batching)
- ✅ Improve model accuracy (fine-tuning, feedback loop)
- ✅ Run regression tests (verify no breakage)

**Deliverables:**
- UX improvements implemented
- Performance optimizations deployed
- Regression test results (all passing)

**Metrics Tracked:**
- P95 latency (target: <90s)
- Profanity detection accuracy (target: >95% precision, >90% recall)
- Task completion rate improvement (target: +10% vs. Week 7)

---

### Week 10-11: Scale Testing & Performance Validation
**Activities:**
- ✅ Load testing (100 concurrent users)
- ✅ Performance validation (meet all latency targets)
- ✅ Golden Set accuracy validation (meet all accuracy targets)
- ✅ System uptime validation (target: >99.5%)

**Deliverables:**
- Load test report
- Performance validation report
- Accuracy validation report

**Metrics Tracked:**
- P95 latency (target: <90s) ✅
- Profanity detection accuracy (target: >95% precision, >90% recall) ✅
- System uptime (target: >99.5%) ✅
- Concurrent user capacity (target: 100 users)

---

### Week 12-13: User Testing Round 2 (Beta)
**Activities:**
- ✅ Recruit 10 beta users (mix of parents and studios)
- ✅ Conduct usability testing (improved workflows)
- ✅ Collect feedback on improvements
- ✅ Measure SUS/CSAT improvement

**Deliverables:**
- Beta testing report
- SUS score (target: >70) ✅
- CSAT score (target: >4.0/5.0) ✅
- Feature usage analytics

**Metrics Tracked:**
- Task completion rate (target: >80%)
- SUS score (target: >70) ✅
- CSAT score (target: >4.0/5.0) ✅
- User activation rate (target: >60%)

---

### Week 14: Final Regression & Pre-Launch Validation
**Activities:**
- ✅ Full regression test suite (all categories)
- ✅ Final performance validation (all metrics meet targets)
- ✅ Security audit (all security tests pass)
- ✅ Golden Set final validation (50+ test cases)

**Deliverables:**
- Pre-launch validation report
- Final metrics dashboard (all targets met)
- Go/No-Go decision criteria

**Metrics Tracked:**
- All 8 core metrics (verify all meet targets)
- Regression test pass rate (target: 100%)
- Security test pass rate (target: 100%)

---

### Week 15: Final User Testing & Launch
**Activities:**
- ✅ Final user testing (15 participants)
- ✅ Measure final SUS/CSAT scores
- ✅ Validate all success criteria met
- ✅ Launch MVP

**Deliverables:**
- Final evaluation report
- Launch readiness assessment
- Success metrics validation

**Metrics Tracked:**
- All 8 core metrics (final validation)
- SUS score (target: >70) ✅
- CSAT score (target: >4.0/5.0) ✅
- User activation rate (target: >60%) ✅

---

## Success Criteria Summary

### MVP Launch Criteria (Week 15)
All metrics must meet targets:

| Metric | Target | Status |
|--------|--------|--------|
| P95 Latency (5min video) | <90s | ✅ |
| Profanity Precision | >95% | ✅ |
| Profanity Recall | >90% | ✅ |
| Task Completion Rate | >75% | ✅ |
| SUS Score | >70 | ✅ |
| System Uptime | >99.5% | ✅ |
| User Activation Rate | >60% | ✅ |
| CSAT Score | >4.0/5.0 | ✅ |

**Go/No-Go Decision:** If ≥7 of 8 metrics meet targets → ✅ Launch  
If <7 metrics meet targets → ⚠️ Defer launch, fix critical issues

---

## Reporting & Communication

### Weekly Status Reports
- **Metrics Dashboard:** Real-time (Grafana)
- **Weekly Summary:** Friday email to team (metrics status, risks, blockers)
- **Stakeholder Update:** Monday email to stakeholders (progress, highlights)

### Monthly Evaluation Reports
- **Comprehensive Report:** All metrics, trends, findings
- **Golden Set Results:** Accuracy metrics, new test cases
- **User Testing Insights:** Findings, recommendations
- **Risk Assessment:** Top risks, mitigation status

### Before Launch (Week 15)
- **Final Evaluation Report:** Complete assessment
- **Launch Readiness:** Go/No-Go decision
- **Success Metrics Validation:** All targets met

