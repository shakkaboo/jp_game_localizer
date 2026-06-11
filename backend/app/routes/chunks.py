import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Chunk, ContextData, Project, SourceFile, SourceLine, Translation
from app.schemas import ChunkDetailRead, ChunkListRead, ChunkRead
from app.services.chunker import Chunker
from app.services.memory_service import MemoryService
from app.services.normalizer import ScriptNormalizer

router = APIRouter(prefix="/chunks", tags=["chunks"])


@router.post("/create/{project_id}")
async def create_chunks(
    project_id: int,
    source_file_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    # Determine which source files to chunk
    query = db.query(SourceFile).filter(SourceFile.project_id == project_id)
    if source_file_id:
        query = query.filter(SourceFile.id == source_file_id)
    source_files = query.all()

    if not source_files:
        raise HTTPException(400, "No source files found for the given criteria")

    all_created: list[Chunk] = []

    for sf in source_files:
        # Delete existing chunks for this source file
        existing = db.query(Chunk).filter(Chunk.source_file_id == sf.id).all()
        for c in existing:
            db.query(SourceLine).filter(SourceLine.chunk_id == c.id).update(
                {SourceLine.chunk_id: None}
            )
            db.delete(c)
        db.flush()

        # Load context for initial memory
        context_data = (
            db.query(ContextData)
            .filter(ContextData.project_id == project_id)
            .order_by(ContextData.id.desc())
            .first()
        )
        normalized_context: dict = {}
        if context_data and context_data.context_json:
            try:
                normalized_context = json.loads(context_data.context_json)
            except json.JSONDecodeError:
                pass

        # Load source lines in order
        source_lines = (
            db.query(SourceLine)
            .filter(
                SourceLine.project_id == project_id,
                SourceLine.source_file_id == sf.id,
            )
            .order_by(SourceLine.id)
            .all()
        )

        if not source_lines:
            continue

        raw = [
            {
                "line_id": sl.line_id or "",
                "character": sl.character or "",
                "source_text_ja": sl.source_text_ja,
                "scene_hint": sl.scene_hint or "",
            }
            for sl in source_lines
        ]
        normalized = ScriptNormalizer().normalize(raw)

        # Build initial memory
        initial_memory = MemoryService.build_initial_memory(normalized_context)
        initial_memory_json = json.dumps(initial_memory, ensure_ascii=False) if initial_memory else None

        # Group lines by scene_hint preserving order
        scene_order: dict[str, list[dict]] = {}
        seen_hints: list[str] = []
        for line_obj in normalized["lines"]:
            hint = line_obj["scene_hint"]
            if hint not in scene_order:
                scene_order[hint] = []
                seen_hints.append(hint)
            scene_order[hint].append(line_obj)

        # Create chunks
        source_lines_by_id: dict[str, SourceLine] = {}
        for sl in source_lines:
            key = sl.line_id or ""
            source_lines_by_id[key] = sl

        chunks_created = 0
        for idx, hint in enumerate(seen_hints, start=1):
            scene_lines = scene_order[hint]

            chunk_ref = Chunk(
                project_id=project_id,
                source_file_id=sf.id,
                chunk_number=idx,
                chunk_title=hint,
                scene_hint=hint,
                status="pending",
                previous_memory_json=initial_memory_json if idx == 1 else None,
            )
            db.add(chunk_ref)
            db.flush()

            # Assign chunk_id to matching source lines
            for line_obj in scene_lines:
                key = line_obj["line_id"]
                match = source_lines_by_id.get(key)
                if match:
                    match.chunk_id = chunk_ref.id

            all_created.append(chunk_ref)
            chunks_created += 1

    db.commit()

    return {
        "message": f"Created {len(all_created)} chunks",
        "project_id": project_id,
        "chunks": [ChunkRead.model_validate(c) for c in all_created],
    }



@router.get("/{project_id}")
async def list_chunks(
    project_id: int,
    source_file_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    query = db.query(Chunk).filter(Chunk.project_id == project_id)
    if source_file_id is not None:
        query = query.filter(Chunk.source_file_id == source_file_id)
    chunks = query.order_by(Chunk.chunk_number).all()

    result = []
    for c in chunks:
        lines_count = (
            db.query(SourceLine)
            .filter(SourceLine.chunk_id == c.id)
            .count()
        )
        result.append(
            ChunkListRead(
                id=c.id,
                chunk_number=c.chunk_number,
                chunk_title=c.chunk_title,
                scene_hint=c.scene_hint,
                source_file_id=c.source_file_id,
                lines_count=lines_count,
                status=c.status,
            )
        )
    return result


@router.get("/detail/{chunk_id}")
async def get_chunk_detail(chunk_id: int, db: Session = Depends(get_db)):
    chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(404, "Chunk not found")

    source_lines = (
        db.query(SourceLine)
        .filter(SourceLine.chunk_id == chunk_id)
        .order_by(SourceLine.id)
        .all()
    )

    translations = (
        db.query(Translation)
        .filter(Translation.chunk_id == chunk_id)
        .order_by(Translation.id)
        .all()
    )

    prev_memory = None
    if chunk.previous_memory_json:
        try:
            prev_memory = json.loads(chunk.previous_memory_json)
        except json.JSONDecodeError:
            prev_memory = chunk.previous_memory_json

    chunk_memory = None
    if chunk.chunk_memory_json:
        try:
            chunk_memory = json.loads(chunk.chunk_memory_json)
        except json.JSONDecodeError:
            chunk_memory = chunk.chunk_memory_json

    return ChunkDetailRead(
        id=chunk.id,
        project_id=chunk.project_id,
        source_file_id=chunk.source_file_id,
        chunk_number=chunk.chunk_number,
        chunk_title=chunk.chunk_title,
        scene_hint=chunk.scene_hint,
        status=chunk.status,
        previous_memory_json=prev_memory,
        chunk_memory_json=chunk_memory,
        source_lines=source_lines,
        translations=translations,
    )
