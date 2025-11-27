# Token & Cost Optimization Strategy

## Current API Usage Analysis

### External API Dependencies
- **Google Vision API:** Violence/NSFW detection ($1.50/1k requests after free tier)
- **OpenAI Whisper API:** Speech-to-text ($0.006/minute audio)
- **OpenAI LLM APIs:** (If used for NLP/text analysis - needs confirmation)

### Estimated Traffic Assumptions
- **Low Traffic (MVP):** 100 videos/month, avg 5min/video = 500 minutes/month
- **Medium Traffic:** 1,000 videos/month, avg 5min/video = 5,000 minutes/month
- **High Traffic:** 10,000 videos/month, avg 5min/video = 50,000 minutes/month

### Current Costs (Estimated)
- **Google Vision API:** 300 frames/video × 100 videos = 30k frames/month = 3k requests (with batching) = $4.50/month
- **OpenAI Whisper:** 500 minutes/month × $0.006 = $3.00/month
- **Total MVP:** ~$7.50/month
- **Scale (10k videos):** ~$750/month

---

## 1. System Prompt Optimization

### Current System Prompt (Estimated)
If using LLM APIs for text analysis/profanity detection, typical system prompt might be:

```
You are an AI assistant that analyzes video transcripts for inappropriate content. 
Your task is to identify profanity and inappropriate language in the provided transcript. 
Compare the transcript against a customizable blocklist of words and phrases. 
Return timestamps for any detected profanity instances. 
Be precise and avoid false positives. Consider context when determining if language is inappropriate.
```

**Token Count:** ~80 tokens (estimated)

### Optimized System Prompt (Essential Only)

**Reduced Version:**
```
Analyze transcript for profanity matching blocklist. Return timestamps. Avoid false positives.
```

**Token Count:** ~15 tokens  
**Savings:** 81% reduction (80 → 15 tokens)

### System Prompt Best Practices

**Essential Elements Only:**
1. ✅ Core task (analyze transcript)
2. ✅ Output format (timestamps)
3. ✅ Critical constraint (avoid false positives)

**Remove:**
- ❌ Explanatory text ("You are an AI assistant...")
- ❌ Redundant instructions ("Be precise" - model already is)
- ❌ Context that's obvious ("Consider context" - model does this by default)

**Rule:** System prompt should be ≤20 tokens for simple tasks, ≤50 tokens for complex tasks

---

## 2. Context Packing Rules

### Current Context Usage (Estimated)
For profanity detection pipeline:
- **Transcript:** 5-minute video ≈ 750 words ≈ 1,000 tokens
- **Blocklist:** 100 words ≈ 200 tokens
- **System prompt:** ~80 tokens
- **Total:** ~1,280 tokens per request

### Optimized Context Packing Rules

#### Rule 1: Max Context Window
**Target:** Keep total context ≤2,000 tokens per request  
**Rationale:** Balance between cost and accuracy

**Implementation:**
```python
MAX_CONTEXT_TOKENS = 2000
MAX_TRANSCRIPT_TOKENS = 1500  # 75% of context
MAX_BLOCKLIST_TOKENS = 400     # 20% of context
SYSTEM_PROMPT_TOKENS = 15      # 5% of context
RESPONSE_BUFFER = 85           # 5% for response
```

#### Rule 2: Top-K Blocklist Matching
**Strategy:** Only send relevant blocklist words (top-k matches) instead of full list

**Algorithm:**
1. Pre-filter blocklist: Extract words that could match transcript vocabulary
2. Use fuzzy matching: Find top 20 most likely matches
3. Send only top-k (k=20) to API instead of full 100-word list

**Savings:** 100 words → 20 words = 80% reduction (200 → 40 tokens)

**Implementation:**
```python
def get_relevant_blocklist(transcript: str, blocklist: List[str], k: int = 20) -> List[str]:
    """
    Return top-k blocklist words most likely to appear in transcript.
    Uses simple substring matching + word frequency.
    """
    # Extract unique words from transcript
    transcript_words = set(transcript.lower().split())
    
    # Score each blocklist word by match probability
    scored = []
    for word in blocklist:
        score = 0
        # Check if word substring exists in transcript
        if word.lower() in transcript.lower():
            score += 10
        # Check word frequency in transcript
        score += transcript.lower().count(word.lower())
        scored.append((score, word))
    
    # Return top-k
    scored.sort(reverse=True)
    return [word for _, word in scored[:k]]
```

