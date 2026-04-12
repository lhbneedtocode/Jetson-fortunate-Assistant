# Lab 2 ASR Deployment Experience

## Summary

This note captures practical deployment experience from the Lab 2 ASR containerization work on Jetson Orin. The focus is on how to run the Faster-Whisper service as a persistent OpenAI-style transcription API with GPU acceleration.

## Key Setup Pattern

- Hardware platform: Jetson Orin
- Container image: `dustynv/faster-whisper:r36.4.0-cu128-24.04`
- API framework: FastAPI + Uvicorn
- Runtime: `--runtime nvidia`

## Recommended Run Configuration

Important runtime parameters used in practice:

- `WHISPER_MODEL=small.en`
- `COMPUTE_TYPE=int8_float16`
- `ASR_DEVICE=cuda`
- mount a writable workspace directory to `/workspace`

Example pattern:

```bash
sudo docker run \
  --runtime nvidia \
  --rm \
  --network=host \
  -e WHISPER_MODEL=small.en \
  -e COMPUTE_TYPE=int8_float16 \
  -e ASR_DEVICE=cuda \
  -v $PWD:/workspace \
  faster-whisper:fastapi
```

## Why Workspace Mounting Matters

The persistent ASR service writes the transcription result to `/workspace/asr_result.txt`. If `/workspace` does not exist or is not writable, the service may fail when handling transcription requests.

## API Verification

Useful checks:

- `curl http://localhost:5092/health`
- `curl http://localhost:5092/v1/models`
- `curl -X POST http://localhost:5092/v1/audio/transcriptions -F "file=@asr_audio.wav" -F "model=faster-whisper"`

## Practical Lessons

- Persistent ASR service is more suitable for integration than one-shot scripts.
- Mounting a persistent directory improves observability and debugging.
- GPU/CPU fallback makes the service more robust across environments.
