from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src" / "backend"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.services.retriever import Retriever


TEST_QUERIES = [
    {
        "question": "How do I connect to the Jetson via SSH?",
        "expected": "labs/Lab1_Prerequisites.md",
    },
    {
        "question": "What endpoint does the ASR service provide for transcription?",
        "expected": "repo_notes/lab2_asr_api_note.md",
    },
]


def main() -> None:
    retriever = Retriever(
        persist_dir=str(ROOT / "data" / "chroma"),
        collection_name="course_knowledge",
    )

    for index, item in enumerate(TEST_QUERIES, start=1):
        print("=" * 80)
        print(f"Test {index}")
        print(f"Question: {item['question']}")
        print(f"Expected source: {item['expected']}")
        print("-" * 80)

        results = retriever.retrieve(item["question"], top_k=3)
        if not results:
            print("No retrieval results returned.\n")
            continue

        hit = False
        for rank, chunk in enumerate(results, start=1):
            snippet = chunk.text[:180].replace("\n", " ").strip()
            print(f"Rank {rank}")
            print(f"Source: {chunk.source}")
            print(f"Page: {chunk.page}")
            print(f"Score: {chunk.score}")
            print(f"Snippet: {snippet}")
            print()
            if chunk.source == item["expected"]:
                hit = True

        print(f"Hit in top 3: {'YES' if hit else 'NO'}")
        print()


if __name__ == "__main__":
    main()
