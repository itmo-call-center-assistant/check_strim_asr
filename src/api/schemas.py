"""
Схемы данных для API
"""

from pydantic import BaseModel, Field


class TranscriptionRequest(BaseModel):
    """Запрос на транскрипцию"""

    audio_format: str | None = Field("wav", description="Формат аудио")
    sample_rate: int | None = Field(8000, description="Частота дискретизации")


class TranscriptionResponse(BaseModel):
    """Ответ с транскрипцией"""

    transcription: str = Field(..., description="Транскрибированный текст")
    status: str = Field("success", description="Статус операции")
    timestamp: str = Field(..., description="Временная метка")
    debug: dict | None = Field(None, description="Отладочная информация (фразы, события)")


class AudioRecordRequest(BaseModel):
    """Запрос на запись аудио"""

    duration_seconds: float = Field(5.0, description="Длительность записи в секундах", ge=0.5, le=30.0)
    sample_rate: int = Field(8000, description="Частота дискретизации")


class AudioRecordResponse(BaseModel):
    """Ответ на запись аудио"""

    transcription: str | None = Field(None, description="Транскрипция (если запрошена)")
    audio_file: str | None = Field(None, description="Путь к файлу (если сохранен)")
    status: str = Field("success", description="Статус операции")
    timestamp: str = Field(..., description="Временная метка")
