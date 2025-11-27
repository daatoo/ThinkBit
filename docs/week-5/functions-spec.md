# Functions Specification

<!-- TODO: Complete Functions Specification -->

<!--
# ⚙️ Aegis AI – Function Calling Specification
**File:** `docs/week-5/functions-spec.md`  
**Project:** ThinkBit / Aegis AI – Video Censoring Platform  
**Purpose:** Define callable functions for the AI assistant to perform automated content censorship actions.

---

## Step 1: Core Functions

### 1. `detect_profanity_audio`
Transcribes audio from uploaded video and detects profanity segments.

### 2. `detect_violence_frames`
Analyzes extracted frames to locate violent or explicit imagery.

### 3. `compose_censored_video`
Reconstructs a censored version of the original video using mute and blur operations.

---

## Step 2: Function Specifications

---

### Function: `detect_profanity_audio`

**Purpose:**  
Transcribe video audio using Whisper and locate segments containing profanity, slurs, or offensive language.

**When AI should call this:**  
- When user uploads or references a new video for censorship  
- When audio segments need semantic inspection before visual review  
- When user requests "check for profanity" or "mute bad words"

**Parameters:**
- `video_url` (string, required): HTTPS link to uploaded video file in S3 or CloudFront.  
- `language` (string, optional): Language code (`"en"`, `"es"`, `"ka"`), default: `"en"`.  
- `custom_keywords` (array of strings, optional): User-defined profanity list to include during detection.

