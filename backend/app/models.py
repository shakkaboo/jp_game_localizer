from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    target_tone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    context_data = relationship("ContextData", back_populates="project", cascade="all, delete-orphan")
    source_files = relationship("SourceFile", back_populates="project", cascade="all, delete-orphan")
    source_lines = relationship("SourceLine", back_populates="project", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="project", cascade="all, delete-orphan")
    translations = relationship("Translation", back_populates="project", cascade="all, delete-orphan")


class ContextData(Base):
    __tablename__ = "context_data"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    context_json = Column(Text, nullable=True)
    raw_context_text = Column(Text, nullable=True)

    project = relationship("Project", back_populates="context_data")


class SourceFile(Base):
    __tablename__ = "source_files"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    total_lines = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="source_files")
    source_lines = relationship("SourceLine", back_populates="source_file", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="source_file", cascade="all, delete-orphan")


class SourceLine(Base):
    __tablename__ = "source_lines"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    source_file_id = Column(Integer, ForeignKey("source_files.id"), nullable=False)
    line_id = Column(String, nullable=True)
    character = Column(String, nullable=True)
    source_text_ja = Column(String, nullable=False)
    scene_hint = Column(String, nullable=True)
    chunk_id = Column(Integer, nullable=True)

    project = relationship("Project", back_populates="source_lines")
    source_file = relationship("SourceFile", back_populates="source_lines")
    translations = relationship("Translation", back_populates="source_line", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    source_file_id = Column(Integer, ForeignKey("source_files.id"), nullable=False)
    chunk_number = Column(Integer, nullable=False)
    chunk_title = Column(String, nullable=True)
    scene_hint = Column(String, nullable=True)
    status = Column(String, default="pending")
    previous_memory_json = Column(Text, nullable=True)
    chunk_memory_json = Column(Text, nullable=True)

    project = relationship("Project", back_populates="chunks")
    source_file = relationship("SourceFile", back_populates="chunks")
    translations = relationship("Translation", back_populates="chunk", cascade="all, delete-orphan")


class Translation(Base):
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    chunk_id = Column(Integer, ForeignKey("chunks.id"), nullable=True)
    source_line_id = Column(Integer, ForeignKey("source_lines.id"), nullable=False)
    literal_meaning = Column(Text, nullable=True)
    localized_text_en = Column(Text, nullable=True)
    final_text_en = Column(Text, nullable=True)
    localization_note = Column(Text, nullable=True)
    status = Column(String, default="pending")

    project = relationship("Project", back_populates="translations")
    chunk = relationship("Chunk", back_populates="translations")
    source_line = relationship("SourceLine", back_populates="translations")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(Integer, ForeignKey("chunks.id"), nullable=False)
    mode = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    prompt_version = Column(String, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    status = Column(String, default="pending", nullable=False)
    request_config = Column(Text, nullable=True)
    generated_memory = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    chunk = relationship("Chunk")
    translations = relationship(
        "EvaluationTranslation", back_populates="evaluation_run", cascade="all, delete-orphan"
    )


class EvaluationTranslation(Base):
    __tablename__ = "evaluation_translations"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_run_id = Column(
        Integer, ForeignKey("evaluation_runs.id"), nullable=False
    )
    source_line_id = Column(Integer, ForeignKey("source_lines.id"), nullable=False)
    line_id = Column(String, nullable=True)
    character = Column(String, nullable=True)
    source_text_ja = Column(String, nullable=False)
    literal_meaning = Column(Text, nullable=True)
    localized_text_en = Column(Text, nullable=True)
    localization_note = Column(Text, nullable=True)

    evaluation_run = relationship("EvaluationRun", back_populates="translations")
    source_line = relationship("SourceLine")


# ---------------------------------------------------------------------------
# Benchmark models (Phase 2A — fully isolated from production tables)
# ---------------------------------------------------------------------------


class BenchmarkDataset(Base):
    __tablename__ = "benchmark_datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    source_or_author = Column(String, nullable=False)
    license_or_usage_status = Column(String, nullable=False)
    reference_translation_method = Column(String, nullable=False)
    review_status = Column(String, nullable=False, default="draft")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_benchmark_dataset_name_version"),
    )

    scenes = relationship("BenchmarkScene", back_populates="dataset", cascade="all, delete-orphan")
    runs = relationship("BenchmarkRun", back_populates="dataset", cascade="all, delete-orphan")


class BenchmarkScene(Base):
    __tablename__ = "benchmark_scenes"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("benchmark_datasets.id"), nullable=False)
    scene_number = Column(Integer, nullable=False)
    title = Column(String, nullable=True)
    genre = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    setting_or_location = Column(String, nullable=True)
    tone = Column(String, nullable=True)
    context_json = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("dataset_id", "scene_number", name="uq_benchmark_scene_number"),
    )

    dataset = relationship("BenchmarkDataset", back_populates="scenes")
    items = relationship("BenchmarkItem", back_populates="scene", cascade="all, delete-orphan")
    memories = relationship("BenchmarkSceneMemory", back_populates="scene", cascade="all, delete-orphan")


