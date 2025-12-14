from dataclasses import dataclass, field


@dataclass
class ContextStore:
    phrases: list[str] = field(default_factory=list)

    def add_phrase(self, text: str) -> None:
        self.phrases.append(text)

    def full_text(self) -> str:
        return "\n".join(self.phrases)
