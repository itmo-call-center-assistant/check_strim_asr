"""
API для Audio Service
"""

from datetime import datetime

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .audio_recorder_service import AudioRecorderService
from .config import AudioConfig, ToneASRConfig
from .schemas import (
    AudioRecordRequest,
    TranscriptionResponse,
)
from .tone_asr_service import ToneASRService


def create_audio_app(
    tone_cfg: ToneASRConfig | None = None,
    audio_cfg: AudioConfig | None = None,
) -> FastAPI:
    """Создает FastAPI приложение для Audio Service"""

    tone_cfg = tone_cfg or ToneASRConfig()
    audio_cfg = audio_cfg or AudioConfig()

    app = FastAPI(
        title="Audio Transcription Service",
        description="Сервис для транскрипции аудио через T-one (check_strim_asr)",
        version="1.0.0",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Инициализация сервисов
    asr_service = ToneASRService(config_path=tone_cfg.config_path, enable_summary=tone_cfg.enable_summary)
    audio_recorder = AudioRecorderService(audio_cfg)

    @app.on_event("startup")
    async def startup_event():
        """Инициализация при запуске"""
        print("[INFO] Starting Audio Transcription Service...")
        asr_service.load()
        # Синхронизируем аудио-параметры с моделью
        audio_cfg.sample_rate = asr_service.sample_rate
        if audio_cfg.chunk_size <= 0:
            audio_cfg.chunk_size = max(1, asr_service.chunk_size_samples)
        audio_recorder.audio_cfg = audio_cfg
        print("[INFO] Service started successfully")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Очистка при остановке"""
        audio_recorder.stop_recording()
        print("[INFO] Service stopped")

    @app.get("/")
    async def root():
        """Корневой endpoint"""
        return {
            "service": "Audio Transcription Service",
            "version": "1.0.0",
            "status": "running",
            "asr_loaded": asr_service.loaded,
            "sample_rate": asr_service.sample_rate,
            "chunk_ms": asr_service.chunk_ms,
        }

    @app.get("/health")
    async def health():
        """Health check"""
        return {
            "status": "healthy",
            "asr": "loaded" if asr_service.loaded else "not loaded",
            "pyaudio_available": audio_recorder.available,
            "sample_rate": asr_service.sample_rate,
            "chunk_ms": asr_service.chunk_ms,
        }

    @app.post("/transcribe", response_model=TranscriptionResponse)
    async def transcribe_audio(file: UploadFile):
        """Транскрибирует аудио файл через Tone ASR"""
        try:
            audio_bytes = await file.read()
            transcription, debug = asr_service.transcribe_bytes(audio_bytes)

            return TranscriptionResponse(
                transcription=transcription,
                status="success",
                timestamp=datetime.now().isoformat(),
                debug=debug,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.post("/record", response_model=TranscriptionResponse)
    async def record_audio(request: AudioRecordRequest):
        """Записывает аудио с микрофона и возвращает транскрипцию через Tone ASR"""
        if not audio_recorder.available:
            raise HTTPException(
                status_code=503,
                detail="PyAudio not available. Install: pip install pyaudio",
            )

        try:
            audio_recorder.start_recording()
            wav_bytes, capture_stats = audio_recorder.record_to_wav_bytes(request.duration_seconds, return_debug=True)
            audio_recorder.stop_recording()

            transcription, debug = asr_service.transcribe_bytes(wav_bytes)
            debug = debug or {}
            debug["capture"] = capture_stats

            return TranscriptionResponse(
                transcription=transcription,
                status="success",
                timestamp=datetime.now().isoformat(),
                debug=debug,
            )
        except Exception as e:
            audio_recorder.stop_recording()
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.post("/record-file")
    async def record_audio_file(request: AudioRecordRequest):
        """Записывает аудио с микрофона и возвращает WAV файл"""
        if not audio_recorder.available:
            raise HTTPException(status_code=503, detail="PyAudio not available")

        try:
            audio_recorder.start_recording()
            wav_bytes = audio_recorder.record_to_wav_bytes(request.duration_seconds)
            audio_recorder.stop_recording()

            import io

            return StreamingResponse(
                io.BytesIO(wav_bytes),
                media_type="audio/wav",
                headers={
                    "Content-Disposition": f"attachment; filename=recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                },
            )
        except Exception as e:
            audio_recorder.stop_recording()
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.websocket("/ws/transcribe")
    async def websocket_transcribe(websocket: WebSocket):
        """WebSocket для streaming транскрипции через Tone ASR"""
        await websocket.accept()

        try:
            while True:
                data = await websocket.receive_bytes()

                try:
                    transcription, debug = asr_service.transcribe_bytes(data)

                    await websocket.send_json(
                        {
                            "transcription": transcription,
                            "status": "success",
                            "debug": debug,
                        }
                    )
                except Exception as e:
                    await websocket.send_json({"error": str(e), "status": "error"})
        except WebSocketDisconnect:
            print("[INFO] WebSocket disconnected")

    return app


# Создаем приложение по умолчанию
tone_cfg = ToneASRConfig()
audio_cfg = AudioConfig()
app = create_audio_app(tone_cfg, audio_cfg)


if __name__ == "__main__":
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="Audio Transcription Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")  # noqa: S104
    parser.add_argument("--port", type=int, default=8001, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)
