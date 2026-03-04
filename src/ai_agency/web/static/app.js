/* === AI Agency Web UI === */

const API = {
  async post(url, data) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return res.json();
  },
  async get(url) {
    const res = await fetch(url);
    return res.json();
  },
};

// --- State ---
let currentPRD = null;
let currentDesigns = null;
let samples = [];

// Track which source each tool uses: 'text' or 'prd'
const toolSource = {
  market: "text",
  competitor: "text",
  viability: "text",
  roadmap: "text",
  pitch: "text",
};

// --- Navigation ---
function navigate(sectionId) {
  document.querySelectorAll(".section").forEach((s) => s.classList.remove("active"));
  document.querySelectorAll(".sidebar-nav a").forEach((a) => a.classList.remove("active"));

  const section = document.getElementById(sectionId);
  if (section) section.classList.add("active");

  const link = document.querySelector(`[data-section="${sectionId}"]`);
  if (link) link.classList.add("active");
}

document.addEventListener("DOMContentLoaded", () => {
  // Nav links
  document.querySelectorAll(".sidebar-nav a").forEach((a) => {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      navigate(a.dataset.section);
    });
  });

  // Load config, samples, and existing PRD
  loadConfig();
  loadSamples();
  loadLatestPRD();
});

async function loadConfig() {
  try {
    const config = await API.get("/api/config");
    document.getElementById("config-provider").textContent = config.provider;
    document.getElementById("config-model").textContent = config.model;
  } catch {
    // ignore
  }
}

async function loadSamples() {
  try {
    const data = await API.get("/api/samples");
    samples = data.samples || [];
    renderExampleCards("pipeline-examples", "pipeline-input");
    renderExampleCards("prd-examples", "prd-input");
    // Render examples for new tools
    renderExampleCards("market-examples", "market-input");
    renderExampleCards("competitor-examples", "competitor-input");
    renderExampleCards("viability-examples", "viability-input");
    renderExampleCards("roadmap-examples", "roadmap-input");
    renderExampleCards("pitch-examples", "pitch-input");
  } catch {
    // ignore
  }
}

function renderExampleCards(containerId, textareaId) {
  const container = document.getElementById(containerId);
  if (!container || samples.length === 0) return;

  container.innerHTML = samples
    .map(
      (s) => `
      <div class="example-card" onclick="loadSample('${s.id}', '${textareaId}')">
        <div class="example-title">${escapeHTML(s.label)}</div>
        <div class="example-desc">${escapeHTML(s.description)}</div>
        <div class="example-action">Use this example &rarr;</div>
      </div>`
    )
    .join("");
}

function loadSample(sampleId, textareaId) {
  const sample = samples.find((s) => s.id === sampleId);
  if (!sample) return;

  const textarea = document.getElementById(textareaId);
  if (textarea) {
    textarea.value = sample.content;
    // Scroll the textarea into view
    textarea.scrollIntoView({ behavior: "smooth", block: "center" });
    textarea.focus();
  }
}

// --- Tool source toggle (text vs PRD) ---
function toggleToolSource(btn, toolName, source) {
  toolSource[toolName] = source;

  // Toggle button active states
  const toggle = btn.closest(".tool-source-toggle");
  toggle.querySelectorAll(".source-btn").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");

  // Toggle input areas
  const textArea = document.getElementById(`${toolName}-text-input`);
  const prdArea = document.getElementById(`${toolName}-prd-input`);

  if (source === "text") {
    textArea.style.display = "block";
    prdArea.style.display = "none";
  } else {
    textArea.style.display = "none";
    prdArea.style.display = "block";
    // Update PRD status
    updatePRDStatus(toolName);
  }
}

function updatePRDStatus(toolName) {
  const statusEl = document.getElementById(`${toolName}-prd-status`);
  if (!statusEl) return;
  if (currentPRD) {
    const name = currentPRD.product_overview?.name || "Unknown";
    statusEl.textContent = `PRD loaded: "${name}" — ready to analyze`;
    statusEl.style.color = "var(--success)";
  } else {
    statusEl.textContent = "No PRD loaded. Generate one first.";
    statusEl.style.color = "var(--text-dim)";
  }
}

function getToolInput(toolName, inputId) {
  if (toolSource[toolName] === "prd" && currentPRD) {
    return { prd_json: currentPRD };
  }
  const text = document.getElementById(inputId)?.value.trim();
  if (!text) return null;
  return { requirements: text };
}

// --- Editor Write/Preview toggle ---
function switchEditorMode(btn, textareaId, previewId) {
  const toolbar = btn.closest(".editor-tabs");
  const tabs = toolbar.querySelectorAll(".editor-tab");
  const textarea = document.getElementById(textareaId);
  const preview = document.getElementById(previewId);
  const isPreview = btn.textContent.trim() === "Preview";

  tabs.forEach((t) => t.classList.remove("active"));
  btn.classList.add("active");

  if (isPreview) {
    textarea.style.display = "none";
    preview.style.display = "block";
    const md = textarea.value.trim();
    preview.innerHTML = md ? renderMarkdown(md) : '<p style="color:var(--text-dim)">Nothing to preview yet.</p>';
  } else {
    textarea.style.display = "block";
    preview.style.display = "none";
  }
}

async function loadLatestPRD() {
  try {
    const data = await API.get("/api/prd/latest");
    if (data.success) {
      currentPRD = data.prd_json;
      document.getElementById("design-status").textContent =
        "PRD available — ready to generate designs";
      document.getElementById("design-status").style.color = "var(--success)";
      // Update all tool PRD statuses
      ["market", "competitor", "viability", "roadmap", "pitch"].forEach(updatePRDStatus);
    }
  } catch {
    // ignore
  }
}

