from __future__ import annotations

import json
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.services.fortune_drawer import get_sign_summary, normalize_sign_id
from app.services.fortune_retriever import FortuneRetriever, FortuneChunk


ROOT = Path(__file__).resolve().parents[4]
SIGN_SUMMARY_PATH = ROOT / "src" / "frontend" / "static" / "data" / "signs_summary.json"


def _compact(text: str, limit: int = 180) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(value) <= limit:
        return value
    return value[:limit].rstrip() + "..."


@lru_cache(maxsize=1)
def _load_summary_map() -> dict[str, dict[str, Any]]:
    try:
        data = json.loads(SIGN_SUMMARY_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list):
            result: dict[str, dict[str, Any]] = {}
            for item in data:
                if not isinstance(item, dict):
                    continue
                try:
                    sid = normalize_sign_id(item.get("sign_id"))
                    result[sid] = item
                except Exception:
                    continue
            return result
    except Exception as exc:
        print(f"[WARN] load signs_summary for similarity failed: {exc}")
    return {}


def _chunk_text_for_query(chunks: list[FortuneChunk], aspect: str | None, question: str) -> str:
    """Build one semantic query text for current sign.

    We intentionally combine current user question + overview + target-aspect chunks,
    so similar-sign retrieval is not only based on the drawn sign itself but also
    follows the user's concern direction.
    """
    selected: list[str] = []
    if question:
        selected.append(f"用户问题：{question}")

    # Prefer the selected aspect, overview, poem/story. Keep it concise so embedding is focused.
    priorities = []
    for chunk in chunks:
        meta = chunk.metadata or {}
        a = str(meta.get("aspect", ""))
        ctype = str(meta.get("chunk_type", ""))
        score = 9
        if aspect and a == aspect:
            score = 0
        elif a == "general" or ctype == "overview":
            score = 1
        elif a == "poem" or ctype == "poem":
            score = 2
        elif a == "story" or ctype == "story":
            score = 3
        priorities.append((score, chunk.text or ""))

    for _, text in sorted(priorities, key=lambda x: x[0])[:6]:
        if text:
            selected.append(_compact(text, 360))

    query = "\n".join(selected).strip()
    return query[:1800]


def _distance_to_score(retriever: FortuneRetriever, distance: float | int | None) -> float:
    try:
        return float(retriever._distance_to_score(distance))  # noqa: SLF001 - reuse existing scoring convention.
    except Exception:
        if distance is None:
            return 0.0
        try:
            d = float(distance)
            return 1.0 / (1.0 + max(d, 0.0))
        except Exception:
            return 0.0


def _keyword_overlap(a: list[str], b: list[str]) -> int:
    set_a = {str(x).strip() for x in a if str(x).strip()}
    set_b = {str(x).strip() for x in b if str(x).strip()}
    return len(set_a & set_b)


def _fallback_by_summary(sign_id: str, top_k: int) -> list[dict[str, Any]]:
    """Fallback when Chroma similarity search is unavailable.

    It uses keyword overlap in signs_summary.json, which is not as strong as embedding,
    but still keeps the UI useful and explainable.
    """
    summary_map = _load_summary_map()
    current = summary_map.get(sign_id) or {}
    current_keywords = current.get("keywords") or []
    rows: list[dict[str, Any]] = []

    for sid, item in summary_map.items():
        if sid == sign_id:
            continue
        keywords = item.get("keywords") or []
        overlap = _keyword_overlap(current_keywords, keywords)
        if overlap <= 0:
            continue
        rows.append(
            {
                "sign_id": sid,
                "sign_key": item.get("sign_key") or f"wong_tai_sin_100_{sid}",
                "level": item.get("level") or "未知",
                "title": item.get("title") or f"第{int(sid)}签",
                "story_title": item.get("story_title") or item.get("title") or "灵签",
                "similarity": round(min(0.72, 0.42 + overlap * 0.08), 3),
                "similarity_percent": int(round(min(0.72, 0.42 + overlap * 0.08) * 100)),
                "keywords": [str(x) for x in keywords[:8]],
                "matched_keywords": list({str(x) for x in current_keywords} & {str(x) for x in keywords})[:6],
                "matched_aspects": [],
                "reason": "基于签卡关键词重合得到的兜底相似推荐。",
                "evidence": [],
                "source": "keyword_fallback",
            }
        )

    rows.sort(key=lambda x: (-x["similarity"], x["sign_id"]))
    return rows[:top_k]


