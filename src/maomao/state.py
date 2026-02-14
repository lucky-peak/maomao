import json
from datetime import datetime
from pathlib import Path
from typing import Any

from maomao.models import IngestionState


class StateManager:
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self._state: IngestionState | None = None

    @property
    def state(self) -> IngestionState:
        if self._state is None:
            self._state = self._load_state()
        return self._state

    def _load_state(self) -> IngestionState:
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    data = json.load(f)
                return IngestionState(**data)
            except Exception:
                pass
        return IngestionState()

    def save_state(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self.state.model_dump(), f, indent=2, default=str)

    def get_source_state(self, source_type: str) -> dict[str, Any]:
        return self.state.source_states.get(source_type, {})

    def update_source_state(self, source_type: str, source_state: dict[str, Any]) -> None:
        self.state.source_states[source_type] = source_state

    def mark_full_ingest(self) -> None:
        self.state.last_full_ingest = datetime.now()
        self.save_state()
