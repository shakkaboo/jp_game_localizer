import json
import os

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ContextData, Project, SourceFile, SourceLine
from app.schemas import (
    ContextUploadResponse,
    ScriptUploadResponse,
    UploadResponse,
)
from app.services.context_parser import ContextParser
from app.services.file_detector import detect_file_type, is_context_file_type, is_script_file_type
from app.services.normalizer import ContextNormalizer, ScriptNormalizer
from app.services.script_parser import ScriptParser

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/context")
async def upload_context(
    file: UploadFile = File(...),
    project_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    content = await file.read()
    filename = file.filename or "unknown"

    file_type = detect_file_type(filename)
    if file_type == "unknown" or not is_context_file_type(file_type):
        raise HTTPException(400, f"Unsupported context file type: {filename}")

    project: Project | None = None
    if project_id:
        project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        project = Project()
        db.add(project)
        db.flush()

    try:
        raw = ContextParser().parse(content, filename)
    except Exception as e:
        raise HTTPException(422, f"Failed to parse context file: {e}")

    if raw is None:
        raw = {}
    if not isinstance(raw, (dict, str)):
        raw = str(raw)

    normalized = ContextNormalizer().normalize(raw)
    warnings = normalized["warnings"]

    proj_data = normalized.get("project") or {}
    project.title = proj_data.get("title") or os.path.splitext(filename)[0]
    project.genre = proj_data.get("genre", "")
    project.target_tone = proj_data.get("target_tone", "")
    db.flush()

    context_data = ContextData(
        project_id=project.id,
        original_filename=filename,
        file_type=file_type,
        context_json=json.dumps(normalized, ensure_ascii=False),
        raw_context_text=normalized.get("raw_context", ""),
    )
    db.add(context_data)
    db.commit()
    db.refresh(context_data)

    return ContextUploadResponse(
        project_id=project.id,
        file_type=file_type,
        project=proj_data,
        characters_count=len(normalized.get("characters", [])),
        relationships_count=len(normalized.get("relationships", [])),
        glossary_count=len(normalized.get("glossary", [])),
        style_rules_count=len(normalized.get("style_rules", [])),
        warnings=warnings,
    )


@router.post("/script/{project_id}")
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

    try:
        raw_lines = ScriptParser().parse(content, filename)
    except Exception as e:
        raise HTTPException(422, f"Failed to parse script file: {e}")

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

    return ScriptUploadResponse(
        project_id=project_id,
        source_file_id=source_file.id,
        file_type=file_type,
        total_lines=len(normalized["lines"]),
        detected_characters=normalized.get("detected_characters", []),
        detected_scene_hints=normalized.get("detected_scene_hints", []),
        warnings=normalized.get("warnings", []),
    )
