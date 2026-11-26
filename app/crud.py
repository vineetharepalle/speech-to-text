from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Transcription
from app.schemas import TranscriptionCreate, TranscriptionUpdate


def create(db: Session, data: TranscriptionCreate) -> Transcription:
    obj = Transcription(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get(db: Session, item_id: int) -> Transcription | None:
    return db.get(Transcription, item_id)


def list_items(
    db: Session, q: str | None = None, skip: int = 0, limit: int = 50
) -> list[Transcription]:
    stmt = select(Transcription).order_by(Transcription.created_at.desc())
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(Transcription.title.ilike(like), Transcription.text.ilike(like))
        )
    return list(db.scalars(stmt.offset(skip).limit(limit)))


def update(
    db: Session, obj: Transcription, data: TranscriptionUpdate
) -> Transcription:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, obj: Transcription) -> None:
    db.delete(obj)
    db.commit()
