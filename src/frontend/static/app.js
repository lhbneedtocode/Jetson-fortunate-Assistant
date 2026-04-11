const API_BASE_URL = `${window.location.protocol}//${window.location.hostname}:18080/api`;
const askBtn = document.getElementById("ask-btn");
const recordBtn = document.getElementById("record-btn");
const questionEl = document.getElementById("question");
const transcriptEl = document.getElementById("transcript");
const answerEl = document.getElementById("answer");
const citationsEl = document.getElementById("citations");
const statusEl = document.getElementById("status");
const audioPlayerEl = document.getElementById("audio-player");
const audioNoteEl = document.getElementById("audio-note");

let mediaRecorder = null;
let mediaStream = null;
let chunks = [];
let isRecording = false;

askBtn.addEventListener("click", async () => {
  const question = questionEl.value.trim();
  if (!question) {
    setStatus("Please enter a question.");
    return;
  }

  setStatus("Sending text question...");
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        synthesize_speech: true,
        voice: "af_bella",
      }),
    });
    const data = await response.json();
    renderResponse(data, question);
    setStatus("Text answer received.");
  } catch (error) {
    console.error(error);
    setStatus("Text request failed.");
    answerEl.textContent = "Failed to get a response from the backend.";
  }
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
    renderResponse(data, data.transcript || "Voice question");
    setStatus("Audio answer received.");
  } catch (error) {
    console.error(error);
    setStatus("Audio request failed.");
    answerEl.textContent = "Failed to process the recorded audio.";
  }
}

function renderResponse(data, fallbackTranscript) {
  transcriptEl.textContent = data.transcript || fallbackTranscript || "No transcript available.";
  answerEl.textContent = data.answer || "No answer returned.";
  renderCitations(data.citations || []);
  renderAudio(data.audio_base64 || null);
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
