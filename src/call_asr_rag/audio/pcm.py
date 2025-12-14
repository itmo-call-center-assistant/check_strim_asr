import numpy as np


def float_to_int16_pcm(x: np.ndarray) -> bytes:
    clipped = np.clip(x, -1.0, 1.0)
    y = (clipped * 32767.0).astype(np.int16)
    return y.tobytes()
