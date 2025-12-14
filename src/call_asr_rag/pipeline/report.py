from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunResult:
    phrases: list[str] = field(default_factory=list)
    pause_events: list[dict[str, Any]] = field(default_factory=list)
    trigger_events: list[dict[str, Any]] = field(default_factory=list)
    summary_debug: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
