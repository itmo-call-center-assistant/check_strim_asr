# ruff: noqa: S101

import numpy as np

from call_asr_rag.context.builder import ContextBuilder
from call_asr_rag.context.store import ContextStore
from call_asr_rag.pause.base import PauseDriver, PauseEvent
from call_asr_rag.pipeline.runner import PipelineDeps, run_pipeline
from call_asr_rag.trigger.base import Trigger, TriggerDecision


class DummyASR:
    def __init__(self):
        self.chunks = 0

    def feed_chunk(self, chunk_f32):
        self.chunks += 1
        if self.chunks % 2 == 0:
            return [f"phrase{self.chunks}"]
        return []

    def finalize(self):
        return []


class DummyPause(PauseDriver):
    def on_chunk(self, chunk_f32, t_ms: int):
        if t_ms >= 200:
            return [PauseEvent(t_ms=t_ms, kind="vad", details={"t": t_ms})]
        return []

    def on_phrase(self, phrase_text: str, t_ms: int):
        return [PauseEvent(t_ms=t_ms, kind="tone_endpoint", details={"text": phrase_text})]


class DummyTrigger(Trigger):
    def on_pause(self, ev: PauseEvent) -> TriggerDecision:
        return TriggerDecision(action="skip", reason=f"seen_{ev.kind}")


def test_context_builder_tail():
    store = ContextStore()
    builder = ContextBuilder(full_tail_chars=5, store=store)
    builder.add_phrase("hello")
    builder.add_phrase("world")
    assert builder.tail_text() == "world"


def test_run_pipeline_collects_events_and_phrases():
    waveform = np.zeros(8000, dtype=np.float32)
    deps = PipelineDeps(
        asr_backend=DummyASR(),
        pause_driver=DummyPause(),
        trigger=DummyTrigger(),
        summarizer=None,
        full_tail_chars=100,
        do_summary=False,
    )
    res = run_pipeline(waveform, sample_rate=8000, chunk_ms=200, deps=deps)
    assert any(ev["kind"] == "vad" for ev in res.pause_events)
    assert any(ev["kind"] == "tone_endpoint" for ev in res.pause_events)
    assert res.phrases
