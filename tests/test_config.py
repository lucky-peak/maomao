import pytest
from maomao.config import SourceConfig, Settings, OllamaConfig, QdrantConfig


class TestSourceConfig:
    def test_source_config_defaults(self):
        config = SourceConfig(type="siyuan", config={})
        assert config.enabled is True
        assert config.knowledge_scope == "global"
        assert config.project_id == ""

    def test_source_config_with_scope(self):
        config = SourceConfig(
            type="local_doc",
            knowledge_scope="project",
            project_id="my-project",
            config={"path": "/test"}
        )
        assert config.knowledge_scope == "project"
        assert config.project_id == "my-project"

    def test_source_config_global_scope(self):
        config = SourceConfig(
            type="siyuan",
            knowledge_scope="global",
            config={"api_url": "http://localhost"}
        )
        assert config.knowledge_scope == "global"
        assert config.project_id == ""


class TestOllamaConfig:
    def test_ollama_config_defaults(self):
        config = OllamaConfig()
        assert config.base_url == "http://127.0.0.1:11434"
        assert config.embedding_model == "bge-m3"
        assert config.embedding_dim == 1024
        assert config.timeout == 120


class TestQdrantConfig:
    def test_qdrant_config_defaults(self):
        config = QdrantConfig()
        assert config.host == "127.0.0.1"
        assert config.port == 6333
        assert config.collection_name == "maomao_knowledge"
        assert config.prefer_grpc is False


class TestSettings:
    def test_settings_defaults(self):
        settings = Settings()
        assert settings.sources == []
        assert settings.log_level == "INFO"

    def test_get_enabled_sources(self):
        settings = Settings(
            sources=[
                SourceConfig(type="siyuan", enabled=True, config={}),
                SourceConfig(type="local_doc", enabled=False, config={}),
            ]
        )
        enabled = settings.get_enabled_sources()
        assert len(enabled) == 1
        assert enabled[0].type == "siyuan"
