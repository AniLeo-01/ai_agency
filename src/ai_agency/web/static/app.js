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
  async delete(url) {
    const res = await fetch(url, { method: "DELETE" });
    return res.json();
  },
};

// --- State ---
let currentPRD = null;
let currentDesigns = null;
let samples = [];
let stitchConfigured = false;
let stitchProjects = [];
const _stitchCodeUrls = {};  // screenId -> direct code download URL
const _stitchCodeCache = {}; // screenId -> fetched HTML string

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

  // Load config, samples, existing PRD, and Stitch status
  loadConfig();
  loadSamples();
  loadLatestPRD();
  loadStitchStatus();
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
    const prdData = await API.get("/api/prd/latest");
    if (!prdData.success) return;

    currentPRD = prdData.prd_json;
    document.getElementById("design-status").textContent =
      "PRD available — ready to generate designs";
    document.getElementById("design-status").style.color = "var(--success)";

    // Check for saved designs too
    let designData = null;
    try {
      designData = await API.get("/api/designs/latest");
    } catch {
      // no designs saved
    }

    if (designData && designData.success) {
      currentDesigns = designData.screens;

      // Check for saved Stitch results
      let stitchData = null;
      try {
        stitchData = await API.get("/api/stitch/latest");
      } catch { /* no stitch results */ }

      if (stitchData && stitchData.success && stitchData.generated && Object.keys(stitchData.generated).length > 0) {
        renderStitchResults(stitchData, stitchData.project_id || "");
      } else {
        // Render as full pipeline results
        const merged = {
          ...prdData,
          screens: designData.screens,
          summary: { ...prdData.summary, screens: designData.screen_count },
        };
        renderPipelineResults(merged);
      }
    } else {
      renderPRDResults(prdData);
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

  const stitchBtn = stitchConfigured
    ? `<button class="btn btn-primary btn-sm" onclick="showStitchModal()"><span>&#9635;</span> Send to Stitch</button>`
    : "";

  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3>Design Prompts</h3>
        <div style="display:flex;gap:8px;align-items:center;">
          <span style="color: var(--text-muted); font-size: 0.82rem;">${screens.length} screens</span>
          ${stitchBtn}
        </div>
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
        ${stitchConfigured ? '<div style="display:flex;justify-content:flex-end;margin-bottom:12px;"><button class="btn btn-primary btn-sm" onclick="showStitchModal()"><span>&#9635;</span> Send to Stitch</button></div>' : ''}
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

  // Tables — collect consecutive pipe-rows, then build <table> with thead/tbody
  html = html.replace(/(^\|.+\|$\n?)+/gm, (block) => {
    const rows = block.trim().split("\n");
    let headerHTML = "";
    const bodyRows = [];

    for (let i = 0; i < rows.length; i++) {
      const cells = rows[i].split("|").filter((c) => c.trim() !== "" || false);
      // Clean: split produces empty strings at start/end
      const cleaned = rows[i].split("|").slice(1, -1).map((c) => c.trim());
      // Check if separator row (e.g. |---|---|)
      if (cleaned.every((c) => /^[-:]+$/.test(c))) continue;
      if (i === 0) {
        headerHTML = "<thead><tr>" + cleaned.map((c) => `<th>${c}</th>`).join("") + "</tr></thead>";
      } else {
        bodyRows.push("<tr>" + cleaned.map((c) => `<td>${c}</td>`).join("") + "</tr>");
      }
    }

    return `<table>${headerHTML}<tbody>${bodyRows.join("")}</tbody></table>`;
  });

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

// --- Stitch Integration ---
async function loadStitchStatus() {
  try {
    const data = await API.get("/api/stitch/status");
    stitchConfigured = data.configured;
    stitchProjects = data.projects || [];
    const badge = document.getElementById("stitch-status");
    if (badge) {
      if (data.configured && data.auth_error) {
        badge.innerHTML = '<span class="dot dot-warn"></span> Stitch: <strong>Token expired</strong>';
        badge.title = data.error || "Refresh your access token";
      } else if (data.configured) {
        badge.innerHTML = '<span class="dot dot-green"></span> Stitch: <strong>Connected</strong>';
      } else {
        badge.innerHTML = '<span class="dot dot-dim"></span> Stitch: <strong>Not configured</strong>';
        badge.title = data.error || "";
      }
    }
  } catch {
    stitchConfigured = false;
  }
}

function getStitchProjectName() {
  // Build name from PRD product name: "SoloInvoice" -> "soloinvoice_stitch"
  if (currentPRD && currentPRD.product_overview && currentPRD.product_overview.name) {
    const name = currentPRD.product_overview.name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_|_$/g, "");
    return `${name}_stitch`;
  }
  return "design_stitch";
}

