import os
from dataclasses import dataclass

from openai import OpenAI


@dataclass
class OpenRouterConfig:
    api_key_env: str
    model: str
    site_url: str = ""
    site_title: str = ""


class LLMSummarizer:
    def __init__(self, cfg: OpenRouterConfig):
        api_key = os.environ.get(cfg.api_key_env)
        if not api_key:
            raise RuntimeError(f"Environment variable {cfg.api_key_env} is required for LLMSummarizer")
        self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        self.cfg = cfg

    def summarize(self, text: str) -> str:
        headers = {}
        if self.cfg.site_url:
            headers["HTTP-Referer"] = self.cfg.site_url
        if self.cfg.site_title:
            headers["X-Title"] = self.cfg.site_title

        prompt = (
            "Сожми диалог в краткую 'память' для ассистента оператора.\n"
            "Только факты из текста. Не выдумывай.\n"
            "Сохраняй важные сущности (имена, номера, суммы, даты), намерение клиента, текущий статус.\n"
            "Ответ: короткими пунктами.\n\n"
            f"Текст:\n{text}"
        )

        resp = self.client.chat.completions.create(
            model=self.cfg.model,
            extra_headers=headers or None,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content or ""
