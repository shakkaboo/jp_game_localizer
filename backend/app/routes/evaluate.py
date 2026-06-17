import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.ai.llm_client import call_llm_json, get_llm_settings, get_normalized_provider
from app.ai.prompts import PROMPT_VERSION, build_chunk_localization_prompt
from app.database import get_db
from app.models import Chunk, ContextData, EvaluationRun, EvaluationTranslation, SourceLine
from app.schemas import EvaluationMode, EvaluationRunDetailRead, EvaluationRunRead, EvaluationTranslateResponse

router = APIRouter(prefix="/evaluate", tags=["evaluate"])


def _load_chunk_lines(chunk_id: int, db: Session) -> tuple[Chunk, list[dict[str, str]]]:
    chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(404, "Chunk not found")

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
    return chunk, chunk_lines


def _load_context(chunk: Chunk, db: Session) -> dict:
    context_data = (
        db.query(ContextData)
        .filter(ContextData.project_id == chunk.project_id)
        .order_by(ContextData.id.desc())
        .first()
    )
    normalized: dict = {}
    if context_data and context_data.context_json:
        try:
            normalized = json.loads(context_data.context_json)
        except json.JSONDecodeError:
            pass
    return normalized


def _resolve_previous_memory(chunk: Chunk, db: Session) -> dict | None:
    if chunk.chunk_number == 1:
        if chunk.previous_memory_json:
            try:
                return json.loads(chunk.previous_memory_json)
            except json.JSONDecodeError:
                return {"raw": chunk.previous_memory_json}
        return None

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
            return json.loads(prev_chunk.chunk_memory_json)
        except json.JSONDecodeError:
            return {"raw": prev_chunk.chunk_memory_json}
    return None


_CATEGORY_LLM_FAILED = "llm_request_failed"
_CATEGORY_INVALID_RESPONSE = "invalid_llm_response"
_CATEGORY_NO_TRANSLATIONS = "no_translations_returned"


def _categorize_error(e: Exception) -> str:
    msg = str(e).lower()
    if "empty" in msg or "invalid json" in msg:
        return _CATEGORY_INVALID_RESPONSE
    if "retry also failed" in msg:
        return _CATEGORY_INVALID_RESPONSE
    return _CATEGORY_LLM_FAILED


@router.post("/chunk/{chunk_id}", response_model=EvaluationTranslateResponse)
async def evaluate_chunk(
    chunk_id: int,
    mode: str = Query(..., description="Evaluation mode: plain, context, or context_memory"),
    db: Session = Depends(get_db),
):
    try:
        eval_mode = EvaluationMode(mode)
    except ValueError:
        raise HTTPException(422, f"Invalid mode '{mode}'. Must be one of: {', '.join(e.value for e in EvaluationMode)}")

    chunk, chunk_lines = _load_chunk_lines(chunk_id, db)
    normalized_context = _load_context(chunk, db)

    previous_memory = None
    if eval_mode == EvaluationMode.context_memory:
        previous_memory = _resolve_previous_memory(chunk, db)

    messages = build_chunk_localization_prompt(
        chunk_lines=chunk_lines,
        project_context=normalized_context.get("project", {}),
        characters=normalized_context.get("characters", []),
        relationships=normalized_context.get("relationships", []),
        glossary=normalized_context.get("glossary", []),
        style_rules=normalized_context.get("style_rules", []),
        raw_context=normalized_context.get("raw_context", ""),
        previous_memory=previous_memory,
        mode=eval_mode.value,
    )

    settings = get_llm_settings()
    request_config = json.dumps({
        "temperature": 0.3,
        "max_tokens": 4096,
        "response_format": True,
    })

    run = EvaluationRun(
        chunk_id=chunk_id,
        mode=eval_mode.value,
        provider=get_normalized_provider(),
        model=settings["model"],
        prompt_version=PROMPT_VERSION,
        request_config=request_config,
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.flush()

    try:
        result = call_llm_json(messages)
    except Exception as e:
        run.status = "failed"
        run.error_message = _categorize_error(e)
        db.commit()
        raise HTTPException(502, f"Evaluation failed: {run.error_message}")

    translations_raw = result.get("translations", [])
    if not translations_raw:
        run.status = "failed"
        run.error_message = _CATEGORY_NO_TRANSLATIONS
        db.commit()
        raise HTTPException(500, "AI returned no translations")

    line_map: dict[str, SourceLine] = {}
    source_lines = (
        db.query(SourceLine)
        .filter(SourceLine.chunk_id == chunk_id)
        .all()
    )
    for sl in source_lines:
        line_map[str(sl.line_id or "")] = sl

    inserted = 0
    for t_raw in translations_raw:
        lid = str(t_raw.get("line_id", ""))
        match = line_map.get(lid)
        if not match:
            continue

        db.add(
            EvaluationTranslation(
                evaluation_run_id=run.id,
                source_line_id=match.id,
                line_id=t_raw.get("line_id", ""),
                character=t_raw.get("character", ""),
                source_text_ja=t_raw.get("source_text_ja", ""),
                literal_meaning=t_raw.get("literal_meaning", ""),
                localized_text_en=t_raw.get("localized_text_en", ""),
                localization_note=t_raw.get("localization_note", ""),
            )
        )
        inserted += 1

    chunk_memory = result.get("chunk_memory", {})
    if eval_mode == EvaluationMode.context_memory:
        run.generated_memory = json.dumps(chunk_memory, ensure_ascii=False)
        response_memory = chunk_memory
    else:
        response_memory = None

    run.status = "completed"
    db.commit()

    return EvaluationTranslateResponse(
        run_id=run.id,
        chunk_id=chunk_id,
        mode=eval_mode.value,
        status="completed",
        translations_count=inserted,
        generated_memory=response_memory,
    )


@router.get("/runs", response_model=list[EvaluationRunRead])
async def list_evaluation_runs(
    chunk_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(EvaluationRun)
    if chunk_id is not None:
        query = query.filter(EvaluationRun.chunk_id == chunk_id)
    return query.order_by(EvaluationRun.id.desc()).all()


@router.get("/runs/{run_id}", response_model=EvaluationRunDetailRead)
async def get_evaluation_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Evaluation run not found")

    generated_memory = None
    if run.generated_memory:
        try:
            generated_memory = json.loads(run.generated_memory)
        except json.JSONDecodeError:
            generated_memory = run.generated_memory

    translations = (
        db.query(EvaluationTranslation)
        .filter(EvaluationTranslation.evaluation_run_id == run_id)
        .order_by(EvaluationTranslation.id)
        .all()
    )

    return EvaluationRunDetailRead(
        id=run.id,
        chunk_id=run.chunk_id,
        mode=run.mode,
        provider=run.provider,
        model=run.model,
        prompt_version=run.prompt_version,
        created_at=run.created_at,
        status=run.status,
        generated_memory=generated_memory,
        error_message=run.error_message,
        translations=[
            {
                "id": t.id,
                "evaluation_run_id": t.evaluation_run_id,
                "source_line_id": t.source_line_id,
                "line_id": t.line_id,
                "character": t.character,
                "source_text_ja": t.source_text_ja,
                "literal_meaning": t.literal_meaning,
                "localized_text_en": t.localized_text_en,
                "localization_note": t.localization_note,
            }
            for t in translations
        ],
    )
