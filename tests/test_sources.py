import pytest
from maomao.sources.base import SourceItem, SourceChange, KnowledgeSource, SourceRegistry


class MockSource(KnowledgeSource):
    @classmethod
    def source_type(cls) -> str:
        return "mock"
    
    @classmethod
    def from_config(cls, config: dict, knowledge_scope: str = "global", project_id: str = "") -> "MockSource":
        return cls(knowledge_scope, project_id)
    
    async def scan(self):
        return []
    
    async def get_changes(self, state: dict):
        return SourceChange()
    
    async def close(self):
        pass


SourceRegistry.register(MockSource)


class TestSourceItem:
    def test_source_item_defaults(self):
        item = SourceItem()
        assert item.content == ""
        assert item.source_type == ""
        assert item.knowledge_scope == "global"
        assert item.project_id == ""
        assert item.chunker_type == "text"
        assert item.metadata == {}

    def test_source_item_with_scope(self):
        item = SourceItem(
            content="test content",
            source_type="test",
            source_path="/test/path",
            source_id="test-id",
            knowledge_scope="project",
            project_id="my-project",
        )
        assert item.knowledge_scope == "project"
        assert item.project_id == "my-project"

    def test_source_item_content_hash(self):
        item1 = SourceItem(content="same content")
        item2 = SourceItem(content="same content")
        item3 = SourceItem(content="different content")
        
        source = MockSource()
        item1.content_hash = source._compute_hash(item1.content) if item1.content else ""
        item2.content_hash = source._compute_hash(item2.content) if item2.content else ""
        item3.content_hash = source._compute_hash(item3.content) if item3.content else ""
        
        assert item1.content_hash == item2.content_hash
        assert item1.content_hash != item3.content_hash


class TestSourceChange:
    def test_source_change_defaults(self):
        change = SourceChange()
        assert change.added == []
        assert change.updated == []
        assert change.deleted_ids == []

    def test_source_change_with_items(self):
        item1 = SourceItem(content="item1")
        item2 = SourceItem(content="item2")
        change = SourceChange(
            added=[item1],
            updated=[item2],
            deleted_ids=["old-id"],
        )
        assert len(change.added) == 1
        assert len(change.updated) == 1
        assert len(change.deleted_ids) == 1


class TestKnowledgeSource:
    def test_knowledge_source_defaults(self):
        source = MockSource()
        assert source.knowledge_scope == "global"
        assert source.project_id == ""

    def test_knowledge_source_with_scope(self):
        source = MockSource(knowledge_scope="project", project_id="my-project")
        assert source.knowledge_scope == "project"
        assert source.project_id == "my-project"


class TestSourceRegistry:
    def test_register_source(self):
        @SourceRegistry.register
        class TestSource(KnowledgeSource):
            @classmethod
            def source_type(cls) -> str:
                return "test_registry_2"
            
            @classmethod
            def from_config(cls, config: dict, knowledge_scope: str = "global", project_id: str = "") -> "TestSource":
                return cls(knowledge_scope, project_id)
            
            async def scan(self):
                return []
            
            async def get_changes(self, state: dict):
                return SourceChange()
            
            async def close(self):
                pass
        
        assert "test_registry_2" in SourceRegistry.list_sources()
        assert SourceRegistry.get("test_registry_2") == TestSource

    def test_create_source_with_scope(self):
        source = SourceRegistry.create(
            "mock",
            {},
            knowledge_scope="project",
            project_id="test-project",
        )
        assert source is not None
        assert source.knowledge_scope == "project"
        assert source.project_id == "test-project"

    def test_get_nonexistent_source(self):
        assert SourceRegistry.get("nonexistent") is None

    def test_create_nonexistent_source(self):
        assert SourceRegistry.create("nonexistent", {}) is None
