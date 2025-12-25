# Backend

FastAPI backend for AegisAI - basically the API that connects everything together.

## What it does

1. You upload a video/audio file
2. Backend saves it, checks if we already processed it before (cache)
3. If not cached, sends it to the AI pipeline (src/aegisai)
4. AI transcribes audio, finds bad words, calculates mute intervals
5. FFmpeg mutes/blurs the bad parts
6. Backend saves the censored file and returns it

## How to run

```bash
pip install -r requirements.txt
python -m backend.main
```

Server runs on http://localhost:8000

API docs at http://localhost:8000/docs

## Endpoints

| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | /health | Check if server is alive |
| GET | /stats | Get DB stats (total media, by status, etc) |
| GET | /media | List all processed media |
| GET | /media/{id} | Get one media by ID |
| POST | /process | Upload and process a file |
| GET | /download/{id} | Download the censored file |
| DELETE | /media/{id} | Delete media and files |

## Database

Uses SQLite by default (aegisai.db file). For production, set DATABASE_URL:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/aegisai python -m backend.main
```

## Files

```
backend/
├── main.py          <- all the endpoints
├── db.py            <- database connection
├── models.py        <- SQLAlchemy tables
├── schemas.py       <- Pydantic models for API
├── services/
│   └── pipeline_wrapper.py  <- connects to AI pipeline
├── uploads/         <- uploaded files go here
└── outputs/         <- censored files go here
```

## Connection to AI

The backend calls `src/aegisai/pipeline/runner.py` through `pipeline_wrapper.py`. That's where the actual AI stuff happens (Google Speech-to-Text, bad word detection, FFmpeg muting).



