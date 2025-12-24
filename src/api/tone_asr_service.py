"""
Tone ASR Service wrapper around check_strim_asr pipeline (T-one + pause/VAD).
"""

import tempfile
from pathlib import Path

from call_asr_rag.asr.tone_lib.model import build_tone_asr
from call_asr_rag.audio.decode import decode_mp3_to_mono
from call_asr_rag.cli import build_pause_driver
from call_asr_rag.config.loader import load_config
from call_asr_rag.config.schema import AppConfig
from call_asr_rag.pipeline.runner import PipelineDeps, run_pipeline
from call_asr_rag.summarizer.mock import MockSummarizer
from call_asr_rag.trigger.noop import NoopTrigger


class ToneASRService:
    """
    Wraps the check_strim_asr pipeline for use in the Audio API.
    """

    def __init__(self, config_path: Path, enable_summary: bool = False) -> None:
        self.config_path = Path(config_path)
        self.enable_summary = enable_summary

        # Load YAML config to know audio params before model init
        self.cfg: AppConfig = load_config(self.config_path)

        # Runtime components
        self.tone_asr = None
        self.pause_driver = None
        self.summarizer = None
        self.trigger = NoopTrigger()

        # Audio params (will be aligned with model after load())
        self.sample_rate: int = self.cfg.audio.sample_rate
        self.chunk_ms: int = self.cfg.audio.chunk_ms
        self.chunk_size_samples: int = int(self.sample_rate * (self.chunk_ms / 1000.0))

        self.loaded = False

    # ------------------------------------------------------------------ utils
    def _build_deps(self) -> PipelineDeps:
        if not self.loaded or not self.tone_asr or not self.pause_driver:
            raise RuntimeError("Tone ASR service not loaded")

        do_summary = self.enable_summary and self.cfg.summary.enabled
        summarizer = None
        if do_summary:
            summarizer = MockSummarizer(max_chars=self.cfg.summary.max_chars)

        return PipelineDeps(
            asr_backend=self.tone_asr,
            pause_driver=self.pause_driver,
            trigger=self.trigger,
            summarizer=summarizer,
            full_tail_chars=self.cfg.context.full_tail_chars,
            do_summary=do_summary,
        )

    # ------------------------------------------------------------------ public
    def load(self) -> bool:
        """Load tone model and prepare drivers."""
        if self.loaded:
            return True

        self.tone_asr = build_tone_asr()

        # Align sample rate/chunk with the model to avoid shape errors
        self.sample_rate = int(self.tone_asr.sample_rate)
        model_chunk_ms = int(round(1000.0 * self.tone_asr.chunk_size / self.sample_rate))
        if model_chunk_ms != self.chunk_ms:
            print(f"[WARN] Overriding chunk_ms from config ({self.chunk_ms}) " f"to match model: {model_chunk_ms} ms")
            self.chunk_ms = model_chunk_ms
        self.chunk_size_samples = self.tone_asr.chunk_size

        # Build pause driver with aligned sample rate
        self.pause_driver = build_pause_driver(self.cfg, sample_rate=self.sample_rate)

        self.loaded = True
        print(
            f"[INFO] Tone ASR loaded: sample_rate={self.sample_rate}, "
            f"chunk_ms={self.chunk_ms}, chunk_samples={self.chunk_size_samples}"
        )
        return True

    def transcribe_file(self, audio_path: Path) -> tuple[str, dict]:
        """Transcribe audio file (mp3/wav). Returns (text, debug)."""
        if not self.loaded and not self.load():
            raise RuntimeError("Tone ASR not loaded")

        waveform, sr = decode_mp3_to_mono(audio_path, target_sample_rate=self.sample_rate)
        if sr != self.sample_rate:
            raise RuntimeError(f"Decoded sample_rate {sr} != expected {self.sample_rate}")

        deps = self._build_deps()
        result = run_pipeline(
            waveform=waveform,
            sample_rate=self.sample_rate,
            chunk_ms=self.chunk_ms,
            deps=deps,
        )

        transcription = " ".join(result.phrases).strip()
        debug = {
            "phrases": result.phrases,
            "pause_events": result.pause_events,
            "trigger_events": result.trigger_events,
            "summary": result.summary_debug,
            "events": result.events,
        }
        return transcription, debug

    def transcribe_bytes(self, audio_bytes: bytes) -> tuple[str, dict]:
        """Transcribe audio bytes (wav/mp3)."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = Path(tmp_file.name)

        try:
            return self.transcribe_file(tmp_path)
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                print("Could not unlink file")
