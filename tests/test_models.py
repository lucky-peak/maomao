import pytest
from maomao.models import (
    KnowledgeScope,
    KnowledgeChunk,
    SourceType,
    ChunkLocation,
    SearchResult,
)


class TestChunkLocation:
    def test_chunk_location_defaults(self):
        location = ChunkLocation()
        assert location.start_line == 0
        assert location.end_line == 0
        assert location.char_start == 0
        assert location.char_end == 0

    def test_chunk_location_with_values(self):
        location = ChunkLocation(
            start_line=10,
            end_line=25,
            char_start=100,
            char_end=250,
        )
        assert location.start_line == 10
        assert location.end_line == 25
        assert location.char_start == 100
        assert location.char_end == 250


class TestKnowledgeScope:
    def test_knowledge_scope_values(self):
        assert KnowledgeScope.GLOBAL.value == "global"
        assert KnowledgeScope.PROJECT.value == "project"

    def test_knowledge_scope_from_string(self):
        assert KnowledgeScope("global") == KnowledgeScope.GLOBAL
        assert KnowledgeScope("project") == KnowledgeScope.PROJECT


class TestKnowledgeChunk:
    def test_knowledge_chunk_defaults(self):
        chunk = KnowledgeChunk(
            content="test content",
            source_type="test",
            source_path="/test/path",
            source_id="test-id",
        )
        assert chunk.knowledge_scope == "global"
        assert chunk.project_id == ""
        assert chunk.content == "test content"
        assert chunk.embedding is None
        assert chunk.location is None

    def test_knowledge_chunk_with_scope(self):
        chunk = KnowledgeChunk(
            content="test content",
            source_type="test",
            source_path="/test/path",
            source_id="test-id",
            knowledge_scope="project",
            project_id="my-project",
        )
        assert chunk.knowledge_scope == "project"
        assert chunk.project_id == "my-project"

    def test_knowledge_chunk_with_embedding(self):
        chunk = KnowledgeChunk(
            content="test content",
            source_type="test",
            source_path="/test/path",
            source_id="test-id",
            embedding=[0.1, 0.2, 0.3],
        )
        assert chunk.embedding == [0.1, 0.2, 0.3]

    def test_knowledge_chunk_with_location(self):
        location = ChunkLocation(start_line=5, end_line=10, char_start=50, char_end=100)
        chunk = KnowledgeChunk(
            content="test content",
            source_type="test",
            source_path="/test/path",
            source_id="test-id",
            location=location,
        )
        assert chunk.location is not None
        assert chunk.location.start_line == 5
        assert chunk.location.end_line == 10


class TestSearchResult:
    def test_search_result_defaults(self):
        chunk = KnowledgeChunk(
            content="test content",
            source_type="test",
            source_path="/test/path",
            source_id="test-id",
        )
        result = SearchResult(chunk=chunk, score=0.95)
        assert result.chunk == chunk
        assert result.score == 0.95
        assert result.context_before == ""
        assert result.context_after == ""

    def test_search_result_with_context(self):
        chunk = KnowledgeChunk(
            content="test content",
            source_type="test",
            source_path="/test/path",
            source_id="test-id",
        )
        result = SearchResult(
            chunk=chunk,
            score=0.95,
            context_before="previous content",
            context_after="next content",
        )
        assert result.context_before == "previous content"
        assert result.context_after == "next content"


class TestSourceType:
    def test_source_type_values(self):
        assert SourceType.SIYUAN.value == "siyuan"
        assert SourceType.LOCAL_DOC.value == "local_doc"
