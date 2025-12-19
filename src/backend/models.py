from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProcessStatus:
    CREATED = "created"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class ProcessedMedia(Base):
    __tablename__ = "processed_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    input_path: Mapped[str] = mapped_column(String(512), nullable=False)
    output_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    input_type: Mapped[str] = mapped_column(String(32), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    filter_audio: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    filter_video: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=ProcessStatus.CREATED, nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_activity: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    segments: Mapped[list["CensorSegment"]] = relationship(
        "CensorSegment", back_populates="media", cascade="all, delete-orphan", lazy="selectin"
    )


class CensorSegment(Base):
    __tablename__ = "censor_segment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("processed_media.id"), nullable=False, index=True)
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    media: Mapped[ProcessedMedia] = relationship("ProcessedMedia", back_populates="segments")
