# Project Progress

## Project

- Title: Jetson-based Voice Course Assistant for Lab and Project Support
- Course: IEMS5709A-25R2
- Group: Group 6

## Current Goal

Build a Jetson-based course assistant that supports course-related question answering through a pipeline of text/voice input, retrieval over course materials, LLM answering, and optional TTS output.

## What We Have Done

### 1. Project direction and abstract

- Confirmed the project topic and scope.
- Defined the system as a course-specific assistant instead of a general chatbot.
- Wrote English and Chinese abstract/design documents in the `proj/` directory outside this repo.

### 2. New project repository

- Created a new standalone repository:
  `Jetson-Voice-Course-Assistant`
- Initialized git for the new repository.
- Defined the initial project structure with:
  - `src/backend`
  - `src/frontend`
  - `src/rag`
  - `data/raw`
  - `data/processed`
  - `data/chroma`
  - `scripts`
  - `tests`

### 3. Initial backend and frontend skeleton

- Added a FastAPI backend entrypoint.
- Added basic routes:
  - `/health`
  - `/api/chat`
  - `/api/ingest`
- Added a minimal frontend page for submitting a text question.
- Added a Docker Compose skeleton for:
  - backend
  - frontend
  - vLLM
  - ASR
  - TTS

### 4. First usable RAG ingestion and retrieval layer

- Implemented document loading for:
  - `.pdf`
  - `.md`
  - `.txt`
- Implemented PDF page extraction with metadata.
- Implemented text chunking with overlap.
- Implemented offline ingestion script:
  - `scripts/ingest_docs.py`
- Implemented first retriever service:
  - `src/backend/app/services/retriever.py`
- Connected `/api/chat` to retrieval so it can return retrieved evidence previews and citations.

### 5. First batch of knowledge-base source files

- Copied course repository documents into:
  - `data/raw/course_repo`
  - `data/raw/labs`
- Added curated repository notes into:
  - `data/raw/repo_notes`
- Current knowledge materials include:
  - course README
  - Lab1/Lab2/Lab3 README
  - Lab1/Lab2/Lab3 Assignment
  - Lab1 Environment
  - Lab1 Prerequisites
  - Lab2 ASR API note
  - Lab3 Compose deployment note

### 6. First local knowledge-base build

- Created a local Python virtual environment in `.venv`.
- Installed the dependencies needed for local RAG ingestion and retrieval testing.
- Ran the first real ingestion successfully with:
  - `12` source files
  - `38` extracted documents
  - `64` chunks
- Built the persisted Chroma knowledge base under `data/chroma`.
- Measured the current Chroma data size:
  - `data/chroma`: about `896K`
- Measured the local Python environment size:
  - `.venv`: about `844M`

### 7. First retrieval smoke test

- Added a simple retrieval smoke test script:
  - `scripts/test_retrieval_smoke.py`
- Tested two representative queries against the local knowledge base.
- Result summary:
  - Query 1: "How do I connect to the Jetson via SSH?"
    - Expected source `labs/Lab1_Prerequisites.md`
    - Hit in top 3: yes
    - Ranked at position 2
  - Query 2: "What endpoint does the ASR service provide for transcription?"
    - Expected source `repo_notes/lab2_asr_api_note.md`
    - Hit in top 3: yes
    - Ranked at position 1
- Initial conclusion:
  - retrieval is working
  - code-note style knowledge entries perform well
  - some ranking refinement may still be useful for course-operation questions

### 8. First RAG answer-generation integration

- Implemented `llm_client.py` using the same OpenAI-compatible vLLM calling style used in the course repository examples.
- Implemented `prompt_builder.py` for course-assistant RAG prompting.
- Updated `/api/chat` so it now:
  - retrieves relevant chunks
  - builds a grounded prompt
  - calls the LLM
  - returns answer + citations + refusal flag
- Added `openai` to backend dependencies.
- Completed syntax checks for the new backend logic.

### 9. First ASR/TTS backend integration

- Implemented `asr_client.py` to call the OpenAI-compatible ASR endpoint:
  - `/v1/audio/transcriptions`
