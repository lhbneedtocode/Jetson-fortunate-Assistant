from __future__ import annotations

from dataclasses import dataclass

from rag.loaders import LoadedDocument


@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: dict[str, object]


def chunk_documents(
    documents: list[LoadedDocument],
    chunk_size: int = 900,
    chunk_overlap: int = 150,
) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be non-negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: list[Chunk] = []
    stride = chunk_size - chunk_overlap

    for doc_index, document in enumerate(documents):
        normalized = _normalize_whitespace(document.content)
        if not normalized:
            continue

        start = 0
        piece_index = 0
        while start < len(normalized):
            end = min(len(normalized), start + chunk_size)
            text = normalized[start:end].strip()
            if text:
                metadata = dict(document.metadata)
                metadata["chunk_index"] = piece_index
                chunks.append(
                    Chunk(
                        chunk_id=_build_chunk_id(doc_index, piece_index, metadata),
                        text=text,
                        metadata=metadata,
                    )
                )
            if end >= len(normalized):
                break
            start += stride
            piece_index += 1
    return chunks


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def _build_chunk_id(doc_index: int, piece_index: int, metadata: dict[str, object]) -> str:
    source = str(metadata.get("source", f"doc-{doc_index}")).replace("/", "_")
    page = metadata.get("page")
    if page is not None:
        return f"{source}-p{page}-c{piece_index}"
    return f"{source}-c{piece_index}"
