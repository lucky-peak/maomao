import hashlib
from pathlib import Path
from typing import Any

import frontmatter
from rich.console import Console

from maomao.sources.base import KnowledgeSource, SourceChange, SourceItem, SourceRegistry

console = Console()


@SourceRegistry.register
class LocalDocSource(KnowledgeSource):
    DEFAULT_PATTERNS = ["*.md", "*.markdown", "*.txt", "*.rst", "*.adoc"]

    SKIP_DIRS = {
        "node_modules",
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "dist",
        "build",
        ".idea",
        ".vscode",
        "target",
        "vendor",
        ".maomao",
    }

    EXTENSION_CHUNKER_MAP = {
        ".md": "markdown",
        ".markdown": "markdown",
        ".txt": "text",
        ".rst": "text",
        ".adoc": "text",
    }

    def __init__(
        self,
        path: str,
        patterns: list[str] | None = None,
        recursive: bool = True,
        chunker_type: str | None = None,
        knowledge_scope: str = "global",
        project_id: str = "",
    ):
        super().__init__(knowledge_scope, project_id)
        self.path = path
        self.patterns = patterns or self.DEFAULT_PATTERNS
        self.recursive = recursive
        self.default_chunker_type = chunker_type

    @classmethod
    def source_type(cls) -> str:
        return "local_doc"

    @classmethod
    def from_config(
        cls,
        config: dict[str, Any],
        knowledge_scope: str = "global",
        project_id: str = "",
    ) -> "LocalDocSource":
        return cls(
            path=config.get("path", ""),
            patterns=config.get("patterns"),
            recursive=config.get("recursive", True),
            chunker_type=config.get("chunker_type"),
            knowledge_scope=knowledge_scope,
            project_id=project_id,
        )

    async def close(self) -> None:
        pass

    async def scan(self) -> list[SourceItem]:
        base_path = Path(self.path).expanduser().absolute()
        if not base_path.exists():
            console.print(f"[red]LocalDocSource: path does not exist: {base_path}[/red]")
            return []

        items: list[SourceItem] = []
        files = self._scan_files(base_path)

        for file_path in files:
            try:
                content, metadata = self._parse_file(file_path)
                if not content.strip():
                    continue

                relative_path = str(file_path.relative_to(base_path))
                content_hash = self._compute_file_hash(file_path)
                chunker_type = self._get_chunker_type(file_path)

                item = SourceItem(
                    source_type=self.source_type(),
                    source_path=f"{self.path}/{relative_path}",
                    source_id=str(file_path),
                    knowledge_scope=self.knowledge_scope,
                    project_id=self.project_id,
                    content=content,
                    content_hash=content_hash,
                    chunker_type=chunker_type,
                    metadata={
                        **metadata,
                        "filename": file_path.name,
                        "extension": file_path.suffix,
                        "base_path": str(base_path),
                    },
                )
                items.append(item)
            except Exception as e:
                console.print(f"[yellow]Error parsing {file_path}: {e}[/yellow]")

        return items

    async def get_changes(self, state: dict[str, Any]) -> SourceChange:
        base_path = Path(self.path).expanduser().absolute()
        if not base_path.exists():
            return SourceChange()

        current_files = self._scan_files(base_path)
        current_map = {str(f): f for f in current_files}
        current_ids = set(current_map.keys())

        previous_info = state.get("files", {})
        previous_ids = set(previous_info.keys())

        added_ids = current_ids - previous_ids
        deleted_ids = previous_ids - current_ids
        common_ids = current_ids & previous_ids

        added: list[SourceItem] = []
        for file_id in added_ids:
            file_path = current_map[file_id]
            item = await self._file_to_item(file_path, base_path)
            if item:
                added.append(item)

        deleted = list(deleted_ids)

        updated: list[SourceItem] = []
        for file_id in common_ids:
            file_path = current_map[file_id]
            current_hash = self._compute_file_hash(file_path)
            previous_hash = previous_info[file_id].get("hash", "")

            if current_hash != previous_hash:
                item = await self._file_to_item(file_path, base_path)
                if item:
                    updated.append(item)

        return SourceChange(added=added, updated=updated, deleted_ids=deleted)

    def _scan_files(self, base_path: Path) -> list[Path]:
        files: list[Path] = []
        for pattern in self.patterns:
            if self.recursive:
                for file_path in base_path.rglob(pattern):
                    if not self._should_skip(file_path):
                        files.append(file_path)
            else:
                for file_path in base_path.glob(pattern):
                    if not self._should_skip(file_path):
                        files.append(file_path)
        return sorted(set(files))

    def _should_skip(self, path: Path) -> bool:
        return any(part in self.SKIP_DIRS for part in path.parts)

    def _get_chunker_type(self, file_path: Path) -> str:
        if self.default_chunker_type:
            return self.default_chunker_type

        ext = file_path.suffix.lower()
        return self.EXTENSION_CHUNKER_MAP.get(ext, "text")

    def _parse_file(self, file_path: Path) -> tuple[str, dict[str, Any]]:
        with open(file_path, encoding="utf-8") as f:
            raw_content = f.read()

        metadata: dict[str, Any] = {}

        if file_path.suffix.lower() in (".md", ".markdown"):
            try:
                post = frontmatter.loads(raw_content)
                content = post.content
                metadata = dict(post.metadata)
            except Exception:
                content = raw_content
        else:
            content = raw_content

        return content.strip(), metadata

    def _compute_file_hash(self, file_path: Path) -> str:
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()[:16]
        except Exception:
            return ""

    async def _file_to_item(self, file_path: Path, base_path: Path) -> SourceItem | None:
        try:
            content, metadata = self._parse_file(file_path)
            if not content.strip():
                return None

            relative_path = str(file_path.relative_to(base_path))
            content_hash = self._compute_file_hash(file_path)
            chunker_type = self._get_chunker_type(file_path)

            return SourceItem(
                source_type=self.source_type(),
                source_path=f"{self.path}/{relative_path}",
                source_id=str(file_path),
                knowledge_scope=self.knowledge_scope,
                project_id=self.project_id,
                content=content,
                content_hash=content_hash,
                chunker_type=chunker_type,
                metadata={
                    **metadata,
                    "filename": file_path.name,
                    "extension": file_path.suffix,
                    "base_path": str(base_path),
                },
            )
        except Exception:
            return None
