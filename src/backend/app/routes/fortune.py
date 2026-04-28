from __future__ import annotations

import random
from typing import Any

from fastapi import APIRouter, HTTPException

from app.schemas.fortune import FortuneRequest, FortuneResponse
from app.services.fortune_history import append_history, build_user_profile
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
STYLE_INSTRUCTIONS = {
    "modern": (
        "输出风格：现代口语。"
        "要求：用普通人容易理解的话解释签文，少用玄学词，句子自然直接。"
        "每段都要像日常建议一样清楚，不要文绉绉。"
    ),
    "traditional": (
        "输出风格：传统古风。"
        "要求：语言庄重含蓄，可适度使用古典表达，如“此签示意”“宜守不宜躁”“凡事贵在持正”。"
        "但不能堆砌文言，必须让现代用户能看懂。"
    ),
    "healing": (
        "输出风格：温柔治愈。"
        "要求：语气温和、安抚、支持，先接住用户的不确定和焦虑。"
        "多使用“不要太责怪自己”“可以慢慢来”“先稳住节奏”等表达。"
        "行动建议要鼓励用户从小步骤开始，避免制造压力。"
    ),
    "sharp": (
        "输出风格：犀利吐槽。"
        "要求：表达可以直接、幽默、有一点吐槽感，例如指出“别被幻想画大饼”“别只感动自己不投简历”。"
        "但不能侮辱用户、不能人身攻击，吐槽必须善意，最后要给出可执行建议。"
    ),
    "rational": (
        "输出风格：理性分析。"
        "要求：尽量减少情绪化安慰，重点拆解现实变量、风险、可控因素和下一步行动。"
        "建议使用“从证据看”“风险点是”“可控变量是”“下一步建议”这类分析表达。"
        "行动建议要具体到求职材料、投递节奏、复盘反馈、信息收集等现实动作。"
    ),
}


def get_style_instruction(style: str | None) -> str:
    style_key = style or "modern"
    return STYLE_INSTRUCTIONS.get(style_key, STYLE_INSTRUCTIONS["modern"])

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
            return method(system_prompt, user_prompt, max_tokens=700)
        except TypeError:
            pass

        try:
            return method(system_prompt=system_prompt, user_prompt=user_prompt, max_tokens=700)
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
    style_instruction = get_style_instruction(getattr(payload, "style", "modern"))

    system_prompt = f"""{system_prompt}

    【当前用户选择的解签风格】
    {getattr(payload, "style", "modern")}

    【表达风格强制要求】
    {style_instruction}

    请注意：
    1. 必须明显体现所选风格，不能所有风格都写成同一种语气。
    2. 保持固定结构：【抽签结果】【白话解释】【针对问题的解读】【行动建议】【提醒】。
    3. 但每个小节里的措辞、语气、侧重点必须符合所选风格。
    4. 解签内容不能宣称可以决定现实结果，只能作为传统文化解释、心理疏导和自我反思参考。
    """
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
    first_meta = {}
    try:
        if evidence and isinstance(evidence, list):
            first_item = evidence[0]
            if isinstance(first_item, dict):
                first_meta = first_item.get("metadata") or {}
    except Exception:
        first_meta = {}

    try:
        append_history({
            "question": payload.question,
            "aspect": aspect,
            "sign_id": sign_id,
            "sign_key": sign_key,
            "level": first_meta.get("level"),
            "story_title": first_meta.get("story_title"),
            "style": getattr(payload, "style", "modern"),
        })
    except Exception as exc:
        print("[WARN] append fortune history failed:", exc)
    return FortuneResponse(
        sign_id=sign_id,
        sign_key=sign_key,
        aspect=aspect,
        answer=answer,
        citations=citations,
        evidence=evidence,
    )

@router.get("/fortune/profile")
def fortune_profile():
    return build_user_profile(limit=200)
