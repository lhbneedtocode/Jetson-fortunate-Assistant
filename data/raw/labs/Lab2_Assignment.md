# Lab 2 Assignment

## Task: Containerization of ASR Model

Please rewrite the Dockerfile and provide a `api.py` script to build a container that provides a persistent transcription service similar to the `kokoro-tts` container. After running the container, use your own audio clip `asr_audio.wav` to test the transcription service and save the transcription result to `asr_result.txt`.

## Test

The rebuilt container should be able to handle the transcription request as follows:
```bash
curl -X POST http://localhost:5092/v1/audio/transcriptions \
  -F "file=@asr_audio.wav" \
  -F "model=faster-whisper"

# (optional) health check
curl http://localhost:5092/health

# (optional) model list
curl http://localhost:5092/v1/models
```

## Submission

Please submit your work to Blackboard by uploading the following files:
```
Dockerfile
faster-whisper/api.py
asr_audio.wav
asr_result.txt
```