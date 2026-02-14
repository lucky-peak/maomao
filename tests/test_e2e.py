import pytest
from maomao.pipeline import IngestionPipeline
from maomao.vectorstore import VectorStore
from maomao.config import Settings, SourceConfig, QdrantConfig, OllamaConfig, IncrementalConfig
import os


def make_config(test_collection, test_docs_dir):
    return Settings(
        sources=[
            SourceConfig(
                type="local_doc",
                enabled=True,
                knowledge_scope="project",
                project_id="test-project",
                config={
                    "path": str(test_docs_dir),
                    "patterns": ["*.md", "*.txt"],
                },
            ),
        ],
        qdrant=QdrantConfig(
            host=os.environ.get("MAOMAO_QDRANT_HOST", "127.0.0.1"),
            port=int(os.environ.get("MAOMAO_QDRANT_PORT", "6333")),
            collection_name=test_collection,
        ),
        ollama=OllamaConfig(
            base_url=os.environ.get("MAOMAO_OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            embedding_model=os.environ.get("MAOMAO_OLLAMA_MODEL", "bge-m3"),
        ),
        incremental=IncrementalConfig(
            enabled=True,
            state_file=str(test_docs_dir.parent / ".maomao_state.json"),
        ),
    )


@pytest.mark.asyncio
class TestFullIngest:
    @pytest.mark.e2e
    async def test_full_ingest_creates_collection(self, ensure_services, test_config):
        pipeline = IngestionPipeline(settings=test_config)
        
        try:
            await pipeline.initialize()
            
            assert pipeline.vector_store is not None
            assert pipeline.embedding_service is not None
            
            result = await pipeline.run_full_ingest()
            
            assert result.total_chunks > 0
            assert result.new_chunks > 0
            assert len(result.errors) == 0
            
        finally:
            await pipeline.close()

    @pytest.mark.e2e
    async def test_full_ingest_stores_vectors(self, ensure_services, test_config):
        pipeline = IngestionPipeline(settings=test_config)
        
        try:
            await pipeline.initialize()
            
            result = await pipeline.run_full_ingest()
            
            count = pipeline.vector_store.count()
            assert count > 0
            assert count == result.new_chunks
            
        finally:
            await pipeline.close()

    @pytest.mark.e2e
    async def test_full_ingest_with_knowledge_scope(self, ensure_services, test_config):
        pipeline = IngestionPipeline(settings=test_config)
        
        try:
            await pipeline.initialize()
            await pipeline.run_full_ingest()
            
            results = pipeline.vector_store.search(
                query_vector=[0.0] * 1024,
                limit=100,
                knowledge_scope="project",
                project_id="test-project",
            )
            
            assert len(results) > 0
            for result in results:
                assert result.chunk.knowledge_scope == "project"
                assert result.chunk.project_id == "test-project"
            
        finally:
            await pipeline.close()

    @pytest.mark.e2e
    async def test_full_ingest_stores_location_info(self, ensure_services, test_config):
        pipeline = IngestionPipeline(settings=test_config)
        
        try:
            await pipeline.initialize()
            await pipeline.run_full_ingest()
            
            results = pipeline.vector_store.search(
                query_vector=[0.0] * 1024,
                limit=100,
            )
            
            assert len(results) > 0
            
            results_with_location = [r for r in results if r.chunk.location is not None]
            assert len(results_with_location) > 0, "At least some chunks should have location info"
            
            for result in results_with_location:
                loc = result.chunk.location
                assert loc.start_line >= 1
                assert loc.end_line >= loc.start_line
                assert loc.char_end > loc.char_start
            
        finally:
            await pipeline.close()


@pytest.mark.asyncio
class TestSearch:
    @pytest.mark.e2e
    async def test_search_returns_relevant_results(self, ensure_services, test_config):
        pipeline = IngestionPipeline(settings=test_config)
        
        try:
            await pipeline.initialize()
            await pipeline.run_full_ingest()
            
            results = await pipeline.search("Python variables", limit=5)
            
            assert len(results) > 0
            
        finally:
            await pipeline.close()

    @pytest.mark.e2e
    async def test_search_with_knowledge_scope_filter(self, ensure_services, test_config):
        pipeline = IngestionPipeline(settings=test_config)
        
        try:
            await pipeline.initialize()
            await pipeline.run_full_ingest()
            
            results = await pipeline.search(
                "programming",
                limit=10,
                knowledge_scope="project",
                project_id="test-project",
            )
            
            assert len(results) > 0
            for result in results:
                assert result.chunk.knowledge_scope == "project"
            
        finally:
            await pipeline.close()

    @pytest.mark.e2e
    async def test_search_returns_empty_for_wrong_project(self, ensure_services, test_config):
        pipeline = IngestionPipeline(settings=test_config)
        
        try:
            await pipeline.initialize()
            await pipeline.run_full_ingest()
            
            results = await pipeline.search(
                "programming",
                limit=10,
                knowledge_scope="project",
                project_id="nonexistent-project",
            )
            
            assert len(results) == 0
            
        finally:
            await pipeline.close()

    @pytest.mark.e2e
    async def test_search_results_include_location(self, ensure_services, test_config):
        pipeline = IngestionPipeline(settings=test_config)
        
        try:
            await pipeline.initialize()
            await pipeline.run_full_ingest()
            
            results = await pipeline.search("Python", limit=5)
            
            assert len(results) > 0
            
            results_with_location = [r for r in results if r.chunk.location is not None]
            assert len(results_with_location) > 0, "At least one result should have location info"
            
            for result in results_with_location:
                loc = result.chunk.location
                assert loc.start_line >= 1, "start_line should be >= 1"
                assert loc.end_line >= loc.start_line, "end_line should be >= start_line"
                assert loc.char_start >= 0, "char_start should be >= 0"
                assert loc.char_end > loc.char_start, "char_end should be > char_start"
            
        finally:
            await pipeline.close()


@pytest.mark.asyncio
class TestIncrementalIngest:
    @pytest.mark.e2e
    async def test_incremental_detects_new_file(self, ensure_services, test_collection, test_docs_dir):
        config = make_config(test_collection, test_docs_dir)
        pipeline = IngestionPipeline(settings=config)
        
        try:
            await pipeline.initialize()
            await pipeline.run_full_ingest()
            
            initial_count = pipeline.vector_store.count()
            
            (test_docs_dir / "new_doc.md").write_text("""# New Document

This is a newly added document for testing incremental ingest.
""")
            
            result = await pipeline.run_incremental_ingest()
            
            assert result.new_chunks > 0
            
            new_count = pipeline.vector_store.count()
            assert new_count > initial_count
            
        finally:
            await pipeline.close()

    @pytest.mark.e2e
    async def test_incremental_detects_updated_file(self, ensure_services, test_collection, test_docs_dir):
        config = make_config(test_collection, test_docs_dir)
        pipeline = IngestionPipeline(settings=config)
        
        try:
            await pipeline.initialize()
            await pipeline.run_full_ingest()
            
            doc1_path = test_docs_dir / "doc1.md"
            original_content = doc1_path.read_text()
            
            doc1_path.write_text(original_content + "\n\n## New Section\n\nThis is new content added for testing.")
            
            result = await pipeline.run_incremental_ingest()
            
            assert result.updated_chunks > 0 or result.new_chunks > 0
            
        finally:
            await pipeline.close()

    @pytest.mark.e2e
    async def test_incremental_detects_deleted_file(self, ensure_services, test_collection, test_docs_dir):
        config = make_config(test_collection, test_docs_dir)
        pipeline = IngestionPipeline(settings=config)
        
        try:
            await pipeline.initialize()
            await pipeline.run_full_ingest()
            
            initial_count = pipeline.vector_store.count()
            
            doc3_path = test_docs_dir / "doc3.txt"
            doc3_path.unlink()
            
            result = await pipeline.run_incremental_ingest()
            
            assert result.deleted_chunks > 0
            
            new_count = pipeline.vector_store.count()
            assert new_count < initial_count
            
        finally:
            await pipeline.close()
