# Speech to Text (Hindi + English, real-time)

FastAPI + faster-whisper (open-source, self-hosted) + PostgreSQL.

## Features
- Live multilingual transcription over WebSocket
- Transcripts saved to PostgreSQL
- Dashboard with create / read / update / delete and search

## Run
    cp .env.example .env
    docker compose up --build
Open http://localhost:8000

## Config
Set WHISPER_MODEL (tiny/base/small/medium) in .env. Larger = more accurate, slower.

## How the real-time flow works
1. The browser captures the mic at 16 kHz; an AudioWorklet converts it to 16-bit PCM.
2. PCM chunks go over the WebSocket to /ws/transcribe.
3. Every 1.5 s the server runs Whisper on the uncommitted audio and sends a partial result.
4. On a pause or after 10 s, the text is committed and the buffer resets.
5. On Stop, the server flushes the rest, saves to PostgreSQL and sends a final message.

## Limitations
- Tables are created with create_all; use Alembic migrations for production.
- Rate limits are in-memory (per process); use Redis storage for slowapi when scaling.
- No authentication yet.
