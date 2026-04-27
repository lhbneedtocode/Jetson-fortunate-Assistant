from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FortuneRequest(BaseModel):
    question: str = Field(..., min_length=1)
    aspect: str | None = None
    sign_id: str | None = None


class FortuneResponse(BaseModel):
    sign_id: str
    sign_key: str
    aspect: str
    answer: str
    citations: list[dict[str, Any]]
    evidence: list[dict[str, Any]]