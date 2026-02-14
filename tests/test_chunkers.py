import pytest
from maomao.chunkers.base import Chunk, ChunkerRegistry, ChunkLocation
from maomao.chunkers.markdown import MarkdownChunker
from maomao.chunkers.text import TextChunker


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


class TestChunk:
    def test_chunk_defaults(self):
        chunk = Chunk(content="test content")
        assert chunk.content == "test content"
        assert chunk.metadata == {}
        assert chunk.content_hash == ""
        assert chunk.location is None

    def test_chunk_with_metadata(self):
        chunk = Chunk(
            content="test content",
            metadata={"title": "Test", "source": "test.md"},
            content_hash="abc123",
        )
        assert chunk.metadata["title"] == "Test"
        assert chunk.content_hash == "abc123"

    def test_chunk_with_location(self):
        location = ChunkLocation(start_line=1, end_line=5, char_start=0, char_end=50)
        chunk = Chunk(
            content="test content",
            location=location,
        )
        assert chunk.location is not None
        assert chunk.location.start_line == 1
        assert chunk.location.end_line == 5


class TestMarkdownChunker:
    def test_chunker_type(self):
        assert MarkdownChunker.chunker_type() == "markdown"

    def test_from_config(self):
        chunker = MarkdownChunker.from_config({
            "max_chunk_size": 500,
            "min_chunk_size": 30,
        })
        assert chunker.max_chunk_size == 500
        assert chunker.min_chunk_size == 30

    def test_chunk_simple_markdown(self):
        chunker = MarkdownChunker(max_chunk_size=1000, min_chunk_size=10)
        content = """# Title 1

This is content under title 1.

## Subtitle 1.1

This is content under subtitle 1.1.

# Title 2

This is content under title 2.
"""
        chunks = chunker.chunk(content, {"source": "test.md"})
        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk.content) >= 10
            assert "source" in chunk.metadata

    def test_chunk_preserves_metadata(self):
        chunker = MarkdownChunker()
        content = "# Test\n\nContent here."
        chunks = chunker.chunk(content, {"source": "test.md", "custom": "value"})
        for chunk in chunks:
            assert chunk.metadata.get("source") == "test.md"
            assert chunk.metadata.get("custom") == "value"

    def test_chunk_location_tracking(self):
        chunker = MarkdownChunker(max_chunk_size=1000, min_chunk_size=10)
        content = """# Title 1

This is content under title 1.

## Subtitle 1.1

This is content under subtitle 1.1.
"""
        chunks = chunker.chunk(content)
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.location is not None
            assert chunk.location.start_line >= 1
            assert chunk.location.end_line >= chunk.location.start_line
            assert chunk.location.char_start >= 0
            assert chunk.location.char_end > chunk.location.char_start


class TestTextChunker:
    def test_chunker_type(self):
        assert TextChunker.chunker_type() == "text"

    def test_from_config(self):
        chunker = TextChunker.from_config({
            "chunk_size": 256,
            "chunk_overlap": 30,
        })
        assert chunker.chunk_size == 256
        assert chunker.chunk_overlap == 30

    def test_chunk_text(self):
        chunker = TextChunker(chunk_size=100, chunk_overlap=20, min_chunk_size=10)
        content = "This is a test. " * 20
        chunks = chunker.chunk(content, {"source": "test.txt"})
        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk.content) >= 10

    def test_chunk_short_text(self):
        chunker = TextChunker(chunk_size=100, min_chunk_size=10)
        content = "Short text."
        chunks = chunker.chunk(content, {})
        assert len(chunks) == 1
        assert chunks[0].content == "Short text."

    def test_chunk_location_tracking(self):
        chunker = TextChunker(chunk_size=100, chunk_overlap=20, min_chunk_size=10)
        content = "First paragraph here.\n\nSecond paragraph here.\n\nThird paragraph here."
        chunks = chunker.chunk(content)
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.location is not None
            assert chunk.location.start_line >= 1
            assert chunk.location.end_line >= chunk.location.start_line
            assert chunk.location.char_start >= 0
            assert chunk.location.char_end > chunk.location.char_start


class TestChunkerRegistry:
    def test_list_chunkers(self):
        chunkers = ChunkerRegistry.list_chunkers()
        assert "markdown" in chunkers
        assert "text" in chunkers

    def test_get_chunker(self):
        assert ChunkerRegistry.get("markdown") == MarkdownChunker
        assert ChunkerRegistry.get("text") == TextChunker

    def test_create_chunker(self):
        chunker = ChunkerRegistry.create("markdown", {"max_chunk_size": 500})
        assert isinstance(chunker, MarkdownChunker)
        assert chunker.max_chunk_size == 500

    def test_get_nonexistent_chunker(self):
        assert ChunkerRegistry.get("nonexistent") is None

    def test_create_nonexistent_chunker(self):
        assert ChunkerRegistry.create("nonexistent", {}) is None
