from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.schemas.fortune import (
    FortuneDrawRequest,
    FortuneDrawResponse,
    FortuneInterpretRequest,
    FortuneRequest,
    FortuneResponse,
)
from app.services.fortune_ai import analyze_question, parse_ai_report, report_to_answer_text
from app.services.fortune_drawer import draw_sign, normalize_sign_id
from app.services.fortune_history import append_history, build_user_profile
from app.services.fortune_radar import build_five_dimension_radar
from app.services.fortune_prompt import (
    ASPECT_ZH,
    build_structured_fortune_prompt,
    build_fortune_retrieval_query,
    classify_aspect,
)
from app.services.fortune_retriever import FortuneRetriever
from app.services.fortune_similarity import build_similar_signs

try:
    from app.services.aspect_classifier import predict_question_aspect
except Exception:
    predict_question_aspect = None

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


fortune_retriever = FortuneRetriever()
llm_client = LLMClient() if LLMClient is not None else None


def get_style_instruction(style: str | None) -> str:
    style_key = style or "modern"
    return STYLE_INSTRUCTIONS.get(style_key, STYLE_INSTRUCTIONS["modern"])


def snippet(text: str, limit: int = 700) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[:limit].rstrip() + "..."


def generate_answer_flexibly(system_prompt: str, user_prompt: str) -> str:
    """Call the original project's LLMClient while tolerating signature differences."""
    if llm_client is None:
        return (
            "当前后端没有成功加载 LLMClient，因此这里只返回占位回答。"
            "请检查 app.services.llm_client 是否存在，以及 LLM 服务是否已启动。"
        )

    if hasattr(llm_client, "generate_answer"):
        method = getattr(llm_client, "generate_answer")

        try:
            return method(system_prompt, user_prompt, max_tokens=1200)
        except TypeError:
            pass

        try:
            return method(system_prompt=system_prompt, user_prompt=user_prompt, max_tokens=1200)
        except TypeError:
            pass

        try:
            return method(prompt=user_prompt, system_prompt=system_prompt)
        except TypeError:
            pass

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


def should_auto_use_aspect(aspect: str | None) -> bool:
    """Whether to use the trained question aspect classifier.

    Frontend can send aspect="auto" or leave aspect empty. Manual selections
    such as career/study/love/... are still respected.
    """
    value = str(aspect or "").strip().lower()
    return value in {"", "auto", "none", "null", "unknown", "智能识别", "自动识别"}


ASPECT_ALIAS = {
    # Classifier label -> existing fortune prompt aspect key
    "relationship": "love",
    "relation": "love",
    "love": "love",
    "career": "career",
    "study": "study",
    "wealth": "wealth",
    "health": "health",
    "general": "general",
    # UI / older aliases
    "family": "family",
    "travel": "travel",
    "business": "business",
    "self": "self",
}


def coerce_aspect_key(aspect: str | None) -> str:
    value = str(aspect or "").strip().lower()
    value = ASPECT_ALIAS.get(value, value)
    if value not in ASPECT_ZH:
        return "general"
    return value


def normalize_prediction(raw_prediction: dict[str, Any]) -> dict[str, Any]:
    """Normalize classifier output so it uses the project's existing aspect keys.

    The offline classifier uses relationship, while this project historically uses
    love for the same concept. This adapter keeps the backend compatible.
    """
    raw_aspect = raw_prediction.get("aspect") or "general"
    aspect = coerce_aspect_key(raw_aspect)

    probabilities = raw_prediction.get("probabilities") or []
    normalized_probs: list[dict[str, Any]] = []
    if isinstance(probabilities, list):
        for item in probabilities:
            if not isinstance(item, dict):
                continue
            item_aspect = coerce_aspect_key(item.get("aspect"))
            normalized_probs.append(
                {
                    "aspect": item_aspect,
                    "label": ASPECT_ZH.get(item_aspect, item.get("label") or item_aspect),
                    "probability": item.get("probability", 0),
                }
            )

    return {
        "aspect": aspect,
        "label": ASPECT_ZH.get(aspect, "综合"),
        "confidence": raw_prediction.get("confidence", 0),
        "probabilities": normalized_probs,
        "source": raw_prediction.get("source", "unknown"),
    }


