from dataclasses import dataclass
from typing import Literal

PauseKind = Literal["tone_endpoint", "vad", "hybrid"]


@dataclass(frozen=True)
class PauseEvent:
    t_ms: int
    kind: PauseKind
    details: dict


class PauseDriver:
    def on_chunk(self, chunk_f32, t_ms: int) -> list[PauseEvent]:
        return []

    def on_phrase(self, phrase_text: str, t_ms: int) -> list[PauseEvent]:
        return []
