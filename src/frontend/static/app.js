const $ = (id) => document.getElementById(id);

const apiBaseInput = $("apiBase");
const questionInput = $("question");
const aspectInput = $("aspect");
const drawModeInput = $("drawMode");
const signIdInput = $("signId");
const signIdField = $("signIdField");
const submitBtn = $("submitBtn");
const clearBtn = $("clearBtn");
const loading = $("loading");
const answerBox = $("answer");
const metaBox = $("meta");
const evidenceList = $("evidenceList");

function defaultApiBase() {
  if (window.location.protocol === "file:") {
    return "http://localhost:8080";
  }

  if (window.location.port && window.location.port !== "8080") {
    return `${window.location.protocol}//${window.location.hostname}:8080`;
  }

  return "";
}

apiBaseInput.value = localStorage.getItem("fortune_api_base") || defaultApiBase();

drawModeInput.addEventListener("change", () => {
  signIdField.style.display = drawModeInput.value === "fixed" ? "block" : "none";
});

drawModeInput.dispatchEvent(new Event("change"));

function getApiBase() {
  const value = apiBaseInput.value.trim();
  localStorage.setItem("fortune_api_base", value);
  return value.replace(/\/$/, "");
}

function formatAnswer(text) {
  if (!text) return "";

  return text
    .replace(/\\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function renderEvidence(items = []) {
  evidenceList.innerHTML = "";

  if (!items.length) {
    evidenceList.innerHTML = `<p class="muted">暂无检索依据。</p>`;
    return;
  }

  items.slice(0, 6).forEach((item, index) => {
    const metadata = item.metadata || {};
    const card = document.createElement("div");
    card.className = "evidence-card";

    card.innerHTML = `
      <div class="evidence-title">
        <strong>资料 ${index + 1}</strong>
        <span>${metadata.sign_id || "-"} · ${metadata.aspect_label || metadata.aspect || "-"} · ${metadata.chunk_type || "-"}</span>
      </div>
      <p>${item.snippet || ""}</p>
      <div class="evidence-meta">
        <span>吉凶：${metadata.level || "-"}</span>
        <span>典故：${metadata.story_title || "-"}</span>
        <span>score：${typeof item.score === "number" ? item.score.toFixed(3) : "-"}</span>
      </div>
    `;

    evidenceList.appendChild(card);
  });
}

async function submitFortune() {
  const question = questionInput.value.trim();

  if (!question) {
    alert("请先输入你的问题。");
    return;
  }

  const apiBase = getApiBase();
  const aspect = aspectInput.value.trim();
  const drawMode = drawModeInput.value;
  const fixedSignId = signIdInput.value.trim();

  const payload = {
    question,
  };

  if (aspect) {
    payload.aspect = aspect;
  }

  if (drawMode === "fixed" && fixedSignId) {
    payload.sign_id = fixedSignId;
  }

  submitBtn.disabled = true;
  loading.classList.remove("hidden");
  answerBox.classList.remove("empty");
  answerBox.textContent = "";
  metaBox.textContent = "正在生成...";
  evidenceList.innerHTML = "";

  try {
    const res = await fetch(`${apiBase}/api/fortune`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`HTTP ${res.status}: ${errText}`);
    }

    const data = await res.json();

    metaBox.textContent = `第 ${data.sign_id} 签 ｜ 方向：${data.aspect} ｜ ${data.sign_key}`;
    answerBox.textContent = formatAnswer(data.answer);
    renderEvidence(data.evidence || []);
  } catch (err) {
    console.error(err);
    metaBox.textContent = "请求失败";
    answerBox.textContent = `请求失败：${err.message}

请检查：
1. FastAPI 后端是否已启动在 8080 端口；
2. API 地址是否正确；
3. 服务器是否允许访问；
4. Qwen/vLLM 是否运行在 8000 端口。`;
    renderEvidence([]);
  } finally {
    submitBtn.disabled = false;
    loading.classList.add("hidden");
  }
}

function clearAll() {
  questionInput.value = "";
  answerBox.textContent = "请在左侧输入问题，然后点击“开始求签解签”。";
  answerBox.classList.add("empty");
  metaBox.textContent = "等待求签...";
  evidenceList.innerHTML = "";
}

submitBtn.addEventListener("click", submitFortune);
clearBtn.addEventListener("click", clearAll);

questionInput.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    submitFortune();
  }
});