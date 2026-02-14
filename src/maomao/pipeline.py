import time
from typing import Any

from rich.console import Console

from maomao.chunkers import Chunk, ChunkerRegistry, ChunkLocation
from maomao.config import Settings, get_settings
from maomao.embeddings import EmbeddingService, get_embedding_service
from maomao.models import ChunkLocation as ModelChunkLocation
from maomao.models import IngestResult, KnowledgeChunk
from maomao.sources import KnowledgeSource, SourceItem, SourceRegistry
from maomao.state import StateManager
from maomao.vectorstore import VectorStore

console = Console()


class IngestionPipeline:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.embedding_service: EmbeddingService | None = None
        self.vector_store: VectorStore | None = None
        self.state_manager: StateManager | None = None
        self._sources: list[KnowledgeSource] = []
        self._chunker_cache: dict[str, Any] = {}

    async def initialize(self) -> None:
        self.embedding_service = await get_embedding_service(self.settings.ollama)
        self.vector_store = VectorStore(
            self.settings.qdrant,
            self.settings.ollama.embedding_dim,
        )
        self.vector_store.ensure_collection()
        self.state_manager = StateManager(self.settings.state_file_path)

        self._sources = []
        for source_config in self.settings.get_enabled_sources():
            source = SourceRegistry.create(
                source_config.type,
                source_config.config,
                source_config.knowledge_scope,
                source_config.project_id,
            )
            if source:
                self._sources.append(source)
            else:
                console.print(f"[yellow]Unknown source type: {source_config.type}[/yellow]")

    async def close(self) -> None:
        for source in self._sources:
            await source.close()
        if self.embedding_service:
            await self.embedding_service.close()

    def _get_chunker(self, chunker_type: str):
        if chunker_type not in self._chunker_cache:
            chunker_config = {}
            if chunker_type == "markdown":
                chunker_config = {
                    "max_chunk_size": self.settings.chunk.chunk_size * 2,
                    "min_chunk_size": self.settings.chunk.min_chunk_size,
                }
            elif chunker_type == "text":
                chunker_config = {
                    "chunk_size": self.settings.chunk.chunk_size,
                    "chunk_overlap": self.settings.chunk.chunk_overlap,
                    "min_chunk_size": self.settings.chunk.min_chunk_size,
                }
            self._chunker_cache[chunker_type] = ChunkerRegistry.create(chunker_type, chunker_config)
        return self._chunker_cache.get(chunker_type)

    async def run_full_ingest(self) -> IngestResult:
        start_time = time.time()
        result = IngestResult()

        await self.initialize()

        try:
            all_chunks: list[KnowledgeChunk] = []

            for source in self._sources:
                console.print(f"[cyan]Scanning source: {source.source_type()}...[/cyan]")
                items = await source.scan()
                console.print(f"  Found {len(items)} items")

                for item in items:
                    chunks = self._item_to_chunks(item)
                    all_chunks.extend(chunks)

                source_state = self._build_source_state(items)
                self.state_manager.update_source_state(source.source_type(), source_state)

            result.total_chunks = len(all_chunks)

            if all_chunks:
                console.print(f"[cyan]Generating embeddings for {len(all_chunks)} chunks...[/cyan]")
                await self._embed_chunks(all_chunks)

                console.print("[cyan]Storing in vector database...[/cyan]")
                self.vector_store.upsert_chunks(all_chunks)
                result.new_chunks = len(all_chunks)

            self.state_manager.mark_full_ingest()

        except Exception as e:
            result.errors.append(str(e))
            console.print(f"[red]Error during ingestion: {e}[/red]")

        result.duration_seconds = time.time() - start_time
        console.print(f"[green]Ingestion completed in {result.duration_seconds:.2f}s[/green]")

        return result

    async def run_incremental_ingest(self) -> IngestResult:
        start_time = time.time()
        result = IngestResult()

        if not self.settings.incremental.enabled:
            return await self.run_full_ingest()

        await self.initialize()

        try:
            for source in self._sources:
                console.print(f"[cyan]Checking changes in: {source.source_type()}...[/cyan]")

                previous_state = self.state_manager.get_source_state(source.source_type())
                changes = await source.get_changes(previous_state)

                added_chunks: list[KnowledgeChunk] = []
                for item in changes.added:
                    chunks = self._item_to_chunks(item)
                    added_chunks.extend(chunks)

                updated_chunks: list[KnowledgeChunk] = []
                for item in changes.updated:
                    chunks = self._item_to_chunks(item)
                    updated_chunks.extend(chunks)

                if changes.deleted_ids:
                    self.vector_store.delete_by_source_ids(changes.deleted_ids)
                    result.deleted_chunks += len(changes.deleted_ids)

                if added_chunks:
                    await self._embed_chunks(added_chunks)
                    self.vector_store.upsert_chunks(added_chunks)
                    result.new_chunks += len(added_chunks)

                if updated_chunks:
                    await self._embed_chunks(updated_chunks)
                    self.vector_store.upsert_chunks(updated_chunks)
                    result.updated_chunks += len(updated_chunks)

                result.total_chunks += len(added_chunks) + len(updated_chunks)

                items = await source.scan()
                new_state = self._build_source_state(items)
                self.state_manager.update_source_state(source.source_type(), new_state)

            self.state_manager.save_state()

        except Exception as e:
            result.errors.append(str(e))

        result.duration_seconds = time.time() - start_time
        return result

    def _item_to_chunks(self, item: SourceItem) -> list[KnowledgeChunk]:
        chunker = self._get_chunker(item.chunker_type)
        if not chunker:
            console.print(f"[yellow]Unknown chunker type: {item.chunker_type}, using text[/yellow]")
            chunker = self._get_chunker("text")

        if not chunker:
            return []

        raw_chunks: list[Chunk] = chunker.chunk(item.content, item.metadata)

        return [
            KnowledgeChunk(
                content=chunk.content,
                source_type=item.source_type,
                source_path=item.source_path,
                source_id=item.source_id,
                knowledge_scope=item.knowledge_scope,
                project_id=item.project_id,
                metadata=chunk.metadata,
                content_hash=chunk.content_hash,
                location=self._convert_location(chunk.location),
            )
            for chunk in raw_chunks
        ]

    def _convert_location(self, location: ChunkLocation | None) -> ModelChunkLocation | None:
        if location is None:
            return None
        return ModelChunkLocation(
            start_line=location.start_line,
            end_line=location.end_line,
            char_start=location.char_start,
            char_end=location.char_end,
        )

    def _build_source_state(self, items: list[SourceItem]) -> dict[str, Any]:
        return {
            "ids": [item.source_id for item in items],
            "hashes": {item.source_id: item.content_hash for item in items},
            "count": len(items),
            "files": {item.source_id: {"hash": item.content_hash} for item in items},
        }

    async def _embed_chunks(self, chunks: list[KnowledgeChunk]) -> None:
        if not self.embedding_service:
            return

        batch_size = 20
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c.content for c in batch]
            embeddings = await self.embedding_service.embed(texts)

            for j, chunk in enumerate(batch):
                if j < len(embeddings):
                    chunk.embedding = embeddings[j]

    async def search(
        self,
        query: str,
        limit: int = 10,
        source_type: str | None = None,
        source_path_prefix: str | None = None,
        knowledge_scope: str | None = None,
        project_id: str | None = None,
        context_lines: int = 5,
    ) -> list[Any]:
        if not self.embedding_service or not self.vector_store:
            await self.initialize()

        query_embedding = await self.embedding_service.embed_single(query)
        return self.vector_store.search(
            query_vector=query_embedding,
            limit=limit,
            source_type=source_type,
            source_path_prefix=source_path_prefix,
            knowledge_scope=knowledge_scope,
            project_id=project_id,
            context_lines=context_lines,
        )
