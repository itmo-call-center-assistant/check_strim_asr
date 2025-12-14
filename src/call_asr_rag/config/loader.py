import pathlib
from typing import Any

import yaml

from .schema import (
    AppConfig,
    AudioConfig,
    ContextConfig,
    HybridConfig,
    OpenRouterConfig,
    PauseConfig,
    SummaryConfig,
    VADConfig,
)


def _require(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping:
        raise KeyError(f"Missing config key: {key}")
    return mapping[key]


def load_config(path: str | pathlib.Path) -> AppConfig:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    audio_raw = _require(raw, "audio")
    pause_raw = _require(raw, "pause")
    vad_raw = _require(raw, "vad")
    hybrid_raw = _require(raw, "hybrid")
    context_raw = _require(raw, "context")
    summary_raw = _require(raw, "summary")
    openrouter_raw = _require(raw, "openrouter")

    cfg = AppConfig(
        audio=AudioConfig(
            sample_rate=int(_require(audio_raw, "sample_rate")),
            chunk_ms=int(_require(audio_raw, "chunk_ms")),
        ),
        pause=PauseConfig(mode=_require(pause_raw, "mode")),
        vad=VADConfig(
            mode=int(_require(vad_raw, "mode")),
            frame_ms=int(_require(vad_raw, "frame_ms")),
            min_silence_ms=int(_require(vad_raw, "min_silence_ms")),
            min_speech_ms=int(_require(vad_raw, "min_speech_ms")),
            hangover_ms=int(_require(vad_raw, "hangover_ms")),
        ),
        hybrid=HybridConfig(idle_ms=int(_require(hybrid_raw, "idle_ms"))),
        context=ContextConfig(full_tail_chars=int(_require(context_raw, "full_tail_chars"))),
        summary=SummaryConfig(
            enabled=bool(_require(summary_raw, "enabled")),
            impl=_require(summary_raw, "impl"),
            max_chars=int(_require(summary_raw, "max_chars")),
        ),
        openrouter=OpenRouterConfig(
            api_key_env=_require(openrouter_raw, "api_key_env"),
            model=_require(openrouter_raw, "model"),
            site_url=str(openrouter_raw.get("site_url", "")),
            site_title=str(openrouter_raw.get("site_title", "")),
        ),
    )
    return cfg
