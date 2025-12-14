from dataclasses import dataclass

from ..pause.base import PauseEvent


@dataclass(frozen=True)
class TriggerDecision:
    action: str
    reason: str


class Trigger:
    def on_pause(self, ev: PauseEvent) -> TriggerDecision:
        raise NotImplementedError
