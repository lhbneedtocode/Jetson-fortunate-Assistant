from __future__ import annotations

import os

from openai import OpenAI


DEFAULT_MODEL = "/root/.cache/huggingface/Qwen3-4B-quantized.w4a16"


class LLMClient:
    def __init__(
        self,
        api_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_url = api_url or os.getenv("LLM_BASE_URL", "http://localhost:8000/v1")
        self.model = model or os.getenv("LLM_MODEL", DEFAULT_MODEL)
        self.client = OpenAI(
            base_url=self.api_url,
            api_key="dummy",
        )

    def generate_answer(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 300,
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        message = response.choices[0].message.content or ""
        return message.strip()
