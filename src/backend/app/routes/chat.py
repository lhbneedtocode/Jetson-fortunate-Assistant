import base64

from fastapi import APIRouter, File, Form, UploadFile

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.asr_client import ASRClient
from app.services.llm_client import LLMClient
from app.services.prompt_builder import build_rag_prompt
from app.services.retriever import Retriever
from app.services.tts_client import TTSClient

router = APIRouter()
retriever = Retriever()
llm_client = LLMClient()
asr_client = ASRClient()
tts_client = TTSClient()


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    return _run_rag_flow(
        question=payload.question,
        transcript=None,
        synthesize_speech=payload.synthesize_speech,
        voice=payload.voice,
    )


@router.post("/chat/audio", response_model=ChatResponse)
async def chat_audio(
    file: UploadFile = File(...),
    synthesize_speech: bool = Form(True),
    voice: str = Form("af_bella"),
) -> ChatResponse:
    audio_bytes = await file.read()
    transcription = asr_client.transcribe(
        audio_bytes=audio_bytes,
        filename=file.filename or "input.wav",
    )
    transcript = str(transcription.get("text", "")).strip()
    return _run_rag_flow(
        question=transcript,
        transcript=transcript,
        synthesize_speech=synthesize_speech,
        voice=voice,
    )


def _run_rag_flow(
    question: str,
    transcript: str | None,
    synthesize_speech: bool,
    voice: str,
) -> ChatResponse:
    chunks = retriever.retrieve(question, top_k=3)
    system_prompt, user_prompt = build_rag_prompt(question, chunks)
    answer = llm_client.generate_answer(system_prompt, user_prompt)
    refusal = _is_refusal(answer, chunks)
    audio_base64 = None
    if synthesize_speech and answer:
        audio_bytes = tts_client.synthesize(answer, voice=voice)
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    return ChatResponse(
        answer=answer,
        citations=[{"source": chunk.source, "page": chunk.page} for chunk in chunks],
        refusal=refusal,
        transcript=transcript,
        audio_base64=audio_base64,
    )


def _is_refusal(answer: str, chunks) -> bool:
    if not chunks:
        return True
    lowered = answer.lower()
    refusal_markers = [
        "cannot confirm",
        "not enough evidence",
        "insufficient",
        "unable to confirm",
        "do not have enough information",
    ]
    return any(marker in lowered for marker in refusal_markers)
