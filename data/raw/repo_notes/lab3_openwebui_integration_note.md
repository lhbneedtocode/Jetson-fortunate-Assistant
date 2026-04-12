# Lab 3 OpenAI-Compatible Voice Service Integration Note

## Summary

This note describes how the lab services were configured to work together through OpenAI-compatible APIs. Even though the current project uses a custom frontend instead of Open WebUI, the same API compatibility pattern is still useful.

## LLM Integration

- API URL: `http://vllm:8000/v1`
- API key: `not-needed`

## ASR Integration

- STT engine style: OpenAI-compatible
- API base URL: `http://asr:5092/v1`
- model: `faster-whisper`

## TTS Integration

- TTS engine style: OpenAI-compatible
- API base URL: `http://tts:8880/v1`
- model: `kokoro`
- voice: `af_bella`

## Why This Matters

Using the same API style across services makes backend orchestration easier. A project backend can treat vLLM, ASR, and TTS as separate but compatible service endpoints instead of tightly coupling itself to model-specific SDKs.

## Reusable Lesson for the Current Project

The course assistant can reuse this exact service pattern:

- backend calls `vllm` for language generation
- backend calls `asr` for transcription
- backend calls `tts` for speech synthesis

This keeps the system modular and easier to debug.
