from .base import PauseDriver, PauseEvent


class PhrasePauseDriver(PauseDriver):
    def on_phrase(self, phrase_text: str, t_ms: int) -> list[PauseEvent]:
        return [PauseEvent(t_ms=t_ms, kind="tone_endpoint", details={"text": phrase_text})]
