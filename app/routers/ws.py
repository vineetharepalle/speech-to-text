import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket

from app import crud
from app.config import settings
from app.database import SessionLocal
from app.schemas import TranscriptionCreate
from app.stt import StreamingSession

router = APIRouter()


@router.websocket("/ws/transcribe")
async def ws_transcribe(ws: WebSocket):
    await ws.accept()
    session = StreamingSession()
    stop = asyncio.Event()

    async def receiver():
        try:
            while True:
                msg = await ws.receive()
                if msg["type"] == "websocket.disconnect":
                    break
                if msg.get("bytes"):
                    session.add_pcm16(msg["bytes"])
                elif msg.get("text"):
                    if json.loads(msg["text"]).get("event") == "stop":
                        break
        finally:
            stop.set()

    async def processor():
        while not stop.is_set():
            await asyncio.sleep(settings.partial_interval_sec)
            if stop.is_set() or not session.has_new_audio():
                continue
            result = await asyncio.to_thread(session.step)
            if result:
                await ws.send_json(result)

    recv_task = asyncio.create_task(receiver())
    proc_task = asyncio.create_task(processor())
    await stop.wait()
    await asyncio.gather(recv_task, proc_task, return_exceptions=True)

    # Flush remaining audio and save to the database
    try:
        await asyncio.to_thread(session.step, True)
        saved_id = None
        if session.full_text:
            title = "Recording " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            db = SessionLocal()
            try:
                rec = crud.create(
                    db,
                    TranscriptionCreate(
                        title=title,
                        text=session.full_text,
                        language=session.language_label,
                        duration_seconds=round(session.duration, 2),
                    ),
                )
                saved_id = rec.id
            finally:
                db.close()
        await ws.send_json({"type": "final", "text": session.full_text, "id": saved_id})
        await ws.close()
    except Exception:
        pass  # client already disconnected