def build_similar_signs(
    retriever: FortuneRetriever,
    *,
    sign_id: str | int,
    aspect: str | None = None,
    question: str = "",
    top_k: int = 4,
) -> list[dict[str, Any]]:
    """Recommend semantically similar signs.

    Implementation:
    1. Load all chunks for the current sign.
    2. Build a compact semantic query from current sign + user question.
    3. Query Chroma without sign filter.
    4. Aggregate matched chunks by sign_id and rank signs by best semantic score.
    5. Enrich with sign title/level/keywords for frontend display.
    """
    normalized = normalize_sign_id(sign_id)

    try:
        current_chunks = retriever.get_sign_chunks(normalized)
    except Exception as exc:
        print(f"[WARN] similarity failed to load current sign chunks: {exc}")
        current_chunks = []

    query_text = _chunk_text_for_query(current_chunks, aspect, question)
    if not query_text:
        query_text = f"黄大仙灵签 第{normalized}签 相似签 推荐"

    try:
        collection = retriever._get_collection()  # noqa: SLF001 - no public full-collection query method yet.
        result = collection.query(
            query_texts=[query_text],
            n_results=90,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        print(f"[WARN] Chroma similar-sign query failed: {exc}")
        return _fallback_by_summary(normalized, top_k)

    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    grouped: dict[str, dict[str, Any]] = {}
    current_summary = get_sign_summary(normalized)
    current_keywords = current_summary.get("keywords") or []

    for text, meta, distance in zip(documents, metadatas, distances):
        meta = meta or {}
        try:
            sid = normalize_sign_id(meta.get("sign_id"))
        except Exception:
            continue
        if sid == normalized:
            continue

        score = _distance_to_score(retriever, distance)
        if sid not in grouped:
            try:
                card = get_sign_summary(sid)
            except Exception:
                card = {}
            grouped[sid] = {
                "sign_id": sid,
                "sign_key": meta.get("sign_key") or card.get("sign_key") or f"wong_tai_sin_100_{sid}",
                "level": meta.get("level") or card.get("level") or "未知",
                "title": card.get("title") or f"第{int(sid)}签",
                "story_title": meta.get("story_title") or card.get("story_title") or card.get("title") or "灵签",
                "best_score": 0.0,
                "score_sum": 0.0,
                "hit_count": 0,
                "keywords": card.get("keywords") or [],
                "matched_aspects": set(),
                "evidence": [],
            }

        row = grouped[sid]
        row["best_score"] = max(float(row["best_score"]), score)
        row["score_sum"] = float(row["score_sum"]) + score
        row["hit_count"] = int(row["hit_count"]) + 1

        aspect_label = meta.get("aspect_label") or meta.get("aspect")
        if aspect_label:
            row["matched_aspects"].add(str(aspect_label))

        if len(row["evidence"]) < 3:
            row["evidence"].append(
                {
                    "snippet": _compact(text, 180),
                    "score": round(score, 4),
                    "aspect": meta.get("aspect"),
                    "aspect_label": meta.get("aspect_label"),
                    "chunk_type": meta.get("chunk_type"),
                }
            )

    rows: list[dict[str, Any]] = []
    for sid, row in grouped.items():
        hit_count = max(int(row.pop("hit_count", 1)), 1)
        best_score = float(row.pop("best_score", 0.0))
        avg_score = float(row.pop("score_sum", 0.0)) / hit_count
        # Keep best score dominant, but reward repeated evidence hits slightly.
        similarity = max(0.0, min(0.99, best_score * 0.82 + avg_score * 0.18 + min(hit_count, 5) * 0.006))
        keywords = [str(x) for x in (row.get("keywords") or [])[:8]]
        matched_keywords = list({str(x) for x in current_keywords} & {str(x) for x in keywords})[:6]
        matched_aspects = sorted(row.pop("matched_aspects", set()))[:6]

        reason_parts = []
        if matched_aspects:
            reason_parts.append("命中相近解释维度：" + "、".join(matched_aspects[:3]))
        if matched_keywords:
            reason_parts.append("共享关键词：" + "、".join(matched_keywords[:4]))
        if not reason_parts:
            reason_parts.append("与当前签的签诗、典故或方向解释在语义向量空间中相近。")

        rows.append(
            {
                **row,
                "keywords": keywords,
                "matched_keywords": matched_keywords,
                "matched_aspects": matched_aspects,
                "similarity": round(similarity, 3),
                "similarity_percent": int(round(similarity * 100)),
                "reason": "；".join(reason_parts),
                "source": "chroma_embedding",
            }
        )

    rows.sort(key=lambda x: (-float(x.get("similarity") or 0), str(x.get("sign_id") or "")))

    if not rows:
        return _fallback_by_summary(normalized, top_k)

    return rows[:top_k]
