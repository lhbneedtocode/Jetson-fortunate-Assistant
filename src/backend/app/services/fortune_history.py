from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
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
    "实习", "工作", "求职", "事业", "面试", "简历", "offer", "机会", "就业", "转行", "方向", "坚持",
    "考试", "学习", "毕业", "论文", "科研", "项目", "复习", "成绩", "读研", "申请",
    "感情", "恋爱", "婚姻", "喜欢", "关系", "沟通", "分手", "复合", "人际", "朋友",
    "财运", "赚钱", "投资", "消费", "收入", "理财", "兼职", "创业", "交易",
    "健康", "焦虑", "压力", "睡眠", "状态", "情绪", "身体", "疲惫", "休息",
    "出行", "搬家", "选择", "未来", "顺利", "贵人", "等待", "变化", "机会", "风险", "稳定",
]


LEVEL_ORDER = ["上上", "上吉", "中吉", "中平", "中", "下下", "未知"]


def append_history(record: dict[str, Any]) -> None:
    """Append one interpretation record to local JSONL history."""
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
                item = json.loads(line)
                if isinstance(item, dict):
                    rows.append(item)
            except Exception:
                continue

    return rows[-limit:]


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def label_aspect(value: Any) -> str:
    return ASPECT_ZH.get(value, value or "综合")


def label_style(value: Any) -> str:
    return STYLE_ZH.get(value, value or "现代口语")


def extract_keywords(question: str) -> list[str]:
    hits = []
    lower_q = str(question or "").lower()

    for kw in KEYWORDS:
        if kw.lower() in lower_q:
            hits.append(kw)

    # Lightweight fallback: capture short Chinese/ASCII tokens that appear meaningful.
    if not hits:
        tokens = re.findall(r"[\u4e00-\u9fa5]{2,6}|[A-Za-z][A-Za-z0-9_+-]{2,}", str(question or ""))
        hits.extend(tokens[:4])

    return list(dict.fromkeys(hits))


def merged_keywords(row: dict[str, Any]) -> list[str]:
    keywords: list[str] = []

    raw_keywords = row.get("keywords")
    if isinstance(raw_keywords, list):
        keywords.extend(str(item).strip() for item in raw_keywords if str(item).strip())

    keywords.extend(extract_keywords(row.get("question") or ""))
    return list(dict.fromkeys(keywords))[:10]


def counter_to_chart(counter: Counter[str], *, total: int | None = None, limit: int = 8) -> list[dict[str, Any]]:
    total_count = total if total is not None else sum(counter.values())
    items: list[dict[str, Any]] = []

    for label, count in counter.most_common(limit):
        ratio = round(count / total_count, 4) if total_count else 0
        items.append({"label": label, "count": count, "ratio": ratio})

    return items


def build_daily_trend(rows: list[dict[str, Any]], days: int = 14) -> list[dict[str, Any]]:
    today = datetime.now().date()
    start = today - timedelta(days=days - 1)
    day_counts: dict[str, int] = defaultdict(int)

    for row in rows:
        dt = parse_dt(row.get("created_at"))
        if not dt:
            continue
        day = dt.date()
        if start <= day <= today:
            day_counts[day.isoformat()] += 1

    trend = []
    for i in range(days):
        day = start + timedelta(days=i)
        trend.append({
            "date": day.strftime("%m-%d"),
            "full_date": day.isoformat(),
            "count": day_counts.get(day.isoformat(), 0),
        })
    return trend


