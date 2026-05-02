from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


ASPECT_LABELS = {
    "general": "综合",
    "career": "事业/求职",
    "study": "学业/考试",
    "love": "感情/姻缘",
    "wealth": "财富/投资",
    "health": "健康",
}

RADAR_DIMENSIONS = [
    {"key": "career", "label": "事业", "short_label": "事业"},
    {"key": "study", "label": "学业", "short_label": "学业"},
    {"key": "love", "label": "感情", "short_label": "感情"},
    {"key": "wealth", "label": "财运", "short_label": "财运"},
    {"key": "health", "label": "健康", "short_label": "健康"},
]

# 签级基础分：先把传统“吉凶等级”转成一个可量化的基础分。
# 后续再根据每个方向解释中的积极/谨慎关键词做修正。
LEVEL_BASE_SCORE = {
    "上上": 92,
    "大吉": 90,
    "上吉": 82,
    "中吉": 72,
    "吉": 68,
    "中平": 58,
    "下吉": 42,
    "下下": 28,
    "凶": 25,
}

POSITIVE_KEYWORDS = {
    "贵人": 7,
    "顺利": 7,
    "亨通": 7,
    "可成": 6,
    "有望": 6,
    "得利": 6,
    "得财": 6,
    "成功": 6,
    "喜": 5,
    "平安": 6,
    "康复": 7,
    "升职": 7,
    "加薪": 7,
    "和合": 6,
    "成就": 6,
    "如意": 6,
    "发展": 4,
    "进步": 4,
    "收成": 5,
    "添丁": 4,
}

CAUTION_KEYWORDS = {
    "不吉": -10,
    "不吉利": -12,
    "未能": -6,
    "结不成": -10,
    "虚无": -7,
    "不要奢求": -9,
    "久病": -10,
    "散了": -6,
    "过眼云烟": -8,
    "大起大落": -8,
    "谨慎": -5,
    "小心": -5,
    "守": -3,
    "宜守": -5,
    "迟": -5,
    "慢": -3,
    "等待": -4,
    "阻": -7,
    "阻滞": -8,
    "难": -7,
    "不利": -8,
    "不可": -7,
    "勿": -5,
    "忌": -5,
    "破": -8,
    "损": -7,
    "失": -6,
    "病": -7,
    "凶": -12,
    "灾": -10,
    "险": -9,
    "争": -5,
    "纠纷": -7,
    "劳": -4,
}

DIMENSION_BOOSTS = {
    "career": {"贵人": 3, "升职": 5, "加薪": 5, "发展": 4, "谋事": 3, "成就": 3, "阻滞": -4},
    "study": {"进步": 5, "成功": 4, "勤": 3, "迟": -3, "难": -4, "懒": -5},
    "love": {"姻缘": 3, "和合": 5, "喜": 3, "婚": 3, "分": -4, "争": -3},
    "wealth": {"财": 4, "利": 4, "得财": 5, "投资": 2, "损": -5, "破财": -8},
    "health": {"平安": 5, "安": 3, "康复": 6, "病": -5, "险": -5, "灾": -6},
}


@dataclass
class KeywordHit:
    keyword: str
    weight: int
    kind: str


def _clamp(value: float, low: int = 15, high: int = 98) -> int:
    return int(max(low, min(high, round(value))))


def _compact(text: str, limit: int = 120) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def _extract_direction_text(text: str) -> str:
    """优先提取“方向解释”段落，避免整段综合提示过长导致关键词噪声太大。"""
    text = str(text or "")
    match = re.search(r"方向解释[：:]?\s*(.*?)(?:\n\s*\n|相关签诗[：:]?|综合提示[：:]?)", text, flags=re.S)
    if match:
        return _compact(match.group(1), 260)
    return _compact(text, 260)


def _level_base(level: str | None) -> int:
    level = str(level or "").strip()
    if level in LEVEL_BASE_SCORE:
        return LEVEL_BASE_SCORE[level]

    # 容错：网页或模型有时会把“签”字带进来。
    for key, score in LEVEL_BASE_SCORE.items():
        if key and key in level:
            return score

    return 55


