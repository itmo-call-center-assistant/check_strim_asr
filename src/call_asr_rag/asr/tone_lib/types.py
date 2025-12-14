from dataclasses import dataclass
from typing import Any


@dataclass
class Phrase:
    text: str
    raw: Any | None = None
