from typing import Protocol


class Summarizer(Protocol):
    def summarize(self, text: str) -> str: ...
