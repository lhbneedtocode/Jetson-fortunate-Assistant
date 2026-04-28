from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]

JSONL_PATH = ROOT / "data" / "processed" / "fortune" / "signs_wong_tai_sin_100.jsonl"
CHROMA_DIR = ROOT / "data" / "chroma"
COLLECTION_NAME = "fortune_knowledge"
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"

EVAL_DIR = ROOT / "outputs" / "eval"
FIG_DIR = ROOT / "outputs" / "figures"

EVAL_CSV = EVAL_DIR / "wts_retrieval_eval_queries.csv"
RESULT_CSV = EVAL_DIR / "wts_retrieval_eval_results.csv"
METRICS_JSON = EVAL_DIR / "wts_retrieval_metrics.json"


ASPECT_QUERIES = {
    "career": [
        "我最近找实习和工作机会顺不顺利？事业 求职 工作 机会",
        "我想知道事业发展和求职是否有希望。",
    ],
    "study": [
        "我最近考试和学业会不会顺利？学习 成绩 考试",
        "我想问学业、论文和考试结果如何。",
    ],
    "love": [
        "我最近感情和姻缘会不会顺利？恋爱 关系 婚姻",
        "我想问感情发展、复合或者恋爱机会。",
    ],
    "wealth": [
        "我最近财运和投资会不会顺利？财富 金钱 投资",
        "我想问收入、理财和赚钱机会。",
    ],
    "health": [
        "我最近身体健康情况怎么样？健康 疾病 康复",
        "我想问身体状态、病情和恢复情况。",
    ],
}


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def ensure_eval_queries(signs: list[dict]) -> None:
    """
    自动构造 RAG 检索评估集。
    每支签取 career / study / love / wealth / health 五类问题方向，
    检查检索结果 Top-k 是否能命中目标 aspect。
    """
    if EVAL_CSV.exists():
        print(f"Eval query file already exists: {EVAL_CSV}")
        return

    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    rows = []

    for sign in signs:
        sign_id = sign["sign_id"]
        aspects = sign.get("aspects", {}) or {}

        for aspect, query_templates in ASPECT_QUERIES.items():
            if aspect not in aspects:
                continue

            for query in query_templates:
                rows.append(
                    {
                        "sign_id": sign_id,
                        "aspect": aspect,
                        "query": query,
                    }
                )

    with EVAL_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["sign_id", "aspect", "query"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Created eval query file: {EVAL_CSV}, rows={len(rows)}")


def load_eval_queries() -> list[dict]:
    with EVAL_CSV.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def reciprocal_rank(retrieved_aspects: list[str], target: str) -> float:
    for idx, aspect in enumerate(retrieved_aspects, start=1):
        if aspect == target:
            return 1.0 / idx
    return 0.0


def save_metric_bar(metrics: dict) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    names = ["Hit@1", "Hit@3", "MRR"]
    values = [metrics["hit_at_1"], metrics["hit_at_3"], metrics["mrr"]]

    plt.figure(figsize=(7, 5))
    plt.bar(names, values)
    plt.ylim(0, 1.05)
    plt.title("RAG Retrieval Evaluation")
    plt.ylabel("Score")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "retrieval_metrics.png", dpi=200)
    plt.close()


def save_aspect_bar(aspect_metrics: dict) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    aspects = list(aspect_metrics.keys())
    values = [aspect_metrics[a]["hit_at_1"] for a in aspects]

    plt.figure(figsize=(8, 5))
    plt.bar(aspects, values)
    plt.ylim(0, 1.05)
    plt.title("Hit@1 by Aspect")
    plt.xlabel("Aspect")
    plt.ylabel("Hit@1")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "retrieval_hit1_by_aspect.png", dpi=200)
    plt.close()


def main() -> None:
    if not JSONL_PATH.exists():
        raise FileNotFoundError(f"JSONL not found: {JSONL_PATH}")

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    signs = load_jsonl(JSONL_PATH)
    ensure_eval_queries(signs)
    eval_rows = load_eval_queries()

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
    )

    print("Collection count:", collection.count())
    print("Eval rows:", len(eval_rows))

    results = []
    hit1 = 0
    hit3 = 0
    mrr_sum = 0.0

    aspect_total = Counter()
    aspect_hit1 = Counter()
    aspect_hit3 = Counter()
    aspect_mrr = defaultdict(float)

    for row in eval_rows:
        sign_id = f"{int(row['sign_id']):03d}"
        target_aspect = row["aspect"]
        query = row["query"]
        sign_key = f"wong_tai_sin_100_{sign_id}"

        result = collection.query(
            query_texts=[query],
            n_results=5,
            where={"sign_key": sign_key},
            include=["documents", "metadatas", "distances"],
        )

        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        retrieved_aspects = [str(meta.get("aspect", "")) for meta in metadatas]
        retrieved_types = [str(meta.get("chunk_type", "")) for meta in metadatas]

        is_hit1 = bool(retrieved_aspects and retrieved_aspects[0] == target_aspect)
        is_hit3 = target_aspect in retrieved_aspects[:3]
        rr = reciprocal_rank(retrieved_aspects, target_aspect)

        hit1 += int(is_hit1)
        hit3 += int(is_hit3)
        mrr_sum += rr

        aspect_total[target_aspect] += 1
        aspect_hit1[target_aspect] += int(is_hit1)
        aspect_hit3[target_aspect] += int(is_hit3)
        aspect_mrr[target_aspect] += rr

        results.append(
            {
                "sign_id": sign_id,
                "target_aspect": target_aspect,
                "query": query,
                "hit_at_1": int(is_hit1),
                "hit_at_3": int(is_hit3),
                "rr": rr,
                "top_aspects": "|".join(retrieved_aspects),
                "top_chunk_types": "|".join(retrieved_types),
                "top_distances": "|".join(str(x) for x in distances),
            }
        )

    total = len(eval_rows)

    metrics = {
        "total_queries": total,
        "hit_at_1": hit1 / total if total else 0,
        "hit_at_3": hit3 / total if total else 0,
        "mrr": mrr_sum / total if total else 0,
        "collection_count": collection.count(),
    }

    aspect_metrics = {}

    for aspect, total_count in aspect_total.items():
        aspect_metrics[aspect] = {
            "count": total_count,
            "hit_at_1": aspect_hit1[aspect] / total_count,
            "hit_at_3": aspect_hit3[aspect] / total_count,
            "mrr": aspect_mrr[aspect] / total_count,
        }

    with RESULT_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "sign_id",
            "target_aspect",
            "query",
            "hit_at_1",
            "hit_at_3",
            "rr",
            "top_aspects",
            "top_chunk_types",
            "top_distances",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    metrics_output = {
        "overall": metrics,
        "by_aspect": aspect_metrics,
    }

    METRICS_JSON.write_text(
        json.dumps(metrics_output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    save_metric_bar(metrics)
    save_aspect_bar(aspect_metrics)

    print("Saved result CSV:", RESULT_CSV)
    print("Saved metrics JSON:", METRICS_JSON)
    print(json.dumps(metrics_output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()