# Evaluation Plan v2

## Success Metrics

### Product Metrics

#### Task Completion Rate
**Definition:** Percentage of users who successfully complete key tasks without abandoning the workflow.

| Task | Target | Measurement Method |
|------|--------|-------------------|
| **Upload First Video** | >85% | Track: `(users who upload video) / (users who visit upload page)` |
| **Process Video Successfully** | >90% | Track: `(videos processed without error) / (videos uploaded)` |
| **Create Custom Profile** | >40% | Track: `(users who create profile) / (users who complete 3+ videos)` |
| **Export Censored Video** | >75% | Track: `(videos exported) / (videos processed)` |
| **Activate Kids Mode Preset** | >70% | Track: `(users who try Kids Mode) / (users who upload first video)` |

**Success Criteria:** 
- Overall task completion rate: **>80%** across all core tasks
- Critical path (upload → process → export): **>75%** completion rate

---

#### Time on Task
**Definition:** Average time users spend completing key tasks (target: minimize while maintaining accuracy).

| Task | Target | Current Baseline | Measurement |
|------|--------|------------------|-------------|
| **Upload Video** | <30s | ~45s | Time from "Choose File" to "Upload Started" |
| **Process 5min Video** | <60s | ~118s | Time from upload complete to processing complete |
| **Create Custom Profile** | <2min | N/A | Time from "Create Profile" to "Save" |
| **Add Custom Keyword** | <30s | N/A | Time from "Add Keyword" to "Saved" |
| **Export Video** | <10s | ~15s | Time from "Export" click to download starts |
| **Find & Activate Preset** | <15s | N/A | Time from landing on presets page to activation |

**Success Criteria:**
- **P50 (median) time on task:** Meet all targets above
- **P95 (95th percentile) time on task:** <2x target (e.g., <120s for 5min video processing)
- **User satisfaction threshold:** Users rate task speed as "Acceptable" or better (>3/5)

---

### Technical Metrics

#### P95 Latency (95th Percentile)
**Definition:** 95% of requests complete within this time threshold.

| Component | Target | Current | Measurement |
|-----------|--------|---------|-------------|
| **Video Upload (client → S3)** | <10s | ~15s | Time from file select to S3 upload complete |
| **Frame Extraction (5min video)** | <15s | ~30s | FFmpeg frame extraction completion |
| **AI Detection (profanity + violence)** | <20s | ~45s | Google Vision API + Whisper API total time |
| **Video Reconstruction** | <10s | ~20s | Apply blur/mute + GPU encoding |
| **Export (S3 → CDN)** | <5s | ~8s | Multipart upload to S3 completion |
| **API Response Time** | <500ms | ~800ms | Flask API endpoint response (P95) |
| **Database Query Time** | <100ms | ~150ms | PostgreSQL query execution (P95) |
| **Queue Processing Time** | <5s | ~10s | Time from job queued to worker pickup |

**Success Criteria:**
- **End-to-end (5min video):** P95 latency **<90s** (target: 60s)
- **Critical path (API → Queue → Worker):** P95 latency **<2s**
- **User-facing operations:** P95 latency **<500ms** (upload status, profile updates)

---

#### Accuracy & Hallucination Rate
**Definition:** Precision and recall of AI detection models, plus false positive rate.

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Profanity Detection Precision** | >95% | `(True Positives) / (True Positives + False Positives)` |
| **Profanity Detection Recall** | >90% | `(True Positives) / (True Positives + False Negatives)` |
| **Violence Detection Precision** | >90% | `(Correctly flagged frames) / (All flagged frames)` |
| **Violence Detection Recall** | >85% | `(Correctly flagged frames) / (All violent frames)` |
| **False Positive Rate** | <2% | `(False Positives) / (Total Detections)` |
| **Hallucination Rate (STT)** | <1% | `(Incorrect transcriptions) / (Total transcriptions)` |
| **Over-censorship Rate** | <5% | User-reported "False Positive" overrides / Total detections |

**Measurement Dataset:**
- **Test Set:** 50 curated videos (10min each) with ground truth annotations
  - 20 videos: Explicit profanity (100+ instances)
  - 20 videos: Graphic violence (50+ scenes)
  - 10 videos: Clean content (control group)

**Success Criteria:**
- **Primary (Profanity):** Precision >95% AND Recall >90%
- **Secondary (Violence):** Precision >90% AND Recall >85%
- **User Experience:** False positive rate <2% (critical for user satisfaction)
- **Model Quality:** Hallucination rate <1% (STT accuracy)