function showStitchModal() {
  if (!currentDesigns || Object.keys(currentDesigns).length === 0) {
    toast("No design prompts available. Generate designs first.", "error");
    return;
  }
  if (!stitchConfigured) {
    toast("Stitch not configured. Set STITCH_ACCESS_TOKEN in .env", "error");
    return;
  }

  const autoName = getStitchProjectName();
  const screenNames = Object.keys(currentDesigns);

  const screenCheckboxes = screenNames
    .map(
      (n) => `
      <label class="stitch-screen-check">
        <input type="checkbox" name="stitch-screen" value="${escapeAttr(n)}" checked />
        <span>${escapeHTML(n)}</span>
      </label>`
    )
    .join("");

  document.getElementById("modal-title").textContent = "Send to Google Stitch";
  document.getElementById("modal-body-content").innerHTML = `
    <p style="margin-bottom:16px;color:var(--text-muted);font-size:0.87rem;">
      A new Stitch project will be created and selected screens will be generated.
    </p>
    <div style="margin-bottom:16px;">
      <label style="display:block;margin-bottom:6px;font-weight:500;">Project Name</label>
      <input id="stitch-project-name" class="stitch-input" value="${escapeAttr(autoName)}" />
    </div>
    <div style="margin-bottom:16px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <label style="font-weight:500;">Screens (${screenNames.length})</label>
        <div style="display:flex;gap:8px;">
          <button class="btn-link" onclick="toggleAllStitchScreens(true)">Select all</button>
          <button class="btn-link" onclick="toggleAllStitchScreens(false)">Deselect all</button>
        </div>
      </div>
      <div class="stitch-screen-list">${screenCheckboxes}</div>
    </div>
    <button class="btn btn-primary" onclick="runStitchGeneration()" style="width:100%;">
      <span>&#9635;</span> Generate Selected Screens in Stitch
    </button>
  `;
  document.getElementById("modal").classList.add("active");
}

function toggleAllStitchScreens(checked) {
  document.querySelectorAll('input[name="stitch-screen"]').forEach((cb) => {
    cb.checked = checked;
  });
}

function getSelectedStitchScreens() {
  const selected = {};
  document.querySelectorAll('input[name="stitch-screen"]:checked').forEach((cb) => {
    const name = cb.value;
    if (currentDesigns[name]) selected[name] = currentDesigns[name];
  });
  return selected;
}

async function runStitchGeneration() {
  const selectedScreens = getSelectedStitchScreens();
  const screenCount = Object.keys(selectedScreens).length;
  if (screenCount === 0) {
    toast("Select at least one screen", "error");
    return;
  }

  const nameInput = document.getElementById("stitch-project-name");
  const projectName = nameInput ? nameInput.value.trim() : getStitchProjectName();

  closeModal();
  showLoader("Creating Stitch project...", `Project: ${projectName}`);

  try {
    // Step 1: Create a new project
    const createRes = await API.post("/api/stitch/project", { name: projectName });
    if (!createRes.success) {
      hideLoader();
      toast(`Failed to create project: ${createRes.error}`, "error");
      return;
    }

    // Extract project ID from response
    const projectId = extractProjectId(createRes.project);
    if (!projectId) {
      hideLoader();
      toast("Project created but could not extract project ID", "error");
      return;
    }

    // Step 2: Generate selected screens
    showLoader("Generating designs in Stitch...", `This may take several minutes (${screenCount} screens)`);

    const data = await API.post("/api/stitch/generate", {
      project_id: projectId,
      screens: selectedScreens,
    });
    hideLoader();

    if (!data.success) {
      toast(`Stitch error: ${data.error}`, "error");
      return;
    }

    toast(`Stitch: ${data.succeeded}/${data.total} screens generated!`);
    renderStitchResults(data, projectId);
    navigate("section-results");
  } catch (err) {
    hideLoader();
    toast(`Stitch request failed: ${err.message}`, "error");
  }
}

