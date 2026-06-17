import json
from datetime import datetime
from enum import Enum
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
# Chunks
# ---------------------------------------------------------------------------

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


class ChunkListRead(BaseModel):
    id: int
    chunk_number: int
    chunk_title: Optional[str] = None
    scene_hint: Optional[str] = None
    source_file_id: int
    lines_count: int = 0
    status: str


class ChunkDetailRead(BaseModel):
    id: int
    project_id: int
    source_file_id: int
    chunk_number: int
    chunk_title: Optional[str] = None
    scene_hint: Optional[str] = None
    status: str
    previous_memory_json: Optional[Any] = None
    chunk_memory_json: Optional[Any] = None
    source_lines: list[SourceLineRead] = []
    translations: list[TranslationRead] = []


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

class ExportRequest(BaseModel):
    project_id: int
    format: str = "csv"  # "csv" | "json"


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

class EvaluationMode(str, Enum):
    plain = "plain"
    context = "context"
    context_memory = "context_memory"


class EvaluationRunRead(BaseModel):
    id: int
    chunk_id: int
    mode: str
    provider: str
    model: str
    prompt_version: str
    created_at: datetime
    status: str
    generated_memory: Optional[Any] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class EvaluationTranslationRead(BaseModel):
    id: int
    evaluation_run_id: int
    source_line_id: int
    line_id: Optional[str] = None
    character: Optional[str] = None
    source_text_ja: str
    literal_meaning: Optional[str] = None
    localized_text_en: Optional[str] = None
    localization_note: Optional[str] = None

    class Config:
        from_attributes = True


class EvaluationRunDetailRead(EvaluationRunRead):
    translations: list[EvaluationTranslationRead] = []


class EvaluationTranslateResponse(BaseModel):
    run_id: int
    chunk_id: int
    mode: str
    status: str
    translations_count: int
    generated_memory: Optional[Any] = None


# ---------------------------------------------------------------------------
# Benchmark (Phase 2A — scene-aware benchmark foundation)
# ---------------------------------------------------------------------------


class BenchmarkDatasetRead(BaseModel):
    id: int
    name: str
    version: str
    source_or_author: str
    license_or_usage_status: str
    reference_translation_method: str
    review_status: str
    description: Optional[str] = None
    created_at: datetime
    scenes: list["BenchmarkSceneRead"] = []

    class Config:
        from_attributes = True


class BenchmarkSceneRead(BaseModel):
    id: int
    dataset_id: int
    scene_number: int
    title: Optional[str] = None
    genre: str
    content_type: str
    setting_or_location: Optional[str] = None
    tone: Optional[str] = None
    context_json: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    items: list["BenchmarkItemRead"] = []

    class Config:
        from_attributes = True


class BenchmarkItemRead(BaseModel):
    id: int
    scene_id: int
    sequence_number: int
    source_text_ja: str
    reference_en: str
    speaker: Optional[str] = None
    character_voice_context: Optional[str] = None
    relationship_context: Optional[str] = None
    glossary_expectations: Optional[str] = None
    placeholder_expectations: Optional[str] = None
    requires_previous_memory: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class BenchmarkDatasetListItem(BaseModel):
    id: int
    name: str
    version: str
    source_or_author: str
    review_status: str
    created_at: datetime
    scene_count: int = 0
    item_count: int = 0

    class Config:
        from_attributes = True


class BenchmarkLoadResponse(BaseModel):
    dataset_id: int
    name: str
    version: str
    scenes_loaded: int
    items_loaded: int


class BenchmarkRunCreate(BaseModel):
    dataset_id: int
    mode: str


class BenchmarkAutomaticScoreRead(BaseModel):
    id: int
    benchmark_output_id: int
    chrf_score: Optional[float] = None
    bleu_score: Optional[float] = None
    glossary_compliant: Optional[bool] = None
    placeholders_preserved: Optional[bool] = None
    missing_output: bool = False
    untranslated_japanese: Optional[bool] = None
    line_id_mismatch: bool = False
    speaker_mismatch: Optional[bool] = None
    details_json: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BenchmarkOutputRead(BaseModel):
    id: int
    run_id: int
    benchmark_item_id: int
    scene_id: int
    sequence_number: int
    output_localized_text_en: Optional[str] = None
    output_literal_meaning: Optional[str] = None
    output_localization_note: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    score: Optional[BenchmarkAutomaticScoreRead] = None

    class Config:
        from_attributes = True


class BenchmarkSceneMemoryRead(BaseModel):
    id: int
    run_id: int
    scene_id: int
    memory_json: str
    created_at: datetime

    class Config:
        from_attributes = True


class BenchmarkRunRead(BaseModel):
    id: int
    dataset_id: int
    mode: str
    llm_provider: str
    llm_model: str
    prompt_version: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    memory_gap: bool = False
    total_scenes: int
    completed_scenes: int
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class BenchmarkRunStartResponse(BaseModel):
    run_id: int
    dataset_id: int
    mode: str
    status: str
    total_scenes: int
    completed_scenes: int
    memory_gap: bool = False


class BenchmarkOutputWithItemRead(BaseModel):
    output: BenchmarkOutputRead
    item: Optional[BenchmarkItemRead] = None
    scene: BenchmarkSceneRead


class BenchmarkRunSceneOutput(BaseModel):
    scene: BenchmarkSceneRead
    outputs: list[BenchmarkOutputWithItemRead] = []


class BenchmarkRunDetailRead(BenchmarkRunRead):
    scenes: list[BenchmarkRunSceneOutput] = []


class BenchmarkMetricsPerCategory(BaseModel):
    count: int = 0
    mean_chrf: Optional[float] = None
    std_chrf: Optional[float] = None


class BenchmarkMetricsSummary(BaseModel):
    dataset_name: str
    dataset_version: str
    mode: str
    model: str
    provider: str
    prompt_version: str
    status: str
    total_items: int
    completed_items: int
    failed_items: int
    chrf: Optional[dict[str, float]] = None
    bleu: Optional[dict[str, float]] = None
    glossary_compliance_rate: Optional[float] = None
    placeholder_preservation_rate: Optional[float] = None
    missing_output_count: int = 0
    untranslated_japanese_count: int = 0
    line_id_mismatch_count: int = 0
    speaker_mismatch_count: int = 0
    memory_gap: bool = False
    per_genre: dict[str, BenchmarkMetricsPerCategory] = {}
    per_content_type: dict[str, BenchmarkMetricsPerCategory] = {}
    per_scene: dict[str, BenchmarkMetricsPerCategory] = {}
    requires_previous_memory: Optional[BenchmarkMetricsPerCategory] = None
    no_previous_memory: Optional[BenchmarkMetricsPerCategory] = None
