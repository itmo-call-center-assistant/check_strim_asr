# ruff: noqa: S101

import numpy as np

from call_asr_rag.audio.chunker import iter_chunks
from call_asr_rag.audio.pcm import float_to_int16_pcm


def test_iter_chunks_lengths_and_timestamps():
    sr = 8000
    chunk_ms = 200
    samples = np.zeros(sr, dtype=np.float32)
    chunks = list(iter_chunks(samples, sr, chunk_ms))
    assert len(chunks) == 5
    assert [c.t_ms for c in chunks] == [0, 200, 400, 600, 800]
    assert all(len(c.samples) == 1600 for c in chunks[:-1])
    assert len(chunks[-1].samples) == 1600


def test_float_to_int16_pcm_scaling_and_clipping():
    x = np.array([-2.0, -1.0, 0.0, 1.0, 2.0], dtype=np.float32)
    pcm = float_to_int16_pcm(x)
    ints = np.frombuffer(pcm, dtype=np.int16)
    assert ints.tolist() == [-32767, -32767, 0, 32767, 32767]
