# Jetson Runbook

## Purpose

This document explains how to pull the repository on the Jetson machine, start the full stack with Docker Compose, and test both text and voice question-answering flows.

## Assumptions

- You can already SSH into the Jetson machine.
- Docker and Docker Compose are available on the Jetson machine.
- The Jetson machine already has access to the required model path:
  - `/opt/models/Qwen3-4B-quantized.w4a16`
- The ASR image `faster-whisper:fastapi` is already available locally on the Jetson machine, or your team has built it there before.

## 1. Pull the Latest Code

### On the Jetson machine

```bash
cd ~
git clone <your-project-repo-url>
cd Jetson-Voice-Course-Assistant
```

If the repo is already cloned:

```bash
cd ~/Jetson-Voice-Course-Assistant
git pull
```

### Recommended workflow

- Run all containers on the remote Jetson machine
- Open the frontend from your local Mac browser
- Use SSH port forwarding so the browser sees `localhost`

## 2. Check the Knowledge Base Data

Make sure these directories exist:

```bash
ls data/raw
ls data/chroma
```

If `data/chroma` is missing, you can either:

- pull it from git if you decide to version it, or
- rebuild it later from `data/raw`

## 3. Build and Start the Full Stack

### On the Jetson machine

From the project root:

```bash
docker compose up --build -d
```

Check running services:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f vllm
docker compose logs -f asr
docker compose logs -f tts
```

Stop everything:

```bash
docker compose down
```

## 4. Service Endpoints

After startup, these ports should be available on the Jetson host:

- Frontend: `13000`
- Backend: `18080`
- vLLM: `8000`
- ASR: `5092`
- TTS: `8880`

## 5. Basic Health Check

Check backend:

```bash
curl http://localhost:18080/health
```

Check vLLM:

```bash
curl http://localhost:8000/v1/models
```

Check ASR:

```bash
curl http://localhost:5092/health
```

## 6. Test Text QA

```bash
curl -X POST http://localhost:18080/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I connect to the Jetson via SSH?",
    "synthesize_speech": false
  }'
```

You should get a JSON response containing:

- `answer`
- `citations`
- `refusal`

## 7. Test Audio QA

If you already have a local test audio file on the Jetson machine:

```bash
curl -X POST http://localhost:18080/api/chat/audio \
  -F "file=@/path/to/test_audio.wav" \
  -F "synthesize_speech=true" \
  -F "voice=af_bella"
```

You should get a JSON response containing:

- `transcript`
- `answer`
- `citations`
- `audio_base64`

## 8. Open the Frontend in a Browser

### Recommended: use SSH port forwarding from your local Mac

### On your local Mac

Minimal forwarding:

```bash
ssh -L 13000:localhost:13000 -L 18080:localhost:18080 <user>@<jetson-ip>
```

Extended forwarding for direct service debugging:

```bash
ssh \
  -L 13000:localhost:13000 \
  -L 18080:localhost:18080 \
  -L 8000:localhost:8000 \
  -L 5092:localhost:5092 \
  -L 8880:localhost:8880 \
  <user>@<jetson-ip>
```

Then, on your local Mac browser, open:

```text
http://localhost:13000
```

The frontend is written to call the backend on the same hostname with port `18080`, so when the page is opened through SSH forwarding, requests will automatically go to the forwarded backend.

### Why SSH forwarding is recommended

- Browser microphone access is usually easier on `localhost`
- It avoids mixed host/IP issues between frontend and backend
- It makes local debugging easier for `frontend` and `backend`

### Alternative: direct browser access to Jetson IP

If you access the Jetson directly from the browser:

- `http://<jetson-ip>:13000`

This can work, but microphone permission is often more troublesome than the SSH-forwarded `localhost` workflow.

### Summary

- Containers run on the remote Jetson
- Browser runs on your local Mac
- SSH forwarding is the recommended access method

## 9. End-to-End Test Flow

### Step A: start services on Jetson

On the Jetson machine:

```bash
cd ~/Jetson-Voice-Course-Assistant
docker compose up --build -d
docker compose ps
```

### Step B: open SSH tunnel from your Mac

On your local Mac:

```bash
ssh -L 13000:localhost:13000 -L 18080:localhost:18080 <user>@<jetson-ip>
```

### Step C: open the frontend

On your local Mac browser:

```text
http://localhost:13000
```

### Step D: test text QA

1. Type a question in the text box
2. Click `Ask by Text`
3. Check:
   - answer
   - citations
   - optional audio reply

### Step E: test voice QA

1. Click `Start Recording`
2. Speak a short course-related question
3. Click again to stop recording
4. Check:
   - transcript
   - answer
   - citations
   - audio reply playback

## 10. Browser Voice Test

If the stack is already running and SSH forwarding is already set:

1. Open `http://localhost:13000`
2. Click `Start Recording`
3. Ask a short course-related question
4. Click again to stop recording
5. Wait for:
   - transcript
   - text answer
   - citations
   - audio reply

Then open:

- `http://localhost:13000`

## 11. Common Issues

### vLLM container fails to start

Check:

- model path exists at `/opt/models/Qwen3-4B-quantized.w4a16`
- available memory on Jetson
- whether another team container is already occupying memory

### Backend starts but answers fail

Check:

- `docker compose logs -f backend`
- whether `vllm`, `asr`, and `tts` are healthy
- whether `data/chroma` exists and contains a built knowledge base

### Frontend loads but cannot reach backend

Check:

- backend is listening on `18080`
- browser is using the correct Jetson hostname or SSH-forwarded localhost
- the SSH tunnel is still open on your local Mac

### Microphone permission issue

Use:

- SSH port forwarding to `localhost`, or
- VS Code / Cursor port forwarding

This is usually easier than using raw `http://<jetson-ip>:13000` with browser security restrictions.
