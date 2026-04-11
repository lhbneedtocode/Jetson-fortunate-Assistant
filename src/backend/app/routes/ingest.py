from fastapi import APIRouter

router = APIRouter()


@router.post("/ingest")
def ingest() -> dict[str, str]:
    return {"status": "todo"}

