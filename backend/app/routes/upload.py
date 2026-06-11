import json

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ContextData, Project, SourceFile, SourceLine
from app.schemas import UploadResponse
from app.services.context_parser import ContextParser
from app.services.file_detector import detect_file_type, is_context_file_type, is_script_file_type
from app.services.normalizer import ContextNormalizer, ScriptNormalizer
from app.services.script_parser import ScriptParser

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/context", response_model=UploadResponse)
async def upload_context(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    content = await file.read()
    filename = file.filename or "unknown"

    file_type = detect_file_type(filename)
    if file_type == "unknown" or not is_context_file_type(file_type):
        raise HTTPException(400, f"Unsupported context file type: {filename}")

    raw = ContextParser().parse(content, filename)
    normalized = ContextNormalizer().normalize(raw)

    context_data = ContextData(
        project_id=project_id,
        original_filename=filename,
        file_type=file_type,
        context_json=json.dumps(normalized, ensure_ascii=False),
        raw_context_text=normalized["raw_context"],
    )
    db.add(context_data)

    if normalized["project"].get("title"):
        project.title = normalized["project"]["title"]
    if normalized["project"].get("genre"):
        project.genre = normalized["project"]["genre"]
    if normalized["project"].get("target_tone"):
        project.target_tone = normalized["project"]["target_tone"]

    db.commit()
    db.refresh(context_data)

    return UploadResponse(
        project_id=project_id,
        file_id=context_data.id,
        filename=filename,
        file_type=file_type,
        message="Context file uploaded and processed",
    )


@router.post("/script", response_model=UploadResponse)
async def upload_script(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    content = await file.read()
    filename = file.filename or "unknown"

    file_type = detect_file_type(filename)
    if file_type == "unknown" or not is_script_file_type(file_type):
        raise HTTPException(400, f"Unsupported script file type: {filename}")

    raw_lines = ScriptParser().parse(content, filename)
    normalized = ScriptNormalizer().normalize(raw_lines)

    source_file = SourceFile(
        project_id=project_id,
        original_filename=filename,
        file_type=file_type,
        total_lines=len(normalized["lines"]),
    )
    db.add(source_file)
    db.flush()

    for line in normalized["lines"]:
        db.add(
            SourceLine(
                project_id=project_id,
                source_file_id=source_file.id,
                line_id=line["line_id"],
                character=line["character"],
                source_text_ja=line["source_text_ja"],
                scene_hint=line["scene_hint"],
            )
        )

    db.commit()
    db.refresh(source_file)

    return UploadResponse(
        project_id=project_id,
        file_id=source_file.id,
        filename=filename,
        file_type=file_type,
        message=f"Script file uploaded with {len(normalized['lines'])} lines",
    )
