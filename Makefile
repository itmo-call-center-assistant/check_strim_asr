UV ?= uv
UV_CACHE_DIR ?= .uvcache
PYTHON ?= 3.11
CONFIG ?= configs/default.yaml
SAMPLE ?= data/test/test_10_seconds.mp3
REPORT ?= reports/report.json

.PHONY: sync test ruff run-sample hf-download-tone download-openstt env set-openrouter-key

sync:
	@echo "Syncing dependencies with uv (Python $(PYTHON))..."
	UV_CACHE_DIR=$(UV_CACHE_DIR) $(UV) sync --python $(PYTHON) --dev

env:
	@test -f .env || cp .env.example .env
	@echo ".env is ready (edit OPENROUTER_API_KEY if you use llm summary)"

set-openrouter-key:
	@[ -n "$(KEY)" ] || (echo "Usage: make set-openrouter-key KEY=your_api_key" && exit 1)
	@echo "Setting OPENROUTER_API_KEY in .env"
	@test -f .env || cp .env.example .env
	@grep -v '^OPENROUTER_API_KEY=' .env > .env.tmp || true
	@printf 'OPENROUTER_API_KEY=%s\n' "$(KEY)" >> .env.tmp
	@mv .env.tmp .env

test:
	UV_CACHE_DIR=$(UV_CACHE_DIR) $(UV) run --python $(PYTHON) pytest

ruff:
	UV_CACHE_DIR=$(UV_CACHE_DIR) $(UV) run --python $(PYTHON) ruff check .

run-sample:
	UV_CACHE_DIR=$(UV_CACHE_DIR) $(UV) run --python $(PYTHON) call-asr-rag --config $(CONFIG) --input $(SAMPLE) --out $(REPORT)

hf-download-tone:
	@echo "Pre-downloading T-one model from Hugging Face..."
	UV_CACHE_DIR=$(UV_CACHE_DIR) $(UV) run --python $(PYTHON) python -c "from huggingface_hub import snapshot_download; snapshot_download('t-tech/T-one')"

download-openstt:
	@echo "Downloading OpenSTT validation dataset..."
	mkdir -p data/openstt
	cd data/openstt && curl -O "https://azureopendatastorage.blob.core.windows.net/openstt/ru_open_stt_opus/archives/asr_calls_2_val.tar.gz"
	cd data/openstt && curl -O "https://azureopendatastorage.blob.core.windows.net/openstt/ru_open_stt_opus/manifests/asr_calls_2_val.csv"
	cd data/openstt && tar -xzf asr_calls_2_val.tar.gz
	@echo "OpenSTT validation dataset downloaded and extracted!"
