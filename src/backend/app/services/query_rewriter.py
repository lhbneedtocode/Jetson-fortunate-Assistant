from __future__ import annotations

from app.schemas.chat import ChatTurn


FOLLOW_UP_MARKERS = (
    "what about",
    "how about",
    "what is the time",
    "and the",
    "then what",
    "那",
    "那么",
    "那 presentation",
    "那时间",
)


def build_retrieval_query(question: str, history: list[ChatTurn] | None = None) -> str:
    normalized_question = " ".join(question.split()).strip()
    if not normalized_question:
        return normalized_question

    history = history or []
    if not _looks_like_follow_up(normalized_question):
        return normalized_question

    recent_user = _last_user_turn(history)
    if not recent_user:
        return normalized_question

    return f"{recent_user} Follow-up question: {normalized_question}"


def _looks_like_follow_up(question: str) -> bool:
    lowered = question.lower()
    if len(question.split()) <= 6:
        return True
    return any(marker in lowered for marker in FOLLOW_UP_MARKERS)


def _last_user_turn(history: list[ChatTurn]) -> str | None:
    for turn in reversed(history):
        if turn.role == "user":
            return turn.content
    return None
