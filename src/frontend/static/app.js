const API_BASE_URL = `${window.location.protocol}//${window.location.hostname}:18080/api`;
const askBtn = document.getElementById("ask-btn");
const recordBtn = document.getElementById("record-btn");
const clearChatBtn = document.getElementById("clear-chat-btn");
const questionEl = document.getElementById("question");
const transcriptEl = document.getElementById("transcript");
const answerEl = document.getElementById("answer");
const citationsEl = document.getElementById("citations");
const statusEl = document.getElementById("status");
const audioPlayerEl = document.getElementById("audio-player");
const audioNoteEl = document.getElementById("audio-note");
const evidenceListEl = document.getElementById("evidence-list");
const stepQuestionEl = document.getElementById("step-question");
const stepRetrievalEl = document.getElementById("step-retrieval");
const stepGenerationEl = document.getElementById("step-generation");
const stepSpeechEl = document.getElementById("step-speech");
const chatHistoryEl = document.getElementById("chat-history");

let mediaRecorder = null;
let mediaStream = null;
let chunks = [];
let isRecording = false;
let conversationHistory = [];

askBtn.addEventListener("click", async () => {
  const question = questionEl.value.trim();
  if (!question) {
    setStatus("Please enter a question.");
    return;
  }

  setStatus("Sending text question...");
  try {
    updatePipelineStart(question, false);
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        history: conversationHistory.slice(-4),
        synthesize_speech: true,
        voice: "af_bella",
      }),
    });
    const data = await response.json();
    renderResponse(data, question, "text");
    setStatus("Text answer received.");
  } catch (error) {
    console.error(error);
    setStatus("Text request failed.");
    answerEl.textContent = "Failed to get a response from the backend.";
  }
});

clearChatBtn.addEventListener("click", () => {
  conversationHistory = [];
  renderConversation();
  setStatus("Conversation history cleared.");
});

recordBtn.addEventListener("click", async () => {
  if (isRecording) {
    stopRecording();
    return;
  }

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setStatus("This browser does not support microphone recording.");
    return;
  }

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    chunks = [];
    mediaRecorder = new MediaRecorder(mediaStream);
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunks.push(event.data);
      }
    };
    mediaRecorder.onstop = async () => {
      const blob = new Blob(chunks, { type: mediaRecorder.mimeType || "audio/webm" });
      await sendAudio(blob);
      cleanupRecorder();
    };
    mediaRecorder.start();
    isRecording = true;
    recordBtn.textContent = "Stop Recording";
    setStatus("Recording... click again to stop.");
  } catch (error) {
    console.error(error);
    setStatus("Failed to access microphone.");
  }
});

function stopRecording() {
  if (!mediaRecorder || !isRecording) {
    return;
  }
  isRecording = false;
  recordBtn.textContent = "Start Recording";
  setStatus("Uploading audio...");
  mediaRecorder.stop();
}