---

#### Uptime & Availability
**Definition:** Percentage of time the system is operational and serving requests.

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **System Uptime** | >99.5% | `(Total Time - Downtime) / Total Time` (monthly) |
| **API Availability** | >99.9% | `(Successful API calls) / (Total API calls)` (weekly) |
| **Worker Availability** | >99.0% | `(Active Workers) / (Total Workers)` (average) |
| **Queue Availability** | >99.9% | RabbitMQ cluster uptime (no message loss) |
| **Database Availability** | >99.9% | PostgreSQL primary + replica uptime |
| **External API Reliability** | >99.0% | Google Vision API + OpenAI Whisper API success rate |

**Downtime Definitions:**
- **Critical:** System completely unavailable (0% requests succeed)
- **Degraded:** >10% of requests failing (circuit breaker active)
- **Partial:** Specific features unavailable (e.g., AI detection down, fallback active)

**Success Criteria:**
- **Monthly Uptime:** >99.5% (max ~3.6 hours downtime/month)
- **No Critical Downtime:** >99.9% (max ~43 minutes/month)
- **Graceful Degradation:** System operates in degraded mode (fallback models) >99.9% of time

---

### Business Metrics

#### CSAT (Customer Satisfaction Score)
**Definition:** Users rate their satisfaction on a 1-5 scale after completing a core task.

**Measurement:**
- **In-app survey:** After video export, prompt: "How satisfied are you with this censored video?"
  - Scale: 1 (Very Dissatisfied) → 5 (Very Satisfied)
- **Post-session survey:** After first week of usage, email survey with 5 questions

**Target:** 
- **CSAT Score:** >4.0/5.0 (80% satisfied)
- **Satisfaction Rate:** >75% rate 4 or 5 (Satisfied/Very Satisfied)

**Questions:**
1. "How satisfied are you with the accuracy of profanity detection?" (1-5)
2. "How satisfied are you with the accuracy of violence detection?" (1-5)
3. "How easy was it to use the video censoring tool?" (1-5)
4. "How fast was the video processing?" (1-5)
5. "Overall, how satisfied are you with Aegis AI?" (1-5)

---

#### NPS (Net Promoter Score)
**Definition:** Likelihood to recommend the product to others (0-10 scale).

**Measurement:**
- **Survey Question:** "On a scale of 0-10, how likely are you to recommend Aegis AI to a friend or colleague?"
- **Follow-up:** Open-ended question: "What is the primary reason for your score?"

**Scoring:**
- **Promoters:** 9-10 (likely to recommend)
- **Passives:** 7-8 (neutral)
- **Detractors:** 0-6 (unlikely to recommend)
- **NPS = % Promoters - % Detractors**

**Target:**
- **NPS Score:** >30 (industry benchmark: SaaS products average ~30)
- **Promoter Rate:** >40% (users scoring 9-10)
- **Detractor Rate:** <20% (users scoring 0-6)

**Segmentation:**
- **Free Users:** Target NPS >20
- **Paid Users:** Target NPS >40
- **Parent Users:** Target NPS >35
- **Studio Users:** Target NPS >25

---

#### "Would Recommend" Rate
**Definition:** Direct percentage of users who would recommend the product.

**Measurement:**
- **Single Question:** "Would you recommend Aegis AI to others?" (Yes/No)
- **Timing:** After user completes 3+ videos (engaged users)

**Target:**
- **Recommendation Rate:** >60% (users answer "Yes")
- **Segment Comparison:** 
  - Free users: >55%
  - Paid users: >70%

**Additional Questions:**
- "What feature do you find most valuable?" (Multiple choice)
- "What would make you more likely to recommend us?" (Open-ended)

---

### Combined Success Criteria Summary

| Category | Metric | Target | Priority |
|----------|--------|--------|----------|
| **Product** | Overall Task Completion Rate | >80% | 🔴 P0 |
| **Product** | Upload → Process → Export Completion | >75% | 🔴 P0 |
| **Product** | P50 Time on Task (5min video) | <60s | 🔴 P0 |
| **Product** | P95 Time on Task (5min video) | <120s | 🟠 P1 |
| **Technical** | P95 End-to-End Latency | <90s | 🔴 P0 |
| **Technical** | Profanity Detection Precision | >95% | 🔴 P0 |
| **Technical** | Profanity Detection Recall | >90% | 🔴 P0 |
| **Technical** | False Positive Rate | <2% | 🔴 P0 |
| **Technical** | System Uptime (Monthly) | >99.5% | 🔴 P0 |
| **Technical** | API Availability | >99.9% | 🟠 P1 |
| **Business** | CSAT Score | >4.0/5.0 | 🟠 P1 |
| **Business** | NPS Score | >30 | 🟠 P1 |
| **Business** | "Would Recommend" Rate | >60% | 🟡 P2 |

