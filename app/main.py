import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database import Base, engine
from app.limiter import limiter
from app.routers import transcriptions, ws
from app.stt import get_model

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)      # use Alembic for real migrations
    await asyncio.to_thread(get_model)         # load Whisper once at startup
    yield


app = FastAPI(title="Speech to Text", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(transcriptions.router)
app.include_router(ws.router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}
