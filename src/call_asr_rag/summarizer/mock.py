from dataclasses import dataclass


@dataclass
class MockSummarizer:
    max_chars: int = 1200

    def summarize(self, text: str) -> str:
        tail = text[-self.max_chars :] if len(text) > self.max_chars else text
        return "[MOCK SUMMARY]\n" + tail
