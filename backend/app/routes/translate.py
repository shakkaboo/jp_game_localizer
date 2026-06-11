from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Translation
from app.schemas import TranslationRead, TranslationUpdate

router = APIRouter(prefix="/translate", tags=["translate"])


@router.get("/{chunk_id}", response_model=list[TranslationRead])
async def list_translations(chunk_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Translation)
        .filter(Translation.chunk_id == chunk_id)
        .order_by(Translation.id)
        .all()
    )


@router.patch("/{translation_id}", response_model=TranslationRead)
async def update_translation(
    translation_id: int,
    body: TranslationUpdate,
    db: Session = Depends(get_db),
):
    txn = db.query(Translation).filter(Translation.id == translation_id).first()
    if not txn:
        raise HTTPException(404, "Translation not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(txn, key, value)

    db.commit()
    db.refresh(txn)
    return txn
