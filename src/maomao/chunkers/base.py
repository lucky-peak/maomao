from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class ChunkLocation:
    start_line: int = 0
    end_line: int = 0
    char_start: int = 0
    char_end: int = 0


@dataclass
class Chunk:
    id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    content_hash: str = ""
    location: ChunkLocation | None = None


class Chunker(ABC):
    @classmethod
    @abstractmethod
    def chunker_type(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def from_config(cls, config: dict[str, Any]) -> "Chunker":
        pass

    @abstractmethod
    def chunk(self, content: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        pass

    def _compute_hash(self, content: str) -> str:
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _compute_location(self, content: str, full_content: str) -> ChunkLocation:
        char_start = full_content.find(content)
        if char_start == -1:
            return ChunkLocation()

        char_end = char_start + len(content)
        start_line = full_content[:char_start].count('\n') + 1
        end_line = full_content[:char_end].count('\n') + 1

        return ChunkLocation(
            start_line=start_line,
            end_line=end_line,
            char_start=char_start,
            char_end=char_end,
        )


class ChunkerRegistry:
    _chunkers: dict[str, type[Chunker]] = {}

    @classmethod
    def register(cls, chunker_cls: type[Chunker]) -> type[Chunker]:
        cls._chunkers[chunker_cls.chunker_type()] = chunker_cls
        return chunker_cls

    @classmethod
    def get(cls, chunker_type: str) -> type[Chunker] | None:
        return cls._chunkers.get(chunker_type)

    @classmethod
    def create(cls, chunker_type: str, config: dict[str, Any] | None = None) -> Chunker | None:
        chunker_cls = cls.get(chunker_type)
        if chunker_cls:
            return chunker_cls.from_config(config or {})
        return None

    @classmethod
    def list_chunkers(cls) -> list[str]:
        return list(cls._chunkers.keys())