**Overall Success Threshold:** 
- **MVP Launch:** Meet all 🔴 P0 metrics
- **Public Launch:** Meet all 🔴 P0 + 🟠 P1 metrics
- **Scale Phase:** Meet all metrics including 🟡 P2

---

## Measurement Methodology

### Data Collection
- **In-app Analytics:** Track user interactions (upload, process, export) via frontend events
- **Backend Metrics:** P95 latency, accuracy rates from processing logs
- **User Surveys:** In-app prompts + email surveys (weekly for first month, monthly thereafter)
- **External Monitoring:** Uptime monitoring via Pingdom/UptimeRobot (5-minute checks)

### Reporting Frequency
- **Daily:** Technical metrics (latency, uptime, error rates)
- **Weekly:** Product metrics (task completion, time on task)
- **Monthly:** Business metrics (CSAT, NPS, recommendation rate)

### Dashboard Tools
- **Technical:** Grafana + Prometheus (latency, uptime, queue depth)
- **Product:** Mixpanel/Amplitude (user behavior, task completion)
- **Business:** Google Analytics + Survey tools (CSAT, NPS)

---

## Baseline vs Target Comparison

| Metric | Week 2 Baseline | Week 4 Target | Optimization Strategy |
|--------|----------------|---------------|----------------------|
| **5min Video Processing** | 118s | 60s | GPU acceleration, API batching, parallel workers |
| **Profanity Precision** | ~85% (estimated) | >95% | Better model tuning, custom blocklist |
| **System Uptime** | N/A (not deployed) | >99.5% | Redundancy, fallbacks, monitoring |
| **Task Completion** | N/A (no data) | >80% | UX improvements, error handling |

---

## Golden Set

### Test Case Distribution

| Category | Percentage | Description | Examples |
|----------|-----------|-------------|----------|
| **Typical** | 70% | Standard use cases with clear, unambiguous content | Explicit profanity, clear violence, common video formats |
| **Edge** | 20% | Challenging cases that test model robustness | Accents, dialects, background noise, ambiguous scenes |
| **Adversarial** | 10% | Intentional evasion attempts and edge cases | Spelling variations, beeps, quick cuts, obfuscation |

**Total Test Cases:** 8-10 initial cases (Week 4), expand to **50+ cases by Week 6**

---

### Test Case Catalog

#### Typical Cases (70% - ~35 cases by Week 6)

##### TC-001: Explicit Profanity in Clear Speech
**Category:** Typical  
**Description:** 3-minute video clip from a movie/TV show with 5-7 instances of explicit profanity (f-words, s-words) spoken clearly in American English.  
**Video Specs:** 1080p MP4, 30fps, stereo audio, clear dialogue  
**Ground Truth:** 5 profanity instances at timestamps: 0:15, 0:42, 1:23, 2:05, 2:47  
**Acceptance Criteria:**
- ✅ Detects ≥4 of 5 profanity instances (≥80% recall)
- ✅ Precision ≥95% (no false positives)
- ✅ Audio muted for exact timestamp ranges (±0.2s tolerance)
- ✅ Processing completes in <60s for 3min video
- ✅ Timeline shows red bars at correct positions

##### TC-002: Graphic Violence Scene
**Category:** Typical  
**Description:** 2-minute action movie clip with visible blood, weapons (gun, knife), and fighting scenes.  
**Video Specs:** 1080p MP4, 24fps, clear visuals  
**Ground Truth:** 3 violent scenes: 0:20-0:35 (gun), 0:50-1:10 (knife), 1:30-1:45 (blood)  
**Acceptance Criteria:**
- ✅ Detects ≥2 of 3 violent scenes (≥67% recall)
- ✅ Precision ≥90% (blurs only violent frames, not normal action)
- ✅ Blur effect applied to entire frame (not just region)
- ✅ Blur intensity ≥70% (clearly obscures content)
- ✅ Timeline shows ⚠️ markers at correct timestamps

