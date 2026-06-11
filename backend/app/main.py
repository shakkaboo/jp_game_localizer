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
from app.schemas import ProjectCreate, ProjectRead
from app.models import Project as ProjectModel
from fastapi import Depends
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
        from fastapi import HTTPException
        raise HTTPException(404, "Project not found")
    return project
