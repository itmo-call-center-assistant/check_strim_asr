import pathlib

import numpy as np
from pydub import AudioSegment


def decode_mp3_to_mono(
    path: str | pathlib.Path,
    target_sample_rate: int,
) -> tuple[np.ndarray, int]:
    """
    Decode an MP3 file to mono float32 waveform and resample to target_sample_rate.
    Requires ffmpeg to be installed (pydub backend).
    """
    audio = AudioSegment.from_file(path)  # type: ignore[arg-type]
    audio = audio.set_channels(1).set_frame_rate(target_sample_rate)

    samples = np.array(audio.get_array_of_samples()).astype(np.float32)
    if audio.sample_width == 2:
        samples /= 32768.0
    elif audio.sample_width == 4:
        samples /= 2147483648.0
    else:
        max_val = float(2 ** (8 * audio.sample_width - 1))
        samples /= max_val

    return samples, audio.frame_rate
