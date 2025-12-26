from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class SegmentResponse(BaseModel):
    id: int
    start_ms: int
    end_ms: int
    action_type: str
    reason: Optional[str] = None

    class Config:
        from_attributes = True


class MediaResponse(BaseModel):
    id: int
    input_path: str
    output_path: Optional[str] = None
    input_type: str
    filter_audio: bool
    filter_video: bool
    subtitle_path: Optional[str] = None
    status: str
    progress: int = 0
    current_activity: Optional[str] = None
    logs: Optional[list[str]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    segments: list[SegmentResponse] = []

    class Config:
        from_attributes = True


class MediaListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[MediaResponse]


class StatsResponse(BaseModel):
    total_media: int
    total_segments: int
    by_status: dict[str, int]
    by_type: dict[str, int]


class RawFileResponse(BaseModel):
    filename: str
    modified_at: datetime


class HealthResponse(BaseModel):
    status: str


class MessageResponse(BaseModel):
    message: str


# Authentication schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
