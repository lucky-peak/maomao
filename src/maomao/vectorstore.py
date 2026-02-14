import os

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from rich.console import Console

from maomao.config import QdrantConfig
from maomao.models import ChunkLocation, KnowledgeChunk, SearchResult

console = Console()


def _disable_proxy_env():
    proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY',
                  'all_proxy', 'ALL_PROXY', 'no_proxy', 'NO_PROXY']
    return {k: os.environ.pop(k, None) for k in proxy_vars}


def _restore_proxy_env(saved):
    for k, v in saved.items():
        if v is not None:
            os.environ[k] = v


class VectorStore:
    def __init__(self, config: QdrantConfig, embedding_dim: int = 1024):
        self.config = config
        self.embedding_dim = embedding_dim

        saved = _disable_proxy_env()
        try:
            self.client = QdrantClient(
                host=config.host,
                port=config.port,
                prefer_grpc=config.prefer_grpc,
            )
        finally:
            _restore_proxy_env(saved)

    def ensure_collection(self) -> None:
        saved = _disable_proxy_env()
        try:
            try:
                self.client.get_collection(self.config.collection_name)
            except UnexpectedResponse:
                self.client.create_collection(
                    collection_name=self.config.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.embedding_dim,
                        distance=models.Distance.COSINE,
                    ),
                )
                console.print(f"[green]Created collection: {self.config.collection_name}[/green]")
        finally:
            _restore_proxy_env(saved)

    def upsert_chunks(self, chunks: list[KnowledgeChunk]) -> None:
        if not chunks:
            return

        points = []
        for chunk in chunks:
            if chunk.embedding is None:
                continue

            payload = {
                "content": chunk.content,
                "source_type": chunk.source_type,
                "source_path": chunk.source_path,
                "source_id": chunk.source_id,
                "knowledge_scope": chunk.knowledge_scope,
                "project_id": chunk.project_id,
                "metadata": chunk.metadata,
                "content_hash": chunk.content_hash,
            }

            if chunk.location:
                payload["location"] = {
                    "start_line": chunk.location.start_line,
                    "end_line": chunk.location.end_line,
                    "char_start": chunk.location.char_start,
                    "char_end": chunk.location.char_end,
                }

            point = models.PointStruct(
                id=chunk.id,
                vector=chunk.embedding,
                payload=payload,
            )
            points.append(point)

        if points:
            saved = _disable_proxy_env()
            try:
                self.client.upsert(
                    collection_name=self.config.collection_name,
                    points=points,
                )
            finally:
                _restore_proxy_env(saved)

    def delete_chunks(self, chunk_ids: list[str]) -> None:
        if not chunk_ids:
            return

        saved = _disable_proxy_env()
        try:
            self.client.delete(
                collection_name=self.config.collection_name,
                points_selector=models.PointIdsList(
                    points=chunk_ids,
                ),
            )
        finally:
            _restore_proxy_env(saved)

    def delete_by_source_ids(self, source_ids: list[str]) -> int:
        if not source_ids:
            return 0

        total_deleted = 0
        saved = _disable_proxy_env()
        try:
            for source_id in source_ids:
                results = self.client.scroll(
                    collection_name=self.config.collection_name,
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="source_id",
                                match=models.MatchValue(value=source_id),
                            )
                        ]
                    ),
                    limit=1000,
                    with_payload=False,
                )

                chunk_ids = [str(point.id) for point in results[0]]
                if chunk_ids:
                    self.delete_chunks(chunk_ids)
                    total_deleted += len(chunk_ids)
        finally:
            _restore_proxy_env(saved)

        return total_deleted

    def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        source_type: str | None = None,
        source_path_prefix: str | None = None,
        knowledge_scope: str | None = None,
        project_id: str | None = None,
        context_lines: int = 5,
    ) -> list[SearchResult]:
        must_filters: list[models.Condition] = []

        if source_type:
            must_filters.append(
                models.FieldCondition(
                    key="source_type",
                    match=models.MatchValue(value=source_type),
                )
            )

        if source_path_prefix:
            must_filters.append(
                models.FieldCondition(
                    key="source_path",
                    match=models.MatchText(text=source_path_prefix),
                )
            )

        if knowledge_scope:
            must_filters.append(
                models.FieldCondition(
                    key="knowledge_scope",
                    match=models.MatchValue(value=knowledge_scope),
                )
            )

        if project_id:
            must_filters.append(
                models.FieldCondition(
                    key="project_id",
                    match=models.MatchValue(value=project_id),
                )
            )

        query_filter = models.Filter(must=must_filters) if must_filters else None

        saved = _disable_proxy_env()
        try:
            results = self.client.query_points(
                collection_name=self.config.collection_name,
                query=query_vector,
                limit=limit,
                query_filter=query_filter,
            )
        finally:
            _restore_proxy_env(saved)

        search_results: list[SearchResult] = []
        for result in results.points:
            payload = result.payload or {}

            location_data = payload.get("location")
            location = None
            if location_data and isinstance(location_data, dict):
                location = ChunkLocation(
                    start_line=location_data.get("start_line", 0),
                    end_line=location_data.get("end_line", 0),
                    char_start=location_data.get("char_start", 0),
                    char_end=location_data.get("char_end", 0),
                )

            chunk = KnowledgeChunk(
                id=str(result.id),
                content=payload.get("content", ""),
                source_type=payload.get("source_type", ""),
                source_path=payload.get("source_path", ""),
                source_id=payload.get("source_id", ""),
                knowledge_scope=payload.get("knowledge_scope", "global"),
                project_id=payload.get("project_id", ""),
                metadata=payload.get("metadata", {}),
                content_hash=payload.get("content_hash", ""),
                location=location,
            )
            search_results.append(
                SearchResult(
                    chunk=chunk,
                    score=result.score,
                )
            )

        return search_results

    def count(self) -> int:
        saved = _disable_proxy_env()
        try:
            result = self.client.count(self.config.collection_name)
            return result.count
        finally:
            _restore_proxy_env(saved)
