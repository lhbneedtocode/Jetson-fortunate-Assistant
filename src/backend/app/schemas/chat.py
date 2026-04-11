from pydantic import BaseModel, Field


class Citation(BaseModel):
    source: str
    page: int | None = None


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    synthesize_speech: bool = False
    voice: str = "af_bella"


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    refusal: bool = False
    transcript: str | None = None
    audio_base64: str | None = None
