from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]

JSONL_PATH = ROOT / "data" / "processed" / "fortune" / "signs_wong_tai_sin_100.jsonl"
FIG_DIR = ROOT / "outputs" / "figures"


ASPECT_LABELS = {
    "career": "Career",
    "study": "Study",
    "love": "Love",
    "wealth": "Wealth",
    "health": "Health",
    "family": "Family",
    "self": "Self",
    "year": "Year",
    "travel": "Travel",
    "friendship": "Friendship",
    "move": "Move",
    "reputation": "Reputation",
    "children": "Children",
    "weather": "Weather",
    "lost_item": "Lost Item",
    "fengshui": "Fengshui",
    "business": "Business",
}


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def save_bar_chart(counter: Counter, title: str, xlabel: str, ylabel: str, out_path: Path) -> None:
    labels = list(counter.keys())
    values = list(counter.values())

    plt.figure(figsize=(10, 5))
    plt.bar(labels, values)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def save_hist(values: list[int], title: str, xlabel: str, ylabel: str, out_path: Path) -> None:
    plt.figure(figsize=(10, 5))
    plt.hist(values, bins=20)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def main() -> None:
    if not JSONL_PATH.exists():
        raise FileNotFoundError(f"JSONL not found: {JSONL_PATH}")

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_jsonl(JSONL_PATH)

    print(f"Loaded signs: {len(rows)}")

    level_counter = Counter(row.get("level", "Unknown") for row in rows)

    aspect_counter = Counter()
    poem_lengths = []
    overall_lengths = []
    aspect_counts_per_sign = []

    for row in rows:
        poem = row.get("poem", [])
        if isinstance(poem, list):
            poem_text = "".join(poem)
        else:
            poem_text = str(poem or "")

        overall = str(row.get("overall_interpretation", "") or "")
        aspects = row.get("aspects", {}) or {}

        poem_lengths.append(len(poem_text))
        overall_lengths.append(len(overall))
        aspect_counts_per_sign.append(len(aspects))

        for aspect in aspects:
            aspect_counter[ASPECT_LABELS.get(aspect, aspect)] += 1

    save_bar_chart(
        level_counter,
        "Distribution of Fortune Levels",
        "Fortune Level",
        "Number of Signs",
        FIG_DIR / "level_distribution.png",
    )

    save_bar_chart(
        aspect_counter,
        "Coverage of Aspect-specific Interpretations",
        "Aspect",
        "Number of Signs",
        FIG_DIR / "aspect_distribution.png",
    )

    save_hist(
        poem_lengths,
        "Distribution of Poem Text Length",
        "Poem Length",
        "Number of Signs",
        FIG_DIR / "poem_length_distribution.png",
    )

    save_hist(
        overall_lengths,
        "Distribution of Overall Interpretation Length",
        "Overall Interpretation Length",
        "Number of Signs",
        FIG_DIR / "overall_length_distribution.png",
    )

    save_hist(
        aspect_counts_per_sign,
        "Number of Aspect Fields per Sign",
        "Aspect Count",
        "Number of Signs",
        FIG_DIR / "aspect_count_per_sign.png",
    )

    summary = {
        "total_signs": len(rows),
        "level_distribution": dict(level_counter),
        "aspect_distribution": dict(aspect_counter),
        "avg_poem_length": sum(poem_lengths) / len(poem_lengths),
        "avg_overall_length": sum(overall_lengths) / len(overall_lengths),
        "avg_aspect_count_per_sign": sum(aspect_counts_per_sign) / len(aspect_counts_per_sign),
    }

    summary_path = FIG_DIR / "dataset_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Saved figures to:", FIG_DIR)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()