from dataclasses import dataclass

from ..pause.base import PauseEvent
from .base import Trigger, TriggerDecision


@dataclass(frozen=True)
class NoopTrigger(Trigger):
    reason: str = "noop_trigger"

    def on_pause(self, ev: PauseEvent) -> TriggerDecision:
        return TriggerDecision(action="skip", reason=self.reason)
