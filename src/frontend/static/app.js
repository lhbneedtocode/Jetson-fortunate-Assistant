
document.addEventListener("DOMContentLoaded", () => {
  const $ = (id) => document.getElementById(id);

  const apiBaseInput = $("apiBase");
  const questionInput = $("question");
  const aspectInput = $("aspect");
  const drawModeInput = $("drawMode");
  const answerStyleInput = $("answerStyle");
  const signIdInput = $("signId");
  const signIdField = $("signIdField");

  const submitBtn = $("submitBtn");
  const clearBtn = $("clearBtn");

  const stageTitle = $("stageTitle");
  const stageSubtitle = $("stageSubtitle");
  const stageStatusText = $("stageStatusText");

  const stepInput = $("stepInput");
  const stepShake = $("stepShake");
  const stepDraw = $("stepDraw");
  const stepRead = $("stepRead");
  const stepExplain = $("stepExplain");

  const tubeContainer = $("tubeContainer");
  const risingStick = $("risingStick");
  const drawCard = $("drawCard");
  const drawNumber = $("drawNumber");
  const drawMeta = $("drawMeta");

  const detailMeta = $("detailMeta");
  const resultContent = $("resultContent");
  const techPanel = $("techPanel");
  const scoreBars = $("scoreBars");
  const evidenceList = $("evidenceList");

  const metricHit1 = $("metricHit1");
  const metricHit3 = $("metricHit3");
  const metricMRR = $("metricMRR");

  const profileBox = $("profileBox");
  const refreshProfileBtn = $("refreshProfileBtn");

  let latestResult = null;
  let running = false;

  const stages = {
    input: stepInput,
    shake: stepShake,
    draw: stepDraw,
    read: stepRead,
    explain: stepExplain
  };

  function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function setStep(name) {
    Object.values(stages).forEach((el) => el?.classList.remove("active"));
    stages[name]?.classList.add("active");
  }

  function setStage(title, subtitle, status, step) {
    if (stageTitle) stageTitle.textContent = title;
    if (stageSubtitle) stageSubtitle.textContent = subtitle;
    if (stageStatusText) stageStatusText.textContent = status;
    setStep(step);
  }

  function pad3(v) {
    const n = Number(v);
    if (Number.isFinite(n)) return String(n).padStart(3, "0");
    return String(v || "---").padStart(3, "0");
  }

  function escapeHtml(str) {
    return String(str ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function getApiBase() {
    const raw = (apiBaseInput?.value || "").trim().replace(/\/+$/, "");
    if (!raw) return window.location.origin;
    if (/^https?:\/\//i.test(raw)) return raw;
    return `${window.location.protocol}//${raw}`;
  }

  function updateSignIdVisibility() {
    if (!drawModeInput || !signIdField) return;
    if (drawModeInput.value === "fixed") {
      signIdField.classList.remove("hidden");
    } else {
      signIdField.classList.add("hidden");
    }
  }

  drawModeInput?.addEventListener("change", updateSignIdVisibility);
  updateSignIdVisibility();

  function resetAnimation() {
    tubeContainer?.classList.remove("animate-tube-shake");
    risingStick?.classList.remove("animate-stick-rise");

    if (drawCard) {
      drawCard.classList.add("hidden");
      drawCard.classList.remove("show");
    }

    if (drawNumber) drawNumber.textContent = "第 --- 签";
    if (drawMeta) drawMeta.textContent = "点击查看签文";
  }

  function resetResult() {
    latestResult = null;

    if (detailMeta) detailMeta.textContent = "尚未求签";

    if (resultContent) {
      resultContent.classList.add("placeholder", "empty");
      resultContent.textContent = "请先输入问题并摇签。抽得灵签后，这里会展示生成的白话解签。";
    }

    techPanel?.classList.add("hidden");
    if (scoreBars) scoreBars.innerHTML = "";
    if (evidenceList) evidenceList.innerHTML = `<p class="muted">暂无签文依据。</p>`;

    if (metricHit1) metricHit1.textContent = "-";
    if (metricHit3) metricHit3.textContent = "-";
    if (metricMRR) metricMRR.textContent = "-";
  }

  function resetAll({ clearQuestion = true } = {}) {
    running = false;

    if (clearQuestion && questionInput) questionInput.value = "";

    resetAnimation();
    resetResult();

    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = "开始摇签";
    }

    setStage(
      "静心默念所问之事",
      "点击“开始摇签”，系统将抽取一支灵签并检索对应签文依据。",
      "等待开始摇签",
      "input"
    );
  }

  function readPath(obj, paths, fallback = "") {
    for (const path of paths) {
      const value = path.split(".").reduce((acc, key) => {
        if (acc && Object.prototype.hasOwnProperty.call(acc, key)) return acc[key];
        return undefined;
      }, obj);

      if (value !== undefined && value !== null && value !== "") return value;
    }
    return fallback;
  }

  function normalizeResult(raw, question) {
    const root = raw?.data ?? raw?.result ?? raw ?? {};
    const firstEvidence = Array.isArray(root.evidence) ? (root.evidence[0] || {}) : {};
    const firstMeta = firstEvidence.metadata || {};
    const firstCitation = Array.isArray(root.citations) ? (root.citations[0] || {}) : {};

    const signNumber =
      readPath(root, ["sign_id", "signId", "signNumber", "sign_number", "number", "id"], "") ||
      readPath(firstMeta, ["sign_id"], "") ||
      readPath(firstCitation, ["sign_id"], "");

    const level =
      readPath(root, ["level", "grade", "fortune_level"], "") ||
      readPath(firstMeta, ["level"], "") ||
      readPath(firstCitation, ["level"], "未知");

    const title =
      readPath(root, ["title", "sign_title", "story_title", "name"], "") ||
      readPath(firstMeta, ["story_title"], "") ||
      readPath(firstCitation, ["story_title"], "灵签");

    const signKey =
      readPath(root, ["sign_key", "code", "slug"], "") ||
      readPath(firstMeta, ["sign_key"], "") ||
      `wong_tai_sin_100_${pad3(signNumber)}`;

    const answer = readPath(root, ["answer", "final_answer", "generated_answer", "explanation", "analysis"], "");

    const evidence = Array.isArray(root.evidence) ? root.evidence : [];
    const metrics = root.metrics || root.retrieval_metrics || {};

    return {
      signNumber,
      level,
      title,
      signKey,
      answer,
      evidence,
      metrics,
      raw,
      question
    };
  }

  async function requestFortune(question) {
    const payload = {
      question,
      style: answerStyleInput?.value || "modern"
    };

    const aspect = aspectInput?.value || "";
    if (aspect) payload.aspect = aspect;

    if (drawModeInput?.value === "fixed" && signIdInput?.value) {
      payload.sign_id = signIdInput.value;
    }

    const res = await fetch(`${getApiBase()}/api/fortune`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text}`);
    }

    return normalizeResult(await res.json(), question);
  }

  function renderScoreBars(evidence) {
    if (!scoreBars) return;

    scoreBars.innerHTML = "";

    if (!Array.isArray(evidence) || evidence.length === 0) {
      scoreBars.innerHTML = `<p class="muted">暂无 RAG 检索分数。</p>`;
      return;
    }

    const maxScore = Math.max(...evidence.map((item) => Number(item.score || 0)), 0.001);

    evidence.slice(0, 6).forEach((item, index) => {
      const meta = item.metadata || {};
      const score = Number(item.score || 0);
      const width = Math.max(4, Math.round((score / maxScore) * 100));

      const row = document.createElement("div");
      row.className = "score-row";
      row.innerHTML = `
        <div class="score-info">
          <strong>Rank ${index + 1}</strong>
          <span>${escapeHtml(meta.aspect_label || meta.aspect || "-")} / ${escapeHtml(meta.chunk_type || "-")}</span>
        </div>
        <div class="score-track">
          <div class="score-fill" style="width:${width}%"></div>
        </div>
        <div class="score-value">${Number.isFinite(score) ? score.toFixed(3) : "-"}</div>
      `;

      scoreBars.appendChild(row);
    });
  }

  function renderEvidence(evidence) {
    if (!evidenceList) return;

    evidenceList.innerHTML = "";

    if (!Array.isArray(evidence) || evidence.length === 0) {
      evidenceList.innerHTML = `<p class="muted">暂无签文依据。</p>`;
      return;
    }

    evidence.slice(0, 6).forEach((item, index) => {
      const metadata = item.metadata || {};
      const div = document.createElement("div");
      div.className = "evidence-card";
      div.innerHTML = `
        <div class="evidence-title">
          <strong>资料 ${index + 1}</strong>
          <span>${escapeHtml(metadata.sign_id || "-")} · ${escapeHtml(metadata.aspect_label || metadata.aspect || "-")} · ${escapeHtml(metadata.chunk_type || "-")}</span>
        </div>
        <p>${escapeHtml(item.snippet || item.text || item.content || "")}</p>
      `;
      evidenceList.appendChild(div);
    });
  }

  
  async function loadUserProfile() {
    if (!profileBox) return;

    try {
      const res = await fetch(`${getApiBase()}/api/fortune/profile`);
      if (!res.ok) {
        profileBox.textContent = "用户画像接口暂不可用。";
        return;
      }

      const data = await res.json();

      if (!data || !data.total) {
        profileBox.textContent = "暂无历史记录。完成一次求签后，这里会展示用户画像。";
        return;
      }

      const topAspects = (data.top_aspects || [])
        .map(([name, count]) => `<span class="profile-tag">${escapeHtml(name)} × ${count}</span>`)
        .join("");

      const topKeywords = (data.top_keywords || [])
        .map(([name, count]) => `<span class="profile-tag">${escapeHtml(name)} × ${count}</span>`)
        .join("");

      const levels = Object.entries(data.level_distribution || {})
        .map(([name, count]) => `<span class="profile-tag">${escapeHtml(name)} × ${count}</span>`)
        .join("");

      const styles = Object.entries(data.style_distribution || {})
        .map(([name, count]) => `<span class="profile-tag">${escapeHtml(name)} × ${count}</span>`)
        .join("");

      profileBox.innerHTML = `
        <div class="profile-item">
          <span class="profile-label">累计求签：</span>${data.total} 次
        </div>
        <div class="profile-item">
          <span class="profile-label">近期画像：</span>${escapeHtml(data.recent_summary || "")}
        </div>
        <div class="profile-item">
          <span class="profile-label">高频方向：</span>
          <div class="profile-tags">${topAspects || '<span class="profile-tag">暂无</span>'}</div>
        </div>
        <div class="profile-item">
          <span class="profile-label">高频关键词：</span>
          <div class="profile-tags">${topKeywords || '<span class="profile-tag">暂无</span>'}</div>
        </div>
        <div class="profile-item">
          <span class="profile-label">签级分布：</span>
          <div class="profile-tags">${levels || '<span class="profile-tag">暂无</span>'}</div>
        </div>
        <div class="profile-item">
          <span class="profile-label">常用风格：</span>
          <div class="profile-tags">${styles || '<span class="profile-tag">暂无</span>'}</div>
        </div>
      `;
    } catch (err) {
      console.warn("loadUserProfile failed:", err);
      profileBox.textContent = "用户画像加载失败，请稍后重试。";
    }
  }

function renderResult(data) {
    if (detailMeta) {
      detailMeta.textContent = `第 ${pad3(data.signNumber)} 签｜${data.level}｜${data.title}｜${data.signKey}`;
    }

    if (resultContent) {
      resultContent.classList.remove("empty", "placeholder");
      resultContent.textContent = data.answer || "系统已完成抽签，但没有返回解签正文。";
    }

    if (metricHit1) metricHit1.textContent = data.metrics.hit1 !== undefined ? Number(data.metrics.hit1).toFixed(3) : "-";
    if (metricHit3) metricHit3.textContent = data.metrics.hit3 !== undefined ? Number(data.metrics.hit3).toFixed(3) : "-";
    if (metricMRR) metricMRR.textContent = data.metrics.mrr !== undefined ? Number(data.metrics.mrr).toFixed(3) : "-";

    renderScoreBars(data.evidence);
    renderEvidence(data.evidence);
    techPanel?.classList.remove("hidden");
  }

  function showDrawCard(data) {
    if (drawNumber) drawNumber.textContent = `第 ${pad3(data.signNumber)} 签`;
    if (drawMeta) drawMeta.textContent = `${data.level}｜${data.title}`;

    drawCard?.classList.remove("hidden");
    requestAnimationFrame(() => {
      drawCard?.classList.add("show");
    });
  }

  async function handleSubmit() {
    if (running) return;

    const question = questionInput?.value.trim() || "";
    if (!question) {
      questionInput?.focus();
      return;
    }

    running = true;
    latestResult = null;

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "正在摇签…";
    }

    resetAnimation();
    resetResult();

    setStage(
      "签筒摇动中",
      "签筒正在摇动，系统同步检索签文并生成解签。",
      "正在摇签，请稍候…",
      "shake"
    );

    tubeContainer?.classList.add("animate-tube-shake");

    const resultPromise = requestFortune(question);

    try {
      // 借鉴参考项目：摇签约 2.5 秒
      await delay(2500);

      setStage(
        "灵签将出",
        "摇动逐渐收束，一支灵签正在升起。",
        "灵签即将出现…",
        "draw"
      );

      tubeContainer?.classList.remove("animate-tube-shake");
      risingStick?.classList.add("animate-stick-rise");

      const result = await resultPromise;
      latestResult = result;

      // 借鉴参考项目：签条升起约 0.8 秒
      await delay(800);

      showDrawCard(result);

      await delay(450);

      setStage(
        "观签中",
        "已抽得灵签，正在展示签号、签级与典故。",
        "已抽得灵签",
        "read"
      );

      await delay(500);

      renderResult(result);

      loadUserProfile();

      setStage(
        "解签完成",
        "系统已根据签文依据与用户问题生成白话解签。",
        "解签已完成",
        "explain"
      );

      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "重新摇签";
      }

      running = false;
    } catch (err) {
      console.error(err);

      tubeContainer?.classList.remove("animate-tube-shake");
      risingStick?.classList.remove("animate-stick-rise");

      if (resultContent) {
        resultContent.classList.remove("empty", "placeholder");
        resultContent.textContent = `请求失败：${err.message}

请检查：
1. FastAPI 后端是否运行在 8080；
2. Qwen/vLLM 是否运行在 8000；
3. Chroma fortune_knowledge 是否已构建。`;
      }

      if (detailMeta) detailMeta.textContent = "请求失败";

      setStage(
        "求签失败",
        "请检查后端、Qwen/vLLM 或 Chroma 服务。",
        "请求失败",
        "input"
      );

      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "重新摇签";
      }

      running = false;
    }
  }

  function handleClear() {
    fullReset(false);
  }

  submitBtn?.addEventListener("click", handleSubmit);
  clearBtn?.addEventListener("click", handleClear);
  refreshProfileBtn?.addEventListener("click", loadUserProfile);

  drawCard?.addEventListener("click", () => {
    if (latestResult) {
      renderResult(latestResult);
      setStage(
        "解签完成",
        "系统已根据签文依据与用户问题生成白话解签。",
        "解签已完成",
        "explain"
      );
    }
  });

  fullReset(true);
  loadUserProfile();
});