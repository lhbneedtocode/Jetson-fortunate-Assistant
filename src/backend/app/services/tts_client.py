from __future__ import annotations

import os

import requests


class TTSClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or os.getenv("TTS_BASE_URL", "http://localhost:8880/v1")

    def synthesize(
        self,
        text: str,
        voice: str = "af_bella",
        model: str = "kokoro",
        response_format: str = "mp3",
    ) -> bytes:
        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": response_format,
        }
        response = requests.post(
            f"{self.base_url}/audio/speech",
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        return response.content
