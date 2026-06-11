from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Chunk, Project, SourceFile, SourceLine
from app.schemas import ChunkGenerateRequest, ChunkRead
from app.services.chunker import Chunker
from app.services.normalizer import ScriptNormalizer

router = APIRouter(prefix="/chunks", tags=["chunks"])


@router.post("/generate")
async def generate_chunks(
    req: ChunkGenerateRequest,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    source_file = (
        db.query(SourceFile)
        .filter(SourceFile.id == req.source_file_id, SourceFile.project_id == req.project_id)
        .first()
    )
    if not source_file:
        raise HTTPException(404, "Source file not found")

    existing = db.query(Chunk).filter(Chunk.source_file_id == req.source_file_id).count()
    if existing > 0:
        raise HTTPException(400, "Chunks already exist for this source file. Delete them first to regenerate.")

    source_lines = (
        db.query(SourceLine)
        .filter(
            SourceLine.project_id == req.project_id,
            SourceLine.source_file_id == req.source_file_id,
        )
        .order_by(SourceLine.id)
        .all()
    )

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
    chunks = Chunker().chunk(normalized.lines, req.project_id, req.source_file_id)

    db_objects = []
    for ch in chunks:
        lines_for_chunk = ch.pop("lines")
        c = Chunk(**ch)
        db.add(c)
        db.flush()
        db_objects.append(c)

        for src_line in source_lines:
            matching = [
                l for l in lines_for_chunk if l.line_id == (src_line.line_id or "")
            ]
            if matching:
                src_line.chunk_id = c.id

    db.commit()

    return {
        "message": f"Generated {len(db_objects)} chunks",
        "project_id": req.project_id,
        "source_file_id": req.source_file_id,
        "chunks": [ChunkRead.model_validate(c) for c in db_objects],
    }


@router.get("/", response_model=list[ChunkRead])
async def list_chunks(
    project_id: int,
    source_file_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Chunk).filter(Chunk.project_id == project_id)
    if source_file_id is not None:
        query = query.filter(Chunk.source_file_id == source_file_id)
    return query.order_by(Chunk.chunk_number).all()


@router.get("/{chunk_id}", response_model=ChunkRead)
async def get_chunk(chunk_id: int, db: Session = Depends(get_db)):
    chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(404, "Chunk not found")
    return chunk
