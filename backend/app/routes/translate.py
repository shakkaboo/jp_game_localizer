import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.llm_client import call_llm_json
from app.ai.prompts import build_chunk_localization_prompt
from app.database import get_db
from app.models import Chunk, ContextData, SourceLine, Translation
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/translate", tags=["translate"])


@router.post("/chunk/{chunk_id}")
async def translate_chunk(chunk_id: int, db: Session = Depends(get_db)):
    chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(404, "Chunk not found")

    # Load context
    context_data = (
        db.query(ContextData)
        .filter(ContextData.project_id == chunk.project_id)
        .order_by(ContextData.id.desc())
        .first()
    )
    normalized_context: dict = {}
    if context_data and context_data.context_json:
        try:
            normalized_context = json.loads(context_data.context_json)
        except json.JSONDecodeError:
            pass

    # Load source lines for this chunk
    source_lines = (
        db.query(SourceLine)
        .filter(SourceLine.chunk_id == chunk_id)
        .order_by(SourceLine.id)
        .all()
    )
    if not source_lines:
        raise HTTPException(400, "Chunk has no source lines")

    chunk_lines = [
        {
            "line_id": sl.line_id or "",
            "character": sl.character or "",
            "source_text_ja": sl.source_text_ja,
        }
        for sl in source_lines
    ]

    # Determine previous memory
    previous_memory: dict | None = None
    if chunk.chunk_number == 1:
        if chunk.previous_memory_json:
            try:
                previous_memory = json.loads(chunk.previous_memory_json)
            except json.JSONDecodeError:
                previous_memory = {"raw": chunk.previous_memory_json}
    else:
        prev_chunk = (
            db.query(Chunk)
            .filter(
                Chunk.project_id == chunk.project_id,
                Chunk.source_file_id == chunk.source_file_id,
                Chunk.chunk_number == chunk.chunk_number - 1,
            )
            .first()
        )
        if prev_chunk and prev_chunk.chunk_memory_json:
            try:
                previous_memory = json.loads(prev_chunk.chunk_memory_json)
            except json.JSONDecodeError:
                previous_memory = {"raw": prev_chunk.chunk_memory_json}

    # Build prompt and call LLM
    messages = build_chunk_localization_prompt(
        project_context=normalized_context.get("project", {}),
        characters=normalized_context.get("characters", []),
        relationships=normalized_context.get("relationships", []),
        glossary=normalized_context.get("glossary", []),
        style_rules=normalized_context.get("style_rules", []),
        raw_context=normalized_context.get("raw_context", ""),
        previous_memory=previous_memory,
        chunk_lines=chunk_lines,
    )

    try:
        result = call_llm_json(messages)
    except Exception as e:
        raise HTTPException(502, f"AI localization failed: {e}")

    translations_raw = result.get("translations", [])
    if not translations_raw:
        raise HTTPException(500, "AI returned no translations")

    # Delete old translations for this chunk to avoid duplicates on retest
    db.query(Translation).filter(Translation.chunk_id == chunk_id).delete()
    db.flush()

    # Build line_id → SourceLine map (string keys)
    line_map: dict[str, SourceLine] = {}
    for sl in source_lines:
        line_map[str(sl.line_id or "")] = sl

    inserted = 0
    warnings: list[str] = []

    for t_raw in translations_raw:
        lid = str(t_raw.get("line_id", ""))
        match = line_map.get(lid)

        if not match:
            warnings.append(f"Skipped translation: line_id '{lid}' does not match any source line")
            continue

        db.add(
            Translation(
                project_id=chunk.project_id,
                chunk_id=chunk.id,
                source_line_id=match.id,
                literal_meaning=t_raw.get("literal_meaning", ""),
                localized_text_en=t_raw.get("localized_text_en", ""),
                final_text_en=t_raw.get("localized_text_en", ""),
                localization_note=t_raw.get("localization_note", ""),
                status="draft",
            )
        )
        inserted += 1

    # Build translations list for fallback
    inserted_translations = [
        {
            "source_text_ja": t_raw.get("source_text_ja", ""),
            "localized_text_en": t_raw.get("localized_text_en", ""),
            "character": t_raw.get("character", ""),
        }
        for t_raw in translations_raw
        if str(t_raw.get("line_id", "")) in line_map
    ]

    # Validate and ensure complete chunk memory
    chunk_memory = result.get("chunk_memory", {})
    chunk_memory = MemoryService.ensure_chunk_memory(
        chunk_memory=chunk_memory,
        previous_memory=previous_memory,
        chunk_lines=chunk_lines,
        translations=inserted_translations,
    )
    chunk.chunk_memory_json = json.dumps(chunk_memory, ensure_ascii=False)
    chunk.status = "translated"

    # Update next chunk's previous_memory
    next_chunk = (
        db.query(Chunk)
        .filter(
            Chunk.project_id == chunk.project_id,
            Chunk.source_file_id == chunk.source_file_id,
            Chunk.chunk_number == chunk.chunk_number + 1,
        )
        .first()
    )
    if next_chunk:
        next_chunk.previous_memory_json = json.dumps(
            chunk_memory, ensure_ascii=False
        )

    db.commit()

    return {
        "chunk_id": chunk.id,
        "status": "translated",
        "translations_count": inserted,
        "chunk_memory": chunk_memory,
        "warnings": warnings,
    }


@router.get("/{chunk_id}")
async def list_translations(chunk_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Translation)
        .filter(Translation.chunk_id == chunk_id)
        .order_by(Translation.id)
        .all()
    )


@router.patch("/{translation_id}")
async def update_translation(
    translation_id: int,
    body: dict,
    db: Session = Depends(get_db),
):
    txn = db.query(Translation).filter(Translation.id == translation_id).first()
    if not txn:
        raise HTTPException(404, "Translation not found")

    for key, value in body.items():
        if hasattr(txn, key):
            setattr(txn, key, value)

    db.commit()
    db.refresh(txn)
    return txn
