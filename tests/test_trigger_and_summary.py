# ruff: noqa: S101

from call_asr_rag.pause.base import PauseEvent
from call_asr_rag.summarizer.mock import MockSummarizer
from call_asr_rag.trigger.noop import NoopTrigger


def test_noop_trigger_always_skip():
    trig = NoopTrigger()
    ev = PauseEvent(t_ms=100, kind="vad", details={})
    decision = trig.on_pause(ev)
    assert decision.action == "skip"
    assert decision.reason == "noop_trigger"


def test_mock_summarizer_takes_tail():
    text = "a" * 10 + "b" * 5
    summ = MockSummarizer(max_chars=8)
    out = summ.summarize(text)
    assert out.startswith("[MOCK SUMMARY]")
    assert out.endswith(text[-8:])