// --- Loader ---
function showLoader(msg, sub) {
  document.getElementById("loader-msg").textContent = msg;
  document.getElementById("loader-sub").textContent = sub || "";
  document.getElementById("loader").classList.add("active");
}

function hideLoader() {
  document.getElementById("loader").classList.remove("active");
}

// --- Toast ---
function toast(msg, type = "success") {
  const existing = document.querySelectorAll(".toast");
  existing.forEach((t) => t.remove());

  const el = document.createElement("div");
  el.className = `toast toast-${type}`;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

// --- PRD Generation ---
async function generatePRD() {
  const text = document.getElementById("prd-input").value.trim();
  if (!text) {
    toast("Please enter requirements text", "error");
    return;
  }

  showLoader("Generating PRD...", "This may take 30-60 seconds depending on complexity");
  const btn = document.getElementById("prd-generate-btn");
  btn.disabled = true;

  try {
    const data = await API.post("/api/prd/generate", { requirements: text });
    hideLoader();
    btn.disabled = false;

    if (!data.success) {
      toast(`Error: ${data.error}`, "error");
      return;
    }

    currentPRD = data.prd_json;
    // Update all tool PRD statuses
    ["market", "competitor", "viability", "roadmap", "pitch"].forEach(updatePRDStatus);
    toast("PRD generated successfully!");
    renderPRDResults(data);
    navigate("section-results");
  } catch (err) {
    hideLoader();
    btn.disabled = false;
    toast(`Request failed: ${err.message}`, "error");
  }
}

// --- Pipeline ---
async function runPipeline() {
  const text = document.getElementById("pipeline-input").value.trim();
  if (!text) {
    toast("Please enter requirements text", "error");
    return;
  }

  showLoader(
    "Running full pipeline...",
    "Step 1/2: Generating PRD... (this may take 30-60 seconds)"
  );
  const btn = document.getElementById("pipeline-btn");
  btn.disabled = true;

  try {
    const data = await API.post("/api/pipeline", { requirements: text });
    hideLoader();
    btn.disabled = false;

    if (!data.success) {
      toast(`Error: ${data.error}`, "error");
      return;
    }

    currentPRD = data.prd_json;
    currentDesigns = data.screens;
    ["market", "competitor", "viability", "roadmap", "pitch"].forEach(updatePRDStatus);
    toast("Pipeline complete!");
    renderPipelineResults(data);
    navigate("section-results");
  } catch (err) {
    hideLoader();
    btn.disabled = false;
    toast(`Request failed: ${err.message}`, "error");
  }
}

// --- Design Generation ---
async function generateDesigns() {
  showLoader("Generating design prompts...", "Extracting screens from PRD");
  const btn = document.getElementById("design-generate-btn");
  btn.disabled = true;

  try {
    const body = currentPRD ? { prd_json: currentPRD } : {};
    const data = await API.post("/api/design/generate", body);
    hideLoader();
    btn.disabled = false;

    if (!data.success) {
      toast(`Error: ${data.error}`, "error");
      return;
    }

    currentDesigns = data.screens;
    toast(`Generated ${data.screen_count} design prompts!`);
    renderDesignResults(data);
    navigate("section-results");
  } catch (err) {
    hideLoader();
    btn.disabled = false;
    toast(`Request failed: ${err.message}`, "error");
  }
}

// --- Market Analysis ---
async function generateMarketAnalysis() {
  const body = getToolInput("market", "market-input");
  if (!body) {
    toast("Please enter a product description or load a PRD", "error");
    return;
  }

  showLoader("Running Market Analysis...", "Analyzing market size, trends, and opportunities");
  const btn = document.getElementById("market-btn");
  btn.disabled = true;

  try {
    const data = await API.post("/api/market-analysis/generate", body);
    hideLoader();
    btn.disabled = false;

    if (!data.success) {
      toast(`Error: ${data.error}`, "error");
      return;
    }

    toast("Market Analysis complete!");
    renderMarketAnalysisResults(data);
    navigate("section-results");
  } catch (err) {
    hideLoader();
    btn.disabled = false;
    toast(`Request failed: ${err.message}`, "error");
  }
}

// --- Competitor Analysis ---
async function generateCompetitorAnalysis() {
  const body = getToolInput("competitor", "competitor-input");
  if (!body) {
    toast("Please enter a product description or load a PRD", "error");
    return;
  }

  showLoader("Running Competitor Analysis...", "Profiling competitors and building SWOT analysis");
  const btn = document.getElementById("competitor-btn");
  btn.disabled = true;

  try {
    const data = await API.post("/api/competitor-analysis/generate", body);
    hideLoader();
    btn.disabled = false;

    if (!data.success) {
      toast(`Error: ${data.error}`, "error");
      return;
    }

    toast("Competitor Analysis complete!");
    renderCompetitorAnalysisResults(data);
    navigate("section-results");
  } catch (err) {
    hideLoader();
    btn.disabled = false;
    toast(`Request failed: ${err.message}`, "error");
  }
}

// --- Viability Assessment ---
async function generateViability() {
  const body = getToolInput("viability", "viability-input");
  if (!body) {
    toast("Please enter a product description or load a PRD", "error");
    return;
  }

  showLoader("Assessing Viability...", "Evaluating technical feasibility, risks, and resources");
  const btn = document.getElementById("viability-btn");
  btn.disabled = true;

  try {
    const data = await API.post("/api/viability/generate", body);
    hideLoader();
    btn.disabled = false;

    if (!data.success) {
      toast(`Error: ${data.error}`, "error");
      return;
    }

    toast("Viability Assessment complete!");
    renderViabilityResults(data);
    navigate("section-results");
  } catch (err) {
    hideLoader();
    btn.disabled = false;
    toast(`Request failed: ${err.message}`, "error");
  }
}

// --- Roadmap Generator ---
async function generateRoadmap() {
  const body = getToolInput("roadmap", "roadmap-input");
  if (!body) {
    toast("Please enter a product description or load a PRD", "error");
    return;
  }

  showLoader("Generating Roadmap...", "Building phased plan with milestones and dependencies");
  const btn = document.getElementById("roadmap-btn");
  btn.disabled = true;

  try {
    const data = await API.post("/api/roadmap/generate", body);
    hideLoader();
    btn.disabled = false;

    if (!data.success) {
      toast(`Error: ${data.error}`, "error");
      return;
    }

    toast("Product Roadmap generated!");
    renderRoadmapResults(data);
    navigate("section-results");
  } catch (err) {
    hideLoader();
    btn.disabled = false;
    toast(`Request failed: ${err.message}`, "error");
  }
}

// --- Pitch Deck Generator ---
async function generatePitchDeck() {
  const body = getToolInput("pitch", "pitch-input");
  if (!body) {
    toast("Please enter a product description or load a PRD", "error");
    return;
  }

  showLoader("Generating Pitch Deck...", "Creating slides with speaker notes and visuals");
  const btn = document.getElementById("pitch-btn");
  btn.disabled = true;

  try {
    const data = await API.post("/api/pitch-deck/generate", body);
    hideLoader();
    btn.disabled = false;

    if (!data.success) {
      toast(`Error: ${data.error}`, "error");
      return;
    }

    toast("Pitch Deck generated!");
    renderPitchDeckResults(data);
    navigate("section-results");
  } catch (err) {
    hideLoader();
    btn.disabled = false;
    toast(`Request failed: ${err.message}`, "error");
  }
}

// --- Rendering: PRD ---
function renderPRDResults(data) {
  const container = document.getElementById("results-content");

  const statsHTML = `
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-value">${data.summary.features}</div><div class="stat-label">Features</div></div>
      <div class="stat-card"><div class="stat-value">${data.summary.api_endpoints}</div><div class="stat-label">API Endpoints</div></div>
      <div class="stat-card"><div class="stat-value">${data.summary.data_models}</div><div class="stat-label">Data Models</div></div>
      <div class="stat-card"><div class="stat-value">${data.summary.personas}</div><div class="stat-label">Personas</div></div>
      <div class="stat-card"><div class="stat-value">${data.summary.journeys}</div><div class="stat-label">Journeys</div></div>
    </div>
  `;

  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3>${escapeHTML(data.summary.product_name)}</h3>
        <button class="btn btn-primary btn-sm" onclick="generateDesigns()">Generate Designs</button>
      </div>
      <p style="color: var(--text-muted); font-size: 0.87rem; margin-bottom: 20px;">${escapeHTML(data.summary.tagline)}</p>
      ${statsHTML}
      <div class="tabs">
        <button class="tab-btn active" onclick="switchTab(this, 'tab-md')">Document</button>
        <button class="tab-btn" onclick="switchTab(this, 'tab-json')">JSON</button>
      </div>
      <div id="tab-md" class="tab-content active">
        <div class="markdown-view">${renderMarkdown(data.prd_markdown)}</div>
      </div>
      <div id="tab-json" class="tab-content">
        <div style="display:flex;justify-content:flex-end;margin-bottom:8px;">
          <button class="copy-btn" onclick="copyJSON()">Copy JSON</button>
        </div>
        <div class="output-block" id="json-output">${escapeHTML(JSON.stringify(data.prd_json, null, 2))}</div>
      </div>
    </div>
  `;

  document.getElementById("results-title").textContent = "PRD Results";
  document.getElementById("results-subtitle").textContent =
    `Generated PRD for "${data.summary.product_name}"`;
}

// --- Rendering: Design ---
function renderDesignResults(data) {
  const container = document.getElementById("results-content");
  const screens = Object.entries(data.screens);

  const cardsHTML = screens
    .map(
      ([name, prompt]) => `
    <div class="screen-card" onclick="showScreenModal('${escapeAttr(name)}')">
      <h4>${escapeHTML(name)}</h4>
      <p>${escapeHTML(prompt.substring(0, 150))}...</p>
    </div>
  `
    )
    .join("");

  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3>Design Prompts</h3>
        <span style="color: var(--text-muted); font-size: 0.82rem;">${screens.length} screens</span>
      </div>
      <div class="screen-grid">${cardsHTML}</div>
    </div>
  `;

  document.getElementById("results-title").textContent = "Design Prompts";
  document.getElementById("results-subtitle").textContent =
    `${screens.length} screen designs generated`;
}

// --- Rendering: Pipeline ---
function renderPipelineResults(data) {
  const container = document.getElementById("results-content");
  const screens = Object.entries(data.screens);

  const statsHTML = `
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-value">${data.summary.features}</div><div class="stat-label">Features</div></div>
      <div class="stat-card"><div class="stat-value">${data.summary.api_endpoints}</div><div class="stat-label">API Endpoints</div></div>
      <div class="stat-card"><div class="stat-value">${data.summary.data_models}</div><div class="stat-label">Data Models</div></div>
      <div class="stat-card"><div class="stat-value">${data.summary.personas}</div><div class="stat-label">Personas</div></div>
      <div class="stat-card"><div class="stat-value">${data.summary.screens}</div><div class="stat-label">Screens</div></div>
    </div>
  `;

  const cardsHTML = screens
    .map(
      ([name, prompt]) => `
    <div class="screen-card" onclick="showScreenModal('${escapeAttr(name)}')">
      <h4>${escapeHTML(name)}</h4>
      <p>${escapeHTML(prompt.substring(0, 150))}...</p>
    </div>
  `
    )
    .join("");

  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3>${escapeHTML(data.summary.product_name)}</h3>
      </div>
      <p style="color: var(--text-muted); font-size: 0.87rem; margin-bottom: 20px;">${escapeHTML(data.summary.tagline)}</p>
      ${statsHTML}

      <div class="tabs">
        <button class="tab-btn active" onclick="switchTab(this, 'tab-md')">PRD Document</button>
        <button class="tab-btn" onclick="switchTab(this, 'tab-json')">PRD JSON</button>
        <button class="tab-btn" onclick="switchTab(this, 'tab-designs')">Design Prompts</button>
      </div>

      <div id="tab-md" class="tab-content active">
        <div class="markdown-view">${renderMarkdown(data.prd_markdown)}</div>
      </div>
      <div id="tab-json" class="tab-content">
        <div style="display:flex;justify-content:flex-end;margin-bottom:8px;">
          <button class="copy-btn" onclick="copyJSON()">Copy JSON</button>
        </div>
        <div class="output-block" id="json-output">${escapeHTML(JSON.stringify(data.prd_json, null, 2))}</div>
      </div>
      <div id="tab-designs" class="tab-content">
        <div class="screen-grid">${cardsHTML}</div>
      </div>
    </div>
  `;

  document.getElementById("results-title").textContent = "Pipeline Results";
  document.getElementById("results-subtitle").textContent =
    `Full pipeline output for "${data.summary.product_name}"`;
}

// --- Rendering: Market Analysis ---
function renderMarketAnalysisResults(data) {
  const container = document.getElementById("results-content");
  const s = data.summary;
  const aj = data.analysis_json;

  // Build opportunity score bars
  const scoresHTML = (aj.opportunity_scores || [])
    .map(
      (o) => `
    <div class="score-bar-row">
      <span class="score-bar-label">${escapeHTML(o.category)}</span>
      <div class="score-bar-track">
        <div class="score-bar-fill" style="width:${o.score * 10}%;"></div>
      </div>
      <span class="score-bar-value">${o.score}/10</span>
    </div>`
    )
    .join("");

  // Build market sizing funnel
  const funnelHTML = `
    <div class="market-funnel">
      <div class="funnel-level funnel-tam"><div class="funnel-label">TAM</div><div class="funnel-value">${escapeHTML(s.tam)}</div></div>
      <div class="funnel-level funnel-sam"><div class="funnel-label">SAM</div><div class="funnel-value">${escapeHTML(s.sam)}</div></div>
      <div class="funnel-level funnel-som"><div class="funnel-label">SOM</div><div class="funnel-value">${escapeHTML(s.som)}</div></div>
    </div>
  `;

  // Build projection table
  const projHTML = (aj.projections || [])
    .map(
      (p) =>
        `<tr><td>${escapeHTML(p.year)}</td><td>${escapeHTML(p.revenue)}</td><td>${escapeHTML(p.users)}</td><td>${escapeHTML(p.market_share)}</td></tr>`
    )
    .join("");

  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3>Market Analysis</h3>
        <span class="badge badge-accent">${s.segments} segments | ${s.trends} trends</span>
      </div>
      <p style="color: var(--text-muted); font-size: 0.87rem; margin-bottom: 20px;">${escapeHTML(aj.executive_summary || "")}</p>

      <div class="stats-grid">
        <div class="stat-card"><div class="stat-value">${escapeHTML(s.tam)}</div><div class="stat-label">TAM</div></div>
        <div class="stat-card"><div class="stat-value">${escapeHTML(s.sam)}</div><div class="stat-label">SAM</div></div>
        <div class="stat-card"><div class="stat-value">${escapeHTML(s.som)}</div><div class="stat-label">SOM</div></div>
        <div class="stat-card"><div class="stat-value">${s.avg_opportunity_score}/10</div><div class="stat-label">Avg. Score</div></div>
      </div>

      <div class="tabs">
        <button class="tab-btn active" onclick="switchTab(this, 'tab-market-viz')">Dashboard</button>
        <button class="tab-btn" onclick="switchTab(this, 'tab-market-md')">Full Report</button>
        <button class="tab-btn" onclick="switchTab(this, 'tab-market-json')">JSON</button>
      </div>

      <div id="tab-market-viz" class="tab-content active">
        <div class="viz-grid">
          <div class="viz-panel">
            <h4>Market Sizing</h4>
            ${funnelHTML}
          </div>
          <div class="viz-panel">
            <h4>Opportunity Scores</h4>
            ${scoresHTML}
          </div>
        </div>
        <div class="viz-panel" style="margin-top:16px;">
          <h4>Growth Projections</h4>
          <table class="data-table">
            <thead><tr><th>Year</th><th>Revenue</th><th>Users</th><th>Market Share</th></tr></thead>
            <tbody>${projHTML}</tbody>
          </table>
        </div>
      </div>
      <div id="tab-market-md" class="tab-content">
        <div class="markdown-view">${renderMarkdown(data.analysis_markdown)}</div>
      </div>
      <div id="tab-market-json" class="tab-content">
        <div style="display:flex;justify-content:flex-end;margin-bottom:8px;">
          <button class="copy-btn" onclick="copyJSON()">Copy JSON</button>
        </div>
        <div class="output-block" id="json-output">${escapeHTML(JSON.stringify(aj, null, 2))}</div>
      </div>
    </div>
  `;

  document.getElementById("results-title").textContent = "Market Analysis";
  document.getElementById("results-subtitle").textContent = "Market sizing, trends, and opportunity assessment";
}

// --- Rendering: Competitor Analysis ---
function renderCompetitorAnalysisResults(data) {
  const container = document.getElementById("results-content");
  const s = data.summary;
  const aj = data.analysis_json;

  // Feature matrix
  const compNames = (aj.competitors || []).map((c) => c.name);
  const matrixHeaderHTML = compNames.map((n) => `<th>${escapeHTML(n)}</th>`).join("");
  const matrixRowsHTML = (aj.feature_matrix || [])
    .map((fm) => {
      const cells = compNames
        .map((n) => {
          const val = fm.competitors[n] || "N/A";
          const cls = val === "none" ? "cell-none" : val === "advanced" ? "cell-advanced" : val === "superior" ? "cell-superior" : "cell-basic";
          return `<td class="${cls}">${escapeHTML(val)}</td>`;
        })
        .join("");
      const ourCls = fm.our_product === "superior" ? "cell-superior" : fm.our_product === "advanced" ? "cell-advanced" : "cell-basic";
      return `<tr><td><strong>${escapeHTML(fm.feature)}</strong></td><td class="${ourCls}">${escapeHTML(fm.our_product)}</td>${cells}</tr>`;
    })
    .join("");

  // SWOT quadrant
  const swotHTML = `
    <div class="swot-grid">
      <div class="swot-quadrant swot-strengths">
        <h4>Strengths</h4>
        ${(aj.swot?.strengths || []).map((s) => `<div class="swot-item"><span class="swot-impact">${s.impact}</span> ${escapeHTML(s.item)}</div>`).join("")}
      </div>
      <div class="swot-quadrant swot-weaknesses">
        <h4>Weaknesses</h4>
        ${(aj.swot?.weaknesses || []).map((w) => `<div class="swot-item"><span class="swot-impact">${w.impact}</span> ${escapeHTML(w.item)}</div>`).join("")}
      </div>
      <div class="swot-quadrant swot-opportunities">
        <h4>Opportunities</h4>
        ${(aj.swot?.opportunities || []).map((o) => `<div class="swot-item"><span class="swot-impact">${o.impact}</span> ${escapeHTML(o.item)}</div>`).join("")}
      </div>
      <div class="swot-quadrant swot-threats">
        <h4>Threats</h4>
        ${(aj.swot?.threats || []).map((t) => `<div class="swot-item"><span class="swot-impact">${t.impact}</span> ${escapeHTML(t.item)}</div>`).join("")}
      </div>
    </div>
  `;

  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3>Competitor Analysis</h3>
        <span class="badge badge-accent">${s.competitors} competitors | ${s.features_compared} features</span>
      </div>
      <p style="color: var(--text-muted); font-size: 0.87rem; margin-bottom: 20px;">${escapeHTML(aj.executive_summary || "")}</p>

      <div class="stats-grid">
        <div class="stat-card"><div class="stat-value">${s.competitors}</div><div class="stat-label">Competitors</div></div>
        <div class="stat-card"><div class="stat-value">${s.features_compared}</div><div class="stat-label">Features</div></div>
        <div class="stat-card"><div class="stat-value">${s.swot_items}</div><div class="stat-label">SWOT Items</div></div>
      </div>

      <div class="tabs">
        <button class="tab-btn active" onclick="switchTab(this, 'tab-comp-viz')">Dashboard</button>
        <button class="tab-btn" onclick="switchTab(this, 'tab-comp-md')">Full Report</button>
        <button class="tab-btn" onclick="switchTab(this, 'tab-comp-json')">JSON</button>
      </div>

      <div id="tab-comp-viz" class="tab-content active">
        <div class="viz-panel">
          <h4>Feature Comparison Matrix</h4>
          <div style="overflow-x:auto;">
            <table class="data-table feature-matrix">
              <thead><tr><th>Feature</th><th>Our Product</th>${matrixHeaderHTML}</tr></thead>
              <tbody>${matrixRowsHTML}</tbody>
            </table>
          </div>
        </div>
        <div class="viz-panel" style="margin-top:16px;">
          <h4>SWOT Analysis</h4>
          ${swotHTML}
        </div>
        <div class="viz-panel" style="margin-top:16px;">
          <h4>Positioning</h4>
          <blockquote class="positioning-quote">${escapeHTML(aj.positioning?.positioning_statement || "")}</blockquote>
          <p style="margin-top:8px;color:var(--text-muted);font-size:0.85rem;"><strong>Value Prop:</strong> ${escapeHTML(s.positioning)}</p>
        </div>
      </div>
      <div id="tab-comp-md" class="tab-content">
        <div class="markdown-view">${renderMarkdown(data.analysis_markdown)}</div>
      </div>
      <div id="tab-comp-json" class="tab-content">
        <div style="display:flex;justify-content:flex-end;margin-bottom:8px;">
          <button class="copy-btn" onclick="copyJSON()">Copy JSON</button>
        </div>
        <div class="output-block" id="json-output">${escapeHTML(JSON.stringify(aj, null, 2))}</div>
      </div>
    </div>
  `;

  document.getElementById("results-title").textContent = "Competitor Analysis";
  document.getElementById("results-subtitle").textContent = "Competitive landscape and positioning";
}

// --- Rendering: Viability ---
function renderViabilityResults(data) {
  const container = document.getElementById("results-content");
  const s = data.summary;
  const vj = data.viability_json;

  const verdictClass = s.verdict === "highly_viable" ? "verdict-great" :
    s.verdict === "viable" ? "verdict-good" :
    s.verdict === "conditionally_viable" ? "verdict-caution" : "verdict-bad";

  // Viability scores bars
  const scoresHTML = (vj.viability_scores || [])
    .map(
      (vs) => `
    <div class="score-bar-row">
      <span class="score-bar-label">${escapeHTML(vs.dimension)}</span>
      <div class="score-bar-track">
        <div class="score-bar-fill" style="width:${vs.score * 10}%;"></div>
      </div>
      <span class="score-bar-value">${vs.score}/10 (x${vs.weight})</span>
    </div>`
    )
    .join("");

  // Risk matrix
  const risksHTML = (vj.risks || [])
    .map(
      (r) => {
        const impactClass = r.impact === "critical" ? "risk-critical" : r.impact === "high" ? "risk-high" : "risk-medium";
        return `<tr class="${impactClass}"><td>${escapeHTML(r.risk)}</td><td>${escapeHTML(r.category)}</td><td>${escapeHTML(r.probability)}</td><td>${escapeHTML(r.impact)}</td><td>${escapeHTML(r.mitigation)}</td></tr>`;
      }
    )
    .join("");

  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3>Product Viability Assessment</h3>
        <span class="badge ${verdictClass}">${s.verdict.replace(/_/g, " ").toUpperCase()}</span>
      </div>
      <p style="color: var(--text-muted); font-size: 0.87rem; margin-bottom: 20px;">${escapeHTML(vj.executive_summary || "")}</p>

      <div class="stats-grid">
        <div class="stat-card"><div class="stat-value">${s.score_pct}%</div><div class="stat-label">Viability Score</div></div>
        <div class="stat-card"><div class="stat-value">${escapeHTML(s.budget)}</div><div class="stat-label">Budget Est.</div></div>
        <div class="stat-card"><div class="stat-value">${escapeHTML(s.timeline)}</div><div class="stat-label">Timeline</div></div>
        <div class="stat-card"><div class="stat-value">${s.risks}</div><div class="stat-label">Risk Factors</div></div>
      </div>

      <div class="tabs">
        <button class="tab-btn active" onclick="switchTab(this, 'tab-via-viz')">Dashboard</button>
        <button class="tab-btn" onclick="switchTab(this, 'tab-via-md')">Full Report</button>
        <button class="tab-btn" onclick="switchTab(this, 'tab-via-json')">JSON</button>
      </div>

      <div id="tab-via-viz" class="tab-content active">
        <div class="viz-grid">
          <div class="viz-panel">
            <h4>Viability Scores</h4>
            ${scoresHTML}
            <div class="score-total">Weighted Total: ${s.weighted_score}/${s.max_score} (${s.score_pct}%)</div>
          </div>
          <div class="viz-panel">
            <h4>Resource Breakdown</h4>
            ${(vj.resource_estimates || []).map((r) => `
              <div class="resource-row">
                <strong>${escapeHTML(r.area)}</strong>
                <div class="resource-detail">${escapeHTML(r.team_size)} | ${escapeHTML(r.duration)} | ${escapeHTML(r.cost_estimate)}</div>
              </div>
            `).join("")}
          </div>
        </div>
        <div class="viz-panel" style="margin-top:16px;">
          <h4>Risk Assessment</h4>
          <div style="overflow-x:auto;">
            <table class="data-table">
              <thead><tr><th>Risk</th><th>Category</th><th>Prob.</th><th>Impact</th><th>Mitigation</th></tr></thead>
              <tbody>${risksHTML}</tbody>
            </table>
          </div>
        </div>
      </div>
      <div id="tab-via-md" class="tab-content">
        <div class="markdown-view">${renderMarkdown(data.viability_markdown)}</div>
      </div>
      <div id="tab-via-json" class="tab-content">
        <div style="display:flex;justify-content:flex-end;margin-bottom:8px;">
          <button class="copy-btn" onclick="copyJSON()">Copy JSON</button>
        </div>
        <div class="output-block" id="json-output">${escapeHTML(JSON.stringify(vj, null, 2))}</div>
      </div>
    </div>
  `;

  document.getElementById("results-title").textContent = "Viability Assessment";
  document.getElementById("results-subtitle").textContent =
    `${s.verdict.replace(/_/g, " ")} — ${s.score_pct}% viability score`;
}

// --- Rendering: Roadmap ---
function renderRoadmapResults(data) {
  const container = document.getElementById("results-content");
  const s = data.summary;
  const rj = data.roadmap_json;

  // Timeline visualization
  const phasesHTML = (rj.phases || [])
    .map(
      (phase) => {
        const featuresHTML = (phase.features || [])
          .map(
            (f) => {
              const prioClass = f.priority === "critical" ? "prio-critical" : f.priority === "high" ? "prio-high" : "prio-medium";
              return `<div class="roadmap-feature ${prioClass}"><span class="feature-effort">${escapeHTML(f.effort)}</span> ${escapeHTML(f.name)}</div>`;
            }
          )
          .join("");

        const milestonesHTML = (phase.milestones || [])
          .map((m) => `<div class="roadmap-milestone">${escapeHTML(m.name)}</div>`)
          .join("");

        return `
          <div class="roadmap-phase">
            <div class="phase-header">
              <div class="phase-number">Phase ${phase.phase_number}</div>
              <h4>${escapeHTML(phase.name)}</h4>
              <span class="phase-duration">${escapeHTML(phase.duration)}</span>
            </div>
            <p class="phase-desc">${escapeHTML(phase.description)}</p>
            <div class="phase-features">${featuresHTML}</div>
            <div class="phase-milestones">${milestonesHTML}</div>
          </div>
        `;
      }
    )
    .join('<div class="phase-connector"></div>');

  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3>Product Roadmap</h3>
        <span class="badge badge-accent">${s.phases} phases | ${s.total_features} features</span>
      </div>
      <p style="color: var(--text-muted); font-size: 0.87rem; margin-bottom: 8px;">${escapeHTML(rj.executive_summary || "")}</p>
      <p style="color: var(--text-muted); font-size: 0.82rem; margin-bottom: 20px;"><strong>Duration:</strong> ${escapeHTML(s.total_duration)} | <strong>Vision:</strong> ${escapeHTML(rj.vision || "")}</p>

      <div class="stats-grid">
        <div class="stat-card"><div class="stat-value">${s.phases}</div><div class="stat-label">Phases</div></div>
        <div class="stat-card"><div class="stat-value">${s.total_features}</div><div class="stat-label">Features</div></div>
        <div class="stat-card"><div class="stat-value">${s.team_roles}</div><div class="stat-label">Team Roles</div></div>
        <div class="stat-card"><div class="stat-value">${s.dependencies}</div><div class="stat-label">Dep. Chains</div></div>
      </div>

      <div class="tabs">
        <button class="tab-btn active" onclick="switchTab(this, 'tab-road-viz')">Timeline</button>
        <button class="tab-btn" onclick="switchTab(this, 'tab-road-md')">Full Report</button>
        <button class="tab-btn" onclick="switchTab(this, 'tab-road-json')">JSON</button>
      </div>

      <div id="tab-road-viz" class="tab-content active">
        <div class="roadmap-timeline">${phasesHTML}</div>
      </div>
      <div id="tab-road-md" class="tab-content">
        <div class="markdown-view">${renderMarkdown(data.roadmap_markdown)}</div>
      </div>
      <div id="tab-road-json" class="tab-content">
        <div style="display:flex;justify-content:flex-end;margin-bottom:8px;">
          <button class="copy-btn" onclick="copyJSON()">Copy JSON</button>
        </div>
        <div class="output-block" id="json-output">${escapeHTML(JSON.stringify(rj, null, 2))}</div>
      </div>
    </div>
  `;

  document.getElementById("results-title").textContent = "Product Roadmap";
  document.getElementById("results-subtitle").textContent =
    `${s.phases} phases over ${s.total_duration}`;
}

// --- Rendering: Pitch Deck ---
function renderPitchDeckResults(data) {
  const container = document.getElementById("results-content");
  const s = data.summary;
  const dj = data.deck_json;

  // Slide cards
  const slidesHTML = (dj.slides || [])
    .map(
      (slide) => `
      <div class="pitch-slide" onclick="showSlideModal(${slide.slide_number})">
        <div class="slide-number">Slide ${slide.slide_number}</div>
        <div class="slide-type">${escapeHTML(slide.slide_type)}</div>
        <h4>${escapeHTML(slide.title)}</h4>
        <p class="slide-headline">${escapeHTML(slide.headline)}</p>
      </div>
    `
    )
    .join("");

  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3>${escapeHTML(s.company_name)} — Pitch Deck</h3>
        <span class="badge badge-accent">${s.slides} slides</span>
      </div>
      <p style="color: var(--text-muted); font-size: 0.87rem; margin-bottom: 8px;"><em>${escapeHTML(s.tagline)}</em></p>
      <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 20px;">${escapeHTML(dj.elevator_pitch || "")}</p>

      <div class="stats-grid">
        <div class="stat-card"><div class="stat-value">${s.slides}</div><div class="stat-label">Slides</div></div>
        <div class="stat-card"><div class="stat-value">${escapeHTML(s.funding_ask)}</div><div class="stat-label">Funding Ask</div></div>
        <div class="stat-card"><div class="stat-value">${(dj.financial_highlights || []).length}</div><div class="stat-label">Financial Metrics</div></div>
      </div>

      <div class="tabs">
        <button class="tab-btn active" onclick="switchTab(this, 'tab-pitch-slides')">Slides</button>
        <button class="tab-btn" onclick="switchTab(this, 'tab-pitch-md')">Full Script</button>
        <button class="tab-btn" onclick="switchTab(this, 'tab-pitch-json')">JSON</button>
      </div>

      <div id="tab-pitch-slides" class="tab-content active">
        <div class="pitch-deck-grid">${slidesHTML}</div>
      </div>
      <div id="tab-pitch-md" class="tab-content">
        <div class="markdown-view">${renderMarkdown(data.deck_markdown)}</div>
      </div>
      <div id="tab-pitch-json" class="tab-content">
        <div style="display:flex;justify-content:flex-end;margin-bottom:8px;">
          <button class="copy-btn" onclick="copyJSON()">Copy JSON</button>
        </div>
        <div class="output-block" id="json-output">${escapeHTML(JSON.stringify(dj, null, 2))}</div>
      </div>
    </div>
  `;

  // Store deck data for modal
  window._currentDeck = dj;

  document.getElementById("results-title").textContent = "Pitch Deck";
  document.getElementById("results-subtitle").textContent =
    `${s.slides}-slide deck for ${s.company_name}`;
}

function showSlideModal(slideNumber) {
  const deck = window._currentDeck;
  if (!deck) return;
  const slide = deck.slides.find((s) => s.slide_number === slideNumber);
  if (!slide) return;

  document.getElementById("modal-title").textContent = `Slide ${slide.slide_number}: ${slide.title}`;
  document.getElementById("modal-body-content").innerHTML = `
    <div class="slide-detail">
      <div class="slide-detail-type">${escapeHTML(slide.slide_type)}</div>
      <h3 class="slide-detail-headline">${escapeHTML(slide.headline)}</h3>
      <div class="slide-detail-section">
        <h4>Key Points</h4>
        <ul>${slide.bullet_points.map((bp) => `<li>${escapeHTML(bp)}</li>`).join("")}</ul>
      </div>
      <div class="slide-detail-section">
        <h4>Visual Suggestion</h4>
        <p>${escapeHTML(slide.visual_suggestion)}</p>
      </div>
      <div class="slide-detail-section">
        <h4>Speaker Notes</h4>
        <p class="speaker-notes">${escapeHTML(slide.speaker_notes)}</p>
      </div>
    </div>
  `;
  document.getElementById("modal").classList.add("active");
}

// --- Tabs ---
function switchTab(btn, tabId) {
  const parent = btn.closest(".card");
  parent.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
  parent.querySelectorAll(".tab-content").forEach((t) => t.classList.remove("active"));
  btn.classList.add("active");
  parent.querySelector(`#${tabId}`).classList.add("active");
}

// --- Modal ---
function showScreenModal(screenName) {
  if (!currentDesigns || !currentDesigns[screenName]) return;

  document.getElementById("modal-title").textContent = screenName;
  document.getElementById("modal-body-content").innerHTML = `
    <div style="display:flex;justify-content:flex-end;margin-bottom:8px;">
      <button class="copy-btn" onclick="copyScreenPrompt('${escapeAttr(screenName)}')">Copy Prompt</button>
    </div>
    <div class="output-block">${escapeHTML(currentDesigns[screenName])}</div>
  `;
  document.getElementById("modal").classList.add("active");
}

function closeModal() {
  document.getElementById("modal").classList.remove("active");
}

// Close modal on overlay click
document.addEventListener("click", (e) => {
  if (e.target.id === "modal") closeModal();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeModal();
});

// --- Clipboard ---
function copyJSON() {
  const json = document.getElementById("json-output")?.textContent;
  if (json) {
    navigator.clipboard.writeText(json);
    toast("JSON copied to clipboard");
  }
}

function copyScreenPrompt(screenName) {
  if (currentDesigns && currentDesigns[screenName]) {
    navigator.clipboard.writeText(currentDesigns[screenName]);
    toast("Prompt copied to clipboard");
  }
}

// --- Markdown renderer (simple) ---
function renderMarkdown(md) {
  if (!md) return "";
  let html = escapeHTML(md);

  // Horizontal rules
  html = html.replace(/^---$/gm, "<hr>");

  // Headers
  html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
  html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
  html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");

  // Bold and italic
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

  // Inline code
  html = html.replace(/`(.+?)`/g, "<code>$1</code>");

  // Blockquotes
  html = html.replace(/^&gt; (.+)$/gm, "<blockquote>$1</blockquote>");

  // Tables
  html = html.replace(
    /^\|(.+)\|$/gm,
    (match) => {
      const cells = match
        .split("|")
        .filter((c) => c.trim())
        .map((c) => c.trim());
      // Check if separator row
      if (cells.every((c) => /^[-:]+$/.test(c))) return "";
      const tag = "td";
      const row = cells.map((c) => `<${tag}>${c}</${tag}>`).join("");
      return `<tr>${row}</tr>`;
    }
  );
  html = html.replace(/(<tr>[\s\S]*?<\/tr>\n?)+/g, (match) => `<table>${match}</table>`);

  // Checkbox lists
  html = html.replace(/^- \[ \] (.+)$/gm, '<li style="list-style:none;">&#9744; $1</li>');
  html = html.replace(/^- \[x\] (.+)$/gm, '<li style="list-style:none;">&#9745; $1</li>');

  // Unordered lists
  html = html.replace(/^  - (.+)$/gm, "<li style='margin-left:20px;'>$1</li>");
  html = html.replace(/^- (.+)$/gm, "<li>$1</li>");
  html = html.replace(/(<li>[\s\S]*?<\/li>\n?)+/g, (match) => `<ul>${match}</ul>`);

  // Paragraphs (double newlines)
  html = html.replace(/\n\n/g, "</p><p>");
  html = `<p>${html}</p>`;

  // Clean up empty paragraphs
  html = html.replace(/<p>\s*<\/p>/g, "");
  html = html.replace(/<p>(<h[123]>)/g, "$1");
  html = html.replace(/(<\/h[123]>)<\/p>/g, "$1");
  html = html.replace(/<p>(<table>)/g, "$1");
  html = html.replace(/(<\/table>)<\/p>/g, "$1");
  html = html.replace(/<p>(<ul>)/g, "$1");
  html = html.replace(/(<\/ul>)<\/p>/g, "$1");
  html = html.replace(/<p>(<hr>)/g, "$1");
  html = html.replace(/(<hr>)<\/p>/g, "$1");
  html = html.replace(/<p>(<blockquote>)/g, "$1");
  html = html.replace(/(<\/blockquote>)<\/p>/g, "$1");

  return html;
}

// --- Helpers ---
function escapeHTML(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function escapeAttr(str) {
  return str.replace(/'/g, "\\'").replace(/"/g, "&quot;");
}
