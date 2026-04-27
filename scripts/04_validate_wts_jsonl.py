from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JSONL_PATH = ROOT / "data" / "processed" / "fortune" / "signs_wong_tai_sin_100.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    rows = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    return rows


def main() -> None:
    rows = load_jsonl(JSONL_PATH)

    print(f"Rows: {len(rows)}")

    sign_ids = [row.get("sign_id") for row in rows]
    expected = {f"{i:03d}" for i in range(1, 101)}
    actual = set(sign_ids)

    print("Missing IDs:", sorted(expected - actual))
    print("Duplicated IDs:", sorted([sid for sid in actual if sign_ids.count(sid) > 1]))

    level_counter = Counter(row.get("level", "") for row in rows)
    print("\nLevel distribution:")
    for level, count in level_counter.most_common():
        print(f"  {level or '[EMPTY]'}: {count}")

    aspect_counter = Counter()
    empty_poem = []
    empty_story = []
    empty_aspects = []

    for row in rows:
        sign_id = row.get("sign_id")

        if not row.get("poem"):
            empty_poem.append(sign_id)

        if not row.get("story_title"):
            empty_story.append(sign_id)

        aspects = row.get("aspects", {})

        if not aspects:
            empty_aspects.append(sign_id)

        for aspect in aspects:
            aspect_counter[aspect] += 1

    print("\nAspect distribution:")
    for aspect, count in aspect_counter.most_common():
        print(f"  {aspect}: {count}")

    print("\nEmpty fields:")
    print("  empty poem:", empty_poem)
    print("  empty story_title:", empty_story)
    print("  empty aspects:", empty_aspects)

    print("\nSample row 023:")
    row_023 = next((row for row in rows if row.get("sign_id") == "023"), None)
    if row_023:
        print(json.dumps(row_023, ensure_ascii=False, indent=2)[:2000])


if __name__ == "__main__":
    main()