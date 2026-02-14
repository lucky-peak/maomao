import asyncio
import os
import time
import uuid
from pathlib import Path

for proxy_var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
    os.environ.pop(proxy_var, None)

import httpx
import pytest


def wait_for_service(url: str, timeout: int = 60, interval: float = 1.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = httpx.get(url, timeout=5.0)
            if response.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False


@pytest.fixture(scope="session")
def ensure_services():
    qdrant_host = os.environ.get("MAOMAO_QDRANT_HOST", "127.0.0.1")
    qdrant_port = int(os.environ.get("MAOMAO_QDRANT_PORT", "6333"))
    ollama_host = os.environ.get("MAOMAO_OLLAMA_BASE_URL", "http://127.0.0.1:11434")

    qdrant_url = f"http://{qdrant_host}:{qdrant_port}/"
    ollama_url = f"{ollama_host}/api/tags"

    qdrant_ready = wait_for_service(qdrant_url, timeout=10)
    ollama_ready = wait_for_service(ollama_url, timeout=10)

    if not qdrant_ready:
        pytest.skip("Qdrant service not available")
    if not ollama_ready:
        pytest.skip("Ollama service not available")

    yield


@pytest.fixture
def test_collection():
    return f"test_maomao_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_docs_dir(tmp_path):
    docs_dir = tmp_path / "test_docs"
    docs_dir.mkdir()
    
    (docs_dir / "doc1.md").write_text("""# Test Document 1

This is a test document about Python programming.

## Variables

Variables in Python are dynamically typed.

## Functions

Functions are defined using the `def` keyword.
""")
    
    (docs_dir / "doc2.md").write_text("""# Test Document 2

This is a test document about JavaScript.

## Variables

JavaScript uses `let`, `const`, and `var` for variables.

## Functions

Functions can be defined using `function` keyword or arrow syntax.
""")
    
    (docs_dir / "doc3.txt").write_text("""This is a plain text document.
It contains some general information about programming best practices.
""")
    
    return docs_dir


@pytest.fixture
def test_config(test_collection, test_docs_dir):
    from maomao.config import Settings, SourceConfig, QdrantConfig, OllamaConfig
    
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
    )
