import asyncio
from abc import ABC, abstractmethod

import httpx
from rich.console import Console

from maomao.config import OllamaConfig

console = Console()


class EmbeddingService(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        pass

    @abstractmethod
    async def embed_single(self, text: str) -> list[float]:
        pass


class OllamaEmbeddingService(EmbeddingService):
    def __init__(self, config: OllamaConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout,
            trust_env=False,
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings: list[list[float]] = []
        batch_size = 10

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            tasks = [self._embed_one(text) for text in batch]
            batch_embeddings = await asyncio.gather(*tasks)
            embeddings.extend(batch_embeddings)

        return embeddings

    async def _embed_one(self, text: str) -> list[float]:
        try:
            response = await self.client.post(
                "/api/embeddings",
                json={
                    "model": self.config.embedding_model,
                    "prompt": text,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
        except Exception as e:
            console.print(f"[red]Embedding error: {e}[/red]")
            return [0.0] * self.config.embedding_dim

    async def embed_single(self, text: str) -> list[float]:
        result = await self._embed_one(text)
        return result

    async def close(self) -> None:
        await self.client.aclose()


async def get_embedding_service(config: OllamaConfig) -> EmbeddingService:
    return OllamaEmbeddingService(config)
