from collections.abc import Iterator
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AudioChunk:
    samples: np.ndarray
    t_ms: int


def iter_chunks(waveform: np.ndarray, sample_rate: int, chunk_ms: int) -> Iterator[AudioChunk]:
    hop = int(sample_rate * (chunk_ms / 1000.0))
    if hop <= 0:
        raise ValueError("chunk_ms results in empty chunk")

    t_ms = 0
    for i in range(0, len(waveform), hop):
        chunk = waveform[i : i + hop].astype(np.float32, copy=False)
        yield AudioChunk(samples=chunk, t_ms=t_ms)
        t_ms += chunk_ms
