from dataclasses import dataclass
from typing import Literal


@dataclass
class AudioConfig:
    sample_rate: int
    chunk_ms: int


PauseMode = Literal["phrase", "vad", "hybrid"]


@dataclass
class PauseConfig:
    mode: PauseMode


@dataclass
class VADConfig:
    mode: int
    frame_ms: int
    min_silence_ms: int
    min_speech_ms: int
    hangover_ms: int


@dataclass
class HybridConfig:
    idle_ms: int


@dataclass
class ContextConfig:
    full_tail_chars: int


@dataclass
class SummaryConfig:
    enabled: bool
    impl: Literal["mock", "llm"]
    max_chars: int


@dataclass
class OpenRouterConfig:
    api_key_env: str
    model: str
    site_url: str = ""
    site_title: str = ""


@dataclass
class AppConfig:
    audio: AudioConfig
    pause: PauseConfig
    vad: VADConfig
    hybrid: HybridConfig
    context: ContextConfig
    summary: SummaryConfig
    openrouter: OpenRouterConfig