def _find_best_chunk(chunks: list[Any], aspect: str) -> Any | None:
    exact = [
        chunk
        for chunk in chunks
        if str((chunk.metadata or {}).get("aspect", "")) == aspect
        and str((chunk.metadata or {}).get("chunk_type", "")) == "aspect_interpretation"
    ]
    if exact:
        return exact[0]

    same_aspect = [chunk for chunk in chunks if str((chunk.metadata or {}).get("aspect", "")) == aspect]
    if same_aspect:
        return same_aspect[0]

    return None


def _find_overview(chunks: list[Any]) -> Any | None:
    for chunk in chunks:
        meta = chunk.metadata or {}
        if meta.get("aspect") == "general" or meta.get("chunk_type") == "overview":
            return chunk
    return chunks[0] if chunks else None


def _collect_hits(text: str, aspect: str) -> tuple[list[KeywordHit], int]:
    hits: list[KeywordHit] = []
    adjustment = 0
    seen: set[str] = set()

    def add_hit(keyword: str, weight: int, kind: str) -> None:
        nonlocal adjustment
        if keyword in seen or any(keyword in prev or prev in keyword for prev in seen):
            return
        if keyword in text:
            seen.add(keyword)
            hits.append(KeywordHit(keyword=keyword, weight=weight, kind=kind))
            adjustment += weight

    # 先处理较长的谨慎短语，避免“不吉利”同时被“吉”这类宽泛字面误判。
    for keyword, weight in sorted(CAUTION_KEYWORDS.items(), key=lambda item: len(item[0]), reverse=True):
        add_hit(keyword, weight, "caution")

    for keyword, weight in sorted(POSITIVE_KEYWORDS.items(), key=lambda item: len(item[0]), reverse=True):
        add_hit(keyword, weight, "positive")

    for keyword, weight in sorted(DIMENSION_BOOSTS.get(aspect, {}).items(), key=lambda item: len(item[0]), reverse=True):
        add_hit(keyword, weight, "dimension")

    # 防止“关键词命中太多”导致分数被拉得过头；它只是修正项，不应该盖过签级本身。
    adjustment = max(-22, min(18, adjustment))
    hits.sort(key=lambda h: abs(h.weight), reverse=True)
    return hits[:6], adjustment