function extractProjectId(result) {
  if (!result || typeof result !== "object") return null;
  // Direct projectId field
  if (result.projectId) return result.projectId;
  // name field: "projects/12345..." -> "12345..."
  if (result.name && result.name.startsWith("projects/")) return result.name.split("/").pop();
  // Nested in content (MCP response)
  if (result.content && Array.isArray(result.content)) {
    for (const item of result.content) {
      if (item.type === "text") {
        try {
          const parsed = JSON.parse(item.text);
          if (parsed.name) return parsed.name.split("/").pop();
          if (parsed.projectId) return parsed.projectId;
        } catch { /* not JSON */ }
      }
    }
  }
  return null;
}

function renderStitchResults(data, projectId) {
  const container = document.getElementById("results-content");
  const generated = Object.entries(data.generated || {});
  const errors = Object.entries(data.errors || {});

  // Flatten: each prompt may have multiple screen variants
  let totalScreens = 0;
  const cardsHTML = generated
    .map(([name, result]) => {
      const screens = extractScreenData(result);
      if (screens.length === 0) {
        // Fallback card if we can't parse screens
        return `
          <div class="stitch-result-card">
            <div class="stitch-preview"><div class="stitch-preview-empty">Preview unavailable</div></div>
            <div class="stitch-result-info">
              <h4>${escapeHTML(name)}</h4>
              <p style="color:var(--success);font-size:0.82rem;">Generated successfully</p>
            </div>
          </div>`;
      }
      totalScreens += screens.length;
      return screens.map((s, si) => {
        const label = s.title || name;
        const codeKey = s.id || `screen_${si}`;
        // Store codeUrl in a lookup so viewStitchCode/downloadStitchCode can use it directly
        if (s.codeUrl) _stitchCodeUrls[codeKey] = s.codeUrl;
        const imgHTML = s.imageUrl
          ? `<img src="${escapeAttr(s.imageUrl)}" alt="${escapeAttr(label)}" class="stitch-preview-img" onclick="viewStitchImage(this.src, '${escapeAttr(label)}')" onerror="this.parentNode.innerHTML='<div class=\\'stitch-preview-empty\\'>Preview unavailable</div>'" />`
          : `<div class="stitch-preview-empty">No preview</div>`;
        const actions = s.id
          ? `<button class="btn btn-primary btn-sm" onclick="viewStitchCode('${escapeAttr(projectId)}','${escapeAttr(s.id)}')">View Code</button>
             <button class="btn btn-sm" onclick="downloadStitchCode('${escapeAttr(projectId)}','${escapeAttr(s.id)}','${escapeAttr(label)}')">Download</button>
             <button class="btn btn-sm" onclick="showEditScreenModal('${escapeAttr(projectId)}','${escapeAttr(s.id)}','${escapeAttr(label)}')">Edit</button>
             <button class="btn btn-sm btn-danger" onclick="deleteStitchScreen('${escapeAttr(projectId)}','${escapeAttr(s.id)}','${escapeAttr(label)}')">Delete</button>`
          : "";
        return `
          <div class="stitch-result-card" data-project="${escapeAttr(projectId)}" data-screen="${escapeAttr(s.id || "")}">
            <div class="stitch-preview">${imgHTML}</div>
            <div class="stitch-result-info">
              <h4>${escapeHTML(label)}</h4>
              <p style="color:var(--success);font-size:0.82rem;">Generated successfully</p>
              <div class="stitch-result-actions">${actions}</div>
            </div>
          </div>`;
      }).join("");
    })
    .join("");

  const errorsHTML = errors
    .map(([name, err]) => `
      <div class="stitch-result-card stitch-result-error">
        <div class="stitch-result-info">
          <h4>${escapeHTML(name)}</h4>
          <p style="color:var(--error);font-size:0.82rem;">${escapeHTML(err)}</p>
        </div>
      </div>`)
    .join("");

  const screenCount = totalScreens || data.succeeded;
  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3>Stitch Design Results</h3>
        <span style="color:var(--text-muted);font-size:0.82rem;">${screenCount} screen variants from ${data.succeeded}/${data.total} prompts</span>
      </div>
      <div class="stats-grid">
        <div class="stat-card"><div class="stat-value">${data.total}</div><div class="stat-label">Prompts</div></div>
        <div class="stat-card"><div class="stat-value">${screenCount}</div><div class="stat-label">Screens</div></div>
        <div class="stat-card"><div class="stat-value">${data.failed}</div><div class="stat-label">Failed</div></div>
      </div>
      <div class="stitch-results-grid">${cardsHTML}${errorsHTML}</div>
    </div>
  `;

  document.getElementById("results-title").textContent = "Stitch Results";
  document.getElementById("results-subtitle").textContent =
    `${screenCount} screens generated in Google Stitch`;
}


function viewStitchImage(src, name) {
  // Create a dedicated fullscreen image viewer with zoom/pan
  let existing = document.getElementById("stitch-image-viewer");
  if (existing) existing.remove();

  const viewer = document.createElement("div");
  viewer.id = "stitch-image-viewer";
  viewer.className = "image-viewer-overlay";
  viewer.innerHTML = `
    <div class="image-viewer-header">
      <span class="image-viewer-title">${escapeHTML(name)}</span>
      <div class="image-viewer-controls">
        <button class="image-viewer-btn" id="iv-zoom-out" title="Zoom out">-</button>
        <span class="image-viewer-zoom" id="iv-zoom-label">Fit</span>
        <button class="image-viewer-btn" id="iv-zoom-in" title="Zoom in">+</button>
        <button class="image-viewer-btn" id="iv-zoom-fit" title="Fit to window">Fit</button>
        <button class="image-viewer-btn" id="iv-zoom-full" title="Actual size">1:1</button>
        <button class="image-viewer-btn image-viewer-close" id="iv-close" title="Close">&times;</button>
      </div>
    </div>
    <div class="image-viewer-canvas" id="iv-canvas">
      <img src="${escapeAttr(src)}" alt="${escapeAttr(name)}" id="iv-img" draggable="false" />
    </div>
  `;
  document.body.appendChild(viewer);

  const img = document.getElementById("iv-img");
  const canvas = document.getElementById("iv-canvas");
  let scale = 1;
  let translateX = 0;
  let translateY = 0;
  let isDragging = false;
  let dragStartX = 0;
  let dragStartY = 0;
  let fitScale = 1;

  function applyTransform() {
    img.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
    const label = document.getElementById("iv-zoom-label");
    if (label) label.textContent = `${Math.round(scale * 100)}%`;
  }

  function fitToWindow() {
    const cw = canvas.clientWidth - 40;
    const ch = canvas.clientHeight - 40;
    const iw = img.naturalWidth || 780;
    const ih = img.naturalHeight || 1768;
    fitScale = Math.min(cw / iw, ch / ih, 1);
    scale = fitScale;
    translateX = 0;
    translateY = 0;
    applyTransform();
  }

  img.onload = fitToWindow;
  if (img.complete) fitToWindow();

  // Zoom controls
  document.getElementById("iv-zoom-in").onclick = () => { scale = Math.min(scale * 1.25, 5); applyTransform(); };
  document.getElementById("iv-zoom-out").onclick = () => { scale = Math.max(scale / 1.25, 0.1); applyTransform(); };
  document.getElementById("iv-zoom-fit").onclick = fitToWindow;
  document.getElementById("iv-zoom-full").onclick = () => { scale = 1; translateX = 0; translateY = 0; applyTransform(); };

  // Mouse wheel zoom
  canvas.addEventListener("wheel", (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    const newScale = Math.min(Math.max(scale * delta, 0.1), 5);
    // Zoom towards cursor position
    const rect = canvas.getBoundingClientRect();
    const cx = e.clientX - rect.left - rect.width / 2;
    const cy = e.clientY - rect.top - rect.height / 2;
    translateX = cx - (cx - translateX) * (newScale / scale);
    translateY = cy - (cy - translateY) * (newScale / scale);
    scale = newScale;
    applyTransform();
  }, { passive: false });

  // Pan (drag)
  canvas.addEventListener("mousedown", (e) => {
    if (e.button !== 0) return;
    isDragging = true;
    dragStartX = e.clientX - translateX;
    dragStartY = e.clientY - translateY;
    canvas.style.cursor = "grabbing";
  });
  const onMouseMove = (e) => {
    if (!isDragging) return;
    translateX = e.clientX - dragStartX;
    translateY = e.clientY - dragStartY;
    applyTransform();
  };
  const onMouseUp = () => {
    isDragging = false;
    if (canvas) canvas.style.cursor = "grab";
  };
  const onKeyDown = (e) => {
    if (e.key === "Escape") closeViewer();
  };
  window.addEventListener("mousemove", onMouseMove);
  window.addEventListener("mouseup", onMouseUp);
  document.addEventListener("keydown", onKeyDown);

  // Close
  function closeViewer() {
    viewer.remove();
    window.removeEventListener("mousemove", onMouseMove);
    window.removeEventListener("mouseup", onMouseUp);
    document.removeEventListener("keydown", onKeyDown);
  }
  document.getElementById("iv-close").onclick = closeViewer;
  canvas.addEventListener("dblclick", fitToWindow);
}

function showEditScreenModal(projectId, screenId, screenName) {
  document.getElementById("modal-title").textContent = `Edit: ${screenName}`;
  document.getElementById("modal-body-content").innerHTML = `
    <p style="margin-bottom:12px;color:var(--text-muted);font-size:0.87rem;">
      Describe the changes you want to make to this screen.
    </p>
    <textarea id="stitch-edit-prompt" class="stitch-edit-textarea" placeholder="e.g. Make the header larger, change the color scheme to blue, add a search bar..."></textarea>
    <button class="btn btn-primary" onclick="editStitchScreen('${escapeAttr(projectId)}','${escapeAttr(screenId)}','${escapeAttr(screenName)}')" style="width:100%;margin-top:12px;">
      Apply Changes
    </button>
  `;
  document.getElementById("modal").classList.add("active");
}

async function editStitchScreen(projectId, screenId, screenName) {
  const prompt = document.getElementById("stitch-edit-prompt").value.trim();
  if (!prompt) { toast("Enter edit instructions", "error"); return; }

  closeModal();

  // Find the card for this screen and show inline editing overlay
  const card = document.querySelector(`.stitch-result-card[data-screen="${CSS.escape(screenId)}"]`);
  if (card) {
    card.classList.add("stitch-editing");
    const preview = card.querySelector(".stitch-preview");
    if (preview) {
      preview.dataset.prevHtml = preview.innerHTML;
      preview.innerHTML = `
        <div class="stitch-editing-overlay">
          <div class="stitch-editing-spinner"></div>
          <div class="stitch-editing-label">Editing...</div>
        </div>`;
    }
  }

  toast(`Editing "${screenName}" in background...`);

  try {
    const data = await API.post("/api/stitch/edit", {
      project_id: projectId,
      screen_ids: [screenId],
      prompt: prompt,
    });

    if (!data.success) {
      toast(`Edit failed: ${data.error}`, "error");
      // Restore the card
      if (card) {
        card.classList.remove("stitch-editing");
        const preview = card.querySelector(".stitch-preview");
        if (preview && preview.dataset.prevHtml) preview.innerHTML = preview.dataset.prevHtml;
      }
      return;
    }

    toast(`Screen "${screenName}" updated!`);
    // Clear cached code for this screen
    delete _stitchCodeCache[screenId];

    // Reload the full results to get the updated screen
    const latest = await API.get("/api/stitch/latest");
    if (latest && latest.success) {
      renderStitchResults(latest, latest.project_id || projectId);
    }
  } catch (err) {
    toast(`Edit failed: ${err.message}`, "error");
    if (card) {
      card.classList.remove("stitch-editing");
      const preview = card.querySelector(".stitch-preview");
      if (preview && preview.dataset.prevHtml) preview.innerHTML = preview.dataset.prevHtml;
    }
  }
}

async function _fetchStitchCode(projectId, screenId) {
  // Return cached HTML if available
  if (_stitchCodeCache[screenId]) return _stitchCodeCache[screenId];

  // Backend proxy handles URL lookup from saved results + Stitch API fallback
  const data = await API.get(`/api/stitch/screen/${projectId}/${screenId}/code`);
  if (data.success && data.html) {
    _stitchCodeCache[screenId] = data.html;
    return data.html;
  }
  throw new Error(data.error || "Failed to fetch code");
}

async function downloadStitchCode(projectId, screenId, screenName) {
  toast("Downloading code...");
  try {
    const html = await _fetchStitchCode(projectId, screenId);

    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${screenName.toLowerCase().replace(/[^a-z0-9]+/g, "_")}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast("Download started!");
  } catch (err) {
    toast(`Download failed: ${err.message}`, "error");
  }
}

async function deleteStitchScreen(projectId, screenId, screenName) {
  // Confirm before deleting
  document.getElementById("modal-title").textContent = `Delete: ${screenName}`;
  document.getElementById("modal-body-content").innerHTML = `
    <p style="margin-bottom:16px;color:var(--text-muted);font-size:0.9rem;">
      Are you sure you want to delete <strong>${escapeHTML(screenName)}</strong>? This cannot be undone.
    </p>
    <div style="display:flex;gap:8px;">
      <button class="btn btn-danger" id="confirm-delete-btn" style="flex:1;">Delete</button>
      <button class="btn" onclick="closeModal()" style="flex:1;">Cancel</button>
    </div>
  `;
  document.getElementById("modal").classList.add("active");

  document.getElementById("confirm-delete-btn").onclick = async () => {
    closeModal();

    // Show deleting state on the card
    const card = document.querySelector(`.stitch-result-card[data-screen="${CSS.escape(screenId)}"]`);
    if (card) {
      card.classList.add("stitch-editing");
      const preview = card.querySelector(".stitch-preview");
      if (preview) {
        preview.innerHTML = `
          <div class="stitch-editing-overlay">
            <div class="stitch-editing-spinner"></div>
            <div class="stitch-editing-label">Deleting...</div>
          </div>`;
      }
    }

    try {
      const data = await API.delete(`/api/stitch/screen/${projectId}/${screenId}`);
      if (!data.success) {
        toast(`Delete failed: ${data.error}`, "error");
        // Reload to restore state
        const latest = await API.get("/api/stitch/latest");
        if (latest && latest.success) renderStitchResults(latest, latest.project_id || projectId);
        return;
      }

      // Remove card with animation
      if (card) {
        card.style.transition = "opacity 0.3s, transform 0.3s";
        card.style.opacity = "0";
        card.style.transform = "scale(0.95)";
        setTimeout(() => {
          card.remove();
          // Update counts in header
          const latest2 = API.get("/api/stitch/latest").then((d) => {
            if (d && d.success) renderStitchResults(d, d.project_id || projectId);
          });
        }, 300);
      }

      toast(`"${screenName}" deleted`);
      delete _stitchCodeCache[screenId];
      delete _stitchCodeUrls[screenId];
    } catch (err) {
      toast(`Delete failed: ${err.message}`, "error");
      const latest = await API.get("/api/stitch/latest");
      if (latest && latest.success) renderStitchResults(latest, latest.project_id || projectId);
    }
  };
}

/**
 * Extract all screen data from a Stitch generation result.
 * Returns an array of {id, title, imageUrl, codeUrl} objects.
 */
function extractScreenData(result) {
  if (!result || typeof result !== "object") return [];

  // Prefer structuredContent (already parsed)
  const sc = result.structuredContent;
  if (sc && sc.outputComponents) {
    return _extractFromComponents(sc.outputComponents);
  }

  // Fallback: parse from content[].text JSON string
  if (result.content && Array.isArray(result.content)) {
    for (const item of result.content) {
      if (item.type === "text") {
        try {
          const parsed = JSON.parse(item.text);
          if (parsed.outputComponents) {
            return _extractFromComponents(parsed.outputComponents);
          }
        } catch { /* not JSON */ }
      }
    }
  }
  return [];
}

function _extractFromComponents(outputComponents) {
  const screens = [];
  for (const comp of outputComponents) {
    if (comp.design && comp.design.screens) {
      for (const s of comp.design.screens) {
        screens.push({
          id: s.id || (s.name ? s.name.split("/").pop() : null),
          title: s.title || "",
          imageUrl: s.screenshot && s.screenshot.downloadUrl ? s.screenshot.downloadUrl : null,
          codeUrl: s.htmlCode && s.htmlCode.downloadUrl ? s.htmlCode.downloadUrl : null,
        });
      }
    }
  }
  return screens;
}

async function viewStitchCode(projectId, screenId) {
  showLoader("Fetching screen code...");
  try {
    const html = await _fetchStitchCode(projectId, screenId);
    hideLoader();

    document.getElementById("modal-title").textContent = "Screen HTML";
    document.getElementById("modal-body-content").innerHTML = `
      <div style="display:flex;justify-content:flex-end;margin-bottom:8px;">
        <button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('stitch-code').textContent);toast('Code copied!')">Copy HTML</button>
      </div>
      <div class="output-block" id="stitch-code">${escapeHTML(html)}</div>
    `;
    document.getElementById("modal").classList.add("active");
  } catch (err) {
    hideLoader();
    toast(`Failed: ${err.message}`, "error");
  }
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