def coerce_score(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        score = float(value)
        if score < 0 or score > 100:
            return None
        return score
    except Exception:
        return None


def build_score_trend(rows: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    points = []
    for row in rows:
        score = coerce_score(row.get("overall_score") or row.get("radar_average"))
        if score is None:
            continue
        dt = parse_dt(row.get("created_at"))
        points.append({
            "date": dt.strftime("%m-%d") if dt else "--",
            "created_at": row.get("created_at"),
            "score": round(score, 1),
            "sign_id": row.get("sign_id"),
            "level": row.get("level") or "未知",
        })
    return points[-limit:]


def build_user_profile(limit: int = 200) -> dict[str, Any]:
    rows = load_history(limit=limit)

    empty_profile = {
        "total": 0,
        "top_aspects": [],
        "top_keywords": [],
        "level_distribution": {},
        "style_distribution": {},
        "recent_questions": [],
        "recent_summary": "暂无历史求签记录，暂不能生成用户画像。",
        "kpis": {
            "total": 0,
            "recent_7_days": 0,
            "recent_30_days": 0,
            "main_aspect": "暂无",
            "main_keyword": "暂无",
            "main_style": "暂无",
            "average_score": None,
        },
        "aspect_distribution": [],
        "keyword_cloud": [],
        "level_chart": [],
        "style_chart": [],
        "daily_trend": build_daily_trend([], days=14),
        "score_trend": [],
    }

    if not rows:
        return empty_profile

    aspect_counter: Counter[str] = Counter()
    level_counter: Counter[str] = Counter()
    style_counter: Counter[str] = Counter()
    keyword_counter: Counter[str] = Counter()

    now = datetime.now()
    recent_7_days = 0
    recent_30_days = 0
    score_values: list[float] = []

    for row in rows:
        aspect = row.get("aspect") or "general"
        level = row.get("level") or "未知"
        style = row.get("style") or "modern"

        aspect_counter[label_aspect(aspect)] += 1
        level_counter[str(level)] += 1
        style_counter[label_style(style)] += 1

        for kw in merged_keywords(row):
            keyword_counter[kw] += 1

        dt = parse_dt(row.get("created_at"))
        if dt:
            if now - dt <= timedelta(days=7):
                recent_7_days += 1
            if now - dt <= timedelta(days=30):
                recent_30_days += 1

        score = coerce_score(row.get("overall_score") or row.get("radar_average"))
        if score is not None:
            score_values.append(score)

    recent_questions = []
    for row in rows[-8:][::-1]:
        score = coerce_score(row.get("overall_score") or row.get("radar_average"))
        recent_questions.append({
            "created_at": row.get("created_at"),
            "question": row.get("question"),
            "aspect": label_aspect(row.get("aspect")),
            "sign_id": row.get("sign_id"),
            "level": row.get("level"),
            "style": label_style(row.get("style")),
            "overall_score": round(score, 1) if score is not None else None,
            "keywords": merged_keywords(row)[:5],
        })

    top_aspects = aspect_counter.most_common(5)
    top_keywords = keyword_counter.most_common(12)
    top_styles = style_counter.most_common(5)

    main_aspect = top_aspects[0][0] if top_aspects else "综合"
    main_keyword = top_keywords[0][0] if top_keywords else "暂无明显关键词"
    main_style = top_styles[0][0] if top_styles else "现代口语"
    average_score = round(sum(score_values) / len(score_values), 1) if score_values else None

    score_text = f"平均综合指数约为 {average_score} 分，" if average_score is not None else "当前综合指数样本还不够稳定，"
    recent_summary = (
        f"根据最近 {len(rows)} 次求签记录，用户较常关注「{main_aspect}」方向，"
        f"高频关键词包括「{main_keyword}」，常用解签风格为「{main_style}」。"
        f"{score_text}后续解签可更多结合用户长期关注点，给出更具体、可执行且不过度迷信的建议。"
    )

    # Keep the old object shape for backwards compatibility, and add chart-ready fields for the dashboard.
    return {
        "total": len(rows),
        "top_aspects": top_aspects,
        "top_keywords": top_keywords,
        "level_distribution": dict(level_counter),
        "style_distribution": dict(style_counter),
        "recent_questions": recent_questions,
        "recent_summary": recent_summary,
        "kpis": {
            "total": len(rows),
            "recent_7_days": recent_7_days,
            "recent_30_days": recent_30_days,
            "main_aspect": main_aspect,
            "main_keyword": main_keyword,
            "main_style": main_style,
            "average_score": average_score,
        },
        "aspect_distribution": counter_to_chart(aspect_counter, total=len(rows), limit=8),
        "keyword_cloud": counter_to_chart(keyword_counter, limit=16),
        "level_chart": counter_to_chart(level_counter, total=len(rows), limit=8),
        "style_chart": counter_to_chart(style_counter, total=len(rows), limit=8),
        "daily_trend": build_daily_trend(rows, days=14),
        "score_trend": build_score_trend(rows, limit=12),
    }