class BenchmarkItem(Base):
    __tablename__ = "benchmark_items"

    id = Column(Integer, primary_key=True, index=True)
    scene_id = Column(Integer, ForeignKey("benchmark_scenes.id"), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    source_text_ja = Column(String, nullable=False)
    reference_en = Column(String, nullable=False)
    speaker = Column(String, nullable=True)
    character_voice_context = Column(Text, nullable=True)
    relationship_context = Column(Text, nullable=True)
    glossary_expectations = Column(Text, nullable=True)
    placeholder_expectations = Column(Text, nullable=True)
    requires_previous_memory = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("scene_id", "sequence_number", name="uq_benchmark_item_sequence"),
    )

    scene = relationship("BenchmarkScene", back_populates="items")
    outputs = relationship("BenchmarkOutput", back_populates="benchmark_item")


class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("benchmark_datasets.id"), nullable=False)
    mode = Column(String, nullable=False)
    llm_provider = Column(String, nullable=False)
    llm_model = Column(String, nullable=False)
    prompt_version = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    memory_gap = Column(Boolean, nullable=False, default=False)
    total_scenes = Column(Integer, nullable=False, default=0)
    completed_scenes = Column(Integer, nullable=False, default=0)
    notes = Column(Text, nullable=True)

    dataset = relationship("BenchmarkDataset", back_populates="runs")
    outputs = relationship("BenchmarkOutput", back_populates="run", cascade="all, delete-orphan")
    memories = relationship("BenchmarkSceneMemory", back_populates="run", cascade="all, delete-orphan")
    scores = relationship("BenchmarkAutomaticScore", back_populates="run", cascade="all, delete-orphan")


class BenchmarkOutput(Base):
    __tablename__ = "benchmark_outputs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("benchmark_runs.id"), nullable=False)
    benchmark_item_id = Column(Integer, ForeignKey("benchmark_items.id"), nullable=False)
    scene_id = Column(Integer, ForeignKey("benchmark_scenes.id"), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    output_localized_text_en = Column(Text, nullable=True)
    output_literal_meaning = Column(Text, nullable=True)
    output_localization_note = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending")
    error_message = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("run_id", "benchmark_item_id", name="uq_benchmark_output_item"),
    )

    run = relationship("BenchmarkRun", back_populates="outputs")
    benchmark_item = relationship("BenchmarkItem", back_populates="outputs")
    score = relationship("BenchmarkAutomaticScore", back_populates="output", cascade="all, delete-orphan", uselist=False)


class BenchmarkSceneMemory(Base):
    __tablename__ = "benchmark_scene_memories"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("benchmark_runs.id"), nullable=False)
    scene_id = Column(Integer, ForeignKey("benchmark_scenes.id"), nullable=False)
    memory_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("run_id", "scene_id", name="uq_benchmark_scene_memory"),
    )

    run = relationship("BenchmarkRun", back_populates="memories")
    scene = relationship("BenchmarkScene", back_populates="memories")