#### Rule 3: Deduplicate Overlaps
**Strategy:** Remove duplicate/overlapping content before sending to API

**Transcript Deduplication:**
- **Window sliding:** If processing 5-minute video, split into 1-minute chunks
- **Overlap:** 10-second overlap between chunks (to catch cross-boundary profanity)
- **Deduplicate:** Remove duplicate detections in overlap regions

**Blocklist Deduplication:**
- **Synonyms:** "damn" and "darn" are similar - deduplicate if both present
- **Stemming:** "damn", "damned", "damning" → send only root "damn"

**Implementation:**
```python
def deduplicate_blocklist(blocklist: List[str]) -> List[str]:
    """
    Remove synonyms and stemmed duplicates from blocklist.
    """
    # Group synonyms
    synonym_groups = {
        'damn': ['damn', 'damned', 'damning'],
        'hell': ['hell', 'hellish'],
        # ... add more groups
    }
    
    # Keep only one word per synonym group
    seen_groups = set()
    deduplicated = []
    for word in blocklist:
        matched = False
        for group_key, synonyms in synonym_groups.items():
            if word.lower() in synonyms:
                if group_key not in seen_groups:
                    deduplicated.append(group_key)
                    seen_groups.add(group_key)
                matched = True
                break
        if not matched:
            deduplicated.append(word)
    
    return deduplicated
```

**Savings:** 20-30% reduction in blocklist tokens

---

## 3. Model Routing Strategy (When to Use Cheaper Models)

### Current Model Stack (Estimated)
- **Primary:** GPT-4 or GPT-4 Turbo (high accuracy, expensive)
- **Fallback:** GPT-3.5 Turbo (lower cost, good accuracy for simple tasks)
- **Local:** Custom keyword matching (free, no API cost)

### Routing Decision Tree

```
┌─────────────────────────────────┐
│  Incoming Request               │
└────────────┬────────────────────┘
             │
             ▼
    ┌────────────────┐
    │ Is it simple?  │
    │ (keyword match)│
    └────┬───────┬───┘
         │       │
    YES  │       │ NO
         │       │
         ▼       ▼
    ┌────────┐ ┌──────────────────┐
    │ Local  │ │ Needs context?   │
    │ Match  │ └────┬──────────┬───┘
    └────────┘      │          │
                 YES│          │NO
                    │          │
                    ▼          ▼
            ┌───────────┐ ┌──────────────┐
            │ GPT-3.5   │ │ GPT-4 Turbo  │
            │ Turbo     │ │ (complex)    │
            └───────────┘ └──────────────┘
```

### Routing Rules

#### Rule 1: Simple Keyword Matching → Local (Free)
**Criteria:**
- Transcript length <500 tokens
- Blocklist <50 words
- No context needed (simple substring matching)

**Implementation:**
```python
def route_to_model(transcript: str, blocklist: List[str], needs_context: bool) -> str:
    """
    Route to appropriate model based on complexity.
    Returns: 'local', 'gpt-3.5-turbo', or 'gpt-4-turbo'
    """
    transcript_tokens = estimate_tokens(transcript)
    blocklist_size = len(blocklist)
    
    # Simple case: Local keyword matching
    if transcript_tokens < 500 and blocklist_size < 50 and not needs_context:
        return 'local'  # Free
    
    # Medium complexity: GPT-3.5 Turbo
    if transcript_tokens < 2000 and blocklist_size < 100:
        return 'gpt-3.5-turbo'  # $0.50/1M input tokens
    
    # Complex case: GPT-4 Turbo
    return 'gpt-4-turbo'  # $10/1M input tokens
```

#### Rule 2: Confidence-Based Routing
**Strategy:** Use cheaper model first, upgrade if confidence low

**Implementation:**
```python
def two_stage_routing(transcript: str, blocklist: List[str]) -> List[Detection]:
    """
    Try GPT-3.5 first, upgrade to GPT-4 if confidence <85%.
    """
    # Stage 1: GPT-3.5 Turbo
    detections = call_gpt_35_turbo(transcript, blocklist)
    
    # Check confidence
    if detections.confidence < 0.85:
        # Stage 2: Upgrade to GPT-4 Turbo
        detections = call_gpt_4_turbo(transcript, blocklist)
    
    return detections
```

**Cost Savings:** 90% of requests use GPT-3.5 (10x cheaper) = 90% cost reduction

#### Rule 3: Batch Processing
**Strategy:** Batch multiple transcripts into single API call

