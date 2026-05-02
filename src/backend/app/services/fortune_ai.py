from __future__ import annotations

import json
import re
from typing import Any

from app.services.fortune_prompt import ASPECT_ZH


EMOTION_KEYWORDS = {
    "焦虑": ["焦虑", "迷茫", "压力", "不安", "担心", "害怕", "慌", "烦", "崩", "内耗", "失眠"],
    "犹豫": ["要不要", "是否", "该不该", "纠结", "选择", "坚持", "放弃", "转", "换"],
    "期待": ["希望", "机会", "能不能", "会不会", "想要", "期待", "成功", "offer", "上岸"],
    "困惑": ["怎么办", "如何", "怎么", "为什么", "看不清", "不知道", "方向"],
}

QUESTION_TYPE_KEYWORDS = {
    "选择型": ["要不要", "是否", "该不该", "选", "选择", "继续", "放弃", "换", "转"],
    "趋势型": ["运势", "未来", "后面", "接下来", "会不会", "能不能", "发展", "结果"],
    "建议型": ["怎么办", "怎么做", "如何", "建议", "应该", "方向"],
    "结果型": ["能否", "能不能", "会不会", "有没有", "可不可以", "成功", "上岸", "录取", "offer"],
}

KEYWORD_CANDIDATES = [
    "工作", "实习", "求职", "面试", "offer", "升职", "跳槽", "科研", "论文", "毕业",
    "考试", "学业", "申请", "成绩", "感情", "恋爱", "复合", "分手", "婚姻", "人际",
    "财运", "投资", "收入", "健康", "身体", "焦虑", "选择", "坚持", "放弃", "机会", "方向",
]

DEFAULT_REPORT = {
    "plain_summary": "这支签提示你先稳定心态，观察现实条件，再逐步推进，不宜被一时情绪带着做决定。",
    "traditional_explanation": "从传统签意看，此签更强调时机、节奏和自我调整，遇事宜谨慎，不宜急躁冒进。",
    "answer_to_question": "结合你的问题，目前更适合先把可控部分做好，再根据外部反馈判断下一步。",
    "action_suggestions": [
        "先把当前最重要的一件事拆成可以执行的小步骤。",
        "主动收集反馈，确认问题到底卡在能力、信息还是时机。",
        "给自己设置一个观察周期，避免在情绪最高点做重大决定。",
    ],
    "risk_warning": "不要把签文当作现实结果预测，也不要用它替代医学、法律、投资或职业决策。",
    "comfort_message": "眼前的不确定并不代表没有转机，先稳住节奏，很多变化会在行动中逐渐清楚。",
}


def analyze_question(question: str, aspect: str | None = None) -> dict[str, Any]:
    """Lightweight question-understanding layer for the report and prompt."""
    q = (question or "").strip()
    lowered = q.lower()

    emotion_scores: dict[str, int] = {}
    for label, words in EMOTION_KEYWORDS.items():
        score = sum(1 for word in words if word.lower() in lowered)
        if score:
            emotion_scores[label] = score
    emotion = max(emotion_scores, key=emotion_scores.get) if emotion_scores else "平静/求稳"

    type_scores: dict[str, int] = {}
    for label, words in QUESTION_TYPE_KEYWORDS.items():
        score = sum(1 for word in words if word.lower() in lowered)
        if score:
            type_scores[label] = score
    question_type = max(type_scores, key=type_scores.get) if type_scores else "建议型"

    keywords = []
    for word in KEYWORD_CANDIDATES:
        if word.lower() in lowered and word not in keywords:
            keywords.append(word)

    return {
        "aspect": aspect or "general",
        "aspect_label": ASPECT_ZH.get(aspect or "general", "综合"),
        "emotion": emotion,
        "question_type": question_type,
        "keywords": keywords[:8],
    }


