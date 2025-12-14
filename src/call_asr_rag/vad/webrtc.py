from collections.abc import Iterable
from dataclasses import dataclass

import webrtcvad

from ..audio.pcm import float_to_int16_pcm


@dataclass
class VADConfig:
    sample_rate: int
    mode: int
    frame_ms: int


class WebRTCVAD:
    def __init__(self, cfg: VADConfig):
        self.cfg = cfg
        self.vad = webrtcvad.Vad(cfg.mode)
        self.frame_bytes = int(cfg.sample_rate * (cfg.frame_ms / 1000.0) * 2)

    def iter_frame_speech(self, chunk_f32) -> Iterable[bool]:
        pcm = float_to_int16_pcm(chunk_f32)
        if self.frame_bytes == 0:
            return []
        for i in range(0, len(pcm) - self.frame_bytes + 1, self.frame_bytes):
            frame = pcm[i : i + self.frame_bytes]
            yield self.vad.is_speech(frame, self.cfg.sample_rate)
