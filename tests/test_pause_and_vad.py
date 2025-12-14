# ruff: noqa: S101

import numpy as np

from call_asr_rag.pause.hybrid import HybridConfig, HybridPauseDriver
from call_asr_rag.pause.phrase import PhrasePauseDriver
from call_asr_rag.pause.vad import VADPauseConfig, VADPauseDriver


class FakeVAD:
    def __init__(self, frame_ms: int, speech_flags: list[bool]):
        self.cfg = type("Cfg", (), {"frame_ms": frame_ms})()
        self.speech_flags = speech_flags

    def iter_frame_speech(self, chunk_f32):
        yield from self.speech_flags


def test_phrase_pause_driver_emits_on_phrase():
    driver = PhrasePauseDriver()
    evs = driver.on_phrase("hello", 1000)
    assert len(evs) == 1
    assert evs[0].kind == "tone_endpoint"
    assert evs[0].t_ms == 1000
    assert evs[0].details["text"] == "hello"


def test_vad_pause_driver_emits_after_silence_with_speech_seen():
    vad = FakeVAD(frame_ms=20, speech_flags=[True, True] + [False] * 6)
    driver = VADPauseDriver(
        vad=vad,
        cfg=VADPauseConfig(min_silence_ms=60, min_speech_ms=20, hangover_ms=20),
    )
    evs = driver.on_chunk(np.zeros(10, dtype=float), t_ms=200)
    assert evs and evs[0].kind == "vad"


def test_hybrid_pause_driver_requires_phrase_and_vad_idle():
    vad = FakeVAD(frame_ms=20, speech_flags=[True, True] + [False] * 10)
    vad_driver = VADPauseDriver(
        vad=vad,
        cfg=VADPauseConfig(min_silence_ms=60, min_speech_ms=20, hangover_ms=20),
    )
    driver = HybridPauseDriver(vad_driver=vad_driver, cfg=HybridConfig(idle_ms=100))

    evs_initial = driver.on_chunk(np.zeros(10, dtype=float), t_ms=0)
    assert evs_initial == []

    driver.on_phrase("p", t_ms=0)
    evs = driver.on_chunk(np.zeros(10, dtype=float), t_ms=200)
    assert len(evs) == 1
    assert evs[0].kind == "hybrid"
