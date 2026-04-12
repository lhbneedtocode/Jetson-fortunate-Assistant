from __future__ import annotations

from app.schemas.chat import ChatTurn
from app.services.retriever import RetrievedChunk


SYSTEM_PROMPT = """You are a course assistant for an edge computing class.
Answer only using the provided course materials.
If the retrieved evidence is insufficient, say clearly that you cannot confirm the answer from the current course materials.
Do not invent policies, deadlines, requirements, or technical instructions.
Do not output hidden reasoning, internal analysis, or any <think> tags.
Keep the answer concise and practical."""


def build_rag_prompt(
    question: str,
    chunks: list[RetrievedChunk],
    history: list[ChatTurn] | None = None,
) -> tuple[str, str]:
    recent_history = _format_recent_history(history or [])
    if not chunks:
        return (
            SYSTEM_PROMPT,
            (
                f"{recent_history}"
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
        f"{recent_history}"
        "Question:\n"
        f"{question}\n\n"
        "Retrieved evidence:\n"
        f"{chr(10).join(evidence_blocks)}\n\n"
        "Instructions:\n"
        "- Answer only from the evidence above.\n"
        "- If the evidence is insufficient, say so clearly.\n"
        "- Do not mention evidence numbers.\n"
        "- Do not output any reasoning process, chain-of-thought, or <think> tags.\n"
        "- Keep the answer short.\n"
    )
    return SYSTEM_PROMPT, user_prompt


def _format_recent_history(history: list[ChatTurn]) -> str:
    if not history:
        return ""

    recent_turns = history[-4:]
    lines = ["Recent conversation context:"]
    for turn in recent_turns:
        role = "User" if turn.role == "user" else "Assistant"
        lines.append(f"{role}: {turn.content}")
    return "\n".join(lines) + "\n\n"