- Implemented `tts_client.py` to call the TTS endpoint:
  - `/v1/audio/speech`
- Extended the chat response schema with:
  - `transcript`
  - `audio_base64`
- Added a new backend route:
  - `POST /api/chat/audio`
- Unified the text and audio flow through the same backend RAG pipeline:
  - text/audio input
  - retrieval
  - prompt building
  - LLM answer
  - optional TTS synthesis
- Added `python-multipart` to backend dependencies.
- Completed syntax checks for the ASR/TTS integration code.

### 10. First voice-enabled frontend integration

- Updated the frontend page to support:
  - text question input
  - microphone recording
  - transcript display
  - citation display
  - audio reply playback
- Added a recording button that uses the browser `MediaRecorder` API.
- Connected the frontend audio flow to:
  - `POST /api/chat/audio`
- Added support for playing returned `audio_base64` in the browser.
- Completed JavaScript syntax checks for the updated frontend code.

### 11. Jetson deployment preparation

- Updated `docker-compose.yml` to better fit full-stack Jetson testing:
  - explicit container names
  - restart policy
  - host port mappings for frontend, backend, vLLM, ASR, and TTS
  - clearer backend environment variables
- Updated the frontend API base logic so it uses the current browser hostname instead of hard-coded `localhost`.
- Added a Jetson runbook:
  - `JETSON_RUNBOOK.md`
- Documented:
  - `git pull`
  - `docker compose up --build -d`
  - running containers on the remote Jetson while opening the frontend from the local Mac
  - SSH port forwarding for `13000` and `18080`
  - service health checks
  - text QA test
  - audio QA test
  - browser voice test
  - common troubleshooting notes

### 12. Lab 3 report cross-check

- Reviewed `lab3/1155238590_Report.pdf` to compare the previous lab deployment with the new project repository.
- Confirmed the key successful Lab 3 practices:
  - SSH port forwarding for browser access
  - reduced vLLM memory settings
  - changing host port to `13000`
  - mounting `/workspace` for ASR to avoid output-path errors
- Updated the new project `docker-compose.yml` based on that experience:
  - added `asr-workspace:/workspace`
  - added `backend-hf-cache` volume for embedding model cache reuse

### 13. Chroma persistence synced through git

- Removed `data/chroma/` from `.gitignore`.
- Added the locally built Chroma knowledge base files into the repository.
- Pushed the persisted knowledge base to GitHub so the Jetson machine can receive it through `git pull`.
- Current Chroma size remains small enough for repository sync:
  - about `896K`

### 14. Answer output cleanup

- Tightened the RAG prompt to explicitly forbid hidden reasoning and `<think>` output.
- Added backend-side answer cleanup to strip `<think>...</think>` blocks before returning the final answer.
- This keeps the frontend answer and TTS output cleaner for demo use.

### 15. Frontend-backend CORS fix

- Added FastAPI `CORSMiddleware` in `src/backend/app/main.py`.
- Allowed browser access from the local forwarded frontend ports used during development.
- This fixes browser `OPTIONS /api/chat` preflight failures when the frontend and backend use different local ports.

### 16. RAG process visualization in UI

- Extended the backend response schema with an `evidence` field containing:
  - source
  - page
  - score
  - snippet
- Updated the frontend to visualize the RAG pipeline more clearly:
  - question step
  - retrieval step
  - generation step
  - speech step
- Added a new evidence card section so retrieved chunks are visible in the UI instead of only final citations.
- This makes the demo feel less empty and helps explain the RAG process during presentation.

### 17. Lightweight multi-turn conversation support

- Added lightweight chat history support to the frontend.
- The frontend now keeps recent turns and displays them in a conversation panel.
- The backend now accepts recent `history` items in `ChatRequest`.
- Prompt construction now includes the recent 1 to 2 rounds of conversation context while keeping retrieval focused on the current user question.
- This makes follow-up questions more natural without turning the system into a heavy session-managed chatbot.

### 18. Follow-up query rewriting for retrieval

- Added a lightweight query rewriting step for short or follow-up-style questions.
- Retrieval now uses a rewritten query that can include the most recent user turn when the current question looks context-dependent.
- This improves follow-up retrieval quality for questions such as:
  - "What about the presentation time?"
  - "How about the grading?"

