from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}


@dataclass
class LoadedDocument:
    source: str
    content: str
    metadata: dict[str, object]


def collect_source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)
    return sorted(files)


def load_document(path: Path, source_root: Path) -> list[LoadedDocument]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _load_pdf(path, source_root)
    if suffix in {".md", ".txt"}:
        text = path.read_text(encoding="utf-8")
        return [
            LoadedDocument(
                source=str(path.relative_to(source_root)),
                content=text,
                metadata={
                    "source": str(path.relative_to(source_root)),
                    "filename": path.name,
                    "file_type": suffix.lstrip("."),
                },
            )
        ]
    raise ValueError(f"Unsupported file type: {path}")


def _load_pdf(path: Path, source_root: Path) -> list[LoadedDocument]:
    reader = PdfReader(str(path))
    docs: list[LoadedDocument] = []
    relative_path = str(path.relative_to(source_root))

    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        docs.append(
            LoadedDocument(
                source=relative_path,
                content=text,
                metadata={
                    "source": relative_path,
                    "filename": path.name,
                    "file_type": "pdf",
                    "page": index,
                },
            )
        )
    return docs
