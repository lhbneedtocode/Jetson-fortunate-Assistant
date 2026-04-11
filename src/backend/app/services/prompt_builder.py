from __future__ import annotations

from app.services.retriever import RetrievedChunk


SYSTEM_PROMPT = """You are a course assistant for an edge computing class.
Answer only using the provided course materials.
If the retrieved evidence is insufficient, say clearly that you cannot confirm the answer from the current course materials.
Do not invent policies, deadlines, requirements, or technical instructions.
Keep the answer concise and practical."""


def build_rag_prompt(question: str, chunks: list[RetrievedChunk]) -> tuple[str, str]:
    if not chunks:
        return (
            SYSTEM_PROMPT,
            (
                "Question:\n"
                f"{question}\n\n"
                "Retrieved evidence:\n"
                "None.\n\n"
                "Please answer that you cannot confirm the answer from the current course materials."
            ),
        )

    evidence_blocks = []
    for index, chunk in enumerate(chunks, start=1):
        source_line = f"Source: {chunk.source}"
        if chunk.page is not None:
            source_line += f", page {chunk.page}"
        evidence_blocks.append(
            f"[Evidence {index}]\n{source_line}\nContent: {chunk.text}"
        )

    user_prompt = (
        "Question:\n"
        f"{question}\n\n"
        "Retrieved evidence:\n"
        f"{chr(10).join(evidence_blocks)}\n\n"
        "Instructions:\n"
        "- Answer only from the evidence above.\n"
        "- If the evidence is insufficient, say so clearly.\n"
        "- Do not mention evidence numbers.\n"
        "- Keep the answer short.\n"
    )
    return SYSTEM_PROMPT, user_prompt
