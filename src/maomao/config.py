import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SourceConfig(BaseModel):
    type: str
    enabled: bool = True
    knowledge_scope: Literal["global", "project"] = "global"
    project_id: str = ""
    config: dict[str, Any] = Field(default_factory=dict)


class OllamaConfig(BaseModel):
    base_url: str = "http://127.0.0.1:11434"
    embedding_model: str = "bge-m3"
    embedding_dim: int = 1024
    timeout: int = 120


class QdrantConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 6333
    collection_name: str = "maomao_knowledge"
    prefer_grpc: bool = False


class ChunkConfig(BaseModel):
    chunk_size: int = 512
    chunk_overlap: int = 50
    min_chunk_size: int = 50


class IncrementalConfig(BaseModel):
    enabled: bool = True
    state_file: str = ".maomao/state.json"
    watch_debounce_seconds: float = 2.0


class _SettingsModel(BaseModel):
    sources: list[SourceConfig] = Field(default_factory=list)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    qdrant: QdrantConfig = Field(default_factory=QdrantConfig)
    chunk: ChunkConfig = Field(default_factory=ChunkConfig)
    incremental: IncrementalConfig = Field(default_factory=IncrementalConfig)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MAOMAO_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    sources: list[SourceConfig] = Field(default_factory=list)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    qdrant: QdrantConfig = Field(default_factory=QdrantConfig)
    chunk: ChunkConfig = Field(default_factory=ChunkConfig)
    incremental: IncrementalConfig = Field(default_factory=IncrementalConfig)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @property
    def state_file_path(self) -> Path:
        return Path(self.incremental.state_file).expanduser().absolute()

    def get_enabled_sources(self) -> list[SourceConfig]:
        return [s for s in self.sources if s.enabled]


def _find_config_file() -> Path | None:
    candidates = [
        Path.cwd() / "maomao.json",
        Path.cwd() / ".maomao.json",
        Path.home() / ".maomao.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def get_settings() -> Settings:
    env_settings = Settings()

    config_file = _find_config_file()
    if config_file:
        try:
            with open(config_file) as f:
                data = json.load(f)

            if "sources" in data:
                env_settings.sources = [SourceConfig(**s) for s in data["sources"]]
            if "ollama" in data:
                env_settings.ollama = OllamaConfig(**data["ollama"])
            if "qdrant" in data:
                env_settings.qdrant = QdrantConfig(**data["qdrant"])
            if "chunk" in data:
                env_settings.chunk = ChunkConfig(**data["chunk"])
            if "incremental" in data:
                env_settings.incremental = IncrementalConfig(**data["incremental"])
            if "log_level" in data:
                env_settings.log_level = data["log_level"]
        except Exception:
            pass

    return env_settings
