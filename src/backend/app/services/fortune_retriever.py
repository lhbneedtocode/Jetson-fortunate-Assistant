from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils import embedding_functions


ROOT = Path(__file__).resolve().parents[4]

DEFAULT_CHROMA_DIR = ROOT / "data" / "chroma"
DEFAULT_COLLECTION = "fortune_knowledge"
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"


@dataclass
class FortuneChunk:
    text: str
    metadata: dict[str, Any]
    distance: float | None = None
    score: float | None = None


class FortuneRetriever:
    """
    Retriever for Wong Tai Sin fortune-stick RAG.

    Core idea:
    1. The user draws a sign first.
    2. We filter Chroma by sign_key.
    3. Then we retrieve chunks only inside that sign.
    """

    def __init__(
        self,
        persist_dir: str | None = None,
        collection_name: str | None = None,
        embedding_model: str | None = None,
    ) -> None:
        self.persist_dir = persist_dir or os.getenv("CHROMA_DIR", str(DEFAULT_CHROMA_DIR))
        self.collection_name = collection_name or os.getenv("CHROMA_COLLECTION", DEFAULT_COLLECTION)
        self.embedding_model = embedding_model or os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)

        self._client = None
        self._collection = None

    def _get_collection(self):
        if self._collection is not None:
            return self._collection

        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model
        )

        self._client = chromadb.PersistentClient(path=self.persist_dir)
        self._collection = self._client.get_collection(
            name=self.collection_name,
            embedding_function=embedding_fn,
        )

        return self._collection

    @staticmethod
    def _distance_to_score(distance: float | int | None) -> float:
        if distance is None:
            return 0.0

        try:
            distance_float = float(distance)
        except Exception:
            return 0.0

        return 1.0 / (1.0 + max(distance_float, 0.0))

    @staticmethod
    def _normalize_sign_id(sign_id: str | int) -> str:
        return f"{int(str(sign_id).strip()):03d}"

    @staticmethod
    def _priority(metadata: dict[str, Any], target_aspect: str | None) -> int:
        """
        Smaller priority means earlier in final evidence order.
        We want target aspect first, then overview, poem, story, then others.
        """
        aspect = str(metadata.get("aspect", ""))
        chunk_type = str(metadata.get("chunk_type", ""))

        if target_aspect and aspect == target_aspect:
            return 0

        if aspect == "general" or chunk_type == "overview":
            return 1

        if aspect == "poem" or chunk_type == "poem":
            return 2

        if aspect == "story" or chunk_type == "story":
            return 3

        return 4


    def get_sign_chunks(
        self,
        sign_id: str | int,
    ) -> list[FortuneChunk]:
        """Return all stored chunks for one fortune sign without semantic re-ranking."""
        collection = self._get_collection()

        normalized_sign_id = self._normalize_sign_id(sign_id)
        sign_key = f"wong_tai_sin_100_{normalized_sign_id}"

        result = collection.get(
            where={"sign_key": sign_key},
            include=["documents", "metadatas"],
        )

        documents = result.get("documents", []) or []
        metadatas = result.get("metadatas", []) or []

        chunks: list[FortuneChunk] = []
        for text, metadata in zip(documents, metadatas):
            chunks.append(
                FortuneChunk(
                    text=text or "",
                    metadata=metadata or {},
                    distance=None,
                    score=None,
                )
            )

        chunks.sort(
            key=lambda c: (
                str((c.metadata or {}).get("sign_id", "")),
                str((c.metadata or {}).get("aspect", "")),
                str((c.metadata or {}).get("chunk_type", "")),
            )
        )
        return chunks

    def retrieve(
        self,
        query: str,
        sign_id: str | int,
        aspect: str | None = None,
        top_k: int = 6,
    ) -> list[FortuneChunk]:
        collection = self._get_collection()

        normalized_sign_id = self._normalize_sign_id(sign_id)
        sign_key = f"wong_tai_sin_100_{normalized_sign_id}"

        # 每支签的 chunk 不多，所以这里多取一些，再手动把目标 aspect 排前面。
        result = collection.query(
            query_texts=[query],
            n_results=20,
            where={"sign_key": sign_key},
            include=["documents", "metadatas", "distances"],
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        chunks: list[FortuneChunk] = []

        for text, metadata, distance in zip(documents, metadatas, distances):
            metadata = metadata or {}
            chunks.append(
                FortuneChunk(
                    text=text,
                    metadata=metadata,
                    distance=float(distance) if distance is not None else None,
                    score=self._distance_to_score(distance),
                )
            )

        # 手动重排：同一签内，优先返回用户问题方向对应的 chunk。
        chunks.sort(
            key=lambda c: (
                self._priority(c.metadata, aspect),
                -(c.score or 0.0),
            )
        )

        return chunks[:top_k]