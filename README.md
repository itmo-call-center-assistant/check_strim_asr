# Call ASR + Pause + Summarize (MVP)

MVP пайплайн для офлайн-прогона звонков (MP3 → чанки → ASR T-one → Pause Driver → Trigger → Summary) с запуском через `uv`.

## Быстрый старт

```bash
# 1) Установить зависимости
make sync

# 2) Подготовить .env с OpenRouter ключом (если нужен LLM summary)
make env
# или
make set-openrouter-key KEY=sk-...

# 3) Запустить на аудиофайле
UV_CACHE_DIR=.uvcache uv run call-asr-rag \
  --config configs/default.yaml \
  --input path/to/call.mp3 \
  --out reports/report.json
```

> Для режима `summary.impl: llm` нужен `OPENROUTER_API_KEY`. Для `mock` сеть не нужна.
> По умолчанию CLI пишет отчёт в `reports/report.json`.

## Что делает пайплайн

- Декодирует MP3 → моно float32, ресемпл до `audio.sample_rate`.
- Бьёт на чанки (`audio.chunk_ms`), скармливает в T-one ASR (стриминговая оболочка, подключается в `asr/tone_lib`).
- Pause Driver: `phrase` — ставит паузы по границам распознанных фраз ASR; `vad` — по VAD (тишина/речь) с параметрами из `vad`; `hybrid` — сочетает VAD и фразовые границы.
- Trigger: сейчас `NoopTrigger` (всегда skip).
- Summarizer: `MockSummarizer` — офлайн-заглушка; `LLMSummarizer` (OpenRouter) — реальная сводка через LLM, нужен `OPENROUTER_API_KEY`.
- Итог в `report.json`: фразы, события пауз, решения триггера, отладочный summary.

### T-one (tone)

- В зависимостях уже есть `tone` из GitHub.
- Модель `t-tech/T-one` подтянется с Hugging Face при первом запуске. Чтобы после скачивания работать без сети, поставьте `HF_HUB_OFFLINE=1`.
- Чтобы скачать заранее: `hf download t-tech/T-one`.
- Под свой способ загрузки/устройство/precision правьте `src/call_asr_rag/asr/tone_lib/model.py` и стриминг-обёртку в `tone_lib/streaming.py`.

## Конфиги

Готовые пресеты в `configs/`:

- `default.yaml` — hybrid.
- `pause_phrase.yaml` — только `phrase`.
- `pause_vad.yaml` — только VAD.
- `pause_hybrid.yaml` — hybrid с изменёнными параметрами.

## Makefile

- `make sync` — `uv sync --python 3.11 --dev`
- `make test` — прогон pytest.
- `make run-sample` — прогон пайплайна на `data/test/test_10_seconds.mp3` с конфигом `configs/default.yaml`, результат в `reports/report.json`.
- `make hf-download-tone` — заранее скачивает модель `t-tech/T-one` в кэш HF.
- `make download-openstt` — качает и распаковывает OpenSTT `asr_calls_2_val` в `data/openstt`.

## Структура

См. `src/call_asr_rag/`:

- `audio/` — декодер MP3, чанкер, PCM конвертация.
- `asr/` — интерфейсы + заглушка T-one (интеграцию подключайте в `tone_lib/`).
- `vad/` — WebRTC VAD враппер.
- `pause/` — драйверы пауз.
- `trigger/` — NoopTrigger.
- `summarizer/` — Mock/LLM.
- `context/` — хранение full context.
- `pipeline/` — раннер и запись отчёта.
- `cli.py` — точка входа `call-asr-rag`.

## Примечания

- Для MP3 нужен установленный `ffmpeg` (используется `pydub`).
- Если нужно адаптировать T-one под свою среду (девайс, precision, метаданные), то следует поменять `asr/tone_lib/model.py` и `tone_lib/streaming.py`.
