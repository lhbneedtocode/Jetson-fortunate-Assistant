from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.routes.chat import router as chat_router
from app.routes.health import router as health_router
from app.routes.ingest import router as ingest_router
from app.routes.fortune import router as fortune_router

app = FastAPI(title="Voice Course Assistant Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:13000",
        "http://127.0.0.1:13000",
        "http://localhost:23000",
        "http://127.0.0.1:23000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(chat_router, prefix="/api")
app.include_router(ingest_router, prefix="/api")
app.include_router(fortune_router, prefix="/api")


# Serve frontend static files
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend" / "static"
print(f"[frontend] static dir = {FRONTEND_DIR}, exists = {FRONTEND_DIR.exists()}")
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

