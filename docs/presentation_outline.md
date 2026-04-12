# Presentation Outline

## Project

- Title: Jetson-based Voice Course Assistant for Lab and Project Support
- Course: IEMS5709A-25R2
- Group: Group 6

## Goal of the Presentation

The presentation should clearly show:

- what problem the project solves
- why the project is meaningful for this course
- how the system works
- what has been implemented
- how the demo proves the system is useful

## Suggested Slide Structure

## Slide 1: Title

### Include

- project title
- course name
- group number
- member names and student IDs

### Speaker Focus

- introduce the project in one sentence
- explain that this is a course-specific voice assistant running on Jetson

## Slide 2: Motivation

### Include

- repeated student questions during labs and project work
- scattered information across README, assignments, setup notes, and deployment notes
- need for a course-specific assistant rather than a general chatbot

### Speaker Focus

- explain the pain point
- explain why RAG is suitable for this scenario

## Slide 3: Project Objective

### Include

- text QA over course materials
- voice QA with ASR and TTS
- citation-based answers
- Jetson deployment with multi-service orchestration

### Speaker Focus

- explain that the project goal is practical course support, not open-domain chatting

## Slide 4: System Architecture

### Include

- frontend
- backend
- retriever / Chroma
- vLLM
- ASR
- TTS
- Docker Compose on Jetson

### Speaker Focus

- walk through the main modules
- emphasize reuse of the course lab pipeline

## Slide 5: RAG Workflow

### Include

- user asks by text or voice
- ASR transcribes speech
- retriever searches course knowledge base
- backend builds prompt
- Qwen generates answer
- TTS produces audio reply
- frontend shows answer, evidence, and citations

### Speaker Focus

- explain the data flow
- mention that answers are grounded in retrieved evidence

## Slide 6: Knowledge Base Construction

### Include

- source files used:
  - lab README files
  - assignments
  - environment/prerequisite notes
  - lecture slides
  - repo notes
  - deployment/troubleshooting notes from reports
- ingestion process:
  - parsing
  - chunking
  - embeddings
  - Chroma persistence

### Speaker Focus

- show that the knowledge base is curated
- explain that deployment experience notes were also transformed into reusable knowledge

## Slide 7: Implementation Highlights

### Include

- OpenAI-compatible vLLM integration
- ASR and TTS service integration
- lightweight multi-turn conversation support
- follow-up query rewriting
- evidence visualization in the frontend

### Speaker Focus

- point out what was actually implemented
- avoid sounding like this is only a design idea

## Slide 8: Deployment on Jetson

### Include

- Docker Compose services
- SSH port forwarding workflow
- memory tuning for vLLM
- `/workspace` mount for ASR

### Speaker Focus

- explain deployment constraints on Jetson
- mention the practical fixes learned from Lab 2 and Lab 3

## Slide 9: Demo Plan

### Recommended Demo Cases

- Case 1: "How do I connect to the Jetson via SSH?"
- Case 2: "What endpoint does the ASR service provide for transcription?"
- Case 3: "Why did the ASR service return HTTP 500 before?"

### Speaker Focus

- explain why these cases were chosen
- show one course-operation case and one deployment/troubleshooting case

## Slide 10: Demo Screens

### Include

- frontend page
- conversation history
- RAG flow panel
- retrieved evidence cards
- citations
- audio reply section

### Speaker Focus

- show that the UI does not only output an answer
- highlight that the RAG process is visible and explainable

## Slide 11: Challenges and Solutions

### Include

- limited Jetson memory
- vLLM startup tuning
- ASR output path issue
- browser CORS issue
- follow-up question retrieval issue

### Speaker Focus

- present each problem with a short fix
- show engineering effort and iteration

## Slide 12: Team Contribution

### Include

- frontend and interaction
- knowledge base and retrieval
- voice pipeline
- backend and deployment

### Speaker Focus

- clearly explain member responsibilities
- make each contribution visible

## Slide 13: Conclusion

### Include

- what the system can do now
- what makes it useful for the course
- possible future improvement directions

### Speaker Focus

- close with the practical value of the project
- emphasize that this is a real teaching-support system, not just a chatbot demo

## Suggested Speaking Order

- Member 1: Slide 1 to Slide 3
- Member 2: Slide 4 to Slide 6
- Member 3: Slide 7 to Slide 10
- Member 4: Slide 11 to Slide 13

## Presentation Tips

- Keep architecture explanations high-level and visual
- Do not spend too long on implementation details before the demo
- Show citations and evidence during the demo because that is one of the strongest RAG-specific selling points
- For follow-up questions, use short and natural examples
- If one demo case fails, switch immediately to a backup text QA case

## Recommended Backup Demo Questions

- "How do I connect to the Jetson via SSH?"
- "What endpoint does the ASR service provide for transcription?"
- "Why do we need to mount /workspace for ASR?"
- "Why was gpu-memory-utilization reduced to 0.35?"
