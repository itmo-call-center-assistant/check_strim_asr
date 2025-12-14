from dataclasses import dataclass

import numpy as np

from ..asr.interfaces import StreamingASR
from ..audio.chunker import iter_chunks
from ..context.builder import ContextBuilder
from ..context.store import ContextStore
from ..pause.base import PauseDriver
from ..pipeline.report import RunResult
from ..summarizer.base import Summarizer
from ..trigger.base import Trigger


@dataclass
class PipelineDeps:
    asr_backend: StreamingASR
    pause_driver: PauseDriver
    trigger: Trigger
    summarizer: Summarizer | None
    full_tail_chars: int
    do_summary: bool


def run_pipeline(
    waveform: np.ndarray,
    sample_rate: int,
    chunk_ms: int,
    deps: PipelineDeps,
) -> RunResult:
    res = RunResult()
    context = ContextBuilder(full_tail_chars=deps.full_tail_chars, store=ContextStore())
    last_summary_phrase_count = 0

    def maybe_append_summary(t_ms: int | None) -> None:
        nonlocal last_summary_phrase_count
        if not (deps.do_summary and deps.summarizer):
            return
        phrase_count = len(context.store.phrases)
        if phrase_count <= last_summary_phrase_count:
            return
        summary_text = deps.summarizer.summarize(context.tail_text())
        res.summary_debug = summary_text
        last_summary_phrase_count = phrase_count
        res.events.append(
            {
                "type": "summary",
                "t_ms": t_ms,
                "summary": summary_text,
                "phrases_seen": phrase_count,
                "final": False,
            }
        )
        res.events.append(
            {
                "type": "rag",
                "t_ms": t_ms,
                "called": False,
                "reason": "rag_not_implemented",
            }
        )

    for ch in iter_chunks(waveform, sample_rate, chunk_ms):
        for ev in deps.pause_driver.on_chunk(ch.samples, ch.t_ms):
            decision = deps.trigger.on_pause(ev)
            res.pause_events.append({"t_ms": ev.t_ms, "kind": ev.kind, "details": ev.details})
            res.trigger_events.append({"t_ms": ev.t_ms, "action": decision.action, "reason": decision.reason})
            res.events.append(
                {
                    "type": "pause",
                    "t_ms": ev.t_ms,
                    "kind": ev.kind,
                    "details": ev.details,
                }
            )
            res.events.append(
                {
                    "type": "trigger",
                    "t_ms": ev.t_ms,
                    "action": decision.action,
                    "reason": decision.reason,
                }
            )
            maybe_append_summary(ev.t_ms)

        new_phrases = deps.asr_backend.feed_chunk(ch.samples)
        for p in new_phrases:
            res.phrases.append(p)
            context.add_phrase(p)
            res.events.append({"type": "phrase", "t_ms": ch.t_ms, "text": p})
            for ev in deps.pause_driver.on_phrase(p, ch.t_ms):
                decision = deps.trigger.on_pause(ev)
                res.pause_events.append({"t_ms": ev.t_ms, "kind": ev.kind, "details": ev.details})
                res.trigger_events.append({"t_ms": ev.t_ms, "action": decision.action, "reason": decision.reason})
                res.events.append(
                    {
                        "type": "pause",
                        "t_ms": ev.t_ms,
                        "kind": ev.kind,
                        "details": ev.details,
                    }
                )
                res.events.append(
                    {
                        "type": "trigger",
                        "t_ms": ev.t_ms,
                        "action": decision.action,
                        "reason": decision.reason,
                    }
                )
                maybe_append_summary(ev.t_ms)

    for p in deps.asr_backend.finalize():
        res.phrases.append(p)
        context.add_phrase(p)
        res.events.append({"type": "phrase", "t_ms": None, "text": p})

    if deps.do_summary and deps.summarizer is not None:
        final_summary = deps.summarizer.summarize(context.tail_text())
        res.summary_debug = final_summary
        res.events.append(
            {
                "type": "summary",
                "t_ms": None,
                "summary": final_summary,
                "phrases_seen": len(context.store.phrases),
                "final": True,
            }
        )
        res.events.append(
            {
                "type": "rag",
                "t_ms": None,
                "called": False,
                "reason": "rag_not_implemented",
                "final": True,
            }
        )

    return res
