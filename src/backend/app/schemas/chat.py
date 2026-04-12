from pydantic import BaseModel, Field


class Citation(BaseModel):
    source: str
    page: int | None = None


class ChatTurn(BaseModel):
    role: str
    content: str


class Evidence(BaseModel):
    source: str
    page: int | None = None
    score: float | None = None
    snippet: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    history: list[ChatTurn] = []
    synthesize_speech: bool = False
    voice: str = "af_bella"


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    evidence: list[Evidence] = []
    refusal: bool = False
    transcript: str | None = None
    audio_base64: str | None = None
