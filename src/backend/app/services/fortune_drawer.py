from __future__ import annotations

import json
import random
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import uuid4


# fortune_drawer.py is under: src/backend/app/services
# parents[3] -> src, so src/frontend/static/data/signs_summary.json works locally.
SRC_DIR = Path(__file__).resolve().parents[3]
PROJECT_ROOT = Path(__file__).resolve().parents[4]

SIGN_SUMMARY_CANDIDATES = [
    SRC_DIR / "frontend" / "static" / "data" / "signs_summary.json",
    PROJECT_ROOT / "src" / "frontend" / "static" / "data" / "signs_summary.json",
    Path.cwd() / "../frontend/static/data/signs_summary.json",
]


def normalize_sign_id(value: str | int | None) -> str:
    """Normalize any 1-100 sign id into a 3-digit string."""
    if value is None or str(value).strip() == "":
        return f"{random.randint(1, 100):03d}"

    try:
        number = int(str(value).strip())
    except ValueError as exc:
        raise ValueError("sign_id must be an integer from 1 to 100") from exc

    if number < 1 or number > 100:
        raise ValueError("sign_id must be between 1 and 100")

    return f"{number:03d}"


@lru_cache(maxsize=1)
def load_sign_summaries() -> list[dict[str, Any]]:
    """Load 100 sign summary cards.

    This keeps draw fast and independent from Chroma/vLLM. If the summary file
    is unavailable, we still return 100 minimal cards so demo will not crash.
    """
    for path in SIGN_SUMMARY_CANDIDATES:
        try:
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, list) and data:
                    return data
        except Exception as exc:
            print(f"[WARN] failed to load signs summary from {path}: {exc}")

    return [
        {
            "sign_id": f"{i:03d}",
            "sign_key": f"wong_tai_sin_100_{i:03d}",
            "title": f"第{i}签",
            "level": "未知",
            "level_class": "level-neutral",
            "story_title": "待解签",
            "keywords": [],
        }
        for i in range(1, 101)
    ]


def get_sign_summary(sign_id: str | int) -> dict[str, Any]:
    normalized = normalize_sign_id(sign_id)
    signs = load_sign_summaries()

    for item in signs:
        try:
            if normalize_sign_id(item.get("sign_id")) == normalized:
                return build_sign_card(item, normalized)
        except Exception:
            continue

    # Last-resort fallback.
    return build_sign_card({}, normalized)


def build_sign_card(item: dict[str, Any], sign_id: str) -> dict[str, Any]:
    sign_key = item.get("sign_key") or f"wong_tai_sin_100_{sign_id}"
    title = item.get("title") or f"第{int(sign_id)}签"
    story_title = item.get("story_title") or item.get("name") or title
    keywords = item.get("keywords") or []
    if not isinstance(keywords, list):
        keywords = [str(keywords)]

    return {
        "sign_id": sign_id,
        "sign_key": sign_key,
        "level": item.get("level") or "未知",
        "level_class": item.get("level_class") or "level-neutral",
        "title": title,
        "story_title": story_title,
        "keywords": [str(k) for k in keywords[:12]],
    }


def draw_sign(sign_id: str | int | None = None) -> dict[str, Any]:
    normalized = normalize_sign_id(sign_id)
    card = get_sign_summary(normalized)
    return {
        "draw_id": uuid4().hex,
        **card,
        "source": "backend_draw",
    }