### 19. Deployment experience notes extracted from reports

- Reviewed the Lab 2 and Lab 3 report PDFs as practical engineering references.
- Converted useful report content into structured reusable notes under `data/raw/repo_notes/`.
- Added new experience-oriented notes for:
  - ASR deployment practice on Jetson
  - multi-service voice pipeline troubleshooting
  - OpenAI-compatible multi-service integration pattern
- This material is intended to improve answers for deployment, integration, and debugging questions after the next knowledge-base rebuild.

### 20. Knowledge base rebuilt with report-derived notes

- Re-ran `scripts/ingest_docs.py --reset` locally after adding the new report-derived notes.
- Updated knowledge-base totals:
  - source files: `15`
  - extracted documents: `41`
  - chunks: `71`
- Updated persisted Chroma size:
  - about `1.2M`
- The refreshed `data/chroma` is ready to sync to Jetson through git.

## Current Status

- Repository structure: ready
- Abstract/design draft: ready
- Basic backend/frontend skeleton: ready
- Offline ingestion script: implemented and tested locally
- Retriever: first version ready
- Knowledge-base raw materials: first batch prepared
- First local Chroma knowledge base: built successfully
- Persisted Chroma knowledge base: tracked in git
- First retrieval smoke test: passed
- LLM answer generation: first version implemented
- ASR/TTS runtime integration in project backend: first version implemented
- Voice-enabled frontend: first version implemented
- Jetson deployment guide: ready
- Lab 3 deployment lessons: incorporated into compose
- Answer formatting cleanup: implemented
- Browser CORS fix: implemented
- RAG process visualization: implemented
- Lightweight multi-turn conversation: implemented
- Follow-up retrieval rewrite: implemented
- Report-derived deployment notes: prepared
- Knowledge base rebuilt with new notes: completed
- Real Jetson deployment for this new project: not started yet

## What Still Needs To Be Done

### High priority

- Add more course materials into `data/raw`
  - lecture slides PDFs
  - project guideline PDFs
  - grading-related documents
  - FAQ notes
- Verify retrieval quality with several course-related questions.
- Decide whether `data/chroma` should be copied to Jetson directly or rebuilt there from raw files.

### Backend

- Add refusal logic when evidence is weak.
- Format citations more clearly in the response.
- Test the new `/api/chat` path against a real running vLLM service.

### Frontend

- Improve chat UI.
- Display citations in a clearer way.
- Test browser recording and playback against the real backend services.

### Voice pipeline

- Test project backend against real ASR and TTS services.
- Support voice question -> text transcription -> RAG -> answer -> speech output in the frontend.

### Deployment

- Run the full stack on the actual Jetson machine.
- Verify Docker Compose settings against the real Jetson environment.
- Confirm the ASR image is available or build it on Jetson.
- Tune memory-related parameters for vLLM, ASR, and TTS if needed.
- Test remote access flow through SSH and browser.

### Knowledge base improvement

- Add more `repo_notes` for important code/config files.
- Decide which PDFs should be included in the course knowledge base.
- Organize raw materials into clearer folders such as:
  - `course_docs`
  - `slides`
  - `labs`
  - `repo_notes`

## Recommended Next Steps

1. Put lecture slides and project-related PDFs into `data/raw`.
2. Run the first real ingestion and test retrieval.
3. Implement LLM answer generation on top of retrieved chunks.
4. Then add ASR and TTS integration.

## Important Paths

- Repo root:
  `/Users/yeylie/Aa/ie/Emgegic topic/Jetson-Voice-Course-Assistant`
- Raw knowledge-base files:
  `/Users/yeylie/Aa/ie/Emgegic topic/Jetson-Voice-Course-Assistant/data/raw`
- Ingestion script:
  `/Users/yeylie/Aa/ie/Emgegic topic/Jetson-Voice-Course-Assistant/scripts/ingest_docs.py`
- Retriever:
  `/Users/yeylie/Aa/ie/Emgegic topic/Jetson-Voice-Course-Assistant/src/backend/app/services/retriever.py`