**Implementation:**
```python
def batch_process(transcripts: List[str], blocklist: List[str], batch_size: int = 10):
    """
    Process multiple transcripts in batches to reduce API calls.
    """
    batches = [transcripts[i:i+batch_size] for i in range(0, len(transcripts), batch_size)]
    
    for batch in batches:
        # Combine transcripts with separators
        combined = "\n\n---TRANSCRIPT---\n\n".join(batch)
        
        # Single API call for batch
        detections = call_api(combined, blocklist)
        
        # Split results back to individual transcripts
        yield split_detections(detections)
```

**Savings:** 10 API calls → 1 API call = 90% reduction in API overhead

---

## 4. Caching Strategy

### Cache Candidates

#### Candidate 1: Transcript Cache
**Key:** Hash of transcript text  
**Value:** Detected profanity timestamps  
**Hit Rate:** 20-30% (users re-process same videos)

**Implementation:**
```python
import hashlib
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_transcript_cache_key(transcript: str) -> str:
    """Generate cache key from transcript hash."""
    transcript_hash = hashlib.sha256(transcript.encode()).hexdigest()
    return f"transcript:{transcript_hash}"

def check_cache(transcript: str) -> Optional[List[Detection]]:
    """Check if transcript was processed before."""
    cache_key = get_transcript_cache_key(transcript)
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    return None

def cache_result(transcript: str, detections: List[Detection], ttl: int = 86400):
    """Cache detection results for 24 hours."""
    cache_key = get_transcript_cache_key(transcript)
    redis_client.setex(cache_key, ttl, json.dumps(detections))
```

**Expected Hit Rate:** 25% (assumes 25% of videos are re-processed)  
**Cost Savings:** 25% reduction in API calls = $1.88/month (MVP) → $187.50/month (scale)

#### Candidate 2: Blocklist Cache
**Key:** Hash of sorted blocklist  
**Value:** Pre-processed blocklist (normalized, deduplicated)  
**Hit Rate:** 60-80% (users reuse same profiles)

**Implementation:**
```python
def get_blocklist_cache_key(blocklist: List[str]) -> str:
    """Generate cache key from sorted blocklist hash."""
    sorted_blocklist = sorted(blocklist)
    blocklist_str = ",".join(sorted_blocklist)
    blocklist_hash = hashlib.sha256(blocklist_str.encode()).hexdigest()
    return f"blocklist:{blocklist_hash}"

def get_cached_blocklist(blocklist: List[str]) -> Optional[List[str]]:
    """Get pre-processed blocklist from cache."""
    cache_key = get_blocklist_cache_key(blocklist)
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)  # Returns deduplicated, normalized blocklist
    return None
```

**Expected Hit Rate:** 70% (users reuse profiles)  
**Cost Savings:** 70% reduction in blocklist processing overhead

#### Candidate 3: Frame Detection Cache
**Key:** Hash of frame image + detection model version  
**Value:** Detection result (violence/NSFW classification)  
**Hit Rate:** 10-15% (same frames appear in multiple videos)

**Implementation:**
```python
import cv2
import numpy as np

def get_frame_cache_key(frame: np.ndarray, model_version: str) -> str:
    """Generate cache key from frame hash + model version."""
    frame_hash = hashlib.sha256(frame.tobytes()).hexdigest()
    return f"frame:{model_version}:{frame_hash}"

def check_frame_cache(frame: np.ndarray, model_version: str) -> Optional[Dict]:
    """Check if frame was detected before."""
    cache_key = get_frame_cache_key(frame, model_version)
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    return None
```

**Expected Hit Rate:** 12% (lower due to frame uniqueness)  
**Cost Savings:** 12% reduction in Google Vision API calls = $0.54/month (MVP) → $54/month (scale)

#### Candidate 4: User Profile Cache
**Key:** User ID + profile ID  
**Value:** User's active profile settings  
**Hit Rate:** 95% (profiles rarely change)

**Implementation:**
```python
def get_profile_cache_key(user_id: str, profile_id: str) -> str:
    """Generate cache key for user profile."""
    return f"profile:{user_id}:{profile_id}"

def get_cached_profile(user_id: str, profile_id: str) -> Optional[Dict]:
    """Get user profile from cache."""
    cache_key = get_profile_cache_key(user_id, profile_id)
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    return None

def cache_profile(user_id: str, profile_id: str, profile: Dict, ttl: int = 3600):
    """Cache user profile for 1 hour."""
    cache_key = get_profile_cache_key(user_id, profile_id)
    redis_client.setex(cache_key, ttl, json.dumps(profile))
```

