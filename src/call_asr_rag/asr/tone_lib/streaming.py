import logging
from typing import Any

import numpy as np

from .types import Phrase


class ToneASR:
    def __init__(self, pipeline: Any, sample_rate: int, chunk_size: int):
        self.pipeline = pipeline
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.state = None

    def reset(self) -> None:
        """Сбросить состояние стриминга после ошибки/звонка."""
        self.state = None

    def _prepare_chunk(self, chunk_f32: np.ndarray) -> np.ndarray:
        arr = np.clip(chunk_f32, -1.0, 1.0)
        # tone.onnx_wrapper требует int32
        arr = (arr * 32767.0).astype(np.int32, copy=False)
        if len(arr) < self.chunk_size:
            # Финальный чанк может быть короче — дополняем нулями.
            arr = np.pad(arr, (0, self.chunk_size - len(arr)), mode="constant")
        elif len(arr) > self.chunk_size:
            raise ValueError(
                f"Длина чанка {len(arr)} не совпадает с ожидаемой {self.chunk_size} сэмплов "
                "— проверьте chunk_ms и sample_rate относительно модели."
            )
        return arr  # int16, длина ровно chunk_size

    def feed_chunk(self, chunk_f32: np.ndarray) -> list[str]:
        try:
            prepared = self._prepare_chunk(chunk_f32)
            phrases, self.state = self.pipeline.forward(prepared, self.state)
            return [p.text if isinstance(p, Phrase) else str(p) for p in phrases]
        except Exception:
            logging.getLogger(__name__).exception("ToneASR.forward failed, resetting state")
            self.reset()
            raise

    def finalize(self) -> list[str]:
        try:
            phrases, _ = self.pipeline.finalize(self.state)
            return [p.text if isinstance(p, Phrase) else str(p) for p in phrases]
        except Exception:
            logging.getLogger(__name__).exception("ToneASR.finalize failed, resetting state")
            self.reset()
            raise
