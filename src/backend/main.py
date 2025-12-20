from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import and_
from sqlalchemy.orm import Session
import sys

# Force UTF-8 encoding for stdout/stderr on Windows to avoid charmap errors
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from .db import get_db, init_db
from .models import CensorSegment, ProcessStatus, ProcessedMedia, utc_now
from .schemas import HealthResponse, MediaListResponse, MediaResponse, MessageResponse, RawFileResponse, SegmentResponse, StatsResponse
from .services.pipeline_wrapper import process_media

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"

MAX_FILE_SIZE = 500 * 1024 * 1024
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".wav", ".mp3", ".flac", ".m4a", ".webm"}
ALLOWED_MIMETYPES = {"video/mp4", "video/quicktime", "video/x-matroska", "video/x-msvideo", 
                     "audio/wav", "audio/mpeg", "audio/flac", "audio/x-m4a", "audio/mp4",
                     "video/webm", "audio/webm"}


def _ensure_directories():
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def _detect_input_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".wav", ".mp3", ".flac", ".m4a"}:
        return "audio"
    if ext in {".mp4", ".mov", ".mkv", ".avi", ".webm"}:
        return "video"
    return "video"


def _compute_file_hash(path: Path) -> str:
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _to_response(media: ProcessedMedia) -> MediaResponse:
    input_name = Path(media.input_path).name if media.input_path else None
    output_name = Path(media.output_path).name if media.output_path else None
    return MediaResponse(
        id=media.id,
        input_path=input_name,
        output_path=output_name,
        input_type=media.input_type,
        filter_audio=media.filter_audio,
        filter_video=media.filter_video,
        status=media.status,
        progress=media.progress,
        current_activity=media.current_activity,
        logs=media.logs.split("\n") if media.logs else [],
        error_message=media.error_message,
        created_at=media.created_at,
        updated_at=media.updated_at,
        segments=[
            SegmentResponse(
                id=seg.id,
                start_ms=seg.start_ms,
                end_ms=seg.end_ms,
                action_type=seg.action_type,
                reason=seg.reason,
            )
            for seg in media.segments
        ],
    )


