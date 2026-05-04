# Jetson Voice Course Assistant

Course project repository for `IEMS5709A-25R2` Group 6.

This project implements a Jetson-based voice course assistant for lab and project support. The system reuses the course LLM/ASR/TTS deployment pattern and adds a course-specific RAG backend plus a lightweight web frontend.
## testing
## Repository Structure

```text
Jetson-Voice-Course-Assistant/
├── README.md
├── .gitignore
├── docker-compose.yml
├── docs/
│   ├── abstract_en.md
│   └── abstract_cn.md
├── data/
│   ├── raw/            # source course docs and curated repo notes
│   ├── processed/      # parsed/chunked intermediates
│   └── chroma/         # persisted vector database
├── scripts/
│   └── ingest_docs.py  # offline knowledge-base build
├── src/
│   ├── backend/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── main.py
│   │       ├── routes/
│   │       │   ├── chat.py
│   │       │   ├── ingest.py
│   │       │   └── health.py
│   │       ├── services/
│   │       │   ├── llm_client.py
│   │       │   ├── asr_client.py
│   │       │   ├── tts_client.py
│   │       │   ├── retriever.py
│   │       │   └── prompt_builder.py
│   │       └── schemas/
│   │           └── chat.py
│   ├── frontend/
│   │   ├── Dockerfile
│   │   └── static/
│   │       ├── index.html
│   │       ├── app.js
│   │       └── style.css
│   └── rag/
│       ├── chunking.py
│       ├── loaders.py
│       └── embeddings.py
└── tests/
    ├── test_health.py
    └── test_retriever.py
```

## Architecture

- `frontend`: browser UI for text/voice input and answer display
- `backend`: FastAPI orchestration service for RAG, citations, and model calls
- `rag`: document loading, chunking, embedding, and retrieval helpers
- `data/raw`: course PDFs, markdown docs, and curated repository knowledge notes
- `docker-compose.yml`: local/Jetson multi-service layout

## Initial Development Focus

1. Build the knowledge base from course docs and repository notes.
2. Implement text-based RAG QA in the backend.
3. Add voice input/output through ASR and TTS services.
4. Deploy the full stack to Jetson with Docker Compose.