def _confidence_for(text: str, has_dimension_chunk: bool) -> int:
    base = 70 if has_dimension_chunk else 45
    richness = min(20, len(text) // 18)
    return _clamp(base + richness, 30, 95)


def _dimension_comment(score: int, hits: list[KeywordHit], text: str) -> str:
    if hits:
        positive = [h.keyword for h in hits if h.weight > 0][:2]
        caution = [h.keyword for h in hits if h.weight < 0][:2]
        parts = []
        if positive:
            parts.append("利好关键词：" + "、".join(positive))
        if caution:
            parts.append("谨慎关键词：" + "、".join(caution))
        if parts:
            return "；".join(parts)

    if score >= 80:
        return "整体偏积极，可主动推进，但仍需保留现实判断。"
    if score >= 65:
        return "趋势较稳，适合在可控范围内逐步推进。"
    if score >= 50:
        return "中性偏保守，更适合观察、准备和稳住节奏。"
    return "风险提示较强，建议降低预期，避免冲动决策。"


def _summary_from_scores(items: list[dict[str, Any]], level: str, story_title: str, focus_aspect: str) -> str:
    if not items:
        return "暂无足够签文数据生成五维分析。"

    sorted_items = sorted(items, key=lambda x: x["score"], reverse=True)
    strongest = sorted_items[0]
    weakest = sorted_items[-1]
    average = sum(int(item["score"]) for item in items) / len(items)

    focus_item = next((item for item in items if item["key"] == focus_aspect), None)
    focus_sentence = ""
    if focus_item:
        focus_sentence = f"你当前关注的“{focus_item['label']}”维度为 {focus_item['score']} 分，建议重点参考该维度的方向解释。"

    if average >= 78:
        trend = "整体签势偏积极，适合主动推进，但不要把好运理解成可以跳过准备。"
    elif average >= 62:
        trend = "整体签势中等偏稳，适合边观察边行动，重点放在可控变量上。"
    elif average >= 48:
        trend = "整体签势偏保守，短期更适合蓄力、复盘和降低风险。"
    else:
        trend = "整体签势提醒较强，近期不宜冒进，更适合暂停、检查和防守。"

    return (
        f"本签为“{level or '未知'}”，典故为“{story_title or '未识别'}”。"
        f"五维中相对较强的是“{strongest['label']}”（{strongest['score']} 分），"
        f"相对需要谨慎的是“{weakest['label']}”（{weakest['score']} 分）。"
        f"{trend}{focus_sentence}"
    )


def build_five_dimension_radar(
    *,
    sign_id: str,
    aspect: str,
    question: str,
    chunks: list[Any],
) -> dict[str, Any]:
    """
    Build a deterministic five-dimension fortune radar.

    This is intentionally rule-based and explainable:
    - level -> base score
    - direction-specific text -> keyword adjustment
    - available aspect chunk -> confidence
    The goal is data modeling + visualization support, not real-world prediction.
    """
    chunks = chunks or []
    overview = _find_overview(chunks)
    overview_meta = overview.metadata if overview else {}

    level = str(overview_meta.get("level") or "")
    story_title = str(overview_meta.get("story_title") or "")
    base_score = _level_base(level)

    # 如果 overview 里没有 level，就从任意 chunk 中补齐。
    if not level:
        for chunk in chunks:
            meta = chunk.metadata or {}
            if meta.get("level"):
                level = str(meta.get("level"))
                base_score = _level_base(level)
                break

    if not story_title:
        for chunk in chunks:
            meta = chunk.metadata or {}
            if meta.get("story_title"):
                story_title = str(meta.get("story_title"))
                break

    overview_text = _extract_direction_text(overview.text if overview else "")
    items: list[dict[str, Any]] = []

    for dimension in RADAR_DIMENSIONS:
        key = dimension["key"]
        chunk = _find_best_chunk(chunks, key)
        has_dimension_chunk = chunk is not None
        text = _extract_direction_text(chunk.text if chunk else overview_text)
        # 优先使用该维度自己的解释文本；只有没有独立维度 chunk 时才回退到综合释义，
        # 避免“综合释义”里的通用积极词把所有维度都拉到同一分数。
        scoring_text = text if has_dimension_chunk else overview_text
        hits, keyword_adjust = _collect_hits(scoring_text, key)

        # 用户当前问题方向稍微增强权重，让图表能突出“用户真正问的事”。
        focus_adjust = 4 if key == aspect else 0
        score = _clamp(base_score + keyword_adjust + focus_adjust)
        confidence = _confidence_for(text, has_dimension_chunk)

        items.append(
            {
                "key": key,
                "label": dimension["label"],
                "short_label": dimension["short_label"],
                "score": score,
                "confidence": confidence,
                "base_score": base_score,
                "keyword_adjust": keyword_adjust,
                "focus_adjust": focus_adjust,
                "aspect_label": ASPECT_LABELS.get(key, dimension["label"]),
                "evidence": text or "暂无该方向的独立解释，已参考本签综合释义。",
                "comment": _dimension_comment(score, hits, text),
                "keywords": [
                    {"word": hit.keyword, "weight": hit.weight, "kind": hit.kind}
                    for hit in hits
                ],
            }
        )

    average_score = _clamp(sum(item["score"] for item in items) / len(items), 0, 100)

    return {
        "title": "五维运势雷达分析",
        "sign_id": sign_id,
        "level": level,
        "story_title": story_title,
        "focus_aspect": aspect,
        "average_score": average_score,
        "dimensions": items,
        "summary": _summary_from_scores(items, level, story_title, aspect),
        "model_explanation": (
            "评分模型 = 签级基础分 + 方向解释关键词修正 + 当前问题方向修正；"
            "该模型用于传统文化文本的量化展示和自我反思，不代表现实预测。"
        ),
    }
