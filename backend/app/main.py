import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME", "JP Game Localizer MVP"),
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# CORS (permissive for local MVP)
# ---------------------------------------------------------------------------
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Startup: create tables
# ---------------------------------------------------------------------------
from app.database import Base, engine
from app.models import *  # noqa: F401, F403 – ensure models are registered


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
from app.routes.upload import router as upload_router
from app.routes.chunks import router as chunks_router
from app.routes.translate import router as translate_router
from app.routes.export import router as export_router

app.include_router(upload_router)
app.include_router(chunks_router)
app.include_router(translate_router)
app.include_router(export_router)


# ---------------------------------------------------------------------------
# Project CRUD (minimal)
# ---------------------------------------------------------------------------
from app.database import get_db
from app.schemas import ProjectContextRead, ProjectCreate, ProjectRead
from app.models import ContextData, Project as ProjectModel
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session


@app.post("/projects", response_model=ProjectRead)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    project = ProjectModel(**body.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@app.get("/projects", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    return db.query(ProjectModel).all()


@app.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@app.get("/projects/{project_id}/context", response_model=ProjectContextRead)
def get_project_context(project_id: int, db: Session = Depends(get_db)):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    ctx = (
        db.query(ContextData)
        .filter(ContextData.project_id == project_id)
        .order_by(ContextData.id.desc())
        .first()
    )

    normalized: dict = {}
    warnings: list[str] = []
    if ctx and ctx.context_json:
        try:
            normalized = json.loads(ctx.context_json)
        except json.JSONDecodeError:
            warnings.append("Stored context JSON is malformed")
        warnings.extend(normalized.get("warnings", []))

    return ProjectContextRead(
        project_id=project.id,
        title=project.title or "",
        genre=project.genre or "",
        target_tone=project.target_tone or "",
        context_id=ctx.id if ctx else 0,
        original_filename=ctx.original_filename if ctx else "",
        file_type=ctx.file_type if ctx else "",
        project_data=normalized.get("project", {}),
        characters=normalized.get("characters", []),
        relationships=normalized.get("relationships", []),
        glossary=normalized.get("glossary", []),
        style_rules=normalized.get("style_rules", []),
        first_environment=normalized.get("first_environment", {}),
        raw_context_text=ctx.raw_context_text if ctx else "",
        warnings=warnings,
    )
