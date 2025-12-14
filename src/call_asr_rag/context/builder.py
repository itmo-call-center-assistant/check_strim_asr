from dataclasses import dataclass

from .store import ContextStore


@dataclass
class ContextBuilder:
    full_tail_chars: int
    store: ContextStore

    def add_phrase(self, text: str) -> None:
        self.store.add_phrase(text)

    def tail_text(self) -> str:
        full = self.store.full_text()
        if len(full) <= self.full_tail_chars:
            return full
        return full[-self.full_tail_chars :]
