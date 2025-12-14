"""
Инициализация T-one (tone) streaming модели.

Требует установленный пакет `tone` и кешированную модель `t-tech/T-one`
(скачивается через Hugging Face при первом запуске).
"""

from tone import StreamingCTCPipeline
from tone.decoder import GreedyCTCDecoder
from tone.logprob_splitter import StreamingLogprobSplitter
from tone.onnx_wrapper import StreamingCTCModel

from .streaming import ToneASR


def build_tone_asr() -> ToneASR:
    model = StreamingCTCModel.from_hugging_face()
    splitter = StreamingLogprobSplitter()
    decoder = GreedyCTCDecoder()
    pipeline = StreamingCTCPipeline(model=model, logprob_splitter=splitter, decoder=decoder)
    return ToneASR(pipeline=pipeline, sample_rate=model.SAMPLE_RATE, chunk_size=model.AUDIO_CHUNK_SAMPLES)
