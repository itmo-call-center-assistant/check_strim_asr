from dataclasses import dataclass

from .base import PauseDriver, PauseEvent
from .vad import VADPauseDriver


@dataclass
class HybridConfig:
    idle_ms: int


class HybridPauseDriver(PauseDriver):
    def __init__(self, vad_driver: VADPauseDriver, cfg: HybridConfig):
        self.vad_driver = vad_driver
        self.cfg = cfg
        self.last_phrase_t_ms: int | None = None

    def on_phrase(self, phrase_text: str, t_ms: int) -> list[PauseEvent]:
        self.last_phrase_t_ms = t_ms
        return []

    def on_chunk(self, chunk_f32, t_ms: int) -> list[PauseEvent]:
        vad_events = self.vad_driver.on_chunk(chunk_f32, t_ms)
        if not vad_events:
            return []

        last = self.last_phrase_t_ms
        if last is None:
            return []

        if (t_ms - last) >= self.cfg.idle_ms:
            return [PauseEvent(t_ms=t_ms, kind="hybrid", details=vad_events[0].details)]

        return []
