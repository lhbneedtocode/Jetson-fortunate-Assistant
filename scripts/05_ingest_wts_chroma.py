from __future__ import annotations

import argparse
import json
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions


ROOT = Path(__file__).resolve().parents[1]

JSONL_PATH = ROOT / "data" / "processed" / "fortune" / "signs_wong_tai_sin_100.jsonl"
CHROMA_DIR = ROOT / "data" / "chroma"

DEFAULT_COLLECTION = "fortune_knowledge"
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"


ASPECT_LABELS = {
    "general": "综合",
    "poem": "签诗",
    "story": "典故",
    "year": "流年",
    "career": "事业/求职",
    "business": "交易/生意",
    "wealth": "财富/财运",
    "self": "自身",
    "family": "家庭/家宅",
    "love": "姻缘/感情",
    "move": "移居",
    "reputation": "名誉",
    "health": "健康/病情",
    "friendship": "友谊",
    "study": "学业/考试",
    "children": "子女/六甲",
    "travel": "出行",
    "lost_item": "遗失",
    "weather": "天时",
    "fengshui": "风水",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest Wong Tai Sin fortune JSONL into Chroma.")
    parser.add_argument("--jsonl-path", default=str(JSONL_PATH))
    parser.add_argument("--persist-dir", default=str(CHROMA_DIR))
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--reset", action="store_true")
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict]:
    rows = []

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue

            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at line {line_no}: {exc}") from exc

    return rows


def normalize_metadata(metadata: dict) -> dict:
    """
    Chroma metadata only supports primitive values.
    """
    output = {}

    for key, value in metadata.items():
        if value is None:
            continue

        if isinstance(value, (str, int, float, bool)):
            output[key] = value
        else:
            output[key] = json.dumps(value, ensure_ascii=False)

    return output


def poem_to_text(poem) -> str:
    if isinstance(poem, list):
        return "\n".join(str(x) for x in poem if str(x).strip())
    return str(poem or "")


def first_source_url(sign: dict) -> str:
    urls = sign.get("source_urls", [])

    if isinstance(urls, list) and urls:
        return str(urls[0])

    return "unknown"


def build_chunks(sign: dict) -> list[dict]:
    sign_id = str(sign["sign_id"])
    sign_key = str(sign["sign_key"])
    oracle_system = str(sign.get("oracle_system", "wong_tai_sin_100"))

    title = str(sign.get("title", ""))
    level = str(sign.get("level", ""))
    story_title = str(sign.get("story_title", ""))
    poem_text = poem_to_text(sign.get("poem", []))
    story = str(sign.get("story", ""))
    overall = str(sign.get("overall_interpretation", ""))
    keywords = sign.get("keywords", [])
    source_url = first_source_url(sign)

    base_meta = {
        "oracle_system": oracle_system,
        "sign_id": sign_id,
        "sign_key": sign_key,
        "title": title,
        "level": level,
        "story_title": story_title,
        "source": source_url,
        "source_url": source_url,
    }

    chunks: list[dict] = []

    overview_text = f"""
签号：{sign_id}
签名：{title}
吉凶等级：{level}
典故标题：{story_title}
关键词：{"、".join(keywords) if isinstance(keywords, list) else keywords}

签诗：
{poem_text}

典故：
{story}

综合解释：
{overall}
""".strip()

    chunks.append(
        {
            "id": f"{sign_key}_overview",
            "text": overview_text,
            "metadata": {
                **base_meta,
                "aspect": "general",
                "aspect_label": "综合",
                "chunk_type": "overview",
            },
        }
    )

    if poem_text.strip():
        chunks.append(
            {
                "id": f"{sign_key}_poem",
                "text": f"""
签号：{sign_id}
签名：{title}
吉凶等级：{level}
典故标题：{story_title}

签诗：
{poem_text}
""".strip(),
                "metadata": {
                    **base_meta,
                    "aspect": "poem",
                    "aspect_label": "签诗",
                    "chunk_type": "poem",
                },
            }
        )

    if story.strip():
        chunks.append(
            {
                "id": f"{sign_key}_story",
                "text": f"""
签号：{sign_id}
签名：{title}
吉凶等级：{level}
典故标题：{story_title}

典故：
{story}
""".strip(),
                "metadata": {
                    **base_meta,
                    "aspect": "story",
                    "aspect_label": "典故",
                    "chunk_type": "story",
                },
            }
        )

    aspects = sign.get("aspects", {})

    if isinstance(aspects, dict):
        for aspect, text in aspects.items():
            text = str(text or "").strip()

            if not text:
                continue

            aspect_label = ASPECT_LABELS.get(aspect, aspect)

            chunk_text = f"""
签号：{sign_id}
签名：{title}
吉凶等级：{level}
典故标题：{story_title}
问题方向：{aspect_label}

方向解释：
{text}

相关签诗：
{poem_text}

综合提示：
{overall}
""".strip()

            chunks.append(
                {
                    "id": f"{sign_key}_{aspect}",
                    "text": chunk_text,
                    "metadata": {
                        **base_meta,
                        "aspect": aspect,
                        "aspect_label": aspect_label,
                        "chunk_type": "aspect_interpretation",
                    },
                }
            )

    return chunks


def main() -> None:
    args = parse_args()

    jsonl_path = Path(args.jsonl_path).resolve()
    persist_dir = Path(args.persist_dir).resolve()

    if not jsonl_path.exists():
        raise FileNotFoundError(f"JSONL file not found: {jsonl_path}")

    persist_dir.mkdir(parents=True, exist_ok=True)

    signs = load_jsonl(jsonl_path)

    all_chunks = []

    for sign in signs:
        all_chunks.extend(build_chunks(sign))

    print(f"Loaded signs: {len(signs)}")
    print(f"Built chunks: {len(all_chunks)}")
    print(f"Embedding model: {args.embedding_model}")

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=args.embedding_model
    )

    client = chromadb.PersistentClient(path=str(persist_dir))

    if args.reset:
        try:
            client.delete_collection(args.collection)
            print(f"Deleted existing collection: {args.collection}")
        except Exception:
            print(f"No existing collection to delete: {args.collection}")

    collection = client.get_or_create_collection(
        name=args.collection,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [chunk["id"] for chunk in all_chunks]
    documents = [chunk["text"] for chunk in all_chunks]
    metadatas = [normalize_metadata(chunk["metadata"]) for chunk in all_chunks]

    batch_size = 64

    for start in range(0, len(all_chunks), batch_size):
        end = start + batch_size

        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )

        print(f"Inserted chunks {start} - {min(end, len(all_chunks))}")

    print("=" * 80)
    print("Ingestion completed.")
    print(f"Collection: {args.collection}")
    print(f"Persist dir: {persist_dir}")
    print(f"Signs: {len(signs)}")
    print(f"Chunks: {len(all_chunks)}")
    print(f"Collection count: {collection.count()}")


if __name__ == "__main__":
    main()