from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class SourceType(StrEnum):
    SIYUAN = "siyuan"
    LOCAL_DOC = "local_doc"


class KnowledgeScope(StrEnum):
    GLOBAL = "global"
    PROJECT = "project"


class ChunkLocation(BaseModel):
    start_line: int = 0
    end_line: int = 0
    char_start: int = 0
    char_end: int = 0


class KnowledgeChunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    source_type: str
    source_path: str
    source_id: str
    knowledge_scope: str = "global"
    project_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    content_hash: str = ""
    embedding: list[float] | None = None
    location: ChunkLocation | None = None


class SearchResult(BaseModel):
    chunk: KnowledgeChunk
    score: float
    context_before: str = ""
    context_after: str = ""


class IngestResult(BaseModel):
    total_chunks: int = 0
    new_chunks: int = 0
    updated_chunks: int = 0
    deleted_chunks: int = 0
    errors: list[str] = Field(default_factory=list)
    duration_seconds: float = 0.0


class FileState(BaseModel):
    path: str
    content_hash: str
    last_modified: float
    chunk_ids: list[str] = Field(default_factory=list)


class IngestionState(BaseModel):
    version: int = 2
    last_full_ingest: datetime | None = None
    source_states: dict[str, dict[str, Any]] = Field(default_factory=dict)
