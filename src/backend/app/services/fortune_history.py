from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
HISTORY_PATH = ROOT / "data" / "processed" / "fortune" / "user_history.jsonl"


ASPECT_ZH = {
    "career": "事业/求职",
    "study": "学业/考试",
    "love": "感情/姻缘",
    "wealth": "财富/财运",
    "health": "健康",
    "family": "家庭",
    "travel": "出行",
    "general": "综合",
    "": "自动识别",
    None: "自动识别",
}


STYLE_ZH = {
    "modern": "现代口语",
    "traditional": "传统古风",
    "healing": "温柔治愈",
    "sharp": "犀利吐槽",
    "rational": "理性分析",
    "": "现代口语",
    None: "现代口语",
}


KEYWORDS = [
    "实习", "工作", "求职", "事业", "面试", "简历", "offer", "机会",
    "考试", "学习", "毕业", "论文",
    "感情", "恋爱", "婚姻", "喜欢",
    "财运", "赚钱", "投资", "消费",
    "健康", "焦虑", "压力", "睡眠",
    "出行", "搬家", "选择", "未来", "顺利",
]


def append_history(record: dict[str, Any]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)

    safe_record = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        **record,
    }

    with HISTORY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(safe_record, ensure_ascii=False) + "\n")


def load_history(limit: int = 200) -> list[dict[str, Any]]:
    if not HISTORY_PATH.exists():
        return []

    rows: list[dict[str, Any]] = []

    with HISTORY_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                rows.append(json.loads(line))
            except Exception:
                continue

    return rows[-limit:]


def extract_keywords(question: str) -> list[str]:
    hits = []
    lower_q = question.lower()

    for kw in KEYWORDS:
        if kw.lower() in lower_q:
            hits.append(kw)

    return hits


def build_user_profile(limit: int = 200) -> dict[str, Any]:
    rows = load_history(limit=limit)

    if not rows:
        return {
            "total": 0,
            "top_aspects": [],
            "top_keywords": [],
            "level_distribution": {},
            "style_distribution": {},
            "recent_questions": [],
            "recent_summary": "暂无历史求签记录，暂不能生成用户画像。",
        }

    aspect_counter: Counter[str] = Counter()
    level_counter: Counter[str] = Counter()
    style_counter: Counter[str] = Counter()
    keyword_counter: Counter[str] = Counter()

    recent_questions = []

    for row in rows:
        aspect = row.get("aspect") or "general"
        level = row.get("level") or "未知"
        style = row.get("style") or "modern"
        question = row.get("question") or ""

        aspect_counter[ASPECT_ZH.get(aspect, aspect)] += 1
        level_counter[level] += 1
        style_counter[STYLE_ZH.get(style, style)] += 1

        for kw in extract_keywords(question):
            keyword_counter[kw] += 1

    for row in rows[-5:][::-1]:
        recent_questions.append({
            "created_at": row.get("created_at"),
            "question": row.get("question"),
            "aspect": ASPECT_ZH.get(row.get("aspect"), row.get("aspect") or "综合"),
            "sign_id": row.get("sign_id"),
            "level": row.get("level"),
            "style": STYLE_ZH.get(row.get("style"), row.get("style") or "现代口语"),
        })

    top_aspects = aspect_counter.most_common(5)
    top_keywords = keyword_counter.most_common(8)
    top_styles = style_counter.most_common(5)

    main_aspect = top_aspects[0][0] if top_aspects else "综合"
    main_keyword = top_keywords[0][0] if top_keywords else "暂无明显关键词"
    main_style = top_styles[0][0] if top_styles else "现代口语"

    recent_summary = (
        f"根据最近 {len(rows)} 次求签记录，用户较常关注「{main_aspect}」方向，"
        f"高频关键词包括「{main_keyword}」，常用解签风格为「{main_style}」。"
        f"后续解签可更多结合用户长期关注点，给出更具体、可执行且不过度迷信的建议。"
    )

    return {
        "total": len(rows),
        "top_aspects": top_aspects,
        "top_keywords": top_keywords,
        "level_distribution": dict(level_counter),
        "style_distribution": dict(style_counter),
        "recent_questions": recent_questions,
        "recent_summary": recent_summary,
    }