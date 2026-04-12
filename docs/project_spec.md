# Project Spec

## Project Information

- Project Title: Jetson-based Voice Course Assistant for Lab and Project Support
- Course: IEMS5709A-25R2
- Group: Group 6

## 1. Project Objective

The project aims to build a course-specific voice assistant deployed on Jetson for lab and project support. The system is designed to help students, teaching assistants, and instructors query course rules, lab instructions, deployment notes, API usage details, and troubleshooting knowledge through text or voice interaction.

The project focuses on retrieval-grounded answers rather than open-domain chatbot behavior. Its main value is to integrate existing course lab assets into a usable teaching-support system that can answer practical questions with cited evidence.

## 2. Problem Statement

Students repeatedly ask similar questions during labs and project work, such as:

- how to connect to the Jetson
- how to call the ASR API
- how to configure multi-service deployment
- why a service failed during deployment

These questions are often answered from scattered course documents, lab instructions, and deployment experience. The project addresses this by building a localized RAG system with a voice-capable frontend and a multi-service backend running on Jetson.

## 3. Scope

### In Scope

- Text question answering over course materials
- Voice question answering through ASR, RAG, LLM, and TTS
- Citation display for retrieved sources
- Lightweight multi-turn conversation support
- Jetson deployment using Docker Compose

### Current Knowledge Scope

- course repository README and lab instructions
- environment and prerequisite setup notes
- curated repository notes
- selected lecture slides
- deployment and troubleshooting notes extracted from lab reports

## 4. System Architecture

The system is composed of five main parts:

1. Frontend
   Browser UI for text input, microphone recording, transcript display, answer display, evidence display, and audio playback.

2. Backend
   FastAPI orchestration service that handles:
   - text question requests
   - audio question requests
   - retrieval
   - prompt construction
   - LLM calls
   - optional TTS synthesis

3. Retrieval Layer
   Chroma-based vector retrieval over a curated course knowledge base.

4. Model Services
   - vLLM for Qwen3-4B answer generation
   - Faster-Whisper ASR service
   - Kokoro TTS service

5. Deployment Layer
   Docker Compose orchestration on a remote Jetson machine accessed by SSH port forwarding.

## 5. Main Workflow

### Text QA Flow

1. User enters a text question in the browser.
2. Frontend sends the request to `POST /api/chat`.
3. Backend optionally rewrites the retrieval query if the question looks like a follow-up.
4. Retriever searches the Chroma knowledge base.
5. Backend builds a grounded prompt using:
   - the current question
   - recent conversation history
   - retrieved evidence
6. vLLM generates the answer.
7. Backend returns:
   - answer
   - citations
   - evidence snippets
   - optional TTS audio
8. Frontend renders the result.

### Voice QA Flow

1. User records audio in the browser.
2. Frontend uploads audio to `POST /api/chat/audio`.
3. Backend sends the audio to the ASR service.
4. ASR returns a transcript.
5. Backend runs the same retrieval and answer-generation flow as text QA.
6. Backend optionally sends the final answer to TTS.
7. Frontend displays transcript, answer, evidence, and playable audio.

## 6. Backend API Design

### `GET /health`

Purpose:
- backend health check

Response:
```json
{"status": "ok"}
```

### `POST /api/chat`

Purpose:
- text-based QA request

Request body:
```json
{
  "question": "How do I connect to the Jetson via SSH?",
  "history": [
    {"role": "user", "content": "previous question"},
    {"role": "assistant", "content": "previous answer"}
  ],
  "synthesize_speech": false,
  "voice": "af_bella"
}
```

Response fields:
- `answer`
- `citations`
- `evidence`
- `refusal`
- `audio_base64`

### `POST /api/chat/audio`

Purpose:
- audio-based QA request

Form fields:
- `file`
- `synthesize_speech`
- `voice`

Response fields:
- `transcript`
- `answer`
- `citations`
- `evidence`
- `refusal`
- `audio_base64`

## 7. Knowledge Base Design

### Input Sources

- `data/raw/course_repo`
- `data/raw/labs`
- `data/raw/slides`
- `data/raw/repo_notes`

### Ingestion Pipeline

1. Load PDF, markdown, and text files.
2. Extract page-level text from PDF files.
3. Normalize and chunk text.
4. Compute embeddings.
5. Store chunks and metadata in Chroma.

### Metadata Used

- source
- filename
- file type
- page
- chunk index

## 8. Retrieval and Answering Strategy

### Retrieval

- Chroma persistent collection: `course_knowledge`
- top-k retrieval over stored chunks
- metadata returned with each chunk

### Multi-turn Support

- frontend stores recent conversation turns
- backend receives recent turns in `history`
- retrieval can use a rewritten query for short or follow-up questions
- prompt includes recent conversation context

### Answer Constraints

- answer only from retrieved evidence
- do not invent missing rules or policies
- return refusal if evidence is insufficient
- strip hidden reasoning from final output

## 9. Deployment Design

The Jetson deployment uses Docker Compose to run:

- `frontend`
- `backend`
- `vllm`
- `asr`
- `tts`

Important deployment considerations:

- `vllm` uses conservative memory parameters
- ASR mounts `/workspace`
- frontend is accessed from a local browser through SSH port forwarding
- backend uses the local Chroma store under `data/chroma`

## 10. Current Implementation Status

Implemented:

- repository structure
- ingestion script
- retrieval service
- text QA
- voice QA
- evidence visualization
- lightweight multi-turn support
- follow-up retrieval rewriting
- Jetson compose deployment

Not fully validated yet:

- repeated voice interaction quality under longer sessions
- broader evaluation over more course PDFs
- optional future improvements such as stronger session memory or better retrieval ranking

## 11. Assumptions and Limitations

- knowledge quality depends on whether the relevant documents are included in `data/raw`
- current retrieval is still relatively lightweight and may miss some follow-up intent
- the system is course-specific and should not be treated as an open-domain assistant
- Jetson resource limits may still require tuning when the document set grows

## 12. Demo Goals

The final demo should show:

1. a stable text QA case
2. a stable voice QA case
3. visible evidence and citations
4. one deployment or troubleshooting question answered from report-derived notes