class BenchmarkAutomaticScore(Base):
    __tablename__ = "benchmark_automatic_scores"

    id = Column(Integer, primary_key=True, index=True)
    benchmark_output_id = Column(Integer, ForeignKey("benchmark_outputs.id"), nullable=False)
    chrf_score = Column(Float, nullable=True)
    bleu_score = Column(Float, nullable=True)
    glossary_compliant = Column(Boolean, nullable=True)
    placeholders_preserved = Column(Boolean, nullable=True)
    missing_output = Column(Boolean, nullable=False, default=False)
    untranslated_japanese = Column(Boolean, nullable=True)
    line_id_mismatch = Column(Boolean, nullable=False, default=False)
    speaker_mismatch = Column(Boolean, nullable=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("benchmark_output_id", name="uq_benchmark_auto_score_output"),
    )

    output = relationship("BenchmarkOutput", back_populates="score")
    run_id = Column(Integer, ForeignKey("benchmark_runs.id"), nullable=False)
    run = relationship("BenchmarkRun", back_populates="scores")


# ---------------------------------------------------------------------------
# Benchmark human review models (Phase 2B — fully isolated from production tables)
# ---------------------------------------------------------------------------


class BenchmarkItemManualEvaluation(Base):
    __tablename__ = "benchmark_item_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    benchmark_output_id = Column(Integer, ForeignKey("benchmark_outputs.id"), nullable=False)
    reviewer_label = Column(String(100), nullable=False)

    meaning_preservation = Column(Integer, nullable=False)
    omission_addition_control = Column(Integer, nullable=False)
    natural_english = Column(Integer, nullable=False)
    character_voice = Column(Integer, nullable=False)
    glossary_consistency = Column(Integer, nullable=False)
    genre_tone_fit = Column(Integer, nullable=False)
    scene_consistency = Column(Integer, nullable=False)
    grammar_punctuation = Column(Integer, nullable=False)

    total_score = Column(Integer, nullable=False)
    reviewer_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("benchmark_output_id", "reviewer_label", name="uq_benchmark_item_eval_reviewer"),
    )

    output = relationship("BenchmarkOutput")


class BenchmarkSceneManualEvaluation(Base):
    __tablename__ = "benchmark_scene_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("benchmark_runs.id"), nullable=False)
    scene_id = Column(Integer, ForeignKey("benchmark_scenes.id"), nullable=False)
    reviewer_label = Column(String(100), nullable=False)

    voice_consistency = Column(Integer, nullable=False)
    terminology_consistency = Column(Integer, nullable=False)
    emotional_progression = Column(Integer, nullable=False)
    relationship_continuity = Column(Integer, nullable=False)
    narrative_coherence = Column(Integer, nullable=False)
    genre_tone_consistency = Column(Integer, nullable=False)

    total_score = Column(Integer, nullable=False)
    reviewer_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("run_id", "scene_id", "reviewer_label", name="uq_benchmark_scene_eval_reviewer"),
    )


class BenchmarkHardFailure(Base):
    __tablename__ = "benchmark_hard_failures"

    id = Column(Integer, primary_key=True, index=True)
    benchmark_output_id = Column(Integer, ForeignKey("benchmark_outputs.id"), nullable=False)
    reviewer_label = Column(String(100), nullable=False)

    invented_plot_information = Column(Boolean, default=False, nullable=False)
    missing_critical_meaning = Column(Boolean, default=False, nullable=False)
    wrong_speaker = Column(Boolean, default=False, nullable=False)
    broken_placeholder = Column(Boolean, default=False, nullable=False)
    major_glossary_violation = Column(Boolean, default=False, nullable=False)
    contradiction_with_previous_scene = Column(Boolean, default=False, nullable=False)
    unjustified_untranslated_japanese = Column(Boolean, default=False, nullable=False)

    explanation = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("benchmark_output_id", "reviewer_label", name="uq_benchmark_hard_failure_reviewer"),
    )

    output = relationship("BenchmarkOutput")
