from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.limiter import limiter
from app.schemas import TranscriptionCreate, TranscriptionOut, TranscriptionUpdate

router = APIRouter(prefix="/api/transcriptions", tags=["transcriptions"])


@router.post("", response_model=TranscriptionOut, status_code=201)
@limiter.limit("20/minute")
def create_transcription(
    request: Request, data: TranscriptionCreate, db: Session = Depends(get_db)
):
    return crud.create(db, data)


@router.get("", response_model=list[TranscriptionOut])
@limiter.limit("60/minute")
def list_transcriptions(
    request: Request,
    q: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return crud.list_items(db, q=q, skip=skip, limit=limit)


@router.get("/{item_id}", response_model=TranscriptionOut)
@limiter.limit("120/minute")
def get_transcription(request: Request, item_id: int, db: Session = Depends(get_db)):
    obj = crud.get(db, item_id)
    if not obj:
        raise HTTPException(404, "Transcription not found")
    return obj


@router.put("/{item_id}", response_model=TranscriptionOut)
@limiter.limit("30/minute")
def update_transcription(
    request: Request,
    item_id: int,
    data: TranscriptionUpdate,
    db: Session = Depends(get_db),
):
    obj = crud.get(db, item_id)
    if not obj:
        raise HTTPException(404, "Transcription not found")
    return crud.update(db, obj, data)


@router.delete("/{item_id}", status_code=204)
@limiter.limit("10/minute")
def delete_transcription(
    request: Request, item_id: int, db: Session = Depends(get_db)
):
    obj = crud.get(db, item_id)
    if not obj:
        raise HTTPException(404, "Transcription not found")
    crud.delete(db, obj)
    return Response(status_code=204)