##### TC-003: Clean Family Content
**Category:** Typical  
**Description:** 4-minute educational video (kids' show) with no profanity or violence.  
**Video Specs:** 720p MP4, 30fps, clean audio  
**Ground Truth:** 0 profanity instances, 0 violent scenes  
**Acceptance Criteria:**
- ✅ Zero false positives (no profanity or violence detected)
- ✅ Processing completes successfully
- ✅ Timeline shows no red bars or ⚠️ markers
- ✅ Export video is identical to input (no unintended censoring)

##### TC-004: Mixed Content (Profanity + Violence)
**Category:** Typical  
**Description:** 5-minute movie clip with both profanity (8 instances) and violence (2 scenes).  
**Video Specs:** 1080p MP4, 24fps  
**Ground Truth:** 8 profanity instances, 2 violent scenes (0:30-0:45, 3:20-3:35)  
**Acceptance Criteria:**
- ✅ Detects ≥7 of 8 profanity instances (≥87.5% recall)
- ✅ Detects ≥1 of 2 violent scenes (≥50% recall)
- ✅ Both audio mute and video blur applied correctly
- ✅ Timeline shows both red bars and ⚠️ markers
- ✅ Processing time <90s for 5min video

##### TC-005: Standard Movie Clip (PG-13 Content)
**Category:** Typical  
**Description:** 6-minute movie clip rated PG-13 with mild profanity (3 instances) and implied violence (no graphic visuals).  
**Video Specs:** 1080p MP4, 24fps  
**Ground Truth:** 3 mild profanity instances (damn, hell, crap)  
**Acceptance Criteria:**
- ✅ Detects ≥2 of 3 instances (≥67% recall) if word is in blocklist
- ✅ Does NOT flag implied violence (no graphic visuals)
- ✅ Respects profile sensitivity setting (Medium/High)

---

#### Edge Cases (20% - ~10 cases by Week 6)

##### TC-006: Heavy Accent (British English)
**Category:** Edge  
**Description:** 2-minute video with British English speaker using profanity (4 instances) with distinct accent.  
**Video Specs:** 1080p MP4, 30fps, clear audio but different accent  
**Ground Truth:** 4 profanity instances: 0:12, 0:38, 1:15, 1:52  
**Acceptance Criteria:**
- ✅ Detects ≥3 of 4 instances (≥75% recall) despite accent
- ✅ STT transcription accuracy ≥90% (correctly transcribes accent)
- ✅ No false positives from accent-induced mispronunciations
- ✅ Processing time <50s for 2min video

##### TC-007: Background Noise and Music
**Category:** Edge  
**Description:** 3-minute video with profanity (3 instances) spoken over loud background music and ambient noise.  
**Video Specs:** 1080p MP4, 30fps, music at -12dB, dialogue at -6dB  
**Ground Truth:** 3 profanity instances: 0:20, 1:10, 2:30  
**Acceptance Criteria:**
- ✅ Detects ≥2 of 3 instances (≥67% recall) despite noise
- ✅ STT handles background music without hallucinating profanity
- ✅ No false positives from music lyrics or background chatter
- ✅ Processing completes successfully (no crashes from audio processing)

##### TC-008: Fast Speech / Rapid Dialogue
**Category:** Edge  
**Description:** 2-minute video with rapid-fire dialogue containing 5 profanity instances spoken quickly.  
**Video Specs:** 1080p MP4, 30fps, speech rate ~180 words/min  
**Ground Truth:** 5 profanity instances: 0:05, 0:18, 0:32, 0:55, 1:22  
**Acceptance Criteria:**
- ✅ Detects ≥4 of 5 instances (≥80% recall) despite fast speech
- ✅ Timestamp accuracy within ±0.5s (acceptable for fast speech)
- ✅ STT correctly transcribes rapid dialogue
- ✅ No false positives from misheard words

##### TC-009: Ambiguous Violence (Martial Arts / Sports)
**Category:** Edge  
**Description:** 3-minute martial arts training video with controlled fighting (no blood, staged combat).  
**Video Specs:** 1080p MP4, 30fps, sports context  
**Ground Truth:** 0 violent scenes (sports/controlled activity, not graphic violence)  
**Acceptance Criteria:**
- ✅ Does NOT flag controlled martial arts as violence (0 false positives)
- ✅ Distinguishes between sports/controlled combat vs. graphic violence
- ✅ Processing completes with no false detections
- ✅ Timeline shows no ⚠️ markers

##### TC-010: Multiple Speakers Overlapping
**Category:** Edge  
**Description:** 2-minute video with 3 speakers talking simultaneously, 2 profanity instances from different speakers.  
**Video Specs:** 1080p MP4, 30fps, overlapping dialogue  
**Ground Truth:** 2 profanity instances: 0:15 (speaker 1), 1:05 (speaker 2)  
**Acceptance Criteria:**
- ✅ Detects ≥1 of 2 instances (≥50% recall) - challenging due to overlap
- ✅ STT correctly identifies speaker separation (if diarization enabled)
- ✅ No false positives from overlapping speech
- ✅ Processing completes successfully

---

#### Adversarial Cases (10% - ~5 cases by Week 6)

##### TC-011: Intentional Misspelling / Phonetic Evasion
**Category:** Adversarial  
**Description:** 2-minute video where speaker intentionally mispronounces profanity to evade detection (e.g., "fudge" instead of "f***", "shoot" instead of "s***").  
**Video Specs:** 1080p MP4, 30fps, clear speech  
**Ground Truth:** 0 actual profanity instances (intentional evasion)  
**Acceptance Criteria:**
- ✅ Does NOT flag intentional misspellings/mispronunciations (0 false positives)
- ✅ System correctly transcribes actual words spoken (not what was intended)
- ✅ User can add custom keywords if needed (e.g., "fudge" to blocklist)
- ✅ Processing completes without errors

##### TC-012: Quick Cuts / Flash Frames
**Category:** Adversarial  
**Description:** 2-minute video with rapid cuts (<0.5s) containing brief violent frames (weapons, blood) interspersed with normal content.  
**Video Specs:** 1080p MP4, 30fps, 10-15 cuts per minute  
**Ground Truth:** 4 brief violent frames: 0:12 (1 frame), 0:45 (2 frames), 1:20 (1 frame), 1:58 (2 frames)  
**Acceptance Criteria:**
- ✅ Detects ≥2 of 4 brief violent frames (≥50% recall) - challenging due to speed
- ✅ Frame extraction captures frames at sufficient rate (≥0.5 FPS)
- ✅ Blur applied to detected frames without affecting adjacent frames
- ✅ Processing completes successfully (no crashes from rapid cuts)

##### TC-013: Audio Beeps / Censoring Already Applied
**Category:** Adversarial  
**Description:** 3-minute video that is already partially censored (TV broadcast version) with beeps over profanity and blurred violence.  
**Video Specs:** 1080p MP4, 30fps, audio contains beeps at 0:20, 1:15, 2:30  
**Ground Truth:** 3 profanity instances (already beeped), 1 violent scene (already blurred)  
**Acceptance Criteria:**
- ✅ System detects profanity instances despite beeps (≥2 of 3 recall)
- ✅ Does NOT double-censor (no duplicate beeps/blurs)
- ✅ Can identify that content is already censored (optional enhancement)
- ✅ Processing completes successfully

##### TC-014: Foreign Language Mixed with English
**Category:** Adversarial  
**Description:** 2-minute video with bilingual dialogue (English + Spanish), 2 English profanity instances, 1 Spanish profanity instance.  
**Video Specs:** 1080p MP4, 30fps, mixed languages  
**Ground Truth:** 2 English profanity instances, 1 Spanish profanity instance  
**Acceptance Criteria:**
- ✅ Detects ≥1 of 2 English profanity instances (≥50% recall)
- ✅ Spanish profanity detection (if supported) OR gracefully handles unsupported language
- ✅ No false positives from foreign language words that sound like English profanity
- ✅ System indicates language detection status (optional enhancement)

##### TC-015: Low Quality / Compressed Video
**Category:** Adversarial  
**Description:** 3-minute video with heavy compression artifacts, low resolution (480p), and low bitrate audio containing 3 profanity instances.  
**Video Specs:** 480p MP4, 24fps, 500kbps bitrate, mono audio  
**Ground Truth:** 3 profanity instances: 0:25, 1:10, 2:20  
**Acceptance Criteria:**
- ✅ Detects ≥2 of 3 instances (≥67% recall) despite low quality
- ✅ STT handles compressed audio without significant degradation
- ✅ Video processing completes successfully (no crashes from low quality)
- ✅ Processing time acceptable (<90s for 3min video)

---

### Golden Set Summary

| Test Case ID | Category | Focus Area | Priority | Status |
|--------------|----------|------------|----------|--------|
| TC-001 | Typical | Profanity Detection | 🔴 P0 | ✅ Defined |
| TC-002 | Typical | Violence Detection | 🔴 P0 | ✅ Defined |
| TC-003 | Typical | False Positive Control | 🔴 P0 | ✅ Defined |
| TC-004 | Typical | Mixed Content | 🔴 P0 | ✅ Defined |
| TC-005 | Typical | Profile Sensitivity | 🟠 P1 | ✅ Defined |
| TC-006 | Edge | Accent Handling | 🟠 P1 | ✅ Defined |
| TC-007 | Edge | Background Noise | 🟠 P1 | ✅ Defined |
| TC-008 | Edge | Fast Speech | 🟠 P1 | ✅ Defined |
| TC-009 | Edge | Ambiguous Content | 🟠 P1 | ✅ Defined |
| TC-010 | Edge | Overlapping Speech | 🟡 P2 | ✅ Defined |
| TC-011 | Adversarial | Evasion Attempts | 🟠 P1 | ✅ Defined |
| TC-012 | Adversarial | Quick Cuts | 🟠 P1 | ✅ Defined |
| TC-013 | Adversarial | Pre-censored Content | 🟡 P2 | ✅ Defined |
| TC-014 | Adversarial | Mixed Languages | 🟡 P2 | ✅ Defined |
| TC-015 | Adversarial | Low Quality | 🟡 P2 | ✅ Defined |

**Current Status:** 10 test cases defined (Week 4)  
**Target:** 50+ test cases by Week 6  
**Expansion Plan:**
- **Typical:** Add 25 more cases (various movie genres, TV shows, user-generated content)
- **Edge:** Add 5 more cases (dialects, technical issues, format variations)
- **Adversarial:** Add 5 more cases (advanced evasion techniques, adversarial examples)

### Test Execution Plan

**Week 4-5:** Run initial 10 test cases weekly  
**Week 6:** Expand to 50+ test cases, establish automated test suite  
**Ongoing:** Add new test cases based on user feedback and edge cases discovered in production

---

## User Testing Protocol

### User Testing Round 1: MVP Validation

**Objective:** Validate core user workflows, identify usability issues, and measure user satisfaction with the video censoring system before public launch.

**Timeline:** Week 8-9 (after MVP features are implemented)  
**Duration:** 45-60 minutes per session  
**Location:** Remote (Zoom/Google Meet) or in-person lab

---

### Participant Profile

**Target:** Primary users (Parents) and Secondary users (Content Creators/Studios)

**Recruitment Criteria:**
- **Parents (3-4 participants):**
  - Have children aged 6-16
  - Regularly monitor children's media consumption
  - Use video streaming platforms (Netflix, YouTube, etc.)
  - Comfortable with basic web applications
  - Mix of tech-savvy and tech-novice users

- **Content Creators/Studios (1-2 participants):**
  - Work with video content production or distribution
  - Need to create multiple versions of content (TV edits, regional ratings)
  - Familiar with video editing tools

**Minimum Participants:** 3 (critical for MVP validation)  
**Recommended Participants:** 5 (better statistical validity)

**Diversity Considerations:**
- Age range: 25-50 years old
- Gender mix: Balanced representation
- Technical proficiency: Mix of beginner/intermediate users
- Geographic: Multiple time zones (if remote)

**Screening Questions:**
1. "Do you have children who watch videos/movies?" (Yes/No)
2. "How often do you monitor or filter content for your children?" (Daily/Weekly/Monthly/Never)
3. "Rate your comfort level with web applications." (1-5 scale)
4. "Have you used video editing or content filtering tools before?" (Yes/No)

---

### Testing Tasks (3-5 Tasks)

#### Task 1: Upload and Process First Video (Core Flow)
**Objective:** Test the primary user workflow - uploading a video and processing it with default settings.

**Scenario:** "You want to censor a 2-minute movie clip so your child can watch it safely. Use Aegis AI to upload and process the video."

**Steps:**
1. Navigate to upload page
2. Select video file (provided: `test-clip-1.mp4` - 2min, contains profanity)
3. Upload video
4. Wait for processing to complete
5. Review censored video in player

**Success Criteria:**
- ✅ Successfully uploads video without errors
- ✅ Processing completes within 90 seconds
- ✅ Can view censored video in player
- ✅ Timeline shows red bars indicating censored segments
- ✅ No system crashes or critical errors

**Time Limit:** 5 minutes (including processing wait time)  
**Expected Completion Rate:** >85%

**Data Captured:**
- Upload time (seconds)
- Processing completion time (seconds)
- Number of errors encountered
- Task completion (Yes/No)

---

#### Task 2: Activate Kids Mode Preset
**Objective:** Test preset activation and verify it applies appropriate censorship.

**Scenario:** "You want to use the 'Kids Mode' preset for stricter censorship. Activate it and reprocess the video."

**Steps:**
1. Navigate to presets page (or find preset selector in player)
2. Select "Kids Mode" preset
3. Reprocess video (if needed) or verify settings are applied
4. Review changes in censored content

**Success Criteria:**
- ✅ Finds preset selector within 30 seconds
- ✅ Successfully activates Kids Mode preset
- ✅ Preset settings are clearly visible/explained
- ✅ Reprocessing completes successfully (if required)
- ✅ Censored content reflects stricter settings

**Time Limit:** 3 minutes  
**Expected Completion Rate:** >70%

**Data Captured:**
- Time to find preset selector (seconds)
- Time to activate preset (seconds)
- User confusion/hesitation points (observer notes)
- Task completion (Yes/No)

---

#### Task 3: Add Custom Keyword to Blocklist
**Objective:** Test custom keyword management and verify it works in reprocessing.

**Scenario:** "The word 'darn' is not on the default blocklist, but you want to censor it. Add 'darn' to your custom blocklist and reprocess the video."

**Steps:**
1. Navigate to profile settings or keyword management
2. Add "darn" to custom keyword blocklist
3. Save profile
4. Reprocess video (or verify it's applied)
5. Verify "darn" is now censored

**Success Criteria:**
- ✅ Finds keyword management interface within 1 minute
- ✅ Successfully adds "darn" to blocklist
- ✅ Saves profile without errors
- ✅ Reprocessing detects and censors "darn"
- ✅ Timeline shows new censored segment

**Time Limit:** 4 minutes  
**Expected Completion Rate:** >60%

**Data Captured:**
- Time to find keyword interface (seconds)
- Time to add keyword (seconds)
- Number of incorrect attempts
- Task completion (Yes/No)

---

#### Task 4: Review and Export Censored Video
**Objective:** Test video review and export functionality.

**Scenario:** "You're satisfied with the censored video. Export it so you can download it."

**Steps:**
1. Review censored video in player (play/pause to verify censoring)
2. Locate export button
3. Initiate export
4. Wait for export to complete
5. Download exported video

**Success Criteria:**
- ✅ Can play/pause video and verify censoring
- ✅ Finds export button within 30 seconds
- ✅ Export completes within 60 seconds
- ✅ Successfully downloads exported video file
- ✅ Downloaded file is playable and contains censored content

**Time Limit:** 3 minutes  
**Expected Completion Rate:** >75%

**Data Captured:**
- Time to find export button (seconds)
- Export completion time (seconds)
- Download success (Yes/No)
- Task completion (Yes/No)

---

#### Task 5: Report False Positive (Optional - Advanced)
**Objective:** Test feedback mechanism for model improvement.

**Scenario:** "You noticed that a word was incorrectly censored (false positive). Report it using the feedback feature."

**Steps:**
1. Identify a false positive in the censored video
2. Find feedback/report button
3. Submit feedback (mark as false positive)
4. Optionally add comment explaining the issue

**Success Criteria:**
- ✅ Identifies false positive correctly
- ✅ Finds feedback button within 1 minute
- ✅ Successfully submits feedback
- ✅ Receives confirmation that feedback was recorded

**Time Limit:** 3 minutes  
**Expected Completion Rate:** >50% (optional task)

**Data Captured:**
- Time to find feedback button (seconds)
- Feedback submission success (Yes/No)
- Task completion (Yes/No)

---

### Data Capture Methods

#### Quantitative Metrics

| Metric | Measurement Method | Target |
|--------|-------------------|--------|
| **Task Completion Rate** | % of tasks completed successfully | >70% overall |
| **Time on Task** | Average time per task (seconds) | Within time limits |
| **Error Count** | Number of errors per task | <2 errors per task |
| **SUS Score** | System Usability Scale (0-100) | >70 (acceptable) |
| **CSAT Score** | Customer Satisfaction (1-5) | >4.0/5.0 |
| **Success Rate** | Tasks completed without assistance | >80% |

#### Qualitative Data

- **Think-Aloud Protocol:** Participants verbalize thoughts while using system
- **Post-Task Interviews:** 5-minute discussion after each task
- **Post-Session Survey:** Comprehensive feedback form
- **Screen Recording:** Record entire session for later analysis
- **Observer Notes:** Researcher notes on confusion points, errors, workarounds

#### Tools for Data Collection

- **Screen Recording:** OBS Studio, Zoom recording, or Loom
- **Survey Tools:** Google Forms, Typeform, or Qualtrics
- **Analytics:** Mixpanel/Amplitude for in-app behavior tracking
- **Note-Taking:** Shared Google Doc or Notion for observer notes

---

### Consent & Privacy

#### Informed Consent Form

**Required Elements:**
- **Study Purpose:** "We are testing a video censoring tool to improve its usability and effectiveness."
- **Procedure:** "You will be asked to complete 3-5 tasks using the Aegis AI platform. The session will take 45-60 minutes."
- **Risks:** "Minimal risk. You may be exposed to brief instances of uncensored inappropriate content (profanity, violence) during testing."
- **Benefits:** "Your feedback will help improve the tool for parents and content creators."
- **Confidentiality:** "All data will be anonymized. Screen recordings will not capture personal information."
- **Right to Withdraw:** "You can stop at any time without penalty."
- **Contact Information:** Researcher name, email, IRB approval number (if applicable)

**Consent Method:**
- Digital consent form (Google Forms) signed before session
- Verbal confirmation at start of session
- Re-confirm consent if sensitive content is shown

#### Privacy Protections

**Data Collection:**
- ✅ **Anonymization:** Remove all PII from recordings and notes
- ✅ **Data Minimization:** Collect only necessary data
- ✅ **Secure Storage:** Encrypted storage (Google Drive with encryption, or secure cloud)
- ✅ **Access Control:** Only research team has access to raw data
- ✅ **Retention Policy:** Delete recordings after 6 months, keep anonymized analysis

**Participant Data:**
- ✅ **No Personal Info:** Don't record names, emails, addresses in videos
- ✅ **Pseudo-IDs:** Use participant numbers (P001, P002, etc.)
- ✅ **Separate Storage:** Store consent forms separately from test data

**Content Privacy:**
- ✅ **Test Videos:** Use curated test clips, not participant's personal videos
- ✅ **No Real Data:** Don't use participant's actual content for testing
- ✅ **Warning:** Explicitly warn participants about uncensored content exposure

**IRB Considerations:**
- ⚠️ **IRB Approval:** May require IRB review if collecting identifiable data
- ⚠️ **Minimal Risk:** Classify as minimal risk research (brief exposure to inappropriate content)
- ⚠️ **Informed Consent:** Required for all participants
- ⚠️ **Data Handling:** Follow institutional data protection policies

---

### Post-Testing Data Analysis

#### Quantitative Analysis

**Metrics Calculated:**
1. **Task Completion Rate:** `(Tasks Completed) / (Total Tasks Attempted) × 100`
2. **Average Time on Task:** Mean time across all participants
3. **Error Rate:** `(Total Errors) / (Total Tasks)`
4. **SUS Score:** Calculate from 10-item SUS questionnaire (0-100 scale)
5. **CSAT Score:** Average of 5 satisfaction questions (1-5 scale)

**Success Thresholds:**
- Task completion rate: >70% ✅
- Average time on task: Within limits ✅
- SUS score: >70 (acceptable usability) ✅
- CSAT score: >4.0/5.0 ✅

#### Qualitative Analysis

**Themes to Identify:**
- Common confusion points
- Navigation issues
- Feature discoverability problems
- Workarounds users create
- Feature requests
- Positive feedback highlights

**Reporting:**
- Create usability report with findings
- Prioritize issues by severity (Critical/High/Medium/Low)
- Provide recommendations for improvements
- Share anonymized insights with development team

---

### Testing Schedule

**Week 8: Preparation**
- Finalize test videos and materials
- Set up screen recording tools
- Prepare consent forms and surveys
- Recruit participants

**Week 9: Testing**
- Monday-Wednesday: Conduct 5 testing sessions (1-2 per day)
- Thursday: Data analysis and preliminary findings
- Friday: Create usability report

**Deliverables:**
- Usability testing report
- Prioritized list of UX issues
- Recommendations for improvements
- Updated evaluation plan based on findings
