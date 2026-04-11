# Lab 2 ASR API Note

## Source

- Local coursework implementation: `lab2/api.py`
- Local coursework container file: `lab2/Dockerfile`

## Purpose

This note summarizes the persistent ASR service built in Lab 2. The service wraps Faster-Whisper with FastAPI and exposes an OpenAI-compatible transcription endpoint so it can be integrated into a larger voice assistant pipeline.

## Main API Endpoints

- `GET /health`
  Returns service status, model name, device, and compute type.
- `GET /v1/models`
  Returns model metadata for the ASR service.
- `POST /v1/audio/transcriptions`
  Accepts an uploaded audio file and returns:
  - transcribed text
  - segment timestamps
  - detected language
  - language probability

## Request Style

The transcription endpoint follows OpenAI-compatible form upload style:

```bash
curl -X POST http://localhost:5092/v1/audio/transcriptions \
  -F "file=@asr_audio.wav" \
  -F "model=faster-whisper"
```

## Implementation Details

- Framework: FastAPI
- ASR backend: Faster-Whisper
- Default model: `small.en`
- Default device: `cuda`
- Default compute type: `int8_float16`
- Result file path: `/workspace/asr_result.txt`

## Integration Value

This service can be used as the speech-to-text entrypoint of the course assistant. In the project pipeline, the frontend uploads audio, the ASR service returns transcription text, and the backend sends the text query to the retrieval and LLM modules.