def resolve_question_aspect(question: str | None, requested_aspect: str | None) -> tuple[str, dict[str, Any]]:
    """Resolve the effective aspect used by retrieval, radar and history.

    If requested_aspect is auto/empty, use the trained classifier. Otherwise,
    respect the user's manual selection.
    """
    requested = str(requested_aspect or "auto").strip()

    if predict_question_aspect is None:
        raw_prediction = {
            "aspect": classify_aspect(question or ""),
            "label": ASPECT_ZH.get(classify_aspect(question or ""), "综合"),
            "confidence": 0.0,
            "probabilities": [],
            "source": "prompt_keyword_fallback",
        }
    else:
        try:
            raw_prediction = predict_question_aspect(question or "")
        except Exception as exc:
            print("[WARN] question aspect classifier failed:", exc)
            fallback_aspect = classify_aspect(question or "")
            raw_prediction = {
                "aspect": fallback_aspect,
                "label": ASPECT_ZH.get(fallback_aspect, "综合"),
                "confidence": 0.0,
                "probabilities": [],
                "source": "exception_fallback",
            }

    prediction = normalize_prediction(raw_prediction)

    if should_auto_use_aspect(requested):
        resolved_aspect = prediction.get("aspect") or "general"
        auto_used = True
    else:
        resolved_aspect = coerce_aspect_key(requested)
        auto_used = False

    aspect_prediction = {
        "requested_aspect": requested,
        "resolved_aspect": resolved_aspect,
        "resolved_aspect_label": ASPECT_ZH.get(resolved_aspect, "综合"),
        "auto_used": auto_used,
        "aspect": prediction.get("aspect"),
        "label": prediction.get("label"),
        "confidence": prediction.get("confidence"),
        "probabilities": prediction.get("probabilities", []),
        "source": prediction.get("source"),
    }
    return resolved_aspect, aspect_prediction


def normalize_aspect(question: str, aspect: str | None) -> str:
    """Backward-compatible aspect normalizer."""
    resolved_aspect, _ = resolve_question_aspect(question, aspect)
    return resolved_aspect


