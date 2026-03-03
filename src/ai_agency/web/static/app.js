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

// --- Rendering ---
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

  // Update results page header
  document.getElementById("results-title").textContent = "PRD Results";
  document.getElementById("results-subtitle").textContent =
    `Generated PRD for "${data.summary.product_name}"`;
}

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

  // Headers
  html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
  html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
  html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");

  // Bold and italic
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

  // Inline code
  html = html.replace(/`(.+?)`/g, "<code>$1</code>");

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
