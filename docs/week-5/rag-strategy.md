# RAG Strategy

<!-- TODO: Complete RAG Strategy -->

<!--
# 🧠 Aegis AI – Week 5 RAG Strategy Document
**File:** `docs/week-5/rag-strategy.md`  
**Project:** ThinkBit / Aegis AI – Intelligent Video Censoring System  
**Purpose:** Define the Retrieval-Augmented Generation (RAG) approach for the AI model that performs content detection and censorship.

---

## 1. Knowledge Sources
What data will Aegis AI access to make accurate, explainable censorship decisions?

### Primary Knowledge Sources

1. **Censorship Policy Corpus**
   - **Location:** `/data/policies/`
   - **Source:** FCC, MPAA, and internal Aegis "Kids/Teen/Studio" policy sets
   - **Volume:** ~120 text files (~350 pages total)
   - **Update Frequency:** Biannual
   - **Content:** Language and visual content rules, severity scales, contextual exceptions  
   - **Purpose:** Provide policy-grounded definitions for "violence," "profanity," "sexual," and "inappropriate" labels

2. **Lexicon Database**
   - **Source:** PostgreSQL table `lexicon`
   - **Records:** ~20,000 entries (multi-language profanity, slang, whitelisted terms)
   - **Update Frequency:** Monthly
   - **Purpose:** Match and disambiguate speech content detected by Whisper

3. **Video & Audio Exemplars**
   - **Location:** `/data/exemplars/`
   - **Records:** ~5,000 annotated video frames + 2,000 audio clips
   - **Labels:** "blocked", "benign", "ambiguous"
   - **Purpose:** Provide embeddings for nearest-neighbor retrieval to compare new scenes with known examples

4. **User Feedback Repository**
   - **Source:** PostgreSQL table `user_feedback`
   - **Records:** ~3,000 feedback items/month
   - **Purpose:** Improve decision thresholds and retrain exemplar sets using real-world user corrections

5. **System Logs (Analytics Layer)**
   - **Source:** AWS CloudWatch + Prometheus metrics
   - **Purpose:** Support monitoring, false positive tracking, and retriever accuracy statistics

---

## 2. RAG Architecture Choice

### ✅ Option B: Hybrid Search (Chosen)
**Pipeline:**

**Justification:**
- **Hybrid search** combines semantic understanding (via embeddings) with **exact term matching** for precise profanity/keyword hits.  
- Reduces false negatives caused by slang, typos, or phonetic variants (e.g., "azz", "f@ck").  
- Maintains interpretability—developers and auditors can inspect both semantic and keyword evidence.

**Fallback:** If no high-similarity results (`score < 0.65`), the system defaults to static policy thresholds (no hallucination risk).

---

## 3. Technical Implementation

### Embedding Model
- **Model:** `text-embedding-3-large`
- **Dimensions:** 3072  
- **Cost:** ~$0.13 per 1M tokens  
- **Why:** High recall for multi-language content (English, Georgian, Spanish, etc.), supports both Whisper transcriptions and text policy retrieval.

**Vision Embeddings:** CLIP ViT-B/32 (512-dim) for frame-level similarity.

---

### Vector Database
- **Service:** PostgreSQL with `pgvector` extension  
- **Tables:** `policy_docs`, `lexicon`, `audio_exemplars`, `vision_exemplars`  
- **Metric:** Cosine similarity  
- **Why:** Local and secure (no external managed service), compatible with cloud RDS and hybrid keyword search via `pg_trgm`.

---

### Chunking Strategy
- **Method:** Recursive text splitter  
- **Chunk size:** 800–1000 tokens  
- **Overlap:** 150 tokens  
- **Why:** Ensures complete context around offensive phrases or visual scene transitions, avoiding cutoff in mid-sentence or frame sequence.

**For transcripts:** chunk per utterance or 5-10 seconds.  
**For video frames:** sample 1 frame per 0.5–1 second.

---

### Retrieval Parameters
- **Top K:** 6 documents or exemplars  
- **Similarity Threshold:** 0.68  
- **Reranking:** Yes – Cross-encoder (mini-LM cross-encoder-ms-marco)  
- **Fallback:** Keyword match if vector retrieval < threshold  
- **Latency Budget:** ≤40 ms for text, ≤60 ms for vision

---

## 4. Citation Strategy
Every censorship decision is paired with human-readable evidence.

### Citation Format
> The phrase **"kick your ass"** was censored under *Kids Policy Section 2.3 – Offensive Language*.  
> [Source: `kids-policy.txt`, paragraph 45, similarity = 0.84]

> The frame at 02:10 was blurred due to **violence detection (blood imagery)**.  
> [Source: `exemplar_violence_112.png`, confidence = 0.91]

**Displayed In-App:**  
- Tooltip: "Muted for profanity (Policy Section 2.3)"  
- Hover/expand: shows retrieved evidence file + similarity score

**Stored In Logs:**  
- Evidence IDs (`policy_id`, `exemplar_id`, `feedback_id`)  
- Confidence and threshold values  
- Time of censorship event  

---

## 5. RAG Alternatives (If Not Using RAG)
If RAG were disabled (offline mode), Aegis AI would rely solely on:

- **Static model outputs:** Whisper + Vision model labels → rule-based filter (regex + thresholds).  
- **Hardcoded context:** Simple keyword list matching; no semantic search.  
- **Updates:** Manual lexicon reload every release.

**Drawbacks:**
- Higher false positives (homographs)  
- No explainability  
- No adaptive learning from feedback  

Hence, the hybrid RAG setup is essential for precision, transparency, and user trust.

---

### ✅ Summary
This RAG design enables Aegis AI to:
- Combine **semantic retrieval** and **keyword precision** for censorship decisions  
- Generate **explainable rationales** and verifiable citations  
- Adapt continuously via user feedback  
- Maintain low latency and privacy (local vector DB)

**Final Architecture:**
-->