def build_fortune_response(
    *,
    question: str,
    sign_id: str,
    aspect: str | None,
    style: str | None,
    draw_id: str | None = None,
) -> FortuneResponse:
    """Shared interpretation pipeline used by /fortune and /fortune/interpret."""
    question = question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question cannot be empty")

    try:
        normalized_sign_id = normalize_sign_id(sign_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    sign_key = f"wong_tai_sin_100_{normalized_sign_id}"
    normalized_aspect, aspect_prediction = resolve_question_aspect(question, aspect)
    style = style or "modern"

    retrieval_query = build_fortune_retrieval_query(
        question=question,
        aspect=normalized_aspect,
        sign_id=normalized_sign_id,
    )

    try:
        chunks = fortune_retriever.retrieve(
            query=retrieval_query,
            sign_id=normalized_sign_id,
            aspect=normalized_aspect,
            top_k=6,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve fortune evidence: {exc}",
        ) from exc

    question_analysis = analyze_question(question, normalized_aspect)
    question_analysis = question_analysis or {}
    question_analysis.update(
        {
            "aspect_prediction": aspect_prediction,
            "requested_aspect": aspect_prediction.get("requested_aspect"),
            "resolved_aspect": aspect_prediction.get("resolved_aspect"),
            "resolved_aspect_label": aspect_prediction.get("resolved_aspect_label"),
            "auto_aspect_used": aspect_prediction.get("auto_used"),
            "predicted_aspect": aspect_prediction.get("aspect"),
            "predicted_aspect_label": aspect_prediction.get("label"),
            "aspect_confidence": aspect_prediction.get("confidence"),
            "aspect_classifier_source": aspect_prediction.get("source"),
        }
    )

    system_prompt, user_prompt = build_structured_fortune_prompt(
        question=question,
        aspect=normalized_aspect,
        sign_id=normalized_sign_id,
        chunks=chunks,
        style=style,
        question_analysis=question_analysis,
    )

    # Keep a final style hint here, even though build_structured_fortune_prompt already uses style.
    # This makes the behavior stable if the prompt builder is later simplified.
    style_instruction = get_style_instruction(style)
    system_prompt = f"""{system_prompt}

【表达风格补充要求】
{style_instruction}
""".strip()

    raw_answer = generate_answer_flexibly(system_prompt, user_prompt)
    ai_report, parsed_ok = parse_ai_report(raw_answer)
    answer = report_to_answer_text(ai_report)

    citations: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []

    for chunk in chunks:
        meta = chunk.metadata or {}

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

    first_meta: dict[str, Any] = {}
    if evidence and isinstance(evidence[0], dict):
        first_meta = evidence[0].get("metadata") or {}

    try:
        sign_chunks = fortune_retriever.get_sign_chunks(normalized_sign_id)
    except Exception as exc:
        print("[WARN] load sign chunks for radar failed:", exc)
        sign_chunks = chunks

    try:
        radar_analysis = build_five_dimension_radar(
            sign_id=normalized_sign_id,
            aspect=normalized_aspect,
            question=question,
            chunks=sign_chunks or chunks,
        )
    except Exception as exc:
        print("[WARN] build five-dimension radar failed:", exc)
        radar_analysis = None

    try:
        similar_signs = build_similar_signs(
            fortune_retriever,
            sign_id=normalized_sign_id,
            aspect=normalized_aspect,
            question=question,
            top_k=4,
        )
    except Exception as exc:
        print("[WARN] build similar signs failed:", exc)
        similar_signs = []

    try:
        radar_average = None
        radar_dimensions: list[dict[str, Any]] = []
        if isinstance(radar_analysis, dict):
            radar_average = radar_analysis.get("average_score") or radar_analysis.get("overall_score")
            raw_dimensions = radar_analysis.get("dimensions")
            if isinstance(raw_dimensions, list):
                for dim in raw_dimensions[:8]:
                    if isinstance(dim, dict):
                        radar_dimensions.append({
                            "key": dim.get("key"),
                            "label": dim.get("label"),
                            "score": dim.get("score"),
                            "confidence": dim.get("confidence"),
                        })

        append_history(
            {
                "question": question,
                "aspect": normalized_aspect,
                "sign_id": normalized_sign_id,
                "sign_key": sign_key,
                "level": first_meta.get("level"),
                "story_title": first_meta.get("story_title"),
                "style": style,
                "draw_id": draw_id,
                "emotion": question_analysis.get("emotion"),
                "question_type": question_analysis.get("question_type"),
                "keywords": question_analysis.get("keywords", []),
                "aspect_prediction": aspect_prediction,
                "overall_score": radar_average,
                "radar_average": radar_average,
                "radar_dimensions": radar_dimensions,
            }
        )
    except Exception as exc:
        print("[WARN] append fortune history failed:", exc)

    story_title = first_meta.get("story_title")
    return FortuneResponse(
        sign_id=normalized_sign_id,
        sign_key=sign_key,
        aspect=normalized_aspect,
        resolved_aspect=normalized_aspect,
        aspect_prediction=aspect_prediction,
        answer=answer,
        ai_report=ai_report,
        question_analysis=question_analysis,
        citations=citations,
        evidence=evidence,
        level=first_meta.get("level"),
        title=story_title,
        story_title=story_title,
        radar_analysis=radar_analysis,
        similar_signs=similar_signs,
        draw_id=draw_id,
        metrics={
            "llm_json_parsed": parsed_ok,
            "flow": "two_stage_interpret",
        },
    )


@router.post("/fortune/draw", response_model=FortuneDrawResponse)
def fortune_draw(payload: FortuneDrawRequest) -> FortuneDrawResponse:
    """Stage 1: draw a sign only; do not call RAG or LLM."""
    try:
        card = draw_sign(payload.sign_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    aspect, aspect_prediction = resolve_question_aspect(payload.question or "", payload.aspect)
    return FortuneDrawResponse(
        **card,
        aspect=aspect,
        resolved_aspect=aspect,
        aspect_prediction=aspect_prediction,
        question=payload.question,
    )


@router.post("/fortune/interpret", response_model=FortuneResponse)
def fortune_interpret(payload: FortuneInterpretRequest) -> FortuneResponse:
    """Stage 2: interpret an already drawn sign."""
    return build_fortune_response(
        question=payload.question,
        sign_id=payload.sign_id,
        aspect=payload.aspect,
        style=payload.style,
        draw_id=payload.draw_id,
    )


@router.post("/fortune", response_model=FortuneResponse)
def fortune(payload: FortuneRequest) -> FortuneResponse:
    """Backward-compatible one-step endpoint.

    Old UI/tests can still call this endpoint. New UI should call /draw first,
    then /interpret after the user clicks the drawn sign card.
    """
    sign_id = normalize_sign_id(payload.sign_id)
    return build_fortune_response(
        question=payload.question,
        sign_id=sign_id,
        aspect=payload.aspect,
        style=payload.style,
        draw_id=None,
    )


@router.get("/fortune/profile")
def fortune_profile():
    return build_user_profile(limit=200)