def _validate_upload(filename: str, content_type: str | None, size: int) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed: {ext}")
    if content_type and content_type not in ALLOWED_MIMETYPES:
        raise HTTPException(status_code=400, detail=f"Invalid content type: {content_type}")
    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max: {MAX_FILE_SIZE // (1024*1024)}MB")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_directories()
    init_db()
    logger.info("Backend started")
    yield
    logger.info("Backend stopped")


app = FastAPI(title="AegisAI", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")


@app.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    total_media = db.query(ProcessedMedia).count()
    total_segments = db.query(CensorSegment).count()

    by_status = {
        ProcessStatus.CREATED: db.query(ProcessedMedia).filter(ProcessedMedia.status == ProcessStatus.CREATED).count(),
        ProcessStatus.PROCESSING: db.query(ProcessedMedia).filter(ProcessedMedia.status == ProcessStatus.PROCESSING).count(),
        ProcessStatus.DONE: db.query(ProcessedMedia).filter(ProcessedMedia.status == ProcessStatus.DONE).count(),
        ProcessStatus.FAILED: db.query(ProcessedMedia).filter(ProcessedMedia.status == ProcessStatus.FAILED).count(),
    }

    by_type = {}
    for row in db.query(ProcessedMedia.input_type).distinct():
        by_type[row[0]] = db.query(ProcessedMedia).filter(ProcessedMedia.input_type == row[0]).count()

    return StatsResponse(total_media=total_media, total_segments=total_segments, by_status=by_status, by_type=by_type)


@app.get("/media", response_model=MediaListResponse)
def list_media(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(ProcessedMedia)
    if status:
        query = query.filter(ProcessedMedia.status == status)

    total = query.count()
    items = query.order_by(ProcessedMedia.created_at.desc()).offset(skip).limit(limit).all()

    return MediaListResponse(total=total, skip=skip, limit=limit, items=[_to_response(m) for m in items])


@app.get("/media/{media_id}", response_model=MediaResponse)
def get_media(media_id: int, db: Session = Depends(get_db)):
    media = db.query(ProcessedMedia).filter(ProcessedMedia.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return _to_response(media)


@app.get("/download/{media_id}")
def download_media(
    media_id: int,
    variant: str = Query("processed", regex="^(original|processed)$"),
    db: Session = Depends(get_db)
):
    media = db.query(ProcessedMedia).filter(ProcessedMedia.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    if variant == "processed":
        if media.status != ProcessStatus.DONE:
            raise HTTPException(status_code=400, detail=f"Processing not complete: {media.status}")

        if not media.output_path:
            raise HTTPException(status_code=404, detail="Output file not found")

        file_path = Path(media.output_path)
    else:
        # Serve original input
        if not media.input_path:
            raise HTTPException(status_code=404, detail="Input file record missing")

        file_path = Path(media.input_path)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"{variant.capitalize()} file missing on disk")

    return FileResponse(path=file_path, filename=file_path.name, media_type="application/octet-stream")


@app.delete("/media/{media_id}", response_model=MessageResponse)
def delete_media(media_id: int, db: Session = Depends(get_db)):
    media = db.query(ProcessedMedia).filter(ProcessedMedia.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    input_path = Path(media.input_path) if media.input_path else None
    output_path = Path(media.output_path) if media.output_path else None

    db.delete(media)
    db.commit()

    if input_path and input_path.exists():
        input_path.unlink()
    if output_path and output_path.exists():
        output_path.unlink()

    return MessageResponse(message="Deleted")


@app.get("/outputs/files", response_model=list[RawFileResponse])
def list_output_files():
    files = []
    if OUTPUTS_DIR.exists():
        for path in OUTPUTS_DIR.iterdir():
            if path.is_file():
                # Get modification time
                stats = path.stat()
                files.append(
                    RawFileResponse(
                        filename=path.name,
                        modified_at=datetime.fromtimestamp(stats.st_mtime)
                    )
                )
    return files


@app.get("/outputs/files/{filename}")
def get_output_file(filename: str):
    file_path = OUTPUTS_DIR / filename
    # Security check: prevent directory traversal
    if not file_path.resolve().is_relative_to(OUTPUTS_DIR.resolve()):
         raise HTTPException(status_code=403, detail="Access denied")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=file_path)


def run_pipeline_background(media_id: int, db: Session):
    try:
        media = db.query(ProcessedMedia).filter(ProcessedMedia.id == media_id).first()
        if not media:
            return

        media.status = ProcessStatus.PROCESSING
        media.progress = 0
        media.current_activity = "Starting..."
        db.commit()

        def progress_callback(progress: int, activity: str):
            try:
                # Re-fetch to avoid stale object? 
                # Or just update inplace if session is alive.
                # Just separate transaction might be safer if frequent updates.
                media.progress = progress
                media.current_activity = activity
                
                # Append to logs
                timestamp = utc_now().strftime("%H:%M:%S")
                log_entry = f"[{timestamp}] {activity}"
                if media.logs:
                    media.logs = media.logs + "\n" + log_entry
                else:
                    media.logs = log_entry
                    
                db.commit()
            except Exception as e:
                logger.error(f"Error updating progress: {e}")

        subtitle_path = Path(media.subtitle_path) if media.subtitle_path else None

        result = process_media(
            input_path=Path(media.input_path),
            input_type=media.input_type,
            output_dir=OUTPUTS_DIR,
            filter_audio=media.filter_audio,
            filter_video=media.filter_video,
            progress_callback=progress_callback,
            subtitle_path=subtitle_path,
        )

        media.output_path = result["output_path"]
        media.status = ProcessStatus.DONE
        media.progress = 100
        media.current_activity = "Completed"
        db.commit()

        for seg in result.get("segments", []):
            db.add(CensorSegment(
                media_id=media.id,
                start_ms=int(seg["start_ms"]),
                end_ms=int(seg["end_ms"]),
                action_type=str(seg.get("action_type") or "mute"),
                reason=str(seg.get("reason") or ""),
            ))

        db.commit()

    except Exception as exc:
        logger.exception("Pipeline failed")
        try:
            media = db.query(ProcessedMedia).filter(ProcessedMedia.id == media_id).first()
            if media:
                media.status = ProcessStatus.FAILED
                media.error_message = str(exc)
                db.commit()
        except:
            pass


@app.post("/process", response_model=MediaResponse)
async def process_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    subtitle_file: UploadFile = File(None),
    filter_audio: bool = Query(True),
    filter_video: bool = Query(False),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename")

    content = await file.read()
    _validate_upload(file.filename, file.content_type, len(content))

    original_name = Path(file.filename)
    upload_path = UPLOADS_DIR / original_name.name

    counter = 1
    while upload_path.exists():
        upload_path = UPLOADS_DIR / f"{original_name.stem}_{counter}{original_name.suffix}"
        counter += 1

    upload_path.write_bytes(content)

    subtitle_path_str = None
    if subtitle_file and subtitle_file.filename:
        # Validate extension
        sub_ext = Path(subtitle_file.filename).suffix.lower()
        if sub_ext not in {".srt", ".vtt"}:
             raise HTTPException(status_code=400, detail=f"Invalid subtitle format: {sub_ext}")

        # Save subtitle file
        sub_content = await subtitle_file.read()
        sub_name = Path(subtitle_file.filename)
        sub_path = UPLOADS_DIR / f"{original_name.stem}_{sub_name.name}"

        # Ensure unique name
        sub_counter = 1
        while sub_path.exists():
             sub_path = UPLOADS_DIR / f"{original_name.stem}_{sub_counter}_{sub_name.name}"
             sub_counter += 1

        sub_path.write_bytes(sub_content)
        subtitle_path_str = str(sub_path)

    input_type = _detect_input_type(upload_path)
    file_hash = _compute_file_hash(upload_path)

    existing = (
        db.query(ProcessedMedia)
        .filter(
            and_(
                ProcessedMedia.file_hash == file_hash,
                ProcessedMedia.filter_audio == filter_audio,
                ProcessedMedia.filter_video == filter_video,
                ProcessedMedia.status == ProcessStatus.DONE,
            )
        )
        .first()
    )

    if existing and existing.output_path:
        upload_path.unlink()
        return _to_response(existing)

    media = ProcessedMedia(
        input_path=str(upload_path),
        input_type=input_type,
        file_hash=file_hash,
        filter_audio=filter_audio,
        filter_video=filter_video,
        subtitle_path=subtitle_path_str,
        status=ProcessStatus.CREATED,
        progress=0,
        current_activity="Queued",
    )
    db.add(media)
    db.commit()
    db.refresh(media)

    background_tasks.add_task(run_pipeline_background, media.id, db)

    return _to_response(media)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8080")), reload=True)
