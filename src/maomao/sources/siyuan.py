from typing import Any

import httpx
from rich.console import Console

from maomao.sources.base import KnowledgeSource, SourceChange, SourceItem, SourceRegistry

console = Console()


@SourceRegistry.register
class SiyuanSource(KnowledgeSource):
    def __init__(
        self,
        api_url: str = "http://127.0.0.1:6806",
        token: str = "",
        box_id: str = "",
        root_block_id: str = "",
        chunker_type: str = "markdown",
        knowledge_scope: str = "global",
        project_id: str = "",
    ):
        super().__init__(knowledge_scope, project_id)
        self.api_url = api_url
        self.token = token
        self.box_id = box_id
        self.root_block_id = root_block_id
        self.chunker_type = chunker_type
        self._client: httpx.AsyncClient | None = None

    @classmethod
    def source_type(cls) -> str:
        return "siyuan"

    @classmethod
    def from_config(
        cls,
        config: dict[str, Any],
        knowledge_scope: str = "global",
        project_id: str = "",
    ) -> "SiyuanSource":
        return cls(
            api_url=config.get("api_url", "http://127.0.0.1:6806"),
            token=config.get("token", ""),
            box_id=config.get("box_id", ""),
            root_block_id=config.get("root_block_id", ""),
            chunker_type=config.get("chunker_type", "markdown"),
            knowledge_scope=knowledge_scope,
            project_id=project_id,
        )

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Token {self.token}"
            self._client = httpx.AsyncClient(
                base_url=self.api_url,
                headers=headers,
                timeout=60.0,
                trust_env=False,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def scan(self) -> list[SourceItem]:
        if not self.box_id:
            console.print("[yellow]SiyuanSource: box_id not configured[/yellow]")
            return []

        items: list[SourceItem] = []
        blocks = await self._fetch_blocks()

        for block in blocks:
            block_id = block.get("id", "")
            content = await self._fetch_block_content(block_id)

            if not content.strip():
                continue

            item = SourceItem(
                source_type=self.source_type(),
                source_path=block.get("hpath", "/"),
                source_id=block_id,
                knowledge_scope=self.knowledge_scope,
                project_id=self.project_id,
                content=content,
                content_hash=self._compute_hash(content),
                chunker_type=self.chunker_type,
                metadata={
                    "title": block.get("content", ""),
                    "box": block.get("box", ""),
                    "hpath": block.get("hpath", ""),
                    "created": block.get("created", ""),
                    "updated": block.get("updated", ""),
                },
            )
            items.append(item)

        return items

    async def get_changes(self, state: dict[str, Any]) -> SourceChange:
        current_items = await self.scan()
        current_ids = {item.source_id for item in current_items}
        current_map = {item.source_id: item for item in current_items}

        previous_state = state.get(self.source_type(), {})
        previous_ids = set(previous_state.get("ids", []))

        added_ids = current_ids - previous_ids
        deleted_ids = previous_ids - current_ids
        common_ids = current_ids & previous_ids

        added = [current_map[i] for i in added_ids]
        deleted = list(deleted_ids)

        updated: list[SourceItem] = []
        previous_hashes = previous_state.get("hashes", {})
        for item_id in common_ids:
            item = current_map[item_id]
            if item.content_hash != previous_hashes.get(item_id):
                updated.append(item)

        return SourceChange(added=added, updated=updated, deleted_ids=deleted)

    async def _fetch_blocks(self) -> list[dict[str, Any]]:
        stmt = "SELECT * FROM blocks WHERE type = 'd'"
        if self.root_block_id:
            stmt += f" AND root_id = '{self.root_block_id}'"
        if self.box_id:
            stmt += f" AND box = '{self.box_id}'"
        stmt += " ORDER BY updated DESC"

        response = await self.client.post(
            "/api/query/sql",
            json={"stmt": stmt},
        )
        response.raise_for_status()
        return response.json().get("data", [])

    async def _fetch_block_content(self, block_id: str) -> str:
        response = await self.client.post(
            "/api/export/exportMdContent",
            json={"id": block_id},
        )
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("content", "")
