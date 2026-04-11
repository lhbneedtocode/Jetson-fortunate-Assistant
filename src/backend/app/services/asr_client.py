from __future__ import annotations

import os
from typing import Any

import requests


class ASRClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or os.getenv("ASR_BASE_URL", "http://localhost:5092/v1")

    def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "input.wav",
        model: str = "faster-whisper",
    ) -> dict[str, Any]:
        files = {
            "file": (filename, audio_bytes, "application/octet-stream"),
        }
        data = {"model": model}
        response = requests.post(
            f"{self.base_url}/audio/transcriptions",
            files=files,
            data=data,
            timeout=120,
        )
        response.raise_for_status()
        return response.json()