**Expected Hit Rate:** 95%  
**Cost Savings:** 95% reduction in database queries (not API costs, but reduces latency)

---

## 5. Cost Optimization Summary

### Current Costs (Estimated MVP - 100 videos/month)
- **Google Vision API:** $4.50/month (3k requests with batching)
- **OpenAI Whisper:** $3.00/month (500 minutes)
- **LLM APIs (if used):** $5.00/month (estimated)
- **Total:** ~$12.50/month

### Optimized Costs (After All Optimizations)

#### Optimizations Applied:
1. **System Prompt Reduction:** 81% reduction (80 → 15 tokens)
2. **Top-K Blocklist:** 80% reduction (100 → 20 words)
3. **Deduplication:** 25% reduction in context
4. **Model Routing:** 90% use GPT-3.5 (10x cheaper) = 90% cost reduction
5. **Transcript Cache:** 25% hit rate = 25% reduction
6. **Frame Cache:** 12% hit rate = 12% reduction

#### New Costs:
- **Google Vision API:** $3.96/month (12% cache hit = 2.64k requests)
- **OpenAI Whisper:** $3.00/month (no caching for audio)
- **LLM APIs:** $0.50/month (90% GPT-3.5 routing + 25% cache hit)
- **Total:** ~$7.46/month

**Savings:** 40% cost reduction ($12.50 → $7.46/month)

### Scale Costs (10,000 videos/month)

**Current (No Optimization):**
- Google Vision API: $450/month
- OpenAI Whisper: $300/month
- LLM APIs: $500/month
- **Total:** ~$1,250/month

**Optimized:**
- Google Vision API: $396/month (12% cache hit)
- OpenAI Whisper: $300/month (no caching)
- LLM APIs: $50/month (90% GPT-3.5 routing + 25% cache hit)
- **Total:** ~$746/month

**Savings:** 40% cost reduction ($1,250 → $746/month) = **$504/month savings**

---

## 6. Implementation Priority

### Phase 1: Quick Wins (Week 4-5)
1. ✅ **System Prompt Reduction:** 1 day implementation, 81% token reduction
2. ✅ **Top-K Blocklist:** 2 days implementation, 80% blocklist reduction
3. ✅ **Transcript Cache:** 2 days implementation, 25% API call reduction

**Total Effort:** 5 days  
**Cost Savings:** ~25% reduction

### Phase 2: Model Routing (Week 6-7)
4. ✅ **Model Routing Logic:** 3 days implementation, 90% cost reduction on LLM calls
5. ✅ **Deduplication:** 2 days implementation, 25% context reduction

**Total Effort:** 5 days  
**Cost Savings:** Additional 15% reduction

### Phase 3: Advanced Caching (Week 8-9)
6. ✅ **Frame Cache:** 3 days implementation, 12% Google Vision API reduction
7. ✅ **Profile Cache:** 1 day implementation, 95% database query reduction

**Total Effort:** 4 days  
**Cost Savings:** Additional 5% reduction

**Total Implementation:** 14 days over 6 weeks  
**Total Cost Savings:** 40% reduction

---

## 7. Monitoring & Metrics

### Key Metrics to Track
1. **Token Usage:** Average tokens per request (target: <500 tokens)
2. **Cache Hit Rate:** 
   - Transcript cache: Target >25%
   - Frame cache: Target >12%
   - Profile cache: Target >95%
3. **Model Routing:** % requests using GPT-3.5 vs GPT-4 (target: >90% GPT-3.5)
4. **Cost per Video:** Track monthly (target: <$0.10/video)

### Dashboard Metrics
- **Daily Token Usage:** Track token consumption per API
- **Cache Hit Rates:** Real-time cache performance
- **Cost Trends:** Weekly cost reports
- **Optimization ROI:** Measure cost savings vs. implementation effort

---

## 8. Expected ROI

### Implementation Costs
- **Development Time:** 14 days × $500/day = $7,000
- **Infrastructure:** Redis cache setup = $15/month

### Annual Savings (10k videos/month)
- **Monthly Savings:** $504/month
- **Annual Savings:** $6,048/year
- **ROI:** Break-even in 1.2 months, 865% ROI in first year

### Break-Even Analysis
- **MVP (100 videos/month):** $5/month savings = Break-even in 1,400 months (not worth it)
- **Scale (10k videos/month):** $504/month savings = Break-even in 1.2 months ✅ **Worth it**

**Recommendation:** Implement optimizations when traffic exceeds 1,000 videos/month.

