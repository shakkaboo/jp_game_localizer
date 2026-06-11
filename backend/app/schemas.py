import json
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Internal normalization structures
# ---------------------------------------------------------------------------

class ScriptLineNormalized(BaseModel):
    line_id: str = ""
    character: str = ""
    source_text_ja: str = ""
    scene_hint: str = ""


class ScriptNormalized(BaseModel):
    lines: list[ScriptLineNormalized] = []
    warnings: list[str] = []


class ContextNormalized(BaseModel):
    project: dict[str, Any] = Field(default_factory=dict)
    first_environment: dict[str, Any] = Field(default_factory=dict)
    characters: list[dict[str, Any]] = Field(default_factory=list)
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    glossary: list[dict[str, Any]] = Field(default_factory=list)
    style_rules: list[dict[str, Any]] = Field(default_factory=list)
    raw_context: str = ""
    warnings: list[str] = []


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    title: Optional[str] = None
    genre: Optional[str] = None
    target_tone: Optional[str] = None


class ProjectRead(ProjectCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Upload responses
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    project_id: int
    file_id: int
    filename: str
    file_type: str
    message: str


class ContextUploadResponse(BaseModel):
    project_id: int
    file_type: str
    project: dict[str, Any] = Field(default_factory=dict)
    characters_count: int = 0
    relationships_count: int = 0
    glossary_count: int = 0
    style_rules_count: int = 0
    warnings: list[str] = []


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

class ContextDataRead(BaseModel):
    id: int
    project_id: int
    original_filename: str
    file_type: str
    context_json: Optional[str] = None
    raw_context_text: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectContextRead(BaseModel):
    project_id: int
    title: str
    genre: str
    target_tone: str
    context_id: int
    original_filename: str
    file_type: str
    project_data: dict[str, Any] = Field(default_factory=dict)
    characters: list[dict[str, Any]] = Field(default_factory=list)
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    glossary: list[dict[str, Any]] = Field(default_factory=list)
    style_rules: list[dict[str, Any]] = Field(default_factory=list)
    first_environment: dict[str, Any] = Field(default_factory=dict)
    raw_context_text: str = ""
    warnings: list[str] = []

    class Config:
        from_attributes = True


class ScriptUploadResponse(BaseModel):
    project_id: int
    source_file_id: int
    file_type: str
    total_lines: int
    detected_characters: list[str] = []
    detected_scene_hints: list[str] = []
    warnings: list[str] = []


# ---------------------------------------------------------------------------
# Source lines
# ---------------------------------------------------------------------------

class SourceLineRead(BaseModel):
    id: int
    project_id: int
    source_file_id: int
    line_id: Optional[str] = None
    character: Optional[str] = None
    source_text_ja: str
    scene_hint: Optional[str] = None
    chunk_id: Optional[int] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Chunks
# ---------------------------------------------------------------------------

class ChunkGenerateRequest(BaseModel):
    project_id: int
    source_file_id: int


class ChunkRead(BaseModel):
    id: int
    project_id: int
    source_file_id: int
    chunk_number: int
    chunk_title: Optional[str] = None
    scene_hint: Optional[str] = None
    status: str
    previous_memory_json: Optional[str] = None
    chunk_memory_json: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------

class TranslationUpdate(BaseModel):
    literal_meaning: Optional[str] = None
    localized_text_en: Optional[str] = None
    final_text_en: Optional[str] = None
    localization_note: Optional[str] = None
    status: Optional[str] = None


class TranslationRead(BaseModel):
    id: int
    project_id: int
    chunk_id: Optional[int] = None
    source_line_id: int
    literal_meaning: Optional[str] = None
    localized_text_en: Optional[str] = None
    final_text_en: Optional[str] = None
    localization_note: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

class ExportRequest(BaseModel):
    project_id: int
    format: str = "csv"  # "csv" | "json"
