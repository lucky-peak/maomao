import re
from typing import Any

from maomao.chunkers.base import Chunk, Chunker, ChunkerRegistry


@ChunkerRegistry.register
class TextChunker(Chunker):
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        min_chunk_size: int = 50,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    @classmethod
    def chunker_type(cls) -> str:
        return "text"

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "TextChunker":
        return cls(
            chunk_size=config.get("chunk_size", 512),
            chunk_overlap=config.get("chunk_overlap", 50),
            min_chunk_size=config.get("min_chunk_size", 50),
        )

    def chunk(self, content: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        chunks: list[Chunk] = []
        paragraphs = self._split_paragraphs(content)

        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk and len(current_chunk) >= self.min_chunk_size:
                    chunks.append(self._create_chunk(
                        current_chunk.strip(),
                        content,
                        metadata,
                        chunk_index,
                    ))
                    chunk_index += 1

                overlap = current_chunk[-self.chunk_overlap :] if self.chunk_overlap > 0 else ""
                current_chunk = overlap + para
            else:
                current_chunk += "\n\n" + para if current_chunk else para

        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append(self._create_chunk(
                current_chunk.strip(),
                content,
                metadata,
                chunk_index,
            ))

        return chunks

    def _split_paragraphs(self, content: str) -> list[str]:
        paragraphs = re.split(r"\n\s*\n", content)
        return [p.strip() for p in paragraphs if p.strip()]

    def _create_chunk(
        self,
        chunk_content: str,
        full_content: str,
        metadata: dict[str, Any] | None,
        index: int,
    ) -> Chunk:
        location = self._compute_location(chunk_content, full_content)
        return Chunk(
            content=chunk_content,
            content_hash=self._compute_hash(chunk_content),
            location=location,
            metadata={
                **(metadata or {}),
                "chunk_index": index,
                "chunk_size": len(chunk_content),
            },
        )
