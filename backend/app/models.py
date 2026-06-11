from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
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
