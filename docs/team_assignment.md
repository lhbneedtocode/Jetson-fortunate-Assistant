# Team Assignment

## Project

- Title: Jetson-based Voice Course Assistant for Lab and Project Support
- Course: IEMS5709A-25R2
- Group: Group 6

## Team Collaboration Principle

The project is divided into four work areas so that each member has a clear ownership scope while still supporting integration with the rest of the system.

## Member 1: Frontend and User Interaction

### Main Responsibility

- Design and implement the browser user interface

### Specific Work

- text input page
- recording button and microphone interaction
- conversation history display
- RAG process visualization
- citation rendering
- audio reply playback

### Deliverables

- frontend page under `src/frontend/static/`
- browser-side interaction logic
- user-facing demo flow

## Member 2: Knowledge Base and Retrieval

### Main Responsibility

- Build and maintain the course knowledge base

### Specific Work

- collect and organize source documents under `data/raw`
- curate repo notes and deployment notes
- maintain ingestion logic
- test chunking and retrieval quality
- rebuild and sync `data/chroma` when the knowledge base changes

### Deliverables

- source document organization
- retrieval-related scripts and notes
- updated vector database content

## Member 3: Voice Pipeline Integration

### Main Responsibility

- Implement and validate ASR and TTS workflow

### Specific Work

- backend ASR integration
- backend TTS integration
- browser recording validation
- audio request/response testing
- debugging voice interaction issues during deployment

### Deliverables

- audio request flow
- transcript handling
- audio reply generation and playback support

## Member 4: Backend Orchestration and Deployment

### Main Responsibility

- Own backend orchestration and Jetson deployment

### Specific Work

- FastAPI backend routes
- LLM client integration
- prompt design
- multi-turn context handling
- Docker Compose configuration
- Jetson deployment, service startup, and troubleshooting

### Deliverables

- backend API logic
- compose deployment configuration
- Jetson runbook

## Shared Responsibilities

All members should contribute to:

- final system integration
- demo preparation
- bug fixing before presentation
- final report and presentation slides

## Suggested Report Attribution

The report can describe team contribution in the following structure:

- Member 1: frontend interaction and UI presentation
- Member 2: knowledge base construction and retrieval
- Member 3: ASR/TTS voice pipeline integration
- Member 4: backend orchestration, LLM integration, and Jetson deployment

## Suggested Demo Attribution

- Member 1: demo the interface and interaction flow
- Member 2: explain the knowledge base and evidence retrieval
- Member 3: explain ASR/TTS voice interaction
- Member 4: explain backend architecture and deployment on Jetson
