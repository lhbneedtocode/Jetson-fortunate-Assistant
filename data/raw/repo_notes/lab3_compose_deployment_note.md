# Lab 3 Docker Compose Deployment Note

## Source

- Course repository: `IEMS5709-25R2-Edge-Computing/Lab3/README.md`
- Local coursework file: `lab3/docker-compose.yml`

## Purpose

This note summarizes the multi-service deployment pattern used in Lab 3. The project uses Docker Compose to orchestrate multiple AI services on Jetson instead of launching each service manually with separate `docker run` commands.

## Services in the Lab 3 Pattern

- `vllm`
  Runs Qwen3-4B with the Jetson vLLM image.
- `asr`
  Runs the persistent Faster-Whisper ASR service.
- `tts`
  Runs the Kokoro TTS service.
- `frontend` or web interface
  Connects to backend services and provides the user-facing interaction page.

## Important Configuration Ideas

- `runtime: nvidia`
  Required for GPU-enabled services on Jetson.
- `shm_size`
  Important for vLLM stability.
- `depends_on`
  Used to order service startup.
- `volumes`
  Used for model path mounting and persistent data.
- `ports`
  Used to expose frontend and backend services to the browser and debugging tools.

## Resource Constraints

Jetson Orin NX has limited shared CPU/GPU memory. In the coursework setup, vLLM is configured conservatively to leave room for ASR and TTS. Typical tuning points include:

- `--gpu-memory-utilization`
- `--max-model-len`
- `--max-num-batched-tokens`

## Integration Value

This deployment pattern is the base of the course assistant project. The project extends the Lab 3 layout by adding a backend orchestration service and a local RAG pipeline while keeping the same multi-service containerized workflow on the remote Jetson machine.
