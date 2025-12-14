from typing import Protocol

import numpy as np


class StreamingASR(Protocol):
    def feed_chunk(self, chunk_f32: np.ndarray) -> list[str]: ...

    def finalize(self) -> list[str]: ...
