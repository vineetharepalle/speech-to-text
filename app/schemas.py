from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TranscriptionCreate(BaseModel):
    title: str = Field(default="Untitled", max_length=200)
    text: str
    language: str | None = None
    duration_seconds: float = 0.0


class TranscriptionUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    text: str | None = None


class TranscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    text: str
    language: str | None
    duration_seconds: float
    created_at: datetime
    updated_at: datetime
