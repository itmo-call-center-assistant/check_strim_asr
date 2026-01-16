"""
Сервис для записи аудио с микрофона
"""

import io

import numpy as np
import soundfile as sf

try:
    import pyaudio

    PYAudio_AVAILABLE = True
except ImportError:
    PYAudio_AVAILABLE = False

from .config import AudioConfig


class AudioRecorderService:
    """Сервис для записи аудио с микрофона"""

    def __init__(self, audio_cfg: AudioConfig | None = None) -> None:
        self.audio_cfg = audio_cfg or AudioConfig()
        if self.audio_cfg.chunk_size <= 0:
            # Fallback: 100ms buffer if chunk_size not provided
            self.audio_cfg.chunk_size = max(1, int(self.audio_cfg.sample_rate * 0.1))
        self.audio = None
        self.stream = None
        self.available = PYAudio_AVAILABLE

        if not self.available:
            print("[WARN] PyAudio not available. Install: pip install pyaudio")

    def start_recording(self) -> None:
        """Начинает запись с микрофона"""
        if not self.available:
            raise RuntimeError("PyAudio not available")

        if self.stream:
            return  # Уже записываем

        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.audio_cfg.sample_rate,
            input=True,
            frames_per_buffer=self.audio_cfg.chunk_size,
        )

    def record(self, duration_seconds: float) -> bytes:
        """Записывает аудио указанной длительности"""
        if not self.stream:
            self.start_recording()

        frames = []
        num_frames = int(self.audio_cfg.sample_rate / self.audio_cfg.chunk_size * duration_seconds)

        for _ in range(num_frames):
            data = self.stream.read(self.audio_cfg.chunk_size)
            frames.append(data)

        return b"".join(frames)

    def stop_recording(self) -> None:
        """Останавливает запись"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        if self.audio:
            self.audio.terminate()
            self.audio = None

    def record_to_wav_bytes(self, duration_seconds: float, return_debug: bool = False):
        """
        Записывает аудио и возвращает WAV bytes.
        Если return_debug=True, возвращает (bytes, stats) с метриками записи.
        """
        audio_data = self.record(duration_seconds)

        # Конвертируем в numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        max_amp = float(np.max(np.abs(audio_array))) if audio_array.size else 0.0
        rms = float(np.sqrt(np.mean(np.square(audio_array)))) if audio_array.size else 0.0

        # Сохраняем в WAV bytes
        wav_buffer = io.BytesIO()
        sf.write(wav_buffer, audio_array, self.audio_cfg.sample_rate, format="WAV")
        wav_buffer.seek(0)
        wav_bytes = wav_buffer.read()

        if return_debug:
            stats = {
                "samples": int(audio_array.size),
                "max_amp": round(max_amp, 6),
                "rms": round(rms, 6),
                "sample_rate": self.audio_cfg.sample_rate,
                "duration_sec": duration_seconds,
            }
            return wav_bytes, stats

        return wav_bytes