**Returns:**
```json
{
  "detections": [
    {"word": "f***", "start": 13.25, "end": 13.75, "confidence": 0.97},
    {"word": "damn", "start": 57.40, "end": 57.60, "confidence": 0.89}
  ],
  "profanity_score": 0.82,
  "transcript_excerpt": "This is the transcribed text snippet..."
}
{
  "name": "detect_profanity_audio",
  "description": "Transcribe video audio and detect segments containing profanity or slurs.",
  "parameters": {
    "type": "object",
    "properties": {
      "video_url": {
        "type": "string",
        "format": "uri",
        "description": "Public or pre-signed URL to the video file"
      },
      "language": {
        "type": "string",
        "description": "Language code for transcription (ISO-639-1)",
        "default": "en"
      },
      "custom_keywords": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Optional list of additional keywords to flag"
      }
    },
    "required": ["video_url"]
  }
}
Example Call:

result = detect_profanity_audio(
    video_url="https://cdn.aegisai.com/uploads/movie.mp4",
    language="en",
    custom_keywords=["idiot", "stupid"]
)
# Returns: {"detections": [...], "profanity_score": 0.82}

Safety Considerations:

Validate URL format and file MIME type (audio/video only).

Redact slurs before logging.

Rate limit: 10 calls/min per user.

Never expose raw audio publicly; use pre-signed URLs.

Function: detect_violence_frames

Purpose:
Analyze keyframes for visual violence, blood, or explicit imagery using Vision APIs + local CNN fallback.

When AI should call this:

After audio review or on user command "check visuals"

When image frames are extracted from uploaded videos

During batch moderation or pre-export checks

Parameters:

frame_urls (array of strings, required): URLs of extracted frames.

threshold (number, optional): Confidence threshold for flagging (default: 0.7).

Returns:

{
  "flagged_frames": [34, 35, 36],
  "avg_confidence": 0.88,
  "labels": ["violence", "blood"]
}


JSON Schema:

{
  "name": "detect_violence_frames",
  "description": "Detect violent or explicit imagery within extracted video frames.",
  "parameters": {
    "type": "object",
    "properties": {
      "frame_urls": {
        "type": "array",
        "items": {"type": "string", "format": "uri"},
        "description": "List of frame image URLs to analyze"
      },
      "threshold": {
        "type": "number",
        "description": "Detection threshold for violence/graphic imagery",
        "default": 0.7
      }
    },
    "required": ["frame_urls"]
  }
}


Example Call:

result = detect_violence_frames(
    frame_urls=[
        "https://cdn.aegisai.com/frames/scene_034.jpg",
        "https://cdn.aegisai.com/frames/scene_035.jpg"
    ],
    threshold=0.8
)
# Returns: {"flagged_frames": [34, 35], "avg_confidence": 0.88}


Safety Considerations:

Do not retain unblurred sensitive frames beyond analysis.

Enforce confidence-based filtering to avoid bias.

Rate limit: 15 calls/min per user.

Function: compose_censored_video

Purpose:
Combine original video with censorship actions (mute + blur overlays) and export processed file.

When AI should call this:

After detect_profanity_audio and detect_violence_frames return results

When user requests "generate censored version" or "apply censorship"

Parameters:

source_video (string, required): URL of the original video file.

mutes (array of arrays, optional): List of [start_time, end_time] ranges (seconds) for muting.

blurs (array of arrays, optional): List of [start_time, end_time] ranges for blurring visuals.

blur_strength (integer, optional): Blur intensity level (default: 15).

Returns:

{
  "output_url": "https://cdn.aegisai.com/processed/movie_censored.mp4",
  "processing_time": 14.3,
  "size_mb": 76.4
}


JSON Schema:

{
  "name": "compose_censored_video",
  "description": "Merge the source video with muting and blurring operations to produce a censored version.",
  "parameters": {
    "type": "object",
    "properties": {
      "source_video": {
        "type": "string",
        "format": "uri",
        "description": "URL to the source video file"
      },
      "mutes": {
        "type": "array",
        "items": {
          "type": "array",
          "items": {"type": "number"},
          "minItems": 2,
          "maxItems": 2
        },
        "description": "List of time ranges (in seconds) to mute audio"
      },
      "blurs": {
        "type": "array",
        "items": {
          "type": "array",
          "items": {"type": "number"},
          "minItems": 2,
          "maxItems": 2
        },
        "description": "List of time ranges (in seconds) to blur video"
      },
      "blur_strength": {
        "type": "integer",
        "description": "Intensity of blur effect",
        "default": 15
      }
    },
    "required": ["source_video"]
  }
}


Example Call:

result = compose_censored_video(
    source_video="https://cdn.aegisai.com/uploads/movie.mp4",
    mutes=[[13.25, 13.75], [57.40, 57.60]],
    blurs=[[120.0, 121.2]],
    blur_strength=18
)
# Returns: {"output_url": ".../movie_censored.mp4", "processing_time": 14.3}


Safety Considerations:

Sanitize file paths and restrict to internal storage buckets.

Validate that mutes and blurs arrays contain only numeric ranges.

Output files expire after 24h via signed URL.

Rate limit: 5 calls/min per user.

Step 3: Summary
Function	Purpose	Triggered When	Primary Risk
detect_profanity_audio	Finds profanity in audio	On new upload	Misclassification of slang
detect_violence_frames	Detects graphic visuals	After keyframe extraction	False positives on sports/action scenes
compose_censored_video	Builds censored final file	After detection tasks complete	Incorrect mute/blur timing
-->
🔄 Function Calling Flow
Step-by-step overview

User Query
→ User says: “Censor this video for kids.”

AI Decision
→ The LLM decides which function(s) are needed:
detect_profanity_audio, detect_violence_frames, and later compose_censored_video.

Function Call (from LLM)
→ The model returns something like:

{
  "name": "detect_profanity_audio",
  "arguments": {
    "video_url": "https://cdn.aegisai.com/uploads/movie.mp4",
    "language": "en"
  }
}


Your Backend Executes It
→ Your code receives that JSON, runs the corresponding Python function (or API call).

Function Result → Back to AI
→ You pass the actual output (as JSON) back into the model’s context:

{
  "detections": [{"word": "f***", "start": 13.25, "end": 13.75}],
  "profanity_score": 0.82
}


AI Response Generation
→ The AI then continues the conversation — now it has real data, not guesses:

“The video contains 1 explicit phrase between 13–14 seconds. I’ll mute it in the output file.”

User Sees Result
→ Final natural language answer with reasoning and citation from the function’s output.

🧩 Python Example Loop (OpenAI-style pseudo-code)
from openai import OpenAI
import json
from functions import detect_profanity_audio, detect_violence_frames, compose_censored_video

client = OpenAI()

def call_function_by_name(name, args):
    if name == "detect_profanity_audio":
        return detect_profanity_audio(**args)
    elif name == "detect_violence_frames":
        return detect_violence_frames(**args)
    elif name == "compose_censored_video":
        return compose_censored_video(**args)
    else:
        raise ValueError(f"Unknown function: {name}")

# 1️⃣ User message
messages = [{"role": "user", "content": "Censor my video for kids."}]

# 2️⃣ Send to model with function specs
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    functions=[  # Register function schemas
        detect_profanity_audio_schema,
        detect_violence_frames_schema,
        compose_censored_video_schema
    ],
    function_call="auto"
)

# 3️⃣ Check if model wants to call a function
if response.choices[0].finish_reason == "function_call":
    fn_call = response.choices[0].message.function_call
    fn_name = fn_call.name
    fn_args = json.loads(fn_call.arguments)

    # 4️⃣ Run function locally
    result = call_function_by_name(fn_name, fn_args)

    # 5️⃣ Send result back to model
    messages.append(response.choices[0].message)
    messages.append({
        "role": "function",
        "name": fn_name,
        "content": json.dumps(result)
    })

    # 6️⃣ Get final synthesized answer
    followup = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    # 7️⃣ Show user the result
    print(followup.choices[0].message.content)

🧠 Conceptual Diagram
flowchart LR
    U[User Query] --> A[AI Model]
    A -->|Decides Function| F[Function Call JSON]
    F -->|Your Code Executes| X[External System or DB/API]
    X --> R[Function Result (JSON)]
    R --> A2[AI Synthesizes Final Response]
    A2 --> U2[User Sees Answer with Data]

⚡ Key Principles

The AI never executes code directly — it only proposes what to call.

Your app executes the function and controls all side effects (security, logging, DB).

You can chain multiple calls: the model can ask to run another function after seeing the first result.

Always validate inputs before execution (no arbitrary code injection)