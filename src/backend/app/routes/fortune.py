from __future__ import annotations

import random
from typing import Any

from fastapi import APIRouter, HTTPException

from app.schemas.fortune import FortuneRequest, FortuneResponse
from app.services.fortune_prompt import (
    ASPECT_ZH,
    build_fortune_prompt,
    build_fortune_retrieval_query,
    classify_aspect,
)
from app.services.fortune_retriever import FortuneRetriever

try:
    from app.services.llm_client import LLMClient
except Exception:
    LLMClient = None


router = APIRouter()

fortune_retriever = FortuneRetriever()
llm_client = LLMClient() if LLMClient is not None else None


def normalize_sign_id(value: str | int | None) -> str:
    if value is None or str(value).strip() == "":
        return f"{random.randint(1, 100):03d}"

    try:
        number = int(str(value).strip())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="sign_id must be an integer from 1 to 100") from exc

    if number < 1 or number > 100:
        raise HTTPException(status_code=400, detail="sign_id must be between 1 and 100")

    return f"{number:03d}"


def snippet(text: str, limit: int = 260) -> str:
    compact = " ".join(text.split())

    if len(compact) <= limit:
        return compact

    return compact[:limit].rstrip() + "..."


def generate_answer_flexibly(system_prompt: str, user_prompt: str) -> str:
    """
    Try to use the original project's LLMClient without assuming too much about its method signature.
    """
    if llm_client is None:
        return (
            "当前后端没有成功加载 LLMClient，因此这里只返回占位回答。"
            "请检查 app.services.llm_client 是否存在，以及 LLM 服务是否已启动。"
        )

    # Most likely method in this project
    if hasattr(llm_client, "generate_answer"):
        method = getattr(llm_client, "generate_answer")

        try:
            return method(system_prompt, user_prompt, max_tokens=420)
        except TypeError:
            pass

        try:
            return method(system_prompt=system_prompt, user_prompt=user_prompt, max_tokens=420)
        except TypeError:
            pass

        try:
            return method(prompt=user_prompt, system_prompt=system_prompt)
        except TypeError:
            pass

    # Other common names
    for method_name in ["generate", "chat", "complete"]:
        if hasattr(llm_client, method_name):
            method = getattr(llm_client, method_name)

            try:
                return method(system_prompt, user_prompt)
            except TypeError:
                pass

            try:
                return method(prompt=user_prompt)
            except TypeError:
                pass

    return (
        "已成功检索到签文资料，但当前 LLMClient 的调用方法无法匹配。"
        "请把 app/services/llm_client.py 的内容或报错发给我，我会帮你适配。"
    )


@router.post("/fortune", response_model=FortuneResponse)
def fortune(payload: FortuneRequest) -> FortuneResponse:
    question = payload.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="question cannot be empty")

    sign_id = normalize_sign_id(payload.sign_id)
    sign_key = f"wong_tai_sin_100_{sign_id}"

    aspect = payload.aspect or classify_aspect(question)

    if aspect not in ASPECT_ZH:
        aspect = "general"

    retrieval_query = build_fortune_retrieval_query(
        question=question,
        aspect=aspect,
        sign_id=sign_id,
    )

    try:
        chunks = fortune_retriever.retrieve(
            query=retrieval_query,
            sign_id=sign_id,
            aspect=aspect,
            top_k=6,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve fortune evidence: {exc}",
        ) from exc

    system_prompt, user_prompt = build_fortune_prompt(
        question=question,
        aspect=aspect,
        sign_id=sign_id,
        chunks=chunks,
    )

    answer = generate_answer_flexibly(system_prompt, user_prompt)

    citations: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []

    for chunk in chunks:
        meta = chunk.metadata

        citations.append(
            {
                "source": meta.get("source_url") or meta.get("source"),
                "sign_id": meta.get("sign_id"),
                "level": meta.get("level"),
                "story_title": meta.get("story_title"),
                "aspect": meta.get("aspect"),
                "aspect_label": meta.get("aspect_label"),
                "chunk_type": meta.get("chunk_type"),
                "score": chunk.score,
            }
        )

        evidence.append(
            {
                "snippet": snippet(chunk.text),
                "metadata": meta,
                "score": chunk.score,
                "distance": chunk.distance,
            }
        )

    return FortuneResponse(
        sign_id=sign_id,
        sign_key=sign_key,
        aspect=aspect,
        answer=answer,
        citations=citations,
        evidence=evidence,
    )