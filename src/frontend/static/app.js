document.addEventListener("DOMContentLoaded", () => {
  const $ = (id) => document.getElementById(id);

  const drawView = $("drawView");
  const reportView = $("reportView");
  const loadingReport = $("loadingReport");
  const errorReport = $("errorReport");
  const errorText = $("errorText");
  const reportContent = $("reportContent");

  const apiBaseInput = $("apiBase");
  const questionInput = $("question");
  const aspectInput = $("aspect");
  const answerStyleInput = $("answerStyle");
  const drawModeInput = $("drawMode");
  const signIdInput = $("signId");
  const signIdField = $("signIdField");
  const toggleAdvancedBtn = $("toggleAdvancedBtn");
  const advancedOptions = $("advancedOptions");

  const submitBtn = $("submitBtn");
  const clearBtn = $("clearBtn");
  const backToDrawBtn = $("backToDrawBtn");
  const newDrawBtn = $("newDrawBtn");

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

  const reportTitle = $("reportTitle");
  const reportMeta = $("reportMeta");
  const reportQuestion = $("reportQuestion");
  const overviewText = $("overviewText");
  const summaryAverage = $("summaryAverage");
  const summaryEvidenceCount = $("summaryEvidenceCount");
  const summarySimilarCount = $("summarySimilarCount");
  const summaryAspect = $("summaryAspect");
  const reportBadgeSign = $("reportBadgeSign");
  const reportLevelChip = $("reportLevelChip");
  const briefSignId = $("briefSignId");
  const briefLevel = $("briefLevel");
  const briefKeywordCount = $("briefKeywordCount");

  const traditionalSignTitle = $("traditionalSignTitle");
  const traditionalSignMeta = $("traditionalSignMeta");
  const selectedKeywords = $("selectedKeywords");
  const traditionalEvidence = $("traditionalEvidence");
  const resultContent = $("resultContent");

  const techPanel = $("techPanel");
  const scoreBars = $("scoreBars");
  const evidenceList = $("evidenceList");
  const similarSignsList = $("similarSignsList");

  const radarPanel = $("radarPanel");
  const radarChart = $("radarChart");
  const radarScores = $("radarScores");
  const radarAverage = $("radarAverage");
  const radarSummary = $("radarSummary");
  const radarModelText = $("radarModelText");
  const currentWordCloud = $("currentWordCloud");

  const metricHit1 = $("metricHit1");
  const metricHit3 = $("metricHit3");
  const metricMRR = $("metricMRR");
  const advancedMetricsBlock = $("advancedMetricsBlock");

  const profileBox = $("profileBox");
  const refreshProfileBtn = $("refreshProfileBtn");

  const stages = {
    input: stepInput,
    shake: stepShake,
    draw: stepDraw,
    read: stepRead,
    explain: stepExplain
  };

  let signs = [];
  let selectedSign = null;
  let latestResult = null;
  let drawing = false;
  let interpreting = false;

  function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
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

  function textToHtml(text) {
    const raw = String(text || "").trim();
    if (!raw) return '<p class="muted">暂无内容。</p>';
    return raw
      .split(/\n{2,}/)
      .map((p) => `<p>${escapeHtml(p).replace(/\n/g, "<br>")}</p>`)
      .join("");
  }

  function safeNumber(value, fallback = 0) {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
  }

  function getApiBase() {
    const raw = (apiBaseInput?.value || "").trim().replace(/\/+$/, "");
    if (!raw) return window.location.origin;
    if (/^https?:\/\//i.test(raw)) return raw;
    return `${window.location.protocol}//${raw}`;
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

  function showView(name) {
    if (name === "report") {
      drawView?.classList.add("hidden");
      reportView?.classList.remove("hidden");
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      reportView?.classList.add("hidden");
      drawView?.classList.remove("hidden");
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  function setReportMode(mode) {
    loadingReport?.classList.toggle("hidden", mode !== "loading");
    errorReport?.classList.toggle("hidden", mode !== "error");
    reportContent?.classList.toggle("hidden", mode !== "content");
  }

  function updateSignIdVisibility() {
    if (!drawModeInput || !signIdField) return;
    signIdField.classList.toggle("hidden", drawModeInput.value !== "fixed");
  }

  async function loadSigns() {
    try {
      const res = await fetch("./data/signs_summary.json", { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      signs = Array.isArray(data) ? data : [];
    } catch (err) {
      console.warn("加载 signs_summary.json 失败，使用前端兜底签号。", err);
      signs = Array.from({ length: 100 }, (_, i) => {
        const signId = pad3(i + 1);
        return {
          sign_id: signId,
          title: `第${i + 1}签`,
          level: "未知",
          story_title: "待解签",
          keywords: []
        };
      });
    }
  }

  function pickSign() {
    if (!signs.length) {
      const n = Math.floor(Math.random() * 100) + 1;
      return { sign_id: pad3(n), title: `第${n}签`, level: "未知", story_title: "待解签", keywords: [] };
    }

    if (drawModeInput?.value === "fixed") {
      const wanted = pad3(signIdInput?.value || "1");
      return signs.find((item) => pad3(item.sign_id) === wanted) || signs[Number(wanted) - 1] || signs[0];
    }

    return signs[Math.floor(Math.random() * signs.length)];
  }

  function resetAnimation() {
    tubeContainer?.classList.remove("animate-tube-shake");
    risingStick?.classList.remove("animate-stick-rise");
    if (drawCard) {
      drawCard.classList.add("hidden");
      drawCard.classList.remove("show");
      drawCard.disabled = false;
    }
    if (drawNumber) drawNumber.textContent = "第 --- 签";
    if (drawMeta) drawMeta.textContent = "点击此签，开始解签";
  }

  function resetReportOnly() {
    latestResult = null;
    setReportMode("loading");
    if (reportTitle) reportTitle.textContent = "灵签解读报告";
    if (reportMeta) reportMeta.textContent = "正在准备报告……";
    if (reportQuestion) reportQuestion.textContent = "";
    if (overviewText) overviewText.textContent = "暂无结论。";
    if (summaryAverage) summaryAverage.textContent = "--";
    if (summaryEvidenceCount) summaryEvidenceCount.textContent = "--";
    if (summarySimilarCount) summarySimilarCount.textContent = "--";
    if (summaryAspect) summaryAspect.textContent = "待识别";
    if (reportBadgeSign) reportBadgeSign.textContent = "---";
    if (reportLevelChip) reportLevelChip.textContent = "签级待定";
    if (briefSignId) briefSignId.textContent = "---";
    if (briefLevel) briefLevel.textContent = "--";
    if (briefKeywordCount) briefKeywordCount.textContent = "--";
    switchTab("ai");
    if (traditionalSignTitle) traditionalSignTitle.textContent = "第 --- 签";
    if (traditionalSignMeta) traditionalSignMeta.textContent = "签级与典故待加载";
    if (selectedKeywords) selectedKeywords.innerHTML = "";
    if (traditionalEvidence) traditionalEvidence.innerHTML = '<p class="muted">暂无签文资料。</p>';
    if (resultContent) resultContent.innerHTML = '<p class="muted">暂无解签。</p>';

    radarPanel?.classList.add("hidden");
    if (radarChart) radarChart.innerHTML = "";
    if (radarScores) radarScores.innerHTML = "";
    if (radarAverage) radarAverage.textContent = "--";
    if (radarSummary) radarSummary.textContent = "暂无五维分析。";
    if (radarModelText) radarModelText.textContent = "基于签级、方向解释关键词和当前问题方向生成量化分析。";
    if (currentWordCloud) currentWordCloud.innerHTML = "暂无关键词。";

    techPanel?.classList.add("hidden");
    if (scoreBars) scoreBars.innerHTML = "";
    if (evidenceList) evidenceList.innerHTML = '<div class="evidence-empty-state"><strong>暂无可展示的检索片段</strong><p>当前接口没有返回 evidence 字段，或知识库暂未命中可展示片段。AI 解读仍可查看，但证据页会保持为空。</p></div>';
    if (similarSignsList) similarSignsList.innerHTML = '<p class="muted">暂无相似签推荐。</p>';

    if (metricHit1) metricHit1.textContent = "-";
    if (metricHit3) metricHit3.textContent = "-";
    if (metricMRR) metricMRR.textContent = "-";
  }

  function resetAll({ clearQuestion = false } = {}) {
    drawing = false;
    interpreting = false;
    selectedSign = null;
    latestResult = null;
    if (clearQuestion && questionInput) questionInput.value = "";
    resetAnimation();
    resetReportOnly();
    setReportMode("loading");
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = "开始摇签";
    }
    setStage(
      "静心默念所问之事",
      "点击“开始摇签”，系统会先抽出签号；点击签卡后才进入完整解签报告。",
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

  function normalizeResult(raw, question, sign) {
    const root = raw?.data ?? raw?.result ?? raw ?? {};
    const firstEvidence = Array.isArray(root.evidence) ? (root.evidence[0] || {}) : {};
    const firstMeta = firstEvidence.metadata || {};
    const firstCitation = Array.isArray(root.citations) ? (root.citations[0] || {}) : {};

    const signNumber =
      readPath(root, ["sign_id", "signId", "signNumber", "sign_number", "number", "id"], "") ||
      readPath(firstMeta, ["sign_id"], "") ||
      readPath(firstCitation, ["sign_id"], "") ||
      sign?.sign_id ||
      "";

    const level =
      readPath(root, ["level", "grade", "fortune_level"], "") ||
      readPath(firstMeta, ["level"], "") ||
      readPath(firstCitation, ["level"], "") ||
      sign?.level ||
      "未知";

    const title =
      readPath(root, ["title", "sign_title", "story_title", "name"], "") ||
      readPath(firstMeta, ["story_title"], "") ||
      readPath(firstCitation, ["story_title"], "") ||
      sign?.story_title ||
      "灵签";

    const signKey =
      readPath(root, ["sign_key", "code", "slug"], "") ||
      readPath(firstMeta, ["sign_key"], "") ||
      `wong_tai_sin_100_${pad3(signNumber)}`;

    const answer = readPath(root, ["answer", "final_answer", "generated_answer", "explanation", "analysis"], "");
    const evidenceRaw = Array.isArray(root.evidence)
      ? root.evidence
      : (Array.isArray(root.citations)
          ? root.citations
          : (Array.isArray(root.retrieved_chunks)
              ? root.retrieved_chunks
              : (Array.isArray(root.chunks) ? root.chunks : [])));
    const evidence = evidenceRaw.map((item) => {
      const metadata = item.metadata || item.meta || {};
      return {
        ...item,
        metadata,
        snippet: item.snippet || item.text || item.content || item.page_content || item.summary || "",
        score: item.score ?? item.similarity ?? item.distance_score
      };
    }).filter((item) => String(item.snippet || "").trim() || Object.keys(item.metadata || {}).length);
    const metrics = root.metrics || root.retrieval_metrics || {};
    const radarAnalysis = root.radar_analysis || root.radarAnalysis || null;
    const similarSigns = Array.isArray(root.similar_signs)
      ? root.similar_signs
      : (Array.isArray(root.similarSigns) ? root.similarSigns : []);
    const aiReport = root.ai_report || root.aiReport || null;
    const questionAnalysis = root.question_analysis || root.questionAnalysis || null;

    return {
      signNumber,
      level,
      title,
      signKey,
      answer,
      evidence,
      metrics,
      radarAnalysis,
      similarSigns,
      aiReport,
      questionAnalysis,
      raw,
      question,
      selectedSign: sign || null
    };
  }

  async function requestDraw(question) {
    const payload = { question };

    const aspect = aspectInput?.value || "";
    if (aspect) payload.aspect = aspect;

    if (drawModeInput?.value === "fixed" && signIdInput?.value) {
      payload.sign_id = pad3(signIdInput.value);
    }

    const res = await fetch(`${getApiBase()}/api/fortune/draw`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`抽签接口失败 HTTP ${res.status}: ${text}`);
    }

    const data = await res.json();
    return {
      sign_id: pad3(data.sign_id),
      sign_key: data.sign_key || `wong_tai_sin_100_${pad3(data.sign_id)}`,
      level: data.level || "未知",
      level_class: data.level_class || "level-neutral",
      title: data.title || `第${Number(data.sign_id || 0)}签`,
      story_title: data.story_title || data.title || "灵签",
      keywords: Array.isArray(data.keywords) ? data.keywords : [],
      draw_id: data.draw_id || null,
      source: data.source || "backend_draw"
    };
  }

  async function requestFortune(question, sign) {
    const payload = {
      question,
      style: answerStyleInput?.value || "modern"
    };

    const aspect = aspectInput?.value || "";
    if (aspect) payload.aspect = aspect;

    if (sign?.sign_id) {
      payload.sign_id = pad3(sign.sign_id);
    }

    if (sign?.draw_id) {
      payload.draw_id = sign.draw_id;
    }

    const res = await fetch(`${getApiBase()}/api/fortune/interpret`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`解签接口失败 HTTP ${res.status}: ${text}`);
    }

    return normalizeResult(await res.json(), question, sign);
  }

  function showDrawCard(sign) {
    if (!sign) return;
    if (drawNumber) drawNumber.textContent = `第 ${pad3(sign.sign_id)} 签`;
    if (drawMeta) drawMeta.textContent = `${sign.level || "未知"}｜${sign.story_title || sign.title || "灵签"}｜点击开始解签`;
    if (drawCard) {
      drawCard.classList.remove("hidden");
      requestAnimationFrame(() => drawCard.classList.add("show"));
    }
  }

  async function handleStartDraw() {
    if (drawing || interpreting) return;
    const question = questionInput?.value.trim() || "";
    if (!question) {
      questionInput?.focus();
      return;
    }

    drawing = true;
    selectedSign = null;
    latestResult = null;
    resetAnimation();
    resetReportOnly();

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "正在摇签…";
    }

    setStage("签筒摇动中", "此阶段只调用后端 /api/fortune/draw 抽签，不调用大模型解签。", "正在摇签，请稍候……", "shake");
    tubeContainer?.classList.add("animate-tube-shake");

    const drawPromise = requestDraw(question);

    try {
      await delay(2300);

      selectedSign = await drawPromise;
      tubeContainer?.classList.remove("animate-tube-shake");
      risingStick?.classList.add("animate-stick-rise");

      setStage("灵签将出", "后端已完成签号抽取，一支灵签正在升起。", "灵签即将出现……", "draw");
      await delay(850);

      showDrawCard(selectedSign);
      setStage("已抽得灵签", "点击签卡后，系统才会开始 RAG 检索、大模型解读和五维雷达分析。", "请点击签卡开始解签", "read");

      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "重新摇签";
      }
      drawing = false;
    } catch (err) {
      console.error(err);
      tubeContainer?.classList.remove("animate-tube-shake");
      risingStick?.classList.remove("animate-stick-rise");
      setStage("抽签失败", "后端抽签接口未正常返回，请检查 FastAPI 服务是否运行。", err.message || "抽签失败", "input");
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "重新摇签";
      }
      drawing = false;
    }
  }

  function trimText(text, limit = 180) {
    const value = String(text || "").replace(/\s+/g, " ").trim();
    if (!value) return "";
    return value.length > limit ? value.slice(0, limit).trim() + "……" : value;
  }

  function extractSection(answer, title) {
    const text = String(answer || "").replace(/[#*_`]/g, "").trim();
    if (!text) return "";

    const escapedTitle = title.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const pattern = new RegExp(`【${escapedTitle}】\\s*([\\s\\S]*?)(?=\\n?【[^】]+】|$)`);
    const match = text.match(pattern);
    return match ? match[1].trim() : "";
  }

  function extractOverview(answer) {
    const compact = String(answer || "").replace(/[#*_`]/g, "").trim();
    if (!compact) return "系统完成了解签，但没有返回可展示的总体结论。";

    const sectionText =
      extractSection(compact, "白话解释") ||
      extractSection(compact, "针对问题的解读") ||
      extractSection(compact, "行动建议") ||
      extractSection(compact, "抽签结果");

    if (sectionText) return trimText(sectionText, 180);

    const lines = compact
      .split(/\n+/)
      .map((line) => line.trim())
      .filter(Boolean)
      .filter((line) => !/^【[^】]+】$/.test(line));

    const preferred = lines.find((line) => /总体|结论|白话|针对|建议/.test(line)) || lines[0] || compact;
    return trimText(preferred, 180) || "系统完成了解签，但白话总结暂未生成完整内容。";
  }


  function renderAiReport(report, fallbackAnswer) {
    if (!report || typeof report !== "object") {
      return textToHtml(fallbackAnswer || "系统已完成抽签，但没有返回结构化解签正文。");
    }

    const suggestions = Array.isArray(report.action_suggestions)
      ? report.action_suggestions.filter(Boolean).slice(0, 3)
      : [];

    const suggestionHtml = suggestions.length
      ? suggestions.map((item, index) => `
          <li>
            <span>${String(index + 1).padStart(2, "0")}</span>
            <p>${escapeHtml(item)}</p>
          </li>
        `).join("")
      : '<li><span>--</span><p class="muted">暂无行动建议。</p></li>';

    return `
      <div class="v10-ai-report">
        <section class="v10-summary-strip">
          <div>
            <div class="ai-section-label">一句话结论</div>
            <h4>${escapeHtml(report.short_conclusion || "当前宜稳不宜急，先守住节奏，再观察转机。")}</h4>
          </div>
          <div class="v10-attitude-pill">${escapeHtml(report.fortune_attitude || "谨慎推进")}</div>
        </section>

        <section class="v10-main-reading-grid">
          <article class="v10-reading-primary">
            <div class="ai-section-label">针对问题的解读</div>
            <p>${escapeHtml(report.answer_to_question || report.plain_summary || "暂无针对问题的解读。")}</p>
          </article>
          <article class="v10-action-list-card">
            <div class="ai-section-label">行动建议</div>
            <ol>${suggestionHtml}</ol>
          </article>
        </section>

        <section class="v10-secondary-grid">
          <article class="v10-small-card">
            <div class="ai-section-label">白话总结</div>
            <p>${escapeHtml(report.plain_summary || "暂无白话总结。")}</p>
          </article>
          <article class="v10-small-card caution-reading">
            <div class="ai-section-label">风险提醒</div>
            <p>${escapeHtml(report.risk_warning || "不要仅凭签文做重大现实决策，重要事项仍需结合事实、资源和专业意见判断。")}</p>
          </article>
          <article class="v10-small-card comfort-reading">
            <div class="ai-section-label">安抚与提醒</div>
            <p>${escapeHtml(report.comfort_message || "先稳住节奏，很多问题会在持续行动中逐渐清楚。")}</p>
          </article>
        </section>

        <details class="v10-traditional-fold">
          <summary>展开传统签意摘要</summary>
          <p>${escapeHtml(report.traditional_explanation || "暂无传统签意解释。")}</p>
        </details>
      </div>
    `;
  }

  function renderQuestionAnalysis(analysis) {
    if (!analysis || typeof analysis !== "object") return "";
    const keywords = Array.isArray(analysis.keywords) ? analysis.keywords : [];
    const keywordHtml = keywords.length
      ? keywords.map((kw) => `<span class="profile-tag">${escapeHtml(kw)}</span>`).join("")
      : '<span class="profile-tag">暂无关键词</span>';
    return `
      <div class="question-analysis-card">
        <span class="qa-pill">方向：${escapeHtml(analysis.aspect_label || "综合")}</span>
        <span class="qa-pill">情绪：${escapeHtml(analysis.emotion || "平静/求稳")}</span>
        <span class="qa-pill">类型：${escapeHtml(analysis.question_type || "建议型")}</span>
        <div class="profile-tags qa-keywords">${keywordHtml}</div>
      </div>
    `;
  }

  function renderScoreBars(evidence) {
    if (!scoreBars) return;
    scoreBars.innerHTML = "";

    if (!Array.isArray(evidence) || evidence.length === 0) {
      scoreBars.innerHTML = '<p class="muted">暂无 RAG 检索分数。</p>';
      return;
    }

    const topEvidence = evidence.slice(0, 3);
    const maxScore = Math.max(...topEvidence.map((item) => Number(item.score || 0)), 0.001);

    topEvidence.forEach((item, index) => {
      const meta = item.metadata || {};
      const score = Number(item.score || 0);
      const width = Math.max(4, Math.round((score / maxScore) * 100));

      const row = document.createElement("div");
      row.className = "score-row compact-score-row";
      row.innerHTML = `
        <div class="score-rank-badge">Top ${index + 1}</div>
        <div class="score-info">
          <strong>${escapeHtml(meta.aspect_label || meta.aspect || "综合")}</strong>
          <span>${escapeHtml(meta.chunk_type || "签文片段")}</span>
        </div>
        <div class="score-track"><div class="score-fill" style="width:${width}%"></div></div>
        <div class="score-value">${Number.isFinite(score) ? score.toFixed(3) : "-"}</div>
      `;
      scoreBars.appendChild(row);
    });
  }

  function renderEvidence(evidence) {
    if (!evidenceList) return;
    evidenceList.innerHTML = "";

    if (!Array.isArray(evidence) || evidence.length === 0) {
      evidenceList.innerHTML = '<div class="evidence-empty-state"><strong>暂无可展示的检索片段</strong><p>当前接口没有返回 evidence 字段，或知识库暂未命中可展示片段。AI 解读仍可查看，但证据页会保持为空。</p></div>';
      return;
    }

    evidence.slice(0, 3).forEach((item, index) => {
      const metadata = item.metadata || {};
      const fullText = String(item.snippet || item.text || "").trim();
      const brief = trimText(fullText, 170);
      const div = document.createElement("div");
      div.className = "evidence-card v9-evidence-card";
      div.innerHTML = `
        <div class="evidence-title">
          <strong>资料 ${index + 1}</strong>
          <span>${escapeHtml(metadata.sign_id || "-")} · ${escapeHtml(metadata.aspect_label || metadata.aspect || "综合")} · ${escapeHtml(metadata.chunk_type || "片段")}</span>
        </div>
        <p class="evidence-excerpt">${escapeHtml(brief || "暂无摘要。")}</p>
        <details class="evidence-fulltext">
          <summary>展开完整片段</summary>
          <p>${escapeHtml(fullText || "暂无完整片段。")}</p>
        </details>
        <div class="evidence-meta">
          <span>score: ${item.score !== undefined ? Number(item.score).toFixed(4) : "-"}</span>
          <span>${escapeHtml(metadata.story_title || "")}</span>
        </div>
      `;
      evidenceList.appendChild(div);
    });
  }

  function renderTraditionalEvidence(evidence) {
    if (!traditionalEvidence) return;
    if (!Array.isArray(evidence) || evidence.length === 0) {
      traditionalEvidence.innerHTML = '<p class="muted">暂无签文资料。</p>';
      return;
    }

    const labelMap = {
      aspect_interpretation: "方向解释",
      overview: "综合解释",
      poem: "签诗原文",
      story: "典故背景"
    };

    const preferred = evidence.slice(0, 4);
    traditionalEvidence.innerHTML = preferred.map((item, idx) => {
      const meta = item.metadata || {};
      const rawType = meta.chunk_type || `资料 ${idx + 1}`;
      const displayType = labelMap[rawType] || rawType;
      const fullText = String(item.snippet || item.text || "").trim();
      return `
        <details class="traditional-snippet v9-traditional-snippet" ${idx < 2 ? "open" : ""}>
          <summary>
            <strong>${escapeHtml(displayType)}</strong>
            <span>${escapeHtml(meta.aspect_label || meta.aspect || "综合")}</span>
          </summary>
          <p>${escapeHtml(fullText || "暂无内容。")}</p>
        </details>
      `;
    }).join("");
  }

  function polarPoint(cx, cy, radius, angle) {
    return {
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle)
    };
  }

  function buildRadarSvg(dimensions) {
    const size = 360;
    const cx = size / 2;
    const cy = size / 2;
    const maxR = 112;
    const count = dimensions.length || 5;

    const ringPolygons = [20, 40, 60, 80, 100].map((pct) => {
      const points = dimensions.map((_, index) => {
        const angle = -Math.PI / 2 + (index * 2 * Math.PI) / count;
        const p = polarPoint(cx, cy, maxR * (pct / 100), angle);
        return `${p.x.toFixed(1)},${p.y.toFixed(1)}`;
      }).join(" ");
      return `<polygon class="radar-ring" points="${points}"></polygon>`;
    }).join("");

    const axes = dimensions.map((item, index) => {
      const angle = -Math.PI / 2 + (index * 2 * Math.PI) / count;
      const p = polarPoint(cx, cy, maxR, angle);
      const labelPoint = polarPoint(cx, cy, maxR + 30, angle);
      const anchor = labelPoint.x > cx + 8 ? "start" : labelPoint.x < cx - 8 ? "end" : "middle";
      const score = Math.round(safeNumber(item.score));
      return `
        <line class="radar-axis" x1="${cx}" y1="${cy}" x2="${p.x.toFixed(1)}" y2="${p.y.toFixed(1)}"></line>
        <text class="radar-label" x="${labelPoint.x.toFixed(1)}" y="${labelPoint.y.toFixed(1)}" text-anchor="${anchor}">${escapeHtml(item.short_label || item.label)} ${score}</text>
      `;
    }).join("");

    const dataPoints = dimensions.map((item, index) => {
      const angle = -Math.PI / 2 + (index * 2 * Math.PI) / count;
      const score = Math.max(0, Math.min(100, safeNumber(item.score)));
      const p = polarPoint(cx, cy, maxR * (score / 100), angle);
      return `${p.x.toFixed(1)},${p.y.toFixed(1)}`;
    }).join(" ");

    const dots = dimensions.map((item, index) => {
      const angle = -Math.PI / 2 + (index * 2 * Math.PI) / count;
      const score = Math.max(0, Math.min(100, safeNumber(item.score)));
      const p = polarPoint(cx, cy, maxR * (score / 100), angle);
      return `<circle class="radar-dot" cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4"></circle>`;
    }).join("");

    return `
      <svg viewBox="0 0 ${size} ${size}" role="img">
        <title>五维运势雷达图</title>
        ${ringPolygons}
        ${axes}
        <polygon class="radar-area" points="${dataPoints}"></polygon>
        <polyline class="radar-line" points="${dataPoints} ${dataPoints.split(" ")[0]}"></polyline>
        ${dots}
      </svg>
    `;
  }

  function renderRadarAnalysis(radar) {
    if (!radarPanel) return;
    const dimensions = Array.isArray(radar?.dimensions) ? radar.dimensions : [];
    if (!radar || dimensions.length === 0) {
      radarPanel.classList.add("hidden");
      return;
    }

    radarPanel.classList.remove("hidden");
    const avg = Math.round(safeNumber(radar.average_score, 0));
    if (radarAverage) radarAverage.textContent = String(avg);
    if (summaryAverage) summaryAverage.textContent = String(avg);
    if (radarSummary) radarSummary.textContent = radar.summary || "已完成五维运势量化分析。";
    if (radarModelText) radarModelText.textContent = radar.model_explanation || "基于签级、关键词和问题方向生成量化参考。";
    if (radarChart) radarChart.innerHTML = buildRadarSvg(dimensions);

    if (radarScores) {
      radarScores.innerHTML = dimensions.map((item) => {
        const score = Math.round(safeNumber(item.score));
        const confidence = Math.round(safeNumber(item.confidence));
        const width = Math.max(5, Math.min(100, score));
        const keywordTags = (item.keywords || []).slice(0, 4).map((kw) => {
          const kind = kw.weight >= 0 ? "pos" : "caution";
          const sign = kw.weight >= 0 ? "+" : "";
          return `<span class="radar-keyword ${kind}">${escapeHtml(kw.word)} ${sign}${kw.weight}</span>`;
        }).join("");

        return `
          <div class="radar-score-item">
            <div class="radar-score-top">
              <strong>${escapeHtml(item.label)}</strong>
              <span>${score} 分 · 可信度 ${confidence}%</span>
            </div>
            <div class="radar-score-track"><div class="radar-score-fill" style="width:${width}%"></div></div>
            <p>${escapeHtml(item.comment || item.evidence || "暂无说明。")}</p>
            <div class="radar-keywords">${keywordTags || '<span class="radar-keyword neutral">无明显关键词</span>'}</div>
          </div>
        `;
      }).join("");
    }
  }

  function normalizeCountItems(value, fallbackTotal = 0) {
    let items = [];

    if (Array.isArray(value)) {
      items = value.map((item) => {
        if (Array.isArray(item)) {
          const label = item[0];
          const count = safeNumber(item[1], 0);
          return { label, count, ratio: fallbackTotal ? count / fallbackTotal : 0 };
        }
        if (item && typeof item === "object") {
          const label = item.label || item.name || item.aspect || item.keyword || "未分类";
          const count = safeNumber(item.count ?? item.value, 0);
          const ratio = safeNumber(item.ratio, fallbackTotal ? count / fallbackTotal : 0);
          return { label, count, ratio };
        }
        return null;
      }).filter(Boolean);
    } else if (value && typeof value === "object") {
      const total = fallbackTotal || Object.values(value).reduce((acc, n) => acc + safeNumber(n, 0), 0);
      items = Object.entries(value).map(([label, count]) => {
        const n = safeNumber(count, 0);
        return { label, count: n, ratio: total ? n / total : 0 };
      });
    }

    return items
      .filter((item) => item.label !== undefined && item.label !== null)
      .sort((a, b) => b.count - a.count);
  }

  const CLOUD_TERM_ALIASES = {
    "事业求职": "事业",
    "学业考试": "学业",
    "财富财运": "财运",
    "感情人际": "感情",
    "健康状态": "健康",
    "求职": "工作",
    "找工作": "工作",
    "找实习": "实习",
    "求实习": "实习",
    "升职": "晋升",
    "加薪": "薪资",
    "破": "阻滞",
    "阻": "阻滞",
    "难": "困难",
    "project": "项目",
    "internship": "实习",
    "job": "工作",
    "work": "工作"
  };

  const CLOUD_FOCUS_TERMS = [
    "实习", "工作", "求职", "面试", "简历", "项目", "科研", "论文", "学习", "学业", "考试",
    "感情", "人际", "财运", "投资", "健康", "焦虑", "选择", "坚持", "机会", "沟通", "方向",
    "晋升", "薪资", "贵人", "阻滞", "顺利", "发展", "等待", "谨慎", "成功", "困难", "小心", "稳定"
  ];

  const CLOUD_STOPWORDS = new Set([
    "如何", "是否", "什么", "怎么", "怎样", "可以", "能否", "有没有", "是不是", "最近", "今天", "今日",
    "明天", "这个", "那个", "一下", "一些", "目前", "问题", "情况", "结果", "方面", "相关", "综合",
    "用户", "签文", "解签", "进行", "感觉", "还是", "应该", "需要", "可能", "比较", "一个", "时候",
    "之后", "之前", "现在", "未来", "继续", "保持", "今日进展", "进展如何", "的今日进展"
  ]);

  function extractCloudKeywords(raw) {
    let text = String(raw || "").trim();
    if (!text || text === "暂无关键词" || text === "-") return [];

    text = text
      .replace(/[｜|/\\#*_`~.,，。！？!?;；:：()[\]{}<>《》"“”'‘’]/g, " ")
      .replace(/\s+/g, " ")
      .trim();

    if (!text) return [];

    if (/^(aspect|aspect_interpretation|overview|poem|story|chunk|metadata|sign|score|keyword|rag|qwen|llm|api|frontend|backend)$/i.test(text)) return [];

    const lower = text.toLowerCase();
    if (CLOUD_TERM_ALIASES[lower]) return [CLOUD_TERM_ALIASES[lower]];
    if (CLOUD_TERM_ALIASES[text]) return [CLOUD_TERM_ALIASES[text]];

    // 对较长短语做主题词抽取，避免“的今日进展 / 进展如何”这类碎片进入词云。
    if (text.length > 4) {
      const hits = CLOUD_FOCUS_TERMS.filter((term) => text.includes(term));
      if (hits.length) return hits;
    }

    if (CLOUD_STOPWORDS.has(text)) return [];
    if (/^[a-z_]{3,}$/i.test(text)) return [];
    if (text.length === 1 && !["财"].includes(text)) return [];
    if (text.length > 8) return [];

    return [CLOUD_TERM_ALIASES[text] || text];
  }

  function normalizeWordCloudItems(items, limit = 26) {
    const rawList = normalizeCountItems(items);
    if (!rawList.length) return [];

    const merged = new Map();
    rawList.forEach((item) => {
      const parts = extractCloudKeywords(item.label);
      parts.forEach((label) => {
        const count = Math.max(1, safeNumber(item.count, 1));
        merged.set(label, (merged.get(label) || 0) + count);
      });
    });

    const list = Array.from(merged.entries())
      .map(([label, count]) => ({ label, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, limit);

    if (!list.length) return [];
    const maxCount = Math.max(...list.map((item) => item.count), 1);

    const positions = [
      [50, 48, -3], [34, 48, 2], [66, 48, 3], [24, 58, -4], [76, 58, 2],
      [50, 62, 0], [41, 36, -2], [59, 35, 4], [18, 42, 5], [82, 42, -5],
      [33, 68, 3], [67, 70, -3], [48, 25, 2], [22, 76, -2], [78, 77, 4],
      [12, 57, -3], [88, 60, 3], [38, 80, -4], [61, 82, 2], [50, 76, 0],
      [30, 29, 4], [70, 28, -4], [14, 34, 2], [86, 34, -2], [42, 88, 2], [58, 88, -2]
    ];

    return list.map((item, index) => {
      const ratio = item.count / maxCount;
      const [x, y, rotate] = positions[index % positions.length];
      return {
        label: item.label,
        count: safeNumber(item.count, 1),
        size: Math.round(16 + ratio * 34 + (index < 3 ? 4 : 0)),
        tone: index < 3 ? "hot" : index < 10 ? "mid" : "soft",
        rotate,
        x,
        y,
        z: 60 - index
      };
    });
  }

  function renderWordCloud(items, emptyText = "暂无关键词") {
    const list = normalizeWordCloudItems(items);
    if (!list.length) return `<p class="muted">${escapeHtml(emptyText)}</p>`;
    return `
      <div class="wordcloud-inner real-wordcloud" aria-label="关键词词云">
        ${list.map((item) => `
          <span class="cloud-word ${item.tone}" style="--s:${item.size}px; --x:${item.x}%; --y:${item.y}%; --r:${item.rotate}deg; --z:${item.z};" title="${escapeHtml(item.label)}：${item.count} 次">
            ${escapeHtml(item.label)}
          </span>
        `).join("")}
      </div>
    `;
  }

  function collectCurrentKeywordItems(data) {
    const counter = new Map();
    const add = (word, weight = 1) => {
      const keys = extractCloudKeywords(word);
      keys.forEach((key) => {
        if (!key || key === "暂无关键词" || key === "-") return;
        counter.set(key, (counter.get(key) || 0) + weight);
      });
    };

    (data.selectedSign?.keywords || []).forEach((kw) => add(kw, 3));
    (data.questionAnalysis?.keywords || []).forEach((kw) => add(kw, 4));
    if (data.questionAnalysis?.aspect_label) add(data.questionAnalysis.aspect_label, 2);

    const dims = Array.isArray(data.radarAnalysis?.dimensions) ? data.radarAnalysis.dimensions : [];
    dims.forEach((dim) => {
      if (dim.label) add(dim.label, 1);
      (dim.keywords || []).slice(0, 4).forEach((kw) => add(kw.word || kw, Math.max(1, Math.abs(safeNumber(kw.weight, 1)))));
    });

    (data.evidence || []).slice(0, 6).forEach((item) => {
      const meta = item.metadata || {};
      if (meta.aspect_label) add(meta.aspect_label, 1);
      if (meta.chunk_type) add(meta.chunk_type, 1);
      if (meta.story_title) add(meta.story_title, 1);
    });

    return Array.from(counter.entries()).map(([label, count]) => ({ label, count })).sort((a, b) => b.count - a.count);
  }

  function renderProfileBars(items, emptyText = "暂无数据") {
    const list = normalizeCountItems(items);
    if (!list.length) return `<p class="muted">${escapeHtml(emptyText)}</p>`;
    const maxCount = Math.max(...list.map((item) => item.count), 1);

    return `
      <div class="profile-bar-list">
        ${list.slice(0, 8).map((item) => {
          const width = Math.max(8, Math.round((item.count / maxCount) * 100));
          const percent = Math.round(safeNumber(item.ratio, 0) * 100);
          return `
            <div class="profile-bar-row">
              <div class="profile-bar-label">${escapeHtml(item.label)}</div>
              <div class="profile-bar-track"><div class="profile-bar-fill" style="width:${width}%"></div></div>
              <div class="profile-bar-value">${item.count}${percent ? ` · ${percent}%` : ""}</div>
            </div>
          `;
        }).join("")}
      </div>
    `;
  }

  function renderProfileChips(items, emptyText = "暂无数据") {
    const list = normalizeCountItems(items);
    if (!list.length) return `<p class="muted">${escapeHtml(emptyText)}</p>`;

    return `<div class="profile-tags enhanced-tags">
      ${list.slice(0, 16).map((item, index) => {
        const sizeClass = index < 3 ? "hot" : index < 8 ? "mid" : "normal";
        return `<span class="profile-tag ${sizeClass}">${escapeHtml(item.label)} × ${item.count}</span>`;
      }).join("")}
    </div>`;
  }

  function buildTinyTrendSvg(points, valueKey, options = {}) {
    const list = Array.isArray(points) ? points : [];
    if (!list.length) return '<p class="muted">暂无趋势数据。</p>';

    const width = 420;
    const height = 150;
    const padX = 28;
    const padY = 22;
    const values = list.map((p) => safeNumber(p[valueKey], 0));
    const minValue = options.minValue !== undefined ? options.minValue : Math.min(...values, 0);
    const maxValue = options.maxValue !== undefined ? options.maxValue : Math.max(...values, 1);
    const range = Math.max(1, maxValue - minValue);
    const denom = Math.max(1, list.length - 1);

    const coords = list.map((p, index) => {
      const x = padX + (index / denom) * (width - padX * 2);
      const y = height - padY - ((safeNumber(p[valueKey], 0) - minValue) / range) * (height - padY * 2);
      return { x, y, value: safeNumber(p[valueKey], 0), label: p.date || p.full_date || "" };
    });

    const polyline = coords.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
    const area = `${padX},${height - padY} ${polyline} ${width - padX},${height - padY}`;
    const dots = coords.map((p) => `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="3.6"><title>${escapeHtml(p.label)}：${p.value}</title></circle>`).join("");
    const labels = list.length >= 2
      ? `<text x="${padX}" y="${height - 3}">${escapeHtml(list[0].date || "")}</text><text x="${width - padX}" y="${height - 3}" text-anchor="end">${escapeHtml(list[list.length - 1].date || "")}</text>`
      : "";

    return `
      <svg class="profile-trend-svg" viewBox="0 0 ${width} ${height}" role="img">
        <path class="profile-trend-area" d="M ${area} Z"></path>
        <polyline class="profile-trend-line" points="${polyline}"></polyline>
        <g class="profile-trend-dots">${dots}</g>
        <text x="${padX}" y="16">${escapeHtml(options.title || "趋势")}</text>
        <text x="${width - padX}" y="16" text-anchor="end">${escapeHtml(options.unit || "")}</text>
        ${labels}
      </svg>
    `;
  }

  function renderRecentQuestions(items) {
    const rows = Array.isArray(items) ? items : [];
    if (!rows.length) return '<p class="muted">暂无最近记录。</p>';

    return `<div class="profile-recent-list">
      ${rows.slice(0, 8).map((row) => {
        const keywords = Array.isArray(row.keywords) ? row.keywords.slice(0, 4) : [];
        const scoreText = row.overall_score !== undefined && row.overall_score !== null ? `${row.overall_score} 分` : "未记录";
        return `
          <article class="profile-recent-card">
            <div class="recent-main">
              <strong>第 ${pad3(row.sign_id || "---")} 签 · ${escapeHtml(row.level || "未知")}</strong>
              <p>${escapeHtml(row.question || "未填写问题")}</p>
              <div class="recent-keywords">${keywords.length ? keywords.map((kw) => `<span>${escapeHtml(kw)}</span>`).join("") : '<span>无关键词</span>'}</div>
            </div>
            <div class="recent-meta">
              <span>${escapeHtml(row.aspect || "综合")}</span>
              <span>${escapeHtml(row.style || "现代口语")}</span>
              <span>${escapeHtml(scoreText)}</span>
            </div>
          </article>
        `;
      }).join("")}
    </div>`;
  }

  function renderProfileDashboard(data) {
    const total = safeNumber(data.total, 0);
    const kpis = data.kpis || {};
    const averageScore = kpis.average_score !== undefined && kpis.average_score !== null ? `${kpis.average_score}` : "--";
    const aspectItems = normalizeCountItems(data.aspect_distribution?.length ? data.aspect_distribution : data.top_aspects, total);
    const keywordItems = normalizeCountItems(data.keyword_cloud?.length ? data.keyword_cloud : data.top_keywords);
    const levelItems = normalizeCountItems(data.level_chart?.length ? data.level_chart : data.level_distribution, total);
    const styleItems = normalizeCountItems(data.style_chart?.length ? data.style_chart : data.style_distribution, total);
    const mainAspect = kpis.main_aspect || aspectItems[0]?.label || "暂无";
    const mainKeyword = kpis.main_keyword || keywordItems[0]?.label || "暂无";
    const mainStyle = kpis.main_style || styleItems[0]?.label || "暂无";

    return `
      <div class="profile-dashboard">
        <div class="profile-kpi-grid">
          <article class="profile-kpi-card primary-kpi">
            <span>累计求签</span>
            <strong>${total}</strong>
            <small>历史解签记录数</small>
          </article>
          <article class="profile-kpi-card">
            <span>近 7 天</span>
            <strong>${safeNumber(kpis.recent_7_days, 0)}</strong>
            <small>近期交互活跃度</small>
          </article>
          <article class="profile-kpi-card">
            <span>主要关注</span>
            <strong>${escapeHtml(mainAspect)}</strong>
            <small>历史最高频方向</small>
          </article>
          <article class="profile-kpi-card">
            <span>平均指数</span>
            <strong>${escapeHtml(averageScore)}</strong>
            <small>五维雷达综合分</small>
          </article>
        </div>

        <article class="profile-insight-card">
          <div>
            <p class="eyebrow small-eyebrow">PROFILE SUMMARY</p>
            <h4>画像结论</h4>
          </div>
          <p>${escapeHtml(data.recent_summary || "暂无画像总结。")}</p>
        </article>

        <div class="profile-chart-grid">
          <article class="profile-chart-card">
            <h4>关注方向分布</h4>
            ${renderProfileBars(aspectItems, "暂无方向分布数据")}
          </article>
          <article class="profile-chart-card">
            <h4>签级分布</h4>
            ${renderProfileBars(levelItems, "暂无签级分布数据")}
          </article>
          <article class="profile-chart-card wide-chart">
            <h4>最近 14 天求签趋势</h4>
            ${buildTinyTrendSvg(data.daily_trend || [], "count", { title: "每日求签次数", unit: "次" })}
          </article>
          <article class="profile-chart-card wide-chart">
            <h4>综合指数趋势</h4>
            ${buildTinyTrendSvg(data.score_trend || [], "score", { title: "五维综合指数", unit: "0-100", minValue: 0, maxValue: 100 })}
          </article>
          <article class="profile-chart-card wordcloud-card">
            <h4>高频关键词词云</h4>
            <div class="keyword-wordcloud profile-wordcloud">
              ${renderWordCloud(keywordItems, "暂无关键词数据")}
            </div>
          </article>
          <article class="profile-chart-card">
            <h4>解签风格偏好</h4>
            ${renderProfileChips(styleItems, "暂无风格数据")}
          </article>
        </div>

        <details class="profile-chart-card recent-panel recent-collapsible">
          <summary>最近求签记录 <span>${Array.isArray(data.recent_questions) ? data.recent_questions.length : 0} 条</span></summary>
          ${renderRecentQuestions(data.recent_questions || [])}
        </details>
      </div>
    `;
  }

  async function loadUserProfile() {
    if (!profileBox) return;
    try {
      profileBox.innerHTML = '<div class="profile-loading">正在加载用户画像…</div>';
      const res = await fetch(`${getApiBase()}/api/fortune/profile`, { cache: "no-store" });
      if (!res.ok) {
        profileBox.textContent = "用户画像接口暂不可用。";
        return;
      }
      const data = await res.json();
      if (!data || !data.total) {
        profileBox.innerHTML = `
          <div class="profile-empty-state">
            <h4>暂无历史画像</h4>
            <p>完成一次求签并进入解签报告后，这里会展示关注方向、关键词、签级分布、综合指数趋势和最近记录。</p>
          </div>
        `;
        return;
      }

      profileBox.innerHTML = renderProfileDashboard(data);
    } catch (err) {
      console.warn("loadUserProfile failed:", err);
      profileBox.textContent = "用户画像加载失败，请稍后重试。";
    }
  }

  function renderSimilarSigns(items) {
    if (!similarSignsList) return;

    if (!Array.isArray(items) || items.length === 0) {
      similarSignsList.innerHTML = `
        <div class="similar-empty-state">
          <h4>暂无相似签推荐</h4>
          <p>可能是 Chroma 知识库未启动，或当前签文资料不足。系统仍可正常展示 AI 解签与五维雷达。</p>
        </div>
      `;
      return;
    }

    const maxSimilarity = Math.max(...items.map((item) => safeNumber(item.similarity_percent, 0)), 1);

    similarSignsList.innerHTML = `
      <div class="similar-network-note">
        <strong></strong>
        <span></span>
      </div>
      <div class="similar-card-grid">
        ${items.map((item, index) => {
          const percent = safeNumber(item.similarity_percent, Math.round(safeNumber(item.similarity, 0) * 100));
          const width = Math.max(8, Math.round((percent / maxSimilarity) * 100));
          const keywords = Array.isArray(item.keywords) ? item.keywords.slice(0, 6) : [];
          const matchedKeywords = Array.isArray(item.matched_keywords) ? item.matched_keywords.slice(0, 5) : [];
          const matchedAspects = Array.isArray(item.matched_aspects) ? item.matched_aspects.slice(0, 4) : [];
          const evidence = Array.isArray(item.evidence) ? item.evidence.slice(0, 2) : [];
          const evidenceHtml = evidence.length
            ? evidence.map((ev) => `<li>${escapeHtml(ev.snippet || "")}</li>`).join("")
            : '<li class="muted">暂无片段摘要。</li>';
          const tagHtml = keywords.length
            ? keywords.map((kw) => `<span>${escapeHtml(kw)}</span>`).join("")
            : '<span>暂无关键词</span>';
          const matchedHtml = [
            ...matchedKeywords.map((kw) => `关键词：${kw}`),
            ...matchedAspects.map((a) => `维度：${a}`)
          ].slice(0, 6);

          return `
            <article class="similar-card">
              <div class="similar-rank">Top ${index + 1}</div>
              <div class="similar-card-main">
                <div>
                  <h4>第 ${pad3(item.sign_id)} 签｜${escapeHtml(item.story_title || item.title || "灵签")}</h4>
                  <p>${escapeHtml(item.level || "未知")}｜${escapeHtml(item.sign_key || "")}</p>
                </div>
                <div class="similar-score">
                  <strong>${percent}%</strong>
                  <span>相似度</span>
                </div>
              </div>
              <div class="similar-track"><div class="similar-fill" style="width:${width}%"></div></div>
              <p class="similar-reason">${escapeHtml(item.reason || "与当前签在语义向量空间中较为接近。")}</p>
              <div class="similar-tags">${tagHtml}</div>
              ${matchedHtml.length ? `<div class="similar-match-row">${matchedHtml.map((x) => `<span>${escapeHtml(x)}</span>`).join("")}</div>` : ""}
              <details class="similar-evidence">
                <summary>查看命中片段</summary>
                <ul>${evidenceHtml}</ul>
              </details>
            </article>
          `;
        }).join("")}
      </div>
    `;
  }

  function renderSelectedSignMeta(data) {
    const sign = data.selectedSign || {};
    const signNo = pad3(data.signNumber);
    if (reportTitle) reportTitle.textContent = `第 ${signNo} 签｜${data.title}`;
    if (reportMeta) reportMeta.textContent = `${data.level}｜${data.signKey}`;
    if (reportQuestion) reportQuestion.textContent = `用户问题：${data.question || "未填写"}`;
    if (reportBadgeSign) reportBadgeSign.textContent = signNo;
    if (reportLevelChip) reportLevelChip.textContent = data.level || "未知签级";
    if (briefSignId) briefSignId.textContent = signNo;
    if (briefLevel) briefLevel.textContent = data.level || "未知";

    if (traditionalSignTitle) traditionalSignTitle.textContent = `第 ${signNo} 签｜${data.title}`;
    if (traditionalSignMeta) traditionalSignMeta.textContent = `${data.level}｜${data.signKey}`;

    const keywords = Array.isArray(sign.keywords) ? sign.keywords : [];
    if (briefKeywordCount) briefKeywordCount.textContent = String(keywords.length || 0);
    if (selectedKeywords) {
      selectedKeywords.innerHTML = keywords.length
        ? keywords.slice(0, 10).map((kw) => `<span>${escapeHtml(kw)}</span>`).join("")
        : '<span>暂无关键词</span>';
    }
  }

  function renderResult(data) {
    latestResult = data;
    setReportMode("content");
    renderSelectedSignMeta(data);

    if (overviewText) {
      overviewText.textContent =
        data.aiReport?.short_conclusion ||
        data.aiReport?.plain_summary ||
        extractOverview(data.answer);
    }
    if (summaryEvidenceCount) summaryEvidenceCount.textContent = Array.isArray(data.evidence) ? String(data.evidence.length) : "0";
    if (summarySimilarCount) summarySimilarCount.textContent = Array.isArray(data.similarSigns) ? String(data.similarSigns.length) : "0";
    if (summaryAspect) summaryAspect.textContent = data.questionAnalysis?.aspect_label || "综合/自动识别";

    switchTab("ai");

    if (resultContent) {
      const analysisHtml = renderQuestionAnalysis(data.questionAnalysis);
      resultContent.innerHTML = analysisHtml + renderAiReport(data.aiReport, data.answer);
    }

    const hasMetrics = data.metrics && [data.metrics.hit1, data.metrics.hit3, data.metrics.mrr].some((v) => v !== undefined && v !== null && v !== "");
    if (metricHit1) metricHit1.textContent = hasMetrics && data.metrics.hit1 !== undefined ? Number(data.metrics.hit1).toFixed(3) : "-";
    if (metricHit3) metricHit3.textContent = hasMetrics && data.metrics.hit3 !== undefined ? Number(data.metrics.hit3).toFixed(3) : "-";
    if (metricMRR) metricMRR.textContent = hasMetrics && data.metrics.mrr !== undefined ? Number(data.metrics.mrr).toFixed(3) : "-";
    advancedMetricsBlock?.classList.toggle("hidden", !hasMetrics);

    renderTraditionalEvidence(data.evidence);
    renderRadarAnalysis(data.radarAnalysis);
    renderSimilarSigns(data.similarSigns);
    renderScoreBars(data.evidence);
    renderEvidence(data.evidence);
    techPanel?.classList.remove("hidden");
  }

  async function startInterpretation() {
    if (interpreting || !selectedSign) return;
    const question = questionInput?.value.trim() || "";
    if (!question) {
      showView("draw");
      questionInput?.focus();
      return;
    }

    interpreting = true;
    setStep("explain");
    setStage("正在解签", "正在整理解签报告。", "正在分析中…", "explain");
    showView("report");
    resetReportOnly();
    setReportMode("loading");

    if (reportTitle) reportTitle.textContent = `第 ${pad3(selectedSign.sign_id)} 签｜${selectedSign.story_title || selectedSign.title || "灵签"}`;
    if (reportMeta) reportMeta.textContent = `${selectedSign.level || "未知"}｜正在生成解读`;
    if (reportQuestion) reportQuestion.textContent = `用户问题：${question}`;
    if (reportBadgeSign) reportBadgeSign.textContent = pad3(selectedSign.sign_id);
    if (reportLevelChip) reportLevelChip.textContent = selectedSign.level || "未知签级";

    try {
      const result = await requestFortune(question, selectedSign);
      renderResult(result);
      await loadUserProfile();
      interpreting = false;
    } catch (err) {
      console.error(err);
      setReportMode("error");
      if (errorText) {
        errorText.textContent = `请求失败：${err.message}\n\n请检查：\n1. 当前页面是否由 FastAPI 项目端口打开，例如 http://192.168.85.136:18080/；\n2. Qwen/vLLM 是否运行在 8000；
3. /api/fortune/draw 与 /api/fortune/interpret 是否可访问；\n3. Chroma fortune_knowledge 是否已构建；\n4. 高级设置里的后端 API 地址是否填错。`;
      }
      interpreting = false;
    }
  }

  function switchTab(tabName) {
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.tab === tabName);
    });
    document.querySelectorAll(".tab-panel").forEach((panel) => {
      panel.classList.toggle("active", panel.id === `tab-${tabName}`);
    });
  }

  toggleAdvancedBtn?.addEventListener("click", () => {
    advancedOptions?.classList.toggle("hidden");
  });

  drawModeInput?.addEventListener("change", updateSignIdVisibility);
  submitBtn?.addEventListener("click", handleStartDraw);
  clearBtn?.addEventListener("click", () => resetAll({ clearQuestion: false }));
  drawCard?.addEventListener("click", startInterpretation);

  backToDrawBtn?.addEventListener("click", () => showView("draw"));
  newDrawBtn?.addEventListener("click", () => {
    resetAll({ clearQuestion: false });
    showView("draw");
  });

  refreshProfileBtn?.addEventListener("click", loadUserProfile);

  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  updateSignIdVisibility();
  resetAll({ clearQuestion: false });
  showView("draw");
});
