import re
from typing import Any

from maomao.chunkers.base import Chunk, Chunker, ChunkerRegistry


@ChunkerRegistry.register
class MarkdownChunker(Chunker):
    def __init__(
        self,
        max_chunk_size: int = 1000,
        min_chunk_size: int = 50,
        heading_levels: list[int] | None = None,
    ):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.heading_levels = heading_levels or [2, 3]

    @classmethod
    def chunker_type(cls) -> str:
        return "markdown"

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "MarkdownChunker":
        return cls(
            max_chunk_size=config.get("max_chunk_size", 1000),
            min_chunk_size=config.get("min_chunk_size", 50),
            heading_levels=config.get("heading_levels"),
        )

    def chunk(self, content: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        chunks: list[Chunk] = []
        sections = self._split_by_headings(content)

        for section in sections:
            if len(section["content"]) < self.min_chunk_size:
                continue

            if len(section["content"]) <= self.max_chunk_size:
                chunks.append(self._create_chunk(section, metadata, content))
            else:
                sub_chunks = self._split_large_section(section, metadata, content)
                chunks.extend(sub_chunks)

        return chunks

    def _split_by_headings(self, content: str) -> list[dict[str, Any]]:
        sections: list[dict[str, Any]] = []
        lines = content.split("\n")

        current_section: dict[str, Any] = {
            "title": "",
            "level": 0,
            "content": "",
            "path": [],
        }

        for line in lines:
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)

            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                if current_section["content"].strip():
                    sections.append(current_section)

                current_section = {
                    "title": title,
                    "level": level,
                    "content": line + "\n",
                    "path": current_section["path"][:level-1] + [title] if level > 0 else [title],
                }
            else:
                current_section["content"] += line + "\n"

        if current_section["content"].strip():
            sections.append(current_section)

        return sections

    def _split_large_section(
        self, section: dict[str, Any], base_metadata: dict[str, Any] | None, full_content: str
    ) -> list[Chunk]:
        content = section["content"]

        if section["level"] < max(self.heading_levels):
            sub_sections = self._split_by_sub_headings(content, section["level"] + 1)
            if len(sub_sections) > 1:
                chunks: list[Chunk] = []
                for sub in sub_sections:
                    if len(sub["content"]) >= self.min_chunk_size:
                        if len(sub["content"]) <= self.max_chunk_size:
                            chunks.append(self._create_chunk(sub, base_metadata, full_content))
                        else:
                            chunks.extend(self._split_by_paragraphs(sub, base_metadata, full_content))
                return chunks

        return self._split_by_paragraphs(section, base_metadata, full_content)

    def _split_by_sub_headings(
        self, content: str, min_level: int
    ) -> list[dict[str, Any]]:
        sections: list[dict[str, Any]] = []
        lines = content.split("\n")

        current_section: dict[str, Any] = {
            "title": "",
            "level": 0,
            "content": "",
            "path": [],
        }

        for line in lines:
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)

            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                if level >= min_level and current_section["content"].strip():
                    sections.append(current_section)
                    current_section = {
                        "title": title,
                        "level": level,
                        "content": line + "\n",
                        "path": [title],
                    }
                else:
                    current_section["content"] += line + "\n"
            else:
                current_section["content"] += line + "\n"

        if current_section["content"].strip():
            sections.append(current_section)

        return sections

    def _split_by_paragraphs(
        self, section: dict[str, Any], base_metadata: dict[str, Any] | None, full_content: str
    ) -> list[Chunk]:
        content = section["content"]
        paragraphs = re.split(r"\n\s*\n", content)

        chunks: list[Chunk] = []
        current_content = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_content) + len(para) + 2 <= self.max_chunk_size:
                current_content += "\n\n" + para if current_content else para
            else:
                if current_content and len(current_content) >= self.min_chunk_size:
                    chunks.append(self._create_chunk({
                        "title": section["title"],
                        "level": section["level"],
                        "content": current_content,
                        "path": section["path"],
                    }, base_metadata, full_content))
                current_content = para

        if current_content and len(current_content) >= self.min_chunk_size:
            chunks.append(self._create_chunk({
                "title": section["title"],
                "level": section["level"],
                "content": current_content,
                "path": section["path"],
            }, base_metadata, full_content))

        return chunks

    def _create_chunk(
        self, section: dict[str, Any], base_metadata: dict[str, Any] | None, full_content: str
    ) -> Chunk:
        content = section["content"].strip()
        location = self._compute_location(content, full_content)
        return Chunk(
            content=content,
            content_hash=self._compute_hash(content),
            location=location,
            metadata={
                **(base_metadata or {}),
                "title": section["title"],
                "heading_level": section["level"],
                "heading_path": section["path"],
            },
        )
