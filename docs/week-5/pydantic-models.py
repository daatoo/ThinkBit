# ========================================
# 📘 Aegis AI – Pydantic Models
# File: docs/week-5/pydantic-models.py
# ========================================

# from pydantic import BaseModel, Field, HttpUrl, conlist
# from typing import List, Optional, Literal, Tuple
# from datetime import datetime

# ========================================
# USER MODELS
# ========================================

# class UserProfile(BaseModel):
#     """Registered Aegis AI user profile"""
#     user_id: str = Field(description="Unique user identifier (UUID)")
#     email: str = Field(description="User email for notifications")
#     profile_type: Literal["kids", "teen", "studio"] = Field(
#         description="Censorship profile preference"
#     )
#     api_tier: Literal["free", "pro", "enterprise"] = Field(
#         description="Subscription tier defining processing limits"
#     )
#     created_at: datetime = Field(default_factory=datetime.now)

#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "user_id": "123e4567-e89b-12d3-a456-426614174000",
#                 "email": "jane@example.com",
#                 "profile_type": "kids",
#                 "api_tier": "pro"
#             }
#         }

# ========================================
# AUDIO DETECTION MODELS
# ========================================

# class AudioDetectionInput(BaseModel):
#     """Input for profanity detection"""
#     video_url: HttpUrl = Field(description="Pre-signed or public URL to video")
#     language: str = Field(default="en", description="Language code (ISO 639-1)")
#     custom_keywords: Optional[List[str]] = Field(
#         default=None, description="User-defined keywords to flag"
#     )

# class AudioDetectionOutput(BaseModel):
#     """Profanity detection results"""
#     detections: List[dict] = Field(
#         description="List of detected profane words with timestamps"
#     )
#     profanity_score: float = Field(ge=0.0, le=1.0, description="Overall profanity intensity")
#     transcript_excerpt: Optional[str] = Field(None, description="Relevant transcription snippet")

#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "detections": [
#                     {"word": "f***", "start": 13.25, "end": 13.75, "confidence": 0.97}
#                 ],
#                 "profanity_score": 0.82,
#                 "transcript_excerpt": "...I'll kick your ass..."
#             }
#         }

# ========================================
# VISUAL DETECTION MODELS
# ========================================

# class VisualDetectionInput(BaseModel):
#     """Input for visual violence/explicit content detection"""
#     frame_urls: List[HttpUrl] = Field(description="List of extracted frame URLs")
#     threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence threshold")

# class VisualDetectionOutput(BaseModel):
#     """Detected violent or explicit frames"""
#     flagged_frames: List[int] = Field(description="Indices of frames flagged for violence")
#     avg_confidence: float = Field(ge=0.0, le=1.0, description="Average detection confidence")
#     labels: List[str] = Field(description="Content categories identified")

#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "flagged_frames": [34, 35, 36],
#                 "avg_confidence": 0.88,
#                 "labels": ["violence", "blood"]
#             }
#         }

# ========================================
# VIDEO COMPOSITION MODELS
# ========================================

# class VideoComposeInput(BaseModel):
#     """Input for final censorship rendering"""
#     source_video: HttpUrl = Field(description="URL of original video file")
#     mutes: Optional[List[Tuple[float, float]]] = Field(
#         None, description="List of [start, end] times (sec) to mute audio"
#     )
#     blurs: Optional[List[Tuple[float, float]]] = Field(
#         None, description="List of [start, end] times (sec) to blur video"
#     )
#     blur_strength: int = Field(default=15, ge=1, le=50, description="Blur intensity")

# class VideoComposeOutput(BaseModel):
#     """Result of censorship rendering"""
#     output_url: HttpUrl = Field(description="URL to censored video file")
#     processing_time: float = Field(description="Time taken to process in seconds")
#     size_mb: float = Field(description="Final video size in megabytes")

#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "output_url": "https://cdn.aegisai.com/processed/movie_censored.mp4",
#                 "processing_time": 14.3,
#                 "size_mb": 76.4
#             }
#         }

# ========================================
# RAG / RETRIEVAL MODELS
# ========================================

# class RetrievedEvidence(BaseModel):
#     """Evidence item retrieved from RAG store"""
#     evidence_id: str
#     type: Literal["policy", "lexicon", "audio_exemplar", "vision_exemplar"]
#     similarity: float = Field(ge=0.0, le=1.0)
#     source_path: str
#     snippet: Optional[str] = None

# class RAGDecisionContext(BaseModel):
#     """Context returned by RAG retrieval before censorship decision"""
#     text_evidence: Optional[List[RetrievedEvidence]] = None
#     visual_evidence: Optional[List[RetrievedEvidence]] = None
#     decision_type: Literal["audio", "vision"]
#     retrieved_at: datetime = Field(default_factory=datetime.now)

# ========================================
# ERROR & LOGGING MODELS
# ========================================

# class ErrorResponse(BaseModel):
#     """Standardized error model for all API endpoints"""
#     error_code: str
#     error_message: str
#     details: Optional[dict] = None
#     timestamp: datetime = Field(default_factory=datetime.now)

#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "error_code": "VIDEO_NOT_FOUND",
#                 "error_message": "The provided video URL could not be accessed.",
#                 "details": {"url": "https://cdn.aegisai.com/uploads/missing.mp4"}
#             }
#         }

# ========================================
# EXAMPLES / SELF-TEST
# ========================================

# if __name__ == "__main__":
#     # Example 1: Create audio detection input
#     inp = AudioDetectionInput(
#         video_url="https://cdn.aegisai.com/uploads/movie.mp4",
#         custom_keywords=["idiot", "stupid"]
#     )
#     print(inp.model_dump_json(indent=2))

#     # Example 2: Parse mock output into structured model
#     out = AudioDetectionOutput(
#         detections=[{"word": "f***", "start": 13.25, "end": 13.75, "confidence": 0.97}],
#         profanity_score=0.82,
#         transcript_excerpt="...I'll kick your ass..."
#     )
#     print(out.model_dump_json(indent=2))

#     # Example 3: Validation demonstration
#     try:
#         bad_input = VisualDetectionInput(frame_urls=[], threshold=1.5)
#     except Exception as e:
#         print(f"Validation error caught: {e}")
