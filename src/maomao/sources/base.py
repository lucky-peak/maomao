from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass
class SourceItem:
    id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    source_type: str = ""
    source_path: str = ""
    source_id: str = ""
    knowledge_scope: str = "global"
    project_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    content_hash: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    chunker_type: str = "text"


@dataclass
class SourceChange:
    added: list[SourceItem] = field(default_factory=list)
    updated: list[SourceItem] = field(default_factory=list)
    deleted_ids: list[str] = field(default_factory=list)


class KnowledgeSource(ABC):
    def __init__(
        self,
        knowledge_scope: str = "global",
        project_id: str = "",
    ):
        self.knowledge_scope = knowledge_scope
        self.project_id = project_id

    @classmethod
    @abstractmethod
    def source_type(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def from_config(cls, config: dict[str, Any]) -> "KnowledgeSource":
        pass

    @abstractmethod
    async def scan(self) -> list[SourceItem]:
        pass

    @abstractmethod
    async def get_changes(self, state: dict[str, Any]) -> SourceChange:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

    def _compute_hash(self, content: str) -> str:
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class SourceRegistry:
    _sources: dict[str, type[KnowledgeSource]] = {}

    @classmethod
    def register(cls, source_cls: type[KnowledgeSource]) -> type[KnowledgeSource]:
        cls._sources[source_cls.source_type()] = source_cls
        return source_cls

    @classmethod
    def get(cls, source_type: str) -> type[KnowledgeSource] | None:
        return cls._sources.get(source_type)

    @classmethod
    def create(
        cls,
        source_type: str,
        config: dict[str, Any],
        knowledge_scope: str = "global",
        project_id: str = "",
    ) -> KnowledgeSource | None:
        source_cls = cls.get(source_type)
        if source_cls:
            return source_cls.from_config(config, knowledge_scope, project_id)
        return None

    @classmethod
    def list_sources(cls) -> list[str]:
        return list(cls._sources.keys())
