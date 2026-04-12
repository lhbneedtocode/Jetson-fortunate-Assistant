# Lab 3 Voice Pipeline Troubleshooting

## Summary

This note summarizes the most important troubleshooting lessons from multi-service voice assistant deployment with Docker Compose on Jetson.

## Problem 1: vLLM Initialization Failure

### Symptom

- Model refresh failed
- vLLM API was unavailable
- EngineCore failed to start

### Cause

Insufficient free GPU memory on Jetson during model initialization.

### Practical Fix

Reduce the vLLM runtime settings:

- `--gpu-memory-utilization 0.35`
- `--max-model-len 2048`
- `--max-num-batched-tokens 1024`

### Lesson

For Jetson deployment, conservative memory settings are often required so that LLM, ASR, and TTS can coexist.

## Problem 2: ASR Returned HTTP 500

### Symptom

- `POST /v1/audio/transcriptions` returned `500`

### Cause

The service attempted to write to `/workspace/asr_result.txt`, but the expected path did not exist inside the container.

### Practical Fix

Mount a writable host directory to `/workspace`:

```yaml
volumes:
  - asr-workspace:/workspace
```

### Lesson

Persistent output paths must be mounted explicitly in Compose-based deployments.

## Problem 3: Port Conflicts During Remote Access

### Symptom

- Browser access failed because expected local ports were already occupied

### Practical Fix

- change the frontend host port to `13000`
- use SSH port forwarding for browser access

Example:

```bash
ssh -N -L 13000:localhost:13000 <user>@<jetson-ip>
```

### Lesson

Remote browser access to Jetson services is more stable when ports are isolated and forwarded through SSH.

## Overall Deployment Lesson

Stable multi-service voice interaction on Jetson depends on:

- conservative vLLM memory tuning
- explicit service dependencies
- correct writable volume mounts
- careful host-port planning
