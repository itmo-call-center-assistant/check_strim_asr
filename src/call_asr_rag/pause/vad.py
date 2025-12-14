from dataclasses import dataclass

from ..vad.webrtc import WebRTCVAD
from .base import PauseDriver, PauseEvent


@dataclass
class VADPauseConfig:
    min_silence_ms: int
    min_speech_ms: int
    hangover_ms: int


class VADPauseDriver(PauseDriver):
    def __init__(self, vad: WebRTCVAD, cfg: VADPauseConfig):
        self.vad = vad
        self.cfg = cfg
        self.silence_ms = 0
        self.speech_ms = 0
        self.in_speech = False

    def on_chunk(self, chunk_f32, t_ms: int) -> list[PauseEvent]:
        events: list[PauseEvent] = []
        frame_ms = self.vad.cfg.frame_ms

        for is_speech in self.vad.iter_frame_speech(chunk_f32):
            if is_speech:
                self.speech_ms += frame_ms
                self.silence_ms = 0
                if self.speech_ms >= self.cfg.min_speech_ms:
                    self.in_speech = True
            else:
                self.silence_ms += frame_ms
                if self.in_speech and self.silence_ms >= self.cfg.min_silence_ms + self.cfg.hangover_ms:
                    events.append(
                        PauseEvent(
                            t_ms=t_ms,
                            kind="vad",
                            details={"silence_ms": self.silence_ms, "frame_ms": frame_ms},
                        )
                    )
                    self.in_speech = False
                    self.speech_ms = 0
                    self.silence_ms = 0

        return events
