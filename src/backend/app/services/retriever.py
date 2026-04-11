from __future__ import annotations

import os
from dataclasses import dataclass

import chromadb
from chromadb.utils import embedding_functions


DEFAULT_COLLECTION = "course_knowledge"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@dataclass
class RetrievedChunk:
    text: str
    source: str
    page: int | None
    score: float | None
    metadata: dict[str, object]


class Retriever:
    def __init__(
        self,
        persist_dir: str | None = None,
        collection_name: str | None = None,
        embedding_model: str | None = None,
    ) -> None:
        self.persist_dir = persist_dir or os.getenv("CHROMA_DIR", "/app/data/chroma")
        self.collection_name = collection_name or os.getenv(
            "CHROMA_COLLECTION", DEFAULT_COLLECTION
        )
        self.embedding_model = embedding_model or os.getenv(
            "EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL
        )
        self._collection = None

    def retrieve(self, query: str, top_k: int = 4) -> list[RetrievedChunk]:
        if not query.strip():
            return []

        collection = self._get_collection()
        result = collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        chunks: list[RetrievedChunk] = []
        for text, metadata, distance in zip(documents, metadatas, distances):
            meta = metadata or {}
            page = meta.get("page")
            chunks.append(
                RetrievedChunk(
                    text=text,
                    source=str(meta.get("source", "unknown")),
                    page=int(page) if isinstance(page, (int, float, str)) and str(page).isdigit() else None,
                    score=_distance_to_score(distance),
                    metadata=meta,
                )
            )
        return chunks

    def _get_collection(self):
        if self._collection is None:
            embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model
            )
            client = chromadb.PersistentClient(path=self.persist_dir)
            self._collection = client.get_collection(
                name=self.collection_name,
                embedding_function=embedding_fn,
            )
        return self._collection


def _distance_to_score(distance: float | None) -> float | None:
    if distance is None:
        return None
    # Convert cosine distance to a simple relevance score.
    return max(0.0, 1.0 - float(distance))
