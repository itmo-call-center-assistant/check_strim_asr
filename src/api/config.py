"""
Конфигурация для Call-Center Service
"""

import os
from dataclasses import dataclass
from pathlib import Path

# Загрузка переменных окружения
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


@dataclass
class AudioConfig:
    """Конфигурация для аудио обработки"""

    sample_rate: int = int(os.getenv("AUDIO_SAMPLE_RATE", "8000"))
    chunk_size: int = int(os.getenv("AUDIO_CHUNK_SIZE", "0"))  # 0 -> will be aligned with ASR
    max_duration_seconds: float = float(os.getenv("AUDIO_MAX_DURATION", "25.0"))


@dataclass
class ToneASRConfig:
    """Конфигурация check_strim_asr (T-one)"""

    config_path: Path = Path(
        os.getenv(
            "ASR_CONFIG_PATH",
            Path(__file__).resolve().parents[2] / "configs" / "default.yaml",
        )
    )
    enable_summary: bool = bool(int(os.getenv("ASR_ENABLE_SUMMARY", "0")))


@dataclass
class ServiceConfig:
    """Общая конфигурация сервисов"""

    audio_service_port: int = int(os.getenv("AUDIO_SERVICE_PORT", "8001"))
    rag_service_port: int = int(os.getenv("RAG_SERVICE_PORT", "8002"))
    frontend_port: int = int(os.getenv("FRONTEND_PORT", "8080"))
