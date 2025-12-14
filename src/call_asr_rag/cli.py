import argparse
import json
import pathlib

from dotenv import load_dotenv

from .asr.tone_lib.model import build_tone_asr
from .audio.decode import decode_mp3_to_mono
from .config.loader import load_config
from .config.schema import AppConfig
from .pause.hybrid import HybridConfig as HybridPauseConfig
from .pause.hybrid import HybridPauseDriver
from .pause.phrase import PhrasePauseDriver
from .pause.vad import VADPauseConfig, VADPauseDriver
from .pipeline.report import RunResult
from .pipeline.runner import PipelineDeps, run_pipeline
from .summarizer.llm_openrouter import LLMSummarizer, OpenRouterConfig
from .summarizer.mock import MockSummarizer
from .trigger.noop import NoopTrigger
from .vad.webrtc import VADConfig as WebRTCVADConfig
from .vad.webrtc import WebRTCVAD


def build_pause_driver(cfg: AppConfig, sample_rate: int):
    mode = cfg.pause.mode
    vad = WebRTCVAD(
        WebRTCVADConfig(
            sample_rate=sample_rate,
            mode=cfg.vad.mode,
            frame_ms=cfg.vad.frame_ms,
        )
    )
    vad_driver = VADPauseDriver(
        vad=vad,
        cfg=VADPauseConfig(
            min_silence_ms=cfg.vad.min_silence_ms,
            min_speech_ms=cfg.vad.min_speech_ms,
            hangover_ms=cfg.vad.hangover_ms,
        ),
    )

    if mode == "vad":
        return vad_driver
    if mode == "phrase":
        return PhrasePauseDriver()
    if mode == "hybrid":
        return HybridPauseDriver(vad_driver=vad_driver, cfg=HybridPauseConfig(idle_ms=cfg.hybrid.idle_ms))
    raise ValueError(f"Unknown pause mode: {mode}")


def build_summarizer(cfg: AppConfig):
    if not cfg.summary.enabled:
        return None
    if cfg.summary.impl == "mock":
        return MockSummarizer(max_chars=cfg.summary.max_chars)
    if cfg.summary.impl == "llm":
        return LLMSummarizer(
            OpenRouterConfig(
                api_key_env=cfg.openrouter.api_key_env,
                model=cfg.openrouter.model,
                site_url=cfg.openrouter.site_url,
                site_title=cfg.openrouter.site_title,
            )
        )
    raise ValueError(f"Unknown summarizer impl: {cfg.summary.impl}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Call ASR + Pause + Summarize MVP")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--input", required=True, help="Path to input MP3 (mono)")
    parser.add_argument(
        "--out",
        default="reports/report.json",
        help="Where to write report.json (default: reports/report.json)",
    )
    args = parser.parse_args(argv)

    load_dotenv()

    cfg = load_config(args.config)
    waveform, sr = decode_mp3_to_mono(args.input, target_sample_rate=cfg.audio.sample_rate)
    if sr != cfg.audio.sample_rate:
        raise RuntimeError(f"Unexpected sample rate after decode: {sr}, wanted {cfg.audio.sample_rate}")

    tone_asr = build_tone_asr()
    pause_driver = build_pause_driver(cfg, sample_rate=sr)
    summarizer = build_summarizer(cfg)
    trigger = NoopTrigger()

    deps = PipelineDeps(
        asr_backend=tone_asr,
        pause_driver=pause_driver,
        trigger=trigger,
        summarizer=summarizer,
        full_tail_chars=cfg.context.full_tail_chars,
        do_summary=cfg.summary.enabled,
    )

    result: RunResult = run_pipeline(
        waveform=waveform,
        sample_rate=cfg.audio.sample_rate,
        chunk_ms=cfg.audio.chunk_ms,
        deps=deps,
    )

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result.__dict__, f, ensure_ascii=False, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