def _strip_code_fence(text: str) -> str:
    cleaned = (text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _extract_json_object(text: str) -> str | None:
    cleaned = _strip_code_fence(text)
    if not cleaned:
        return None

    # Fast path: whole text is JSON.
    if cleaned.startswith("{") and cleaned.endswith("}"):
        return cleaned

    # Robust path: find the outermost JSON object.
    start = cleaned.find("{")
    if start < 0:
        return None

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(cleaned)):
        ch = cleaned[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return cleaned[start : i + 1]
    return None


def _section(text: str, title: str) -> str:
    compact = str(text or "").replace("#", "").replace("*", "").strip()
    pattern = re.compile(rf"【{re.escape(title)}】\s*([\s\S]*?)(?=\n?【[^】]+】|$)")
    match = pattern.search(compact)
    return match.group(1).strip() if match else ""


def _fallback_from_text(text: str) -> dict[str, Any]:
    return {
        "plain_summary": _section(text, "白话解释") or DEFAULT_REPORT["plain_summary"],
        "traditional_explanation": _section(text, "抽签结果") or DEFAULT_REPORT["traditional_explanation"],
        "answer_to_question": _section(text, "针对问题的解读") or DEFAULT_REPORT["answer_to_question"],
        "action_suggestions": _parse_suggestions(_section(text, "行动建议")) or DEFAULT_REPORT["action_suggestions"],
        "risk_warning": _section(text, "提醒") or DEFAULT_REPORT["risk_warning"],
        "comfort_message": DEFAULT_REPORT["comfort_message"],
    }


def _parse_suggestions(text: str) -> list[str]:
    if not text:
        return []
    lines = [line.strip(" -\t0123456789.、") for line in text.splitlines()]
    lines = [line for line in lines if line]
    if len(lines) >= 2:
        return lines[:3]
    parts = re.split(r"[；;。]\s*", text)
    parts = [p.strip(" -\t0123456789.、") for p in parts if p.strip()]
    return parts[:3]


def normalize_ai_report(value: Any, raw_text: str = "") -> dict[str, Any]:
    if not isinstance(value, dict):
        value = {}

    fallback = _fallback_from_text(raw_text)
    report = dict(DEFAULT_REPORT)
    report.update(fallback)

    for key in [
        "plain_summary",
        "traditional_explanation",
        "answer_to_question",
        "risk_warning",
        "comfort_message",
    ]:
        if isinstance(value.get(key), str) and value.get(key).strip():
            report[key] = value[key].strip()

    suggestions = value.get("action_suggestions")
    if isinstance(suggestions, list):
        cleaned = [str(item).strip() for item in suggestions if str(item).strip()]
        if cleaned:
            report["action_suggestions"] = cleaned[:3]
    elif isinstance(suggestions, str) and suggestions.strip():
        parsed = _parse_suggestions(suggestions)
        if parsed:
            report["action_suggestions"] = parsed[:3]

    # Keep optional fields if the model returned them.
    for key in ["fortune_attitude", "short_conclusion", "style_note"]:
        if isinstance(value.get(key), str) and value.get(key).strip():
            report[key] = value[key].strip()

    return report


def parse_ai_report(raw_text: str) -> tuple[dict[str, Any], bool]:
    json_text = _extract_json_object(raw_text)
    if not json_text:
        return normalize_ai_report({}, raw_text), False

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        # Try removing common trailing commas.
        try:
            data = json.loads(re.sub(r",\s*([}\]])", r"\1", json_text))
        except json.JSONDecodeError:
            return normalize_ai_report({}, raw_text), False

    return normalize_ai_report(data, raw_text), True


def report_to_answer_text(report: dict[str, Any]) -> str:
    suggestions = report.get("action_suggestions") or []
    if isinstance(suggestions, str):
        suggestions = _parse_suggestions(suggestions)
    suggestion_text = "\n".join(f"{idx + 1}. {item}" for idx, item in enumerate(suggestions[:3]))

    return "\n\n".join([
        f"【白话解释】\n{report.get('plain_summary', '')}",
        f"【传统签意】\n{report.get('traditional_explanation', '')}",
        f"【针对问题的解读】\n{report.get('answer_to_question', '')}",
        f"【行动建议】\n{suggestion_text}",
        f"【提醒】\n{report.get('risk_warning', '')}\n{report.get('comfort_message', '')}",
    ]).strip()