async function sendAudio(blob) {
  const formData = new FormData();
  formData.append("file", blob, "question.webm");
  formData.append("synthesize_speech", "true");
  formData.append("voice", "af_bella");

  try {
    const response = await fetch(`${API_BASE_URL}/chat/audio`, {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    renderResponse(data, data.transcript || "Voice question", "voice");
    setStatus("Audio answer received.");
  } catch (error) {
    console.error(error);
    setStatus("Audio request failed.");
    answerEl.textContent = "Failed to process the recorded audio.";
  }
}

function renderResponse(data, fallbackTranscript, mode) {
  const transcript = data.transcript || fallbackTranscript || "No transcript available.";
  transcriptEl.textContent = transcript;
  answerEl.textContent = data.answer || "No answer returned.";
  appendConversationTurn("user", transcript, mode);
  appendConversationTurn("assistant", data.answer || "No answer returned.", "answer");
  renderCitations(data.citations || []);
  renderEvidence(data.evidence || []);
  renderAudio(data.audio_base64 || null);
  updatePipelineResult({
    transcript,
    answer: data.answer || "",
    evidence: data.evidence || [],
    hasAudio: Boolean(data.audio_base64),
    refusal: Boolean(data.refusal),
  });
}

function appendConversationTurn(role, content, kind) {
  conversationHistory.push({ role, content, kind });
  if (conversationHistory.length > 8) {
    conversationHistory = conversationHistory.slice(-8);
  }
  renderConversation();
}

function renderConversation() {
  chatHistoryEl.innerHTML = "";
  if (!conversationHistory.length) {
    chatHistoryEl.innerHTML = '<p class="empty-state">No conversation yet.</p>';
    return;
  }

  conversationHistory.forEach((turn) => {
    const item = document.createElement("article");
    item.className = `chat-turn ${turn.role}`;

    const meta = document.createElement("div");
    meta.className = "chat-meta";
    meta.textContent = turn.role === "user"
      ? turn.kind === "voice" ? "User (voice)" : "User"
      : "Assistant";

    const body = document.createElement("p");
    body.className = "chat-body";
    body.textContent = turn.content;

    item.appendChild(meta);
    item.appendChild(body);
    chatHistoryEl.appendChild(item);
  });
}

function renderCitations(citations) {
  citationsEl.innerHTML = "";
  if (!citations.length) {
    citationsEl.innerHTML = "<li>No citations returned.</li>";
    return;
  }

  citations.forEach((citation) => {
    const item = document.createElement("li");
    item.textContent = citation.page
      ? `${citation.source} (page ${citation.page})`
      : citation.source;
    citationsEl.appendChild(item);
  });
}

function renderAudio(audioBase64) {
  if (!audioBase64) {
    audioPlayerEl.removeAttribute("src");
    audioPlayerEl.load();
    audioNoteEl.textContent = "No audio response yet.";
    return;
  }

  audioPlayerEl.src = `data:audio/mpeg;base64,${audioBase64}`;
  audioNoteEl.textContent = "Audio response ready.";
}

function renderEvidence(evidenceItems) {
  evidenceListEl.innerHTML = "";
  if (!evidenceItems.length) {
    evidenceListEl.innerHTML = '<p class="empty-state">No evidence cards yet.</p>';
    return;
  }

  evidenceItems.forEach((item, index) => {
    const card = document.createElement("article");
    card.className = "evidence-card";

    const title = document.createElement("div");
    title.className = "evidence-meta";
    const scoreLabel = item.score ? ` | relevance ${item.score.toFixed(2)}` : "";
    title.textContent = item.page
      ? `Evidence ${index + 1}: ${item.source} (page ${item.page})${scoreLabel}`
      : `Evidence ${index + 1}: ${item.source}${scoreLabel}`;

    const snippet = document.createElement("p");
    snippet.className = "evidence-snippet";
    snippet.textContent = item.snippet;

    card.appendChild(title);
    card.appendChild(snippet);
    evidenceListEl.appendChild(card);
  });
}

function updatePipelineStart(question, isVoice) {
  stepQuestionEl.textContent = isVoice
    ? `Voice question captured: ${question}`
    : `Text question submitted: ${question}`;
  stepRetrievalEl.textContent = "Searching the course knowledge base...";
  stepGenerationEl.textContent = "Preparing grounded answer...";
  stepSpeechEl.textContent = "Speech output pending.";
}

function updatePipelineResult({ transcript, answer, evidence, hasAudio, refusal }) {
  stepQuestionEl.textContent = transcript || "Question received.";
  stepRetrievalEl.textContent = evidence.length
    ? `Retrieved ${evidence.length} evidence chunk(s) from the course knowledge base.`
    : "No evidence chunks retrieved.";
  stepGenerationEl.textContent = refusal
    ? "The assistant refused due to weak evidence."
    : `Grounded answer generated (${answer.length} characters).`;
  stepSpeechEl.textContent = hasAudio
    ? "Audio reply synthesized and ready to play."
    : "No audio reply returned.";
}

function cleanupRecorder() {
  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
  }
  mediaRecorder = null;
  mediaStream = null;
  chunks = [];
}

function setStatus(message) {
  statusEl.textContent = message;
}
