from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rag.chunking import chunk_documents
from rag.loaders import collect_source_files, load_document


DEFAULT_COLLECTION = "course_knowledge"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the course knowledge base.")
    parser.add_argument(
        "--source-dir",
        default=str(ROOT / "data" / "raw"),
        help="Directory containing PDF/MD/TXT source files.",
    )
    parser.add_argument(
        "--persist-dir",
        default=str(ROOT / "data" / "chroma"),
        help="Directory used by Chroma for persistence.",
    )
    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
        help="Chroma collection name.",
    )
    parser.add_argument(
        "--embedding-model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="SentenceTransformer model name for embeddings.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=900,
        help="Chunk size in characters.",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=150,
        help="Chunk overlap in characters.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and recreate the collection before ingesting.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_dir = Path(args.source_dir).resolve()
    persist_dir = Path(args.persist_dir).resolve()
    persist_dir.mkdir(parents=True, exist_ok=True)

    files = collect_source_files(source_dir)
    if not files:
        print(f"No supported files found under {source_dir}")
        return

    documents = []
    for path in files:
        documents.extend(load_document(path, source_dir))

    chunks = chunk_documents(
        documents,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    if not chunks:
        print("No content chunks were produced. Check the source documents.")
        return

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=args.embedding_model
    )
    client = chromadb.PersistentClient(path=str(persist_dir))

    if args.reset:
        try:
            client.delete_collection(args.collection)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=args.collection,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [chunk.chunk_id for chunk in chunks]
    texts = [chunk.text for chunk in chunks]
    metadatas = [_stringify_metadata(chunk.metadata) for chunk in chunks]

    # Chroma can upsert in batches to avoid oversized requests.
    batch_size = 64
    for start in range(0, len(chunks), batch_size):
        end = start + batch_size
        collection.upsert(
            ids=ids[start:end],
            documents=texts[start:end],
            metadatas=metadatas[start:end],
        )

    print(
        json.dumps(
            {
                "source_dir": str(source_dir),
                "persist_dir": str(persist_dir),
                "collection": args.collection,
                "files": len(files),
                "documents": len(documents),
                "chunks": len(chunks),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _stringify_metadata(metadata: dict[str, object]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            normalized[key] = value
        else:
            normalized[key] = json.dumps(value, ensure_ascii=False)
    return normalized


if __name__ == "__main__":
    main()
