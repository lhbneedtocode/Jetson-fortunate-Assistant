from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

JSONL_PATH = ROOT / "data" / "processed" / "fortune" / "signs_wong_tai_sin_100.jsonl"
OUT_DIR = ROOT / "src" / "frontend" / "static" / "data"
OUT_PATH = OUT_DIR / "signs_summary.json"


def level_class(level: str) -> str:
    level = str(level or "").strip()

    if level == "上上":
        return "level-best"
    if level == "上吉":
        return "level-good"
    if level == "中吉":
        return "level-midgood"
    if level == "中平":
        return "level-neutral"
    if level in {"下下", "下吉"}:
        return "level-bad"

    return "level-unknown"


def load_jsonl(path: Path) -> list[dict]:
    rows = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    return rows


def main() -> None:
    if not JSONL_PATH.exists():
        raise FileNotFoundError(f"JSONL not found: {JSONL_PATH}")

    rows = load_jsonl(JSONL_PATH)

    summary = []

    for row in rows:
        sign_id = str(row.get("sign_id", "")).zfill(3)
        level = str(row.get("level", ""))
        story_title = str(row.get("story_title", ""))

        keywords = row.get("keywords", [])
        if not isinstance(keywords, list):
            keywords = []

        summary.append(
            {
                "sign_id": sign_id,
                "title": row.get("title", f"第{int(sign_id)}签"),
                "level": level,
                "level_class": level_class(level),
                "story_title": story_title,
                "keywords": keywords[:6],
            }
        )

    summary.sort(key=lambda x: int(x["sign_id"]))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Exported {len(summary)} signs to {OUT_PATH}")
    print("Level distribution:")
    print(dict(Counter(item["level"] for item in summary)))


if __name__ == "__main__":
    main()