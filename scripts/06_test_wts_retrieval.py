from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions


ROOT = Path(__file__).resolve().parents[1]

CHROMA_DIR = ROOT / "data" / "chroma"
COLLECTION_NAME = "fortune_knowledge"
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"


def main() -> None:
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
    )

    print(f"Collection count: {collection.count()}")

    sign_key = "wong_tai_sin_100_023"

    query = "我最近找实习和工作机会顺不顺利？事业 求职 工作 机会"

    result = collection.query(
        query_texts=[query],
        n_results=6,
        where={"sign_key": sign_key},
        include=["documents", "metadatas", "distances"],
    )

    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    distances = result["distances"][0]

    print("=" * 80)
    print(f"Query: {query}")
    print(f"Filter: sign_key = {sign_key}")
    print(f"Retrieved: {len(documents)}")
    print("=" * 80)

    for i, (doc, meta, distance) in enumerate(zip(documents, metadatas, distances), start=1):
        print(f"[Rank {i}]")
        print(f"distance: {distance}")
        print(f"sign_id: {meta.get('sign_id')}")
        print(f"level: {meta.get('level')}")
        print(f"story_title: {meta.get('story_title')}")
        print(f"aspect: {meta.get('aspect')}")
        print(f"aspect_label: {meta.get('aspect_label')}")
        print(f"chunk_type: {meta.get('chunk_type')}")
        print("text preview:")
        print(doc[:500])
        print("-" * 80)


if __name__ == "__main__":
    main()