const routes = [
  { path: "/", title: "Dashboard", kicker: "Operations", icon: "D" },
  { path: "/jobs-page", title: "Jobs", kicker: "Execution Console", icon: "J" },
  { path: "/new-batch", title: "New Batch", kicker: "Submission", icon: "N" },
  { path: "/websites-page", title: "Websites", kicker: "Publishing", icon: "W" },
  { path: "/website-builder", title: "Website Builder", kicker: "One Click Site", icon: "B" },
  { path: "/api-keys-page", title: "API Keys", kicker: "Integrations", icon: "K" },
  { path: "/prompts-page", title: "Prompts", kicker: "Configuration", icon: "P" },
  { path: "/settings-page", title: "Settings", kicker: "System", icon: "S" },
  { path: "/console", title: "Jobs", kicker: "Execution Console", icon: "J", alias: "/jobs-page" },
];

const stages = [
  ["init", "Init"],
  ["research", "Research"],
  ["content_generation", "Content"],
  ["image_generation", "Images"],
  ["image_composition", "Pin"],
  ["wordpress_publish", "WordPress"],
  ["pinterest_metadata", "Pinterest"],
  ["complete", "Done"],
];

const APP_TIME_ZONE = "Africa/Casablanca";
const APP_TIME_ZONE_LABEL = "Casablanca";
const pinFontOptions = [
  "Lilita One",
  "Noto Serif Ethiopic Condensed",
  "Canva Sans",
  "Chewy",
  "Arimo",
  "Impact",
  "Arial Black",
  "Arial Rounded",
  "Cooper",
  "Futura",
  "Georgia Bold",
  "Comic Sans Bold",
];

const appState = {
  jobs: [],
  stats: null,
  logs: [],
  websites: [],
  pinTemplates: [],
  editingWebsiteId: null,
  websiteEditorOpen: false,
  pinStyleRequestId: 0,
  health: null,
  currentJob: null,
  openArticlePreviews: new Set(),
  batchWebsiteReady: false,
  timer: null,
  refreshingJobs: false,
  selectedJobIds: new Set(),
};

const app = document.getElementById("app");
const toastEl = document.getElementById("toast");

function routePath() {
  const found = routes.find(r => r.path === location.pathname);
  return found?.alias || found?.path || "/";
}

function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function normalizeSiteName(name) {
  if (!name) return name;
  return String(name)
    .trim()
    .toLowerCase()
    .split(/\s+/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function pinFontSelectOptions(current = "") {
  return pinFontOptions.map(font => `<option value="${esc(font)}"${font === current ? " selected" : ""}>${esc(font)}</option>`).join("");
}

function fmtDate(value) {
  if (!value) return "-";
  const d = parseDate(value);
  if (Number.isNaN(d.getTime())) return String(value).slice(0, 19).replace("T", " ");
  return d.toLocaleString([], {
    timeZone: APP_TIME_ZONE,
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function casablancaDateTimeLocalValue(date = new Date()) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: APP_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(date).reduce((acc, part) => {
    if (part.type !== "literal") acc[part.type] = part.value;
    return acc;
  }, {});
  const hour = parts.hour === "24" ? "00" : parts.hour;
  return `${parts.year}-${parts.month}-${parts.day}T${hour}:${parts.minute}`;
}

function casablancaDateValue(date = new Date()) {
  return casablancaDateTimeLocalValue(date).slice(0, 10);
}

function casablancaTimeValue(date = new Date()) {
  return casablancaDateTimeLocalValue(date).slice(11, 16);
}

function fmtDuration(seconds) {
  seconds = Number(seconds || 0);
  if (!seconds) return "-";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const min = Math.floor(seconds / 60);
  const sec = Math.round(seconds % 60);
  return `${min}m ${sec}s`;
}

function websiteLabel(id) {
  const site = appState.websites.find(w => String(w.id) === String(id));
  return site ? site.name : (id || "-");
}

function jobTimestamp(job) {
  const value = job.updated_at || job.created_at;
  if (!value) return null;
  const parsed = parseDate(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function dateInputValue(date) {
  if (!date) return "";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function timeInputValue(date) {
  if (!date) return "";
  return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await res.text();
  const data = text ? JSON.parse(text) : {};
  if (!res.ok) throw new Error(data.detail || data.message || res.statusText);
  return data;
}

const WEBSITE_BACKUP_KEY = "automationDashboardWebsites";

function normaliseWebsiteUrl(value) {
  return String(value || "").trim().replace(/\/+$/, "");
}

function storedWebsites() {
  try {
    const parsed = JSON.parse(localStorage.getItem(WEBSITE_BACKUP_KEY) || "[]");
    return Array.isArray(parsed) ? parsed.filter(site => site && site.base_url && (site.username || site.site_type === "html_static") && site.password) : [];
  } catch (_) {
    return [];
  }
}

function rememberWebsite(site) {
  if (!site?.base_url || (!site?.username && site?.site_type !== "html_static")) return;
  const backup = {
    name: String(site.name || "").trim(),
    base_url: normaliseWebsiteUrl(site.base_url),
    site_type: String(site.site_type || site.siteType || "wordpress"),
    username: String(site.username || "").trim(),
    password: String(site.password || ""),
    publish_endpoint: String(site.publish_endpoint || site.publishEndpoint || ""),
    pin_template: String(site.pin_template || ""),
    publish_status: String(site.publish_status || "draft"),
  };
  const sites = storedWebsites();
  const index = sites.findIndex(item => normaliseWebsiteUrl(item.base_url) === backup.base_url);
  if (index >= 0) sites[index] = { ...sites[index], ...backup };
  else sites.push(backup);
  try {
    localStorage.setItem(WEBSITE_BACKUP_KEY, JSON.stringify(sites));
  } catch (_) {}
}

function forgetWebsite(site) {
  if (!site?.base_url) return;
  const baseUrl = normaliseWebsiteUrl(site.base_url);
  const sites = storedWebsites().filter(item => normaliseWebsiteUrl(item.base_url) !== baseUrl);
  try {
    localStorage.setItem(WEBSITE_BACKUP_KEY, JSON.stringify(sites));
  } catch (_) {}
}

function storedWebsiteFor(site) {
  const baseUrl = normaliseWebsiteUrl(site?.base_url);
  return storedWebsites().find(item => normaliseWebsiteUrl(item.base_url) === baseUrl) || null;
}

async function loadWebsitesWithRestore() {
  const response = await api("/websites").catch(() => ({ websites: [] }));
  const websites = response.websites || [];
  websites.forEach(site => {
    const stored = storedWebsiteFor(site);
    if (stored?.password) {
      rememberWebsite({
        ...site,
        password: stored.password,
        pin_template: site.pin_template || stored.pin_template,
        publish_status: site.publish_status || stored.publish_status,
      });
    }
  });
  return websites;
}

function toast(message) {
  toastEl.textContent = message;
  toastEl.classList.add("show");
  setTimeout(() => toastEl.classList.remove("show"), 3200);
}

function pageMeta(path = routePath()) {
  return routes.find(r => (r.alias || r.path) === path) || routes[0];
}

function navigate(path) {
  history.pushState({}, "", path);
  render();
}

function renderNav() {
  const current = routePath();
  document.getElementById("nav").innerHTML = routes
    .filter(r => !r.alias)
    .map(r => `
      <a href="${r.path}" class="nav-link ${r.path === current ? "active" : ""}" data-route="${r.path}">
        <span class="nav-icon">${r.icon}</span><span>${r.title}</span>
      </a>
    `).join("");
}

function setTitle() {
  const meta = pageMeta();
  document.getElementById("page-title").textContent = meta.title;
  document.getElementById("page-kicker").textContent = meta.kicker;
}

function statusBadge(status) {
  const value = status || "unknown";
  return `<span class="badge ${esc(value)}">${esc(value)}</span>`;
}

function progressBar(value) {
  return `<div class="progress"><span style="width:${Math.max(0, Math.min(100, Number(value || 0)))}%"></span></div>`;
}

function parseDate(value) {
  if (!value) return null;
  let normalized = String(value).includes("T") ? String(value) : String(value).replace(" ", "T");
  if (!/[zZ]|[+-]\d{2}:?\d{2}$/.test(normalized)) {
    normalized = `${normalized}+01:00`;
  }
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function elapsedSince(value, endValue = null) {
  const start = parseDate(value);
  if (!start) return "-";
  const end = endValue ? parseDate(endValue) || new Date() : new Date();
  const seconds = Math.max(0, Math.floor((end - start) / 1000));
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest ? `${hours}h ${rest}m` : `${hours}h`;
}

function metric(label, value, hint = "", accent = "") {
  return `
    <div class="metric">
      <label>${esc(label)}</label>
      <div class="metric-row">
        <div>
          <strong>${esc(value)}</strong>
          <small>${esc(hint)}</small>
        </div>
        <span class="metric-accent">${esc(accent || label.slice(0, 1))}</span>
      </div>
    </div>
  `;
}

function jobRows(jobs, compact = false) {
  if (!jobs.length) return `<tr><td colspan="${compact ? 7 : 8}"><div class="empty">No jobs found.</div></td></tr>`;
  return jobs.map(j => `
    <tr class="row-click ${appState.currentJob?.id === j.id ? "selected" : ""}" data-job="${j.id}">
      ${compact ? "" : `<td><input class="job-select" type="checkbox" value="${j.id}" data-job-checkbox ${appState.selectedJobIds.has(String(j.id)) ? "checked" : ""}></td>`}
      <td class="nowrap"><strong>#${j.id}</strong></td>
      <td>${esc(j.keyword)}</td>
      <td>${statusBadge(j.status)}</td>
      ${compact ? `<td>${esc(j.stage || "-")}</td>` : ""}
      ${compact ? "" : `<td>${progressBar(j.progress ?? stageProgress(j.stage, j.status))}</td>`}
      <td>${esc(websiteLabel(j.website_id))}</td>
      <td class="nowrap">${elapsedSince(j.created_at, ["completed", "failed", "canceled", "cancelled"].includes(j.status) ? j.updated_at : null)}</td>
      <td class="nowrap">${jobUploadTime(j)}</td>
    </tr>
  `).join("");
}

function jobUploadTime(job) {
  if (job.finished_at) return fmtDate(job.finished_at);
  if (job.status === "completed" && job.updated_at) return fmtDate(job.updated_at);
  return "-";
}

function stageProgress(stage, status) {
  if (status === "completed") return 100;
  if (status === "failed" || status === "canceled" || status === "cancelled") return 0;
  const map = { init: 5, research: 15, content_generation: 30, image_generation: 55, image_composition: 68, wordpress_publish: 82, pinterest_metadata: 93, pinterest_schedule: 96, complete: 100 };
  return map[stage] || 0;
}

async function loadCore() {
  const [stats, jobs, health, websites] = await Promise.all([
    api("/stats").catch(() => null),
    api("/jobs?limit=100").catch(() => ({ jobs: [] })),
    api("/status").catch(() => null),
    loadWebsitesWithRestore().catch(() => []),
  ]);
  appState.stats = stats;
  appState.jobs = jobs.jobs || [];
  appState.health = health;
  appState.websites = websites || [];
}

async function renderDashboard() {
  await loadCore();
  const h = appState.health || {};
  const allStats = summarizeJobs(appState.jobs);
  const activeJobs = appState.jobs.filter(j => ["pending", "processing", "retrying"].includes(j.status));
  const failedJobs = appState.jobs.filter(j => j.status === "failed");
  const lastCompleted = appState.jobs.find(j => j.status === "completed");
  app.innerHTML = `
    <section class="ops-hero">
      <div class="ops-hero-main">
        <div class="hero-copy">
          <span class="hero-label">Automation health</span>
          <h2>Content Operations Center</h2>
          <p>Monitor article generation, publishing, pin creation, and recovery work from one focused console.</p>
          <div class="hero-actions">
            <button class="btn primary" data-route="/new-batch">Queue Keywords</button>
            <button class="btn ghost" data-route="/jobs-page">Review Jobs</button>
          </div>
        </div>
        <div class="status-strip executive">
          ${statusTile("Worker", h.celery_status)}
          ${statusTile("Broker", h.redis_status)}
          ${statusTile("Database", h.db_status)}
        </div>
      </div>
      <div class="ops-hero-footer">
        <span>Loaded jobs: <strong>${esc(appState.jobs.length)}</strong></span>
        <span>Active now: <strong>${esc(activeJobs.length)}</strong></span>
        <span>Last completed: <strong>${lastCompleted ? `#${lastCompleted.id}` : "-"}</strong></span>
        <span>Casablanca time: <strong id="dashboard-clock">${esc(casablancaClock())}</strong></span>
      </div>
    </section>
    ${dashboardFiltersHtml()}
    <div class="grid dashboard-kpis" id="dashboard-metrics">
      ${metric("Total Jobs", allStats.total, "loaded in console", "T")}
      ${metric("Success Rate", `${allStats.success_rate}%`, `${allStats.completed} completed`, "OK")}
      ${metric("Active", activeJobs.length, `${h.queued_jobs ?? 0} queued overall`, "IN")}
      ${metric("Failed", failedJobs.length, `${allStats.canceled} canceled`, "!")}
    </div>
    <div class="dashboard-filter-line">
      <span id="dashboard-filter-count">${appState.jobs.length} of ${appState.jobs.length} loaded jobs shown</span>
      <span>Auto-refresh keeps this view current while workers run.</span>
    </div>
    <div class="grid dashboard-main">
      <div class="section-stack">
        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>Activity Volume</h2>
              <p class="panel-subtitle">Last 30 days, day by day</p>
            </div>
            <span class="mini muted">daily job volume</span>
          </div>
          <div class="panel-body" id="dashboard-activity-volume"></div>
        </section>
        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>Activity</h2>
              <p class="panel-subtitle">Filtered volume by day</p>
            </div>
            <span class="mini muted">filtered jobs</span>
          </div>
          <div class="panel-body" id="dashboard-activity"></div>
        </section>
      </div>
      <div class="section-stack">
        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>Failure Queue</h2>
              <p class="panel-subtitle">Jobs that need attention</p>
            </div>
            <span class="badge failed">${failedJobs.length}</span>
          </div>
          <div class="panel-body" id="dashboard-failures"></div>
        </section>
        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>Website Mix</h2>
              <p class="panel-subtitle">Publishing destinations</p>
            </div>
          </div>
          <div class="panel-body" id="dashboard-websites"></div>
        </section>
        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>Operations Brief</h2>
              <p class="panel-subtitle">Filtered snapshot</p>
            </div>
          </div>
          <div class="panel-body" id="dashboard-brief"></div>
        </section>
      </div>
    </div>
  `;
  attachDashboardFilters();
  updateDashboardFilters();
}

function dashboardFiltersHtml() {
  return `
    <div class="filters">
      <div class="filter-field">
        <label>Keyword</label>
        <input id="dash-search" placeholder="Search keyword...">
      </div>
      <div class="filter-field">
        <label>Status</label>
        <select id="dash-status">
          <option value="">All statuses</option>
          <option>pending</option><option>processing</option><option>completed</option><option>failed</option><option>retrying</option><option>canceled</option>
        </select>
      </div>
      <div class="filter-field">
        <label>Website</label>
        <select id="dash-website">
          <option value="">All websites</option>
          <option value="__none">No website</option>
          ${appState.websites.map(w => `<option value="${w.id}">${esc(w.name)}</option>`).join("")}
        </select>
      </div>
      ${dateRangeFilterHtml("dash")}
      <div class="filter-actions">
        <button class="btn" id="clear-dashboard-filters">Clear</button>
      </div>
    </div>
  `;
}

function attachDashboardFilters() {
  ["dash-search", "dash-status", "dash-website", "dash-date-range", "dash-custom-from", "dash-custom-to"].forEach(id => {
    document.getElementById(id).addEventListener("input", updateDashboardFilters);
    document.getElementById(id).addEventListener("change", updateDashboardFilters);
  });
  document.getElementById("dash-date-range").addEventListener("change", () => updateCustomDateFields("dash"));
  updateCustomDateFields("dash");
  document.getElementById("clear-dashboard-filters").addEventListener("click", clearDashboardFilters);
}

function updateDashboardFilters() {
  const jobs = filteredJobs("dash");
  const stats = summarizeJobs(jobs);
  const h = appState.health || {};
  document.getElementById("dashboard-metrics").innerHTML = `
    ${metric("Filtered Jobs", stats.total, "matching current filters", "T")}
    ${metric("Success Rate", `${stats.success_rate}%`, `${stats.completed} completed`, "OK")}
    ${metric("Active", stats.processing, `${h.queued_jobs ?? 0} queued overall`, "IN")}
    ${metric("Failed", stats.failed, `${stats.canceled} canceled`, "!")}
  `;
  document.getElementById("dashboard-filter-count").textContent = `${jobs.length} of ${appState.jobs.length} loaded jobs shown`;
  document.getElementById("dashboard-activity-volume").innerHTML = activityVolume30Days(jobs);
  document.getElementById("dashboard-activity").innerHTML = activityChart(activityFromJobs(jobs));
  document.getElementById("dashboard-failures").innerHTML = failureQueue(jobs);
  document.getElementById("dashboard-websites").innerHTML = websiteMix(jobs);
  document.getElementById("dashboard-brief").innerHTML = opsBrief(stats, h);
}

function clearDashboardFilters() {
  ["dash-search", "dash-status", "dash-website", "dash-date-range", "dash-custom-from", "dash-custom-to"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });
  updateCustomDateFields("dash");
  updateDashboardFilters();
}

function statusTile(label, value = "unknown") {
  return `
    <div class="status-tile">
      <span>${esc(label)}</span>
      <strong><i class="dot ${value === "online" ? "ok" : value === "offline" ? "bad" : ""}"></i>${esc(value || "unknown")}</strong>
    </div>
  `;
}

function actionCard(route, title, body) {
  return `<button class="action-card" data-route="${esc(route)}"><strong>${esc(title)}</strong><span>${esc(body)}</span></button>`;
}

function dateRangeFilterHtml(prefix) {
  return `
    <div class="filter-field">
      <label>Date range</label>
      <select id="${prefix}-date-range">
        <option value="">All dates</option>
        <option value="today">Today</option>
        <option value="yesterday">Yesterday</option>
        <option value="last7">Last 7 days</option>
        <option value="last30">Last 30 days</option>
        <option value="last90">Last 90 days</option>
        <option value="custom">Custom</option>
      </select>
    </div>
    <div class="filter-field custom-date-field" id="${prefix}-custom-from-wrap">
      <label>Custom from</label>
      <input id="${prefix}-custom-from" type="date">
    </div>
    <div class="filter-field custom-date-field" id="${prefix}-custom-to-wrap">
      <label>Custom to</label>
      <input id="${prefix}-custom-to" type="date">
    </div>
  `;
}

function updateCustomDateFields(prefix) {
  const visible = document.getElementById(`${prefix}-date-range`)?.value === "custom";
  [`${prefix}-custom-from-wrap`, `${prefix}-custom-to-wrap`].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.hidden = !visible;
  });
}

function casablancaClock() {
  return new Date().toLocaleTimeString([], {
    timeZone: APP_TIME_ZONE,
    hour: "2-digit",
    minute: "2-digit",
  });
}

function opsBrief(stats, health) {
  const failed = Number(stats.failed || 0);
  const canceled = Number(stats.canceled || 0);
  const processing = Number(stats.processing || 0);
  const queued = Number(health.queued_jobs || 0);
  const success = Number(stats.success_rate || 0);
  const items = [
    { tone: failed ? "danger" : "ok", label: failed ? `${failed} failed jobs need attention` : "No failed jobs in the current view", value: failed ? "Review" : "Clean" },
    { tone: canceled ? "warn" : "ok", label: canceled ? `${canceled} jobs were canceled` : "No canceled jobs in the current view", value: canceled ? "Canceled" : "Clear" },
    { tone: processing || queued ? "warn" : "ok", label: `${processing} running and ${queued} queued`, value: processing || queued ? "Active" : "Idle" },
    { tone: success >= 80 ? "ok" : success ? "warn" : "", label: `${success}% success rate across completed work`, value: success >= 80 ? "Strong" : "Watch" },
  ];
  return `<div class="insight-list">${items.map(item => `
    <div class="insight ${item.tone}">
      <span class="insight-dot"></span>
      <span>${esc(item.label)}</span>
      <strong>${esc(item.value)}</strong>
    </div>
  `).join("")}</div>`;
}

function summarizeJobs(jobs) {
  const total = jobs.length;
  const completed = jobs.filter(j => j.status === "completed").length;
  const failed = jobs.filter(j => j.status === "failed").length;
  const canceled = jobs.filter(j => j.status === "canceled" || j.status === "cancelled").length;
  const processing = jobs.filter(j => ["pending", "processing", "retrying"].includes(j.status)).length;
  return {
    total,
    completed,
    failed,
    canceled,
    processing,
    success_rate: total ? Math.round((completed / total) * 1000) / 10 : 0,
  };
}

function activityFromJobs(jobs) {
  const byDay = new Map();
  jobs.forEach(job => {
    const date = jobTimestamp(job);
    if (!date) return;
    const day = dateInputValue(date);
    const row = byDay.get(day) || { day, total: 0, completed: 0, failed: 0, canceled: 0 };
    row.total += 1;
    if (job.status === "completed") row.completed += 1;
    if (job.status === "failed") row.failed += 1;
    if (job.status === "canceled" || job.status === "cancelled") row.canceled += 1;
    byDay.set(day, row);
  });
  return [...byDay.values()].sort((a, b) => a.day.localeCompare(b.day));
}

function activityVolume30Days(jobs) {
  const days = [];
  const today = startOfDay(new Date());
  for (let offset = 29; offset >= 0; offset -= 1) {
    const date = addDays(today, -offset);
    days.push({
      day: dateInputValue(date),
      label: date.toLocaleDateString([], { timeZone: APP_TIME_ZONE, weekday: "short" }),
      dateLabel: date.toLocaleDateString([], { timeZone: APP_TIME_ZONE, month: "short", day: "numeric" }),
      axisLabel: date.toLocaleDateString("en-US", { timeZone: APP_TIME_ZONE, month: "2-digit", day: "2-digit" }),
      total: 0,
      completed: 0,
      failed: 0,
      active: 0,
    });
  }
  const byDay = new Map(days.map(day => [day.day, day]));
  jobs.forEach(job => {
    const date = jobTimestamp(job);
    if (!date) return;
    const key = dateInputValue(date);
    const row = byDay.get(key);
    if (!row) return;
    row.total += 1;
    if (job.status === "completed") row.completed += 1;
    if (job.status === "failed") row.failed += 1;
    if (["pending", "processing", "retrying"].includes(job.status)) row.active += 1;
  });
  const max = Math.max(1, ...days.map(day => day.completed));
  const axis = activityAxis(max);
  const xLabelStep = Math.max(1, Math.ceil(days.length / 10));
  const total = days.reduce((sum, day) => sum + day.completed, 0);
  return `
    <div class="activity-volume-summary">
      <strong>${total}</strong>
      <span>completed articles across the last 30 days</span>
    </div>
    <div class="activity-volume-chart">
      <div class="activity-y-axis">
        ${axis.ticks.map(tick => `<span>${tick}</span>`).join("")}
      </div>
      <div class="activity-volume-bars">
        ${days.map((day, index) => `
          <div class="activity-bar-day" title="${esc(day.dateLabel)} · ${day.completed} completed articles">
            <div class="activity-bar-track">
              <span style="height:${Math.max(5, (day.completed / axis.max) * 100)}%"></span>
            </div>
            <div class="activity-axis">
              <small class="${index % xLabelStep && index !== days.length - 1 ? "muted-axis-label" : ""}">${esc(day.axisLabel)}</small>
            </div>
          </div>
        `).join("")}
      </div>
    </div>
  `;
}

function activityAxis(maxValue) {
  const rawStep = Math.max(1, maxValue / 5);
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const normalized = rawStep / magnitude;
  const step = (normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10) * magnitude;
  const axisMax = Math.max(step, Math.ceil(maxValue / step) * step);
  const ticks = [];
  for (let value = axisMax; value >= 0; value -= step) {
    ticks.push(value);
  }
  return { max: axisMax, ticks };
}

function filteredJobs(prefix) {
  const q = document.getElementById(`${prefix}-search`)?.value.toLowerCase() || "";
  const status = document.getElementById(`${prefix}-status`)?.value || "";
  const website = document.getElementById(`${prefix}-website`)?.value || "";
  const { fromDate, toDate } = dateRangeBounds(prefix);

  return appState.jobs.filter(j => {
    const updated = jobTimestamp(j);
    const matchesWebsite =
      !website ||
      (website === "__none" ? !j.website_id : String(j.website_id || "") === website);

    return (
      (!q || (j.keyword || "").toLowerCase().includes(q)) &&
      (!status || j.status === status) &&
      matchesWebsite &&
      (!fromDate || (updated && updated >= fromDate)) &&
      (!toDate || (updated && updated <= toDate))
    );
  });
}

function startOfDay(date) {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  return d;
}

function endOfDay(date) {
  const d = new Date(date);
  d.setHours(23, 59, 59, 999);
  return d;
}

function addDays(date, days) {
  const d = new Date(date);
  d.setDate(d.getDate() + days);
  return d;
}

function dateRangeBounds(prefix) {
  const value = document.getElementById(`${prefix}-date-range`)?.value || "";
  const today = new Date();
  if (value === "today") {
    return { fromDate: startOfDay(today), toDate: endOfDay(today) };
  }
  if (value === "yesterday") {
    const yesterday = addDays(today, -1);
    return { fromDate: startOfDay(yesterday), toDate: endOfDay(yesterday) };
  }
  if (value === "last7") {
    return { fromDate: startOfDay(addDays(today, -6)), toDate: endOfDay(today) };
  }
  if (value === "last30") {
    return { fromDate: startOfDay(addDays(today, -29)), toDate: endOfDay(today) };
  }
  if (value === "last90") {
    return { fromDate: startOfDay(addDays(today, -89)), toDate: endOfDay(today) };
  }
  if (value === "custom") {
    const from = document.getElementById(`${prefix}-custom-from`)?.value || "";
    const to = document.getElementById(`${prefix}-custom-to`)?.value || "";
    return {
      fromDate: from ? new Date(`${from}T00:00:00`) : null,
      toDate: to ? new Date(`${to}T23:59:59.999`) : null,
    };
  }
  return { fromDate: null, toDate: null };
}

function activityChart(activity) {
  const max = Math.max(1, ...activity.map(d => d.total || 0));
  if (!activity.length) return `<div class="empty">No activity yet.</div>`;
  return `<div class="chart">${activity.map(d => `
    <div class="bar">
      <div class="bar-fill" title="${d.total} jobs" style="height:${Math.max(5, (d.total / max) * 150)}px"></div>
      <small>${esc((d.day || "").slice(5))}</small>
    </div>
  `).join("")}</div>`;
}

function failureQueue(jobs) {
  const failed = jobs.filter(j => j.status === "failed").slice(0, 5);
  if (!failed.length) return `<div class="empty compact">No failed jobs in this view.</div>`;
  return `<div class="work-list">${failed.map(job => `
    <button class="work-item" data-route="/jobs-page" title="Open jobs">
      <span class="work-status danger">!</span>
      <span>
        <strong>#${job.id} ${esc(job.keyword)}</strong>
        <small>${esc(job.stage || "unknown stage")} · ${fmtDate(job.updated_at)}</small>
      </span>
    </button>
  `).join("")}</div>`;
}

function websiteMix(jobs) {
  const counts = new Map();
  jobs.forEach(job => {
    const label = websiteLabel(job.website_id);
    const current = counts.get(label) || { total: 0, completed: 0, failed: 0 };
    current.total += 1;
    if (job.status === "completed") current.completed += 1;
    if (job.status === "failed") current.failed += 1;
    counts.set(label, current);
  });
  const rows = [...counts.entries()]
    .sort((a, b) => b[1].total - a[1].total)
    .slice(0, 5);
  if (!rows.length) return `<div class="empty compact">No website activity yet.</div>`;
  const max = Math.max(1, ...rows.map(([, item]) => item.total));
  return `<div class="website-mix">${rows.map(([name, item]) => `
    <div class="website-row">
      <div>
        <strong>${esc(name)}</strong>
        <small>${item.completed} complete · ${item.failed} failed</small>
      </div>
      <div class="mix-bar"><span style="width:${Math.max(6, (item.total / max) * 100)}%"></span></div>
      <b>${item.total}</b>
    </div>
  `).join("")}</div>`;
}

async function renderJobs() {
  await loadCore();
  app.innerHTML = `
    <div class="filters">
      <div class="filter-field">
        <label>Keyword</label>
        <input id="job-search" placeholder="Search keyword...">
      </div>
      <div class="filter-field">
        <label>Status</label>
        <select id="job-status">
          <option value="">All statuses</option>
          <option>pending</option><option>processing</option><option>completed</option><option>failed</option><option>retrying</option><option>canceled</option>
        </select>
      </div>
      <div class="filter-field">
        <label>Website</label>
        <select id="job-website">
          <option value="">All websites</option>
          <option value="__none">No website</option>
          ${appState.websites.map(w => `<option value="${w.id}">${esc(w.name)}</option>`).join("")}
        </select>
      </div>
      ${dateRangeFilterHtml("job")}
      <div class="filter-actions">
        <button class="btn" id="clear-job-filters">Clear</button>
      </div>
    </div>
    <div class="toolbar">
      <select id="bulk-job-action" style="max-width:180px">
        <option value="">Select action</option>
        <option value="pause">Pause selected</option>
        <option value="resume">Resume selected</option>
        <option value="retry">Retry selected</option>
        <option value="cancel">Cancel selected</option>
      </select>
      <button class="btn" id="apply-bulk-job-action">Apply</button>
      <span class="mini muted" id="selected-jobs-count">0 selected</span>
      <span class="mini muted" id="jobs-refresh-state">Auto-refresh on</span>
    </div>
    <div class="grid wide-left">
      <section class="panel">
        <div class="panel-head"><h2>All Jobs</h2><span class="mini muted">${appState.jobs.length} loaded</span></div>
        <div class="table-wrap"><table><thead><tr><th><input id="select-visible-jobs" type="checkbox" aria-label="Select visible jobs"></th><th>ID</th><th>Keyword</th><th>Status</th><th>Progress</th><th>Website</th><th>Elapsed</th><th>Upload Time</th></tr></thead><tbody id="jobs-body"></tbody></table></div>
      </section>
      <section class="panel" id="job-detail">
        <div class="panel-head"><h2>Job Detail</h2></div>
        <div class="empty">Select a job to inspect progress, logs, artifacts, and controls.</div>
      </section>
    </div>
  `;
  ["job-search", "job-status", "job-website", "job-date-range", "job-custom-from", "job-custom-to"].forEach(id => {
    document.getElementById(id).addEventListener("input", filterJobs);
    document.getElementById(id).addEventListener("change", filterJobs);
  });
  document.getElementById("job-date-range").addEventListener("change", () => updateCustomDateFields("job"));
  updateCustomDateFields("job");
  document.getElementById("clear-job-filters").addEventListener("click", clearJobFilters);
  document.getElementById("apply-bulk-job-action").addEventListener("click", applyBulkJobAction);
  document.getElementById("select-visible-jobs").addEventListener("change", toggleVisibleJobs);
  filterJobs();
  startJobsAutoRefresh();
}

async function refreshJobsPage() {
  const selectedId = appState.currentJob?.id;
  await loadCore();
  filterJobs();
  if (selectedId) await showJob(selectedId);
  updateJobsRefreshState("Jobs refreshed.");
}

function updateJobsRefreshState(message = "") {
  const el = document.getElementById("jobs-refresh-state");
  if (!el) return;
  const now = new Date().toLocaleTimeString([], {
    timeZone: APP_TIME_ZONE,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  el.textContent = message ? `${message} ${now} ${APP_TIME_ZONE_LABEL}` : `Auto-refresh on · ${now} ${APP_TIME_ZONE_LABEL}`;
}

function startJobsAutoRefresh() {
  updateJobsRefreshState();
  appState.timer = setInterval(async () => {
    if (routePath() !== "/jobs-page" || appState.refreshingJobs) return;
    appState.refreshingJobs = true;
    try {
      const selectedId = appState.currentJob?.id;
      await loadCore();
      filterJobs();
      if (selectedId) await showJob(selectedId);
      updateJobsRefreshState();
    } catch (e) {
      updateJobsRefreshState("Refresh failed.");
    } finally {
      appState.refreshingJobs = false;
    }
  }, 5000);
}

function filterJobs() {
  const jobs = filteredJobs("job");
  document.getElementById("jobs-body").innerHTML = jobRows(jobs);
  updateVisibleJobsCheckbox(jobs);
  updateSelectedJobsCount();
}

function clearJobFilters() {
  ["job-search", "job-status", "job-website", "job-date-range", "job-custom-from", "job-custom-to"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });
  updateCustomDateFields("job");
  filterJobs();
}

function selectedJobIds() {
  return [...appState.selectedJobIds];
}

function updateSelectedJobsCount() {
  const visibleInputs = [...document.querySelectorAll("[data-job-checkbox]")];
  visibleInputs.forEach(input => {
    input.checked = appState.selectedJobIds.has(String(input.value));
  });
  updateVisibleJobsCheckbox();
  const count = appState.selectedJobIds.size;
  const label = document.getElementById("selected-jobs-count");
  if (label) label.textContent = `${count} selected`;
}

function updateVisibleJobsCheckbox(jobs = null) {
  const selectAll = document.getElementById("select-visible-jobs");
  if (!selectAll) return;
  const ids = jobs
    ? jobs.map(job => String(job.id))
    : [...document.querySelectorAll("[data-job-checkbox]")].map(input => String(input.value));
  const selectedVisible = ids.filter(id => appState.selectedJobIds.has(id)).length;
  selectAll.checked = ids.length > 0 && selectedVisible === ids.length;
  selectAll.indeterminate = selectedVisible > 0 && selectedVisible < ids.length;
}

function toggleVisibleJobs(e) {
  document.querySelectorAll("[data-job-checkbox]").forEach(input => {
    input.checked = e.target.checked;
    if (e.target.checked) {
      appState.selectedJobIds.add(String(input.value));
    } else {
      appState.selectedJobIds.delete(String(input.value));
    }
  });
  updateSelectedJobsCount();
}

async function applyBulkJobAction() {
  const action = document.getElementById("bulk-job-action").value;
  const ids = selectedJobIds();
  if (!action) return toast("Choose an action first.");
  if (!ids.length) return toast("Select at least one job.");
  if (action === "cancel" && !confirm(`Cancel ${ids.length} selected job(s)?`)) return;

  let ok = 0;
  for (const id of ids) {
    try {
      await api(`/jobs/${id}/${action}`, { method: "POST", body: JSON.stringify({ reason: "Dashboard bulk action" }) });
      ok += 1;
    } catch (e) {
      toast(`Job #${id}: ${e.message}`);
    }
  }
  await loadCore();
  ids.forEach(id => appState.selectedJobIds.delete(String(id)));
  filterJobs();
  if (appState.currentJob?.id) await showJob(appState.currentJob.id);
  toast(`${action} applied to ${ok} job(s).`);
}

async function showJob(id) {
  const detail = await api(`/jobs/${id}`);
  appState.currentJob = detail;
  markSelectedJob(id);
  const artifacts = detail.artifacts || {};
  const logs = (await api(`/logs?job_id=${id}&limit=80`).catch(() => ({ logs: [] }))).logs || [];
  document.getElementById("job-detail").innerHTML = `
    <div class="panel-head">
      <h2>#${detail.id}: ${esc(detail.keyword)}</h2>
      <div class="toolbar" style="margin-bottom:0">
        ${statusBadge(detail.status)}
      </div>
    </div>
    <div class="panel-body grid">
      <div class="split"><span class="muted">Stage</span><strong>${esc(detail.stage)}</strong></div>
      <div class="split"><span class="muted">Elapsed</span><strong>${elapsedSince(detail.created_at, ["completed", "failed", "canceled", "cancelled"].includes(detail.status) ? detail.updated_at : null)}</strong></div>
      <div class="split"><span class="muted">Started</span><strong>${fmtDate(detail.started_at || detail.created_at)}</strong></div>
      <div class="split"><span class="muted">Upload Time</span><strong>${jobUploadTime(detail)}</strong></div>
      ${progressBar(detail.progress)}
      <div class="steps">${stages.map(([key, label]) => stepHtml(key, label, detail)).join("")}</div>
      ${jobControls(detail)}
      ${artifactSection(artifacts, detail.id)}
      ${detail.errors?.length ? `<div class="panel danger-zone"><div class="panel-head"><h3>Errors</h3></div><div class="panel-body">${detail.errors.map(e => `<p><strong>${esc(e.error_type)}</strong> ${esc(e.error_message)}</p>`).join("")}</div></div>` : ""}
      <div class="logbox">${renderLogLines(logs.reverse())}</div>
    </div>
  `;
}

function markSelectedJob(id) {
  document.querySelectorAll("[data-job]").forEach(row => {
    row.classList.toggle("selected", String(row.dataset.job) === String(id));
  });
}

function jobControls(job) {
  const status = job.status || "";
  const canPause = ["pending", "processing", "retrying"].includes(status);
  const canResume = canPause;
  const canCancel = ["pending", "processing", "retrying", "paused"].includes(status);
  const canRetry = ["failed", "canceled", "cancelled"].includes(status);
  const buttons = [];

  if (canPause) buttons.push(`<button class="btn" data-job-action="pause" data-id="${job.id}">Pause</button>`);
  if (canResume) buttons.push(`<button class="btn" data-job-action="resume" data-id="${job.id}">Resume</button>`);
  if (canRetry) buttons.push(`<button class="btn" data-job-action="retry" data-id="${job.id}">Retry</button>`);
  if (canCancel) buttons.push(`<button class="btn danger" data-job-action="cancel" data-id="${job.id}">Cancel</button>`);

  return buttons.length ? `<div class="toolbar">${buttons.join("")}</div>` : "";
}

function stepHtml(key, label, job) {
  const current = stages.findIndex(s => s[0] === job.stage);
  const idx = stages.findIndex(s => s[0] === key);
  let cls = "";
  if ((job.status === "failed" || job.status === "canceled" || job.status === "cancelled") && key === job.stage) cls = "failed";
  else if (idx < current || job.status === "completed") cls = "done";
  else if (idx === current) cls = "active";
  return `<div class="step ${cls}">${esc(label)}</div>`;
}

function artifactSection(a, jobId) {
  const localArtifactUrl = path => {
    const value = String(path || "").trim();
    if (!value) return "";
    if (/^https?:\/\//i.test(value) || value.startsWith("/")) return value;
    return `/${value}`;
  };
  const images = [
    ["Recipe Image", localArtifactUrl(a.recipe_image_path) || a.image_u1 || a.hero_image_url || a.midjourney_image_url],
    ["Pinterest Top", localArtifactUrl(a.pinterest_top_image_path) || a.midjourney_image_url],
    ["Pinterest Bottom", localArtifactUrl(a.pinterest_bottom_image_path) || a.midjourney_image_url_2],
    ["Pinterest Pin", localArtifactUrl(a.pinterest_pin_path) || a.pinterest_pin_wp_url || a.pin_url],
  ].filter(x => x[1]);
  const article = a.wp_post_url || a.article_html || a.article_title;
  if (!images.length && !article) return `<div class="empty">No artifacts yet.</div>`;
  const articlePreviewOpen = appState.openArticlePreviews.has(String(jobId)) ? " open" : "";
  return `
    ${images.length ? `<div class="artifact-grid">${images.map(([name, url]) => `<a class="artifact" href="${esc(url)}" target="_blank"><img src="${esc(url)}" alt="${esc(name)}"><div>${esc(name)}</div></a>`).join("")}</div>` : ""}
    ${a.wp_post_url ? `<a class="btn primary" href="${esc(a.wp_post_url)}" target="_blank">Open WordPress Post</a>` : ""}
    ${a.article_html ? `<details class="article-preview-panel" data-article-preview="${esc(jobId)}"${articlePreviewOpen}><summary class="btn">Article Preview</summary><div class="panel-body">${a.article_html}</div></details>` : ""}
  `;
}

async function jobAction(action, id) {
  if (["cancel"].includes(action) && !confirm(`Confirm ${action} for job #${id}?`)) return;
  const res = await api(`/jobs/${id}/${action}`, { method: "POST", body: JSON.stringify({ reason: "Dashboard action" }) });
  toast(action === "retry" ? `Retry queued for job #${res.job_id}` : `Job #${id} ${res.status || res.action || action}`);
  await loadCore();
  filterJobs();
  await showJob(id);
}

async function renderNewBatch() {
  appState.websites = await loadWebsitesWithRestore().catch(() => []);
  appState.batchWebsiteReady = false;
  const suggested = (() => {
    try {
      return JSON.parse(localStorage.getItem("batchScheduleSettings") || "{}");
    } catch (_) {
      return {};
    }
  })();
  const suggestionText = [
    suggested.mode ? `Last mode: ${suggested.mode}` : "",
    suggested.keywords_per_day ? `${suggested.keywords_per_day}/day` : "",
    suggested.delay_between_jobs_hours !== undefined && suggested.delay_between_jobs_hours !== "" ? `${suggested.delay_between_jobs_hours}h delay` : "",
    suggested.start_time_each_day ? `starts ${suggested.start_time_each_day}` : "",
  ].filter(Boolean).join(" · ");
  app.innerHTML = `
    <div class="grid wide-right">
      <section class="panel">
        <div class="panel-head"><h2>Batch Settings</h2></div>
        <div class="panel-body">
          <label class="field">Target Website <span class="required">*</span></label>
          <select id="batch-site" required><option value="">Select website</option>${appState.websites.map(w => `<option value="${w.id}">${esc(w.name)} - ${esc(w.base_url)}</option>`).join("")}</select>
          <p class="field-help">Choose where this batch will publish.</p>
          <div id="batch-site-status" class="form-message info">Checking selected website...</div>
          ${suggestionText ? `<div class="form-message info compact">Suggested from last batch: ${esc(suggestionText)}</div>` : ""}
          <div class="form-row" style="margin-top:12px"><div><label class="field">Batch Name</label><input id="batch-name" placeholder="Optional campaign name"><p class="field-help">Used only to identify this batch later.</p></div><div><label class="field">Template</label><select><option>Default article pipeline</option></select><p class="field-help">Keeps the current article generation workflow.</p></div></div>
          <label class="field">Distribution Mode <span class="required">*</span></label>
          <select id="batch-distribution-mode" required>
            <option value="auto" selected>Auto Mode (recommended)</option>
            <option value="manual">Manual Mode</option>
          </select>
          <p class="field-help">Auto spreads keywords evenly. Manual gives you exact control.</p>
          <div class="form-row">
            <div><label class="field">Start Date <span class="required">*</span></label><input id="batch-schedule-date" type="date" required placeholder="yyyy-mm-dd"><p class="field-help">First day jobs can start.</p></div>
            <div><label class="field">Start Time Each Day <span class="required">*</span></label><input id="batch-start-time" type="text" inputmode="numeric" required placeholder="08:00" pattern="^([01]\\d|2[0-3]):[0-5]\\d$"><p class="field-help">First publish slot for each scheduled day.</p></div>
          </div>
          <div id="auto-schedule-fields">
            <label class="field">Max Jobs Per Day <span class="tooltip" title="Optional cap. Leave empty and Auto Mode will choose a balanced daily volume.">?</span></label>
            <input id="batch-max-jobs-per-day" type="number" min="1" step="1" placeholder="Optional, e.g. 5">
            <p class="field-help">Optional. Auto Mode uses this as the maximum number of jobs for any day.</p>
          </div>
          <div id="manual-schedule-fields">
            <div class="form-row">
              <div><label class="field">Keywords Per Day <span class="required">*</span> <span class="tooltip" title="How many keywords can be scheduled on one day.">?</span></label><input id="batch-keywords-per-day" type="number" min="1" step="1" placeholder="Required in manual mode"><p class="field-help">Manual Mode requires the exact number of jobs allowed per day.</p></div>
              <div><label class="field">Delay Between Jobs <span class="required">*</span> <span class="tooltip" title="Time gap between each job. Choose no delay to run jobs back-to-back with a small safety gap.">?</span></label><select id="batch-delay-hours"><option value="">Select delay</option><option value="0">No delay (run jobs back-to-back)</option><option value="1">1 hour</option><option value="2">2 hours</option><option value="3">3 hours</option></select><p class="field-help">No delay still adds a small 10-second buffer to avoid collisions.</p></div>
            </div>
          </div>
          <div class="form-row">
            <div><label class="field">Timezone <span class="required">*</span></label><select id="batch-timezone" required><option value="">Select timezone</option><option value="Africa/Casablanca">Africa/Casablanca</option><option value="UTC">UTC</option><option value="America/New_York">America/New_York</option><option value="Europe/London">Europe/London</option></select><p class="field-help">Schedule timestamps are saved using this timezone.</p></div>
          </div>
          <div id="batch-delay-note" class="form-message info" hidden>Jobs will run continuously with a minimal 10-second gap.</div>
          <label class="field">Keywords <span class="required">*</span></label>
          <textarea id="batch-keywords" required placeholder="One keyword per line"></textarea>
          <p class="field-help">Paste keywords one per line or upload a CSV.</p>
          <div id="batch-submit-message" class="form-message" hidden></div>
          <div class="toolbar" style="margin-top:12px"><input id="csv-file" type="file" accept=".csv,text/csv"><button class="btn" id="preview-batch" type="button">Preview</button><button class="btn primary" id="submit-batch" type="button" disabled>Submit Batch</button></div>
        </div>
      </section>
      <section class="panel batch-preview-panel">
        <div class="panel-head"><h2>Preview</h2><span class="mini muted" id="estimate">No keywords</span></div>
        <div class="panel-body" id="batch-preview"><div class="empty">Paste keywords or upload a CSV.</div></div>
      </section>
    </div>
  `;
  document.getElementById("csv-file").addEventListener("change", importCsv);
  document.getElementById("preview-batch").addEventListener("click", previewBatch);
  document.getElementById("submit-batch").addEventListener("click", submitBatch);
  document.getElementById("batch-site").addEventListener("change", async () => {
    await checkBatchWebsite();
    updateBatchFormState();
  });
  ["batch-distribution-mode", "batch-schedule-date", "batch-start-time", "batch-max-jobs-per-day", "batch-keywords-per-day", "batch-delay-hours", "batch-timezone", "batch-keywords"].forEach(id => {
    document.getElementById(id)?.addEventListener("input", previewBatch);
    document.getElementById(id)?.addEventListener("change", previewBatch);
  });
  checkBatchWebsite().then(updateBatchFormState);
  previewBatch();
}

async function checkBatchWebsite() {
  const site = document.getElementById("batch-site");
  const status = document.getElementById("batch-site-status");
  const submit = document.getElementById("submit-batch");
  const websiteId = Number(site?.value || 0);
  if (!site || !status || !submit) return false;
  if (!websiteId) {
    appState.batchWebsiteReady = false;
    status.hidden = false;
    status.className = "form-message error";
    status.textContent = "Add or select a website before submitting.";
    updateBatchFormState();
    return false;
  }
  status.hidden = false;
  status.className = "form-message info";
  status.textContent = "Checking WordPress image upload access...";
  appState.batchWebsiteReady = false;
  updateBatchFormState();
  try {
    const res = await api(`/websites/${websiteId}/test`, { method: "POST" });
    if (!res.ok) {
      appState.batchWebsiteReady = false;
      status.className = "form-message error";
      status.textContent = res.message || "Selected website cannot upload images.";
      updateBatchFormState();
      return false;
    }
    appState.batchWebsiteReady = true;
    status.className = "form-message success";
    status.textContent = res.message || "Website is ready.";
    updateBatchFormState();
    return true;
  } catch (error) {
    appState.batchWebsiteReady = false;
    status.className = "form-message error";
    status.textContent = error.message || "Could not test selected website.";
    updateBatchFormState();
    return false;
  }
}

function keywords() {
  return document.getElementById("batch-keywords").value.split(/\r?\n|,/).map(x => x.trim()).filter(Boolean);
}

async function importCsv(e) {
  const file = e.target.files[0];
  if (!file) return;
  document.getElementById("batch-keywords").value = await file.text();
  previewBatch();
}

function previewBatch() {
  const list = keywords();
  const schedule = buildBatchSchedule(list);
  const mode = document.getElementById("batch-distribution-mode")?.value || "auto";
  const noDelay = mode === "manual" && Number(document.getElementById("batch-delay-hours")?.value) === 0;
  const perDayInput = document.getElementById("batch-keywords-per-day");
  const manualFields = document.getElementById("manual-schedule-fields");
  const autoFields = document.getElementById("auto-schedule-fields");
  const delayNote = document.getElementById("batch-delay-note");
  if (manualFields) manualFields.hidden = mode !== "manual";
  if (autoFields) autoFields.hidden = mode !== "auto";
  if (perDayInput) perDayInput.disabled = false;
  if (delayNote) delayNote.hidden = !noDelay;
  const days = schedule.length ? new Set(schedule.map(item => item.scheduled_at.slice(0, 10))).size : 0;
  const estimate = mode === "auto"
    ? `${list.length} jobs evenly distributed${days ? ` over ${days} day${days === 1 ? "" : "s"}` : ""}`
    : noDelay
      ? `${list.length} jobs back-to-back`
      : `${list.length} jobs${days ? ` over ${days} day${days === 1 ? "" : "s"}` : ""}`;
  document.getElementById("estimate").textContent = list.length ? estimate : "No keywords";
  document.getElementById("batch-preview").innerHTML = list.length
    ? `<ol class="batch-preview-list">${list.map((keyword, index) => {
        const item = schedule[index];
        const timing = item
          ? `${item.scheduled_at.replace("T", " ")} ${item.timezone}`
          : "Add start date, time, and timezone to calculate schedule";
        return `<li><strong>${esc(keyword)}</strong><br><span class="mini muted">${esc(timing)}</span></li>`;
      }).join("")}</ol>`
    : `<div class="empty">No keywords detected.</div>`;
  updateBatchFormState();
}

function buildBatchSchedule(list) {
  const date = document.getElementById("batch-schedule-date")?.value;
  const startTime = normaliseBatchTime(document.getElementById("batch-start-time")?.value);
  const timezone = document.getElementById("batch-timezone")?.value;
  if (!list.length || !date || !startTime || !timezone) return [];
  const mode = document.getElementById("batch-distribution-mode")?.value || "auto";
  const manualPerDay = Number(document.getElementById("batch-keywords-per-day")?.value || 0);
  const manualDelayRaw = document.getElementById("batch-delay-hours")?.value;
  const maxJobsPerDay = Number(document.getElementById("batch-max-jobs-per-day")?.value || 0);
  const perDay = mode === "auto"
    ? calculateAutoKeywordsPerDay(list.length, maxJobsPerDay)
    : Math.max(1, manualPerDay);
  const delayHours = mode === "auto" ? 0 : Number(manualDelayRaw);
  if (mode === "manual" && (!manualPerDay || manualDelayRaw === "")) return [];
  const noDelay = delayHours === 0;
  const start = new Date(`${date}T${startTime}:00`);
  const autoDayCounts = mode === "auto" ? buildAutoDayCounts(list.length, maxJobsPerDay) : [];
  let dayOffset = 0;
  let slot = 0;
  return list.map((keyword, index) => {
    if (mode === "auto") {
      let cursor = index;
      dayOffset = 0;
      for (const count of autoDayCounts) {
        if (cursor < count) {
          slot = cursor;
          break;
        }
        cursor -= count;
        dayOffset += 1;
      }
    } else {
      dayOffset = Math.floor(index / perDay);
      slot = index % perDay;
    }
    const scheduled = new Date(start.getTime());
    scheduled.setDate(start.getDate() + dayOffset);
    if (noDelay) {
      scheduled.setSeconds(start.getSeconds() + (slot * 10), 0);
    } else {
      scheduled.setHours(start.getHours() + (slot * delayHours), start.getMinutes(), 0, 0);
    }
    const yyyy = scheduled.getFullYear();
    const mm = String(scheduled.getMonth() + 1).padStart(2, "0");
    const dd = String(scheduled.getDate()).padStart(2, "0");
    const hh = String(scheduled.getHours()).padStart(2, "0");
    const mi = String(scheduled.getMinutes()).padStart(2, "0");
    const ss = String(scheduled.getSeconds()).padStart(2, "0");
    return { keyword, scheduled_at: `${yyyy}-${mm}-${dd}T${hh}:${mi}:${ss}`, timezone };
  });
}

function calculateAutoKeywordsPerDay(totalKeywords, maxJobsPerDay) {
  if (!totalKeywords) return 0;
  return Math.max(...buildAutoDayCounts(totalKeywords, maxJobsPerDay));
}

function buildAutoDayCounts(totalKeywords, maxJobsPerDay) {
  if (!totalKeywords) return [];
  const cap = maxJobsPerDay > 0 ? Math.max(1, Math.min(totalKeywords, maxJobsPerDay)) : 10;
  const days = Math.max(1, Math.ceil(totalKeywords / cap));
  const base = Math.floor(totalKeywords / days);
  const extra = totalKeywords % days;
  return Array.from({ length: days }, (_, index) => base + (index < extra ? 1 : 0));
}

function getBatchValidationError() {
  const list = keywords();
  const mode = document.getElementById("batch-distribution-mode")?.value || "auto";
  const websiteId = Number(document.getElementById("batch-site")?.value || 0);
  const date = document.getElementById("batch-schedule-date")?.value;
  const startTime = normaliseBatchTime(document.getElementById("batch-start-time")?.value);
  const timezone = document.getElementById("batch-timezone")?.value;
  if (!websiteId) return "Select a target website.";
  if (!appState.batchWebsiteReady) return "Wait until the selected website is verified.";
  if (!date) return "Choose a start date.";
  if (!startTime) return "Enter start time as HH:MM, for example 08:00.";
  if (!timezone) return "Choose a timezone.";
  if (!list.length) return "Enter at least one keyword.";
  if (mode === "manual") {
    if (!Number(document.getElementById("batch-keywords-per-day")?.value || 0)) return "Enter keywords per day.";
    if ((document.getElementById("batch-delay-hours")?.value || "") === "") return "Select delay between jobs.";
  }
  return "";
}

function updateBatchFormState() {
  const submit = document.getElementById("submit-batch");
  if (!submit) return;
  const error = getBatchValidationError();
  submit.disabled = Boolean(error);
  submit.title = error || "Submit batch";
}

function normaliseBatchTime(value) {
  const raw = String(value || "").trim();
  const match = raw.match(/^(\d{1,2})(?::?(\d{2}))?$/);
  if (!match) return "";
  const hour = Number(match[1]);
  const minute = Number(match[2] || 0);
  if (hour < 0 || hour > 23 || minute < 0 || minute > 59) return "";
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}

async function submitBatch() {
  const list = keywords();
  const websiteId = Number(document.getElementById("batch-site").value || 0);
  const msg = document.getElementById("batch-submit-message");
  const btn = document.getElementById("submit-batch");
  const showMessage = (kind, text) => {
    msg.hidden = false;
    msg.className = `form-message ${kind}`;
    msg.textContent = text;
  };
  msg.hidden = true;
  const validationError = getBatchValidationError();
  if (validationError) {
    showMessage("error", validationError);
    return;
  }
  if (!(await checkBatchWebsite())) {
    showMessage("error", "Fix the selected website credentials before submitting this batch.");
    return;
  }
  const mode = document.getElementById("batch-distribution-mode").value;
  const maxJobsPerDay = Number(document.getElementById("batch-max-jobs-per-day").value || 0);
  const autoPerDay = calculateAutoKeywordsPerDay(list.length, maxJobsPerDay);
  const keywordsPerDay = mode === "auto" ? autoPerDay : Number(document.getElementById("batch-keywords-per-day").value);
  const delayHours = mode === "auto" ? 0 : Number(document.getElementById("batch-delay-hours").value);
  const startDate = document.getElementById("batch-schedule-date").value;
  const startTime = normaliseBatchTime(document.getElementById("batch-start-time").value);
  const timezone = document.getElementById("batch-timezone").value;
  btn.disabled = true;
  btn.textContent = "Checking...";
  showMessage("info", "Checking website credentials before queueing the batch...");
  try {
    localStorage.setItem("batchScheduleSettings", JSON.stringify({
      mode,
      keywords_per_day: keywordsPerDay,
      delay_between_jobs_hours: delayHours,
      start_time_each_day: startTime,
      timezone,
    }));
    const res = await api("/generate", {
      method: "POST",
      body: JSON.stringify({
        website_id: websiteId,
        batch_name: document.getElementById("batch-name").value,
        keywords: list,
        distribution_mode: mode,
        max_jobs_per_day: maxJobsPerDay || null,
        scheduled_time: `${startDate}T${startTime}`,
        schedule_start_date: startDate,
        keywords_per_day: keywordsPerDay,
        delay_between_jobs_hours: delayHours,
        start_time_each_day: startTime,
        timezone,
      })
    });
    showMessage("success", res.message || "Batch queued.");
    toast(res.message || "Batch queued.");
    setTimeout(() => navigate("/jobs-page"), 650);
  } catch (error) {
    showMessage("error", error.message || "Batch could not be submitted.");
    toast(error.message || "Batch could not be submitted.");
  } finally {
    btn.textContent = "Submit Batch";
    updateBatchFormState();
  }
}

async function renderWebsites() {
  document.querySelectorAll("body > .action-menu-panel").forEach(item => item.remove());
  appState.websites = await loadWebsitesWithRestore().catch(() => []);
  appState.pinTemplates = (await api("/pin-templates").catch(() => ({ templates: [] }))).templates || [];
  const templateOptions = appState.pinTemplates.map(t => `<option value="${esc(t.id)}">${esc(t.label)}</option>`).join("");
  const templateLabel = id => (appState.pinTemplates.find(t => t.id === id)?.label || id || "Default");
  const editingSite = appState.websites.find(w => String(w.id) === String(appState.editingWebsiteId));
  const showWebsiteEditor = appState.websiteEditorOpen || !!editingSite;
  const previewTemplate = editingSite?.pin_template || appState.pinTemplates[0]?.id || "";
  const previewUrl = id => `/pin-templates/${encodeURIComponent(id || previewTemplate)}/preview`;
  const siteType = editingSite?.site_type || editingSite?.siteType || "wordpress";
  app.innerHTML = `
    <div class="grid ${showWebsiteEditor ? "wide-left" : ""}">
      <section class="panel">
        <div class="panel-head"><h2>Websites</h2><div class="toolbar"><span class="mini muted">${appState.websites.length} saved</span><button class="btn primary" id="add-website">Add Website</button></div></div>
        <div class="table-wrap"><table class="websites-table"><thead><tr><th>Name</th><th>Type</th><th>URL</th><th>Auth</th><th>Pin Template</th><th>Post Status</th><th>Categories</th><th>Added</th><th>Actions</th></tr></thead><tbody>${appState.websites.map(w => `<tr><td><strong>${esc(w.name)}</strong></td><td>${esc((w.site_type || w.siteType || "wordpress").replace("_", " "))}</td><td>${esc(w.base_url)}</td><td>${(w.site_type || w.siteType) === "html_static" ? (w.api_enabled || w.apiEnabled ? "API enabled" : "API off") : esc(w.username || w.wpUsername || "")}</td><td>${esc(templateLabel(w.pin_template))}</td><td>${esc((w.publish_status || "draft").toUpperCase())}</td><td><strong>${Number(w.category_count || 0)}</strong><br><span class="mini muted">${w.categories_synced_at ? `synced ${fmtDate(w.categories_synced_at)}` : "not synced"}</span></td><td>${fmtDate(w.created_at)}</td><td><div class="action-menu"><button type="button" class="icon-btn action-menu-toggle" data-action-menu="${w.id}" aria-label="Website actions" aria-expanded="false">...</button><div class="action-menu-panel" data-action-menu-panel="${w.id}"><button type="button" data-site-edit="${w.id}">Edit</button><button type="button" data-site-test="${w.id}">Test</button><button type="button" data-site-sync-categories="${w.id}">Sync Categories</button><button type="button" class="danger" data-site-delete="${w.id}">Delete</button></div></div></td></tr>`).join("") || `<tr><td colspan="9"><div class="empty">No websites yet.</div></td></tr>`}</tbody></table></div>
      </section>
      ${showWebsiteEditor ? `
      <section class="panel">
        <div class="panel-head"><h2>${editingSite ? "Edit Website" : "Add Website"}</h2>${editingSite ? `<span class="mini muted">#${editingSite.id}</span>` : ""}</div>
        <div class="panel-body">
          <label class="field">Name</label><input id="site-name" value="${esc(editingSite?.name || "")}">
          <label class="field" style="margin-top:10px">Base URL</label><input id="site-url" placeholder="https://example.com" value="${esc(editingSite?.base_url || "")}">
          <label class="field" style="margin-top:10px">Website Type</label>
          <select id="site-type">
            <option value="wordpress">WordPress</option>
            <option value="html_static">HTML Static</option>
          </select>
          <div id="wordpress-fields">
            <label class="field" style="margin-top:10px">Username / Admin Email</label><input id="site-user" value="${esc(editingSite?.username || editingSite?.wpUsername || "")}">
            <label class="field" style="margin-top:10px">App Password</label><input id="site-pass" type="password" placeholder="${editingSite ? "Leave blank to keep existing password" : ""}">
          </div>
          <div id="html-static-fields">
            <label class="field" style="margin-top:10px">Publish Endpoint</label><input id="site-publish-endpoint" placeholder="https://example.com/internal-api/publish" value="${esc(editingSite?.publish_endpoint || editingSite?.publishEndpoint || "")}">
            <label class="field" style="margin-top:10px">API Key</label><input id="site-api-key" type="password" placeholder="${editingSite ? "Leave blank to keep existing key" : "Paste or generate an API key"}">
            <div class="toolbar" style="margin-top:10px"><button class="btn" id="generate-site-api-key" type="button">Regenerate Key</button><button class="btn" data-site-test="${editingSite?.id || ""}" type="button"${editingSite ? "" : " disabled"}>Test Connection</button></div>
            <label style="display:block;margin-top:10px"><input id="site-api-enabled" type="checkbox" ${editingSite?.api_enabled || editingSite?.apiEnabled || !editingSite ? "checked" : ""}> API enabled</label>
          </div>
          <label class="field" style="margin-top:10px">WordPress Post Status</label>
          <select id="site-publish-status">
            <option value="draft">Draft</option>
            <option value="publish">Publish</option>
          </select>
          <label class="field" style="margin-top:10px">Pinterest Pin Template</label><select id="site-pin-template">${templateOptions}</select>
          <div class="template-style-editor">
            <label class="field">Template Style</label>
            <label class="field" style="margin-top:8px">Font</label>
            <select id="pin-font-family">${pinFontSelectOptions()}</select>
            <div class="color-grid">
              <label class="color-field">
                <span>Band background</span>
                <input id="pin-band-color" type="color" value="#ff585d">
                <code data-value-for="pin-band-color">#ff585d</code>
              </label>
              <label class="color-field">
                <span>Font color</span>
                <input id="pin-font-color" type="color" value="#ffffff">
                <code data-value-for="pin-font-color">#ffffff</code>
              </label>
            </div>
            <label class="field" style="margin-top:12px">Subtitle</label>
            <input id="pin-badge-text" placeholder="easy recipe">
            <select id="pin-badge-font-family">${pinFontSelectOptions()}</select>
            <div class="color-grid" style="margin-top:10px">
              <label class="color-field">
                <span>Subtitle background</span>
                <input id="pin-badge-bg" type="color" value="#ffffff">
                <code data-value-for="pin-badge-bg">#ffffff</code>
              </label>
              <label class="color-field">
                <span>Subtitle font color</span>
                <input id="pin-badge-fill" type="color" value="#111111">
                <code data-value-for="pin-badge-fill">#111111</code>
              </label>
            </div>
            <button class="btn" id="save-pin-template-style" type="button">Save Website Template Style</button>
          </div>
          <div class="toolbar" style="margin-top:10px">
            <a class="btn" id="open-pin-template-preview" href="${esc(previewUrl(previewTemplate))}" target="_blank" rel="noopener">Open Preview</a>
          </div>
          <a id="pin-template-preview-link" href="${esc(previewUrl(previewTemplate))}" target="_blank" rel="noopener">
            <img id="pin-template-preview-img" src="${esc(previewUrl(previewTemplate))}" alt="Pinterest pin template preview" style="width:100%; max-width:220px; aspect-ratio:2/3; object-fit:cover; margin-top:12px; border:1px solid var(--border); border-radius:8px; box-shadow:var(--shadow-sm);">
          </a>
          <div class="toolbar" style="margin-top:14px">
            <button class="btn primary" id="save-site">${editingSite ? "Update Website" : "Save Website"}</button>
            <button class="btn" id="cancel-site-edit">Cancel</button>
          </div>
        </div>
      </section>
      ` : ""}
    </div>
  `;
  document.getElementById("add-website").addEventListener("click", () => {
    appState.editingWebsiteId = null;
    appState.websiteEditorOpen = true;
    renderWebsites();
  });
  if (showWebsiteEditor) {
    document.getElementById("site-type").value = siteType;
    const syncSiteTypeFields = () => {
      const current = document.getElementById("site-type").value;
      document.getElementById("wordpress-fields").style.display = current === "wordpress" ? "block" : "none";
      document.getElementById("html-static-fields").style.display = current === "html_static" ? "block" : "none";
    };
    syncSiteTypeFields();
    document.getElementById("site-type").addEventListener("change", syncSiteTypeFields);
    document.getElementById("generate-site-api-key")?.addEventListener("click", async () => {
      if (editingSite?.id) {
        const result = await api(`/websites/${editingSite.id}/regenerate-api-key`, { method: "POST" });
        document.getElementById("site-api-key").value = result.api_key || "";
        toast("HTML static API key regenerated. Save it somewhere secure.");
        return;
      }
      const bytes = new Uint8Array(32);
      crypto.getRandomValues(bytes);
      document.getElementById("site-api-key").value = btoa(String.fromCharCode(...bytes)).replace(/[+/=]/g, "");
    });
    if (editingSite) document.getElementById("site-pin-template").value = editingSite.pin_template || "";
    document.getElementById("site-publish-status").value = editingSite?.publish_status || "draft";
    updatePinTemplatePreview();
    document.getElementById("save-site").addEventListener("click", saveWebsite);
    document.getElementById("site-pin-template").addEventListener("change", () => {
      updatePinTemplatePreview({ preferWebsiteStyle: false });
    });
    document.getElementById("save-pin-template-style").addEventListener("click", savePinTemplateStyle);
    ["pin-band-color", "pin-font-color", "pin-font-family", "pin-badge-text", "pin-badge-font-family", "pin-badge-bg", "pin-badge-fill"].forEach(id => {
      document.getElementById(id).addEventListener("input", updateTemplateColorLabels);
    });
    document.getElementById("cancel-site-edit")?.addEventListener("click", () => {
      appState.editingWebsiteId = null;
      appState.websiteEditorOpen = false;
      renderWebsites();
    });
  }
}

function currentEditingSite() {
  return appState.websites.find(w => String(w.id) === String(appState.editingWebsiteId));
}

function selectedTemplateMatchesWebsite(site = currentEditingSite()) {
  return !!(appState.editingWebsiteId && site && valOrEmpty("site-pin-template") === (site.pin_template || ""));
}

function hasWebsiteTemplateStyle(site = currentEditingSite()) {
  return !!(site?.pin_template_style && Object.keys(site.pin_template_style).length);
}

function pinTemplatePreviewUrl({ preferWebsiteStyle = true } = {}) {
  const templateId = activePinTemplateId();
  if (preferWebsiteStyle && selectedTemplateMatchesWebsite() && hasWebsiteTemplateStyle()) {
    return `/websites/${encodeURIComponent(appState.editingWebsiteId)}/pin-template-preview`;
  }
  return `/pin-templates/${encodeURIComponent(templateId)}/preview`;
}

function updatePinTemplatePreview(options = {}) {
  const url = pinTemplatePreviewUrl(options);
  const previewUrl = `${url}${url.includes("?") ? "&" : "?"}t=${Date.now()}`;
  const img = document.getElementById("pin-template-preview-img");
  const link = document.getElementById("pin-template-preview-link");
  const open = document.getElementById("open-pin-template-preview");
  if (img) img.src = previewUrl;
  if (link) link.href = previewUrl;
  if (open) open.href = previewUrl;
  loadPinTemplateStyle(options);
}

function updateTemplateColorLabels() {
  document.querySelectorAll("[data-value-for]").forEach(label => {
    const input = document.getElementById(label.dataset.valueFor);
    if (input) label.textContent = input.type === "checkbox" ? (input.checked ? "on" : "off") : input.value;
  });
}

function activePinTemplateId() {
  return valOrEmpty("template-admin-select") || valOrEmpty("site-pin-template") || appState.pinTemplates[0]?.id || "";
}

function valOrEmpty(id) {
  const el = document.getElementById(id);
  return el ? el.value.trim() : "";
}

function setValue(id, value) {
  const el = document.getElementById(id);
  if (el) el.value = value;
}

function setChecked(id, value) {
  const el = document.getElementById(id);
  if (el) el.checked = !!value;
}

function checked(id) {
  return !!document.getElementById(id)?.checked;
}

async function loadPinTemplateStyle({ preferWebsiteStyle = true } = {}) {
  const templateId = activePinTemplateId();
  if (!templateId) return;
  const requestId = ++appState.pinStyleRequestId;
  const styleUrl = preferWebsiteStyle && selectedTemplateMatchesWebsite() && hasWebsiteTemplateStyle()
    ? `/websites/${encodeURIComponent(appState.editingWebsiteId)}/pin-template-style`
    : `/pin-templates/${encodeURIComponent(templateId)}/style`;
  const style = await api(styleUrl).catch(() => null);
  if (!style || requestId !== appState.pinStyleRequestId || templateId !== activePinTemplateId()) return;
  setValue("pin-band-color", style.band_background || "#ff585d");
  setValue("pin-band-border-color", style.band_border_color || "#ffffff");
  setValue("pin-band-border-width", style.band_border_width || 0);
  setValue("pin-band-radius", style.band_radius || 0);
  setValue("pin-font-color", style.font_color || "#ffffff");
  setValue("pin-font-family", style.font_family || "");
  setValue("pin-font-size-max", style.font_size_max || 92);
  setValue("pin-font-size-min", style.font_size_min || 44);
  setValue("pin-max-lines", style.max_lines || 2);
  setValue("pin-max-words", style.max_words || 8);
  setChecked("pin-uppercase", style.uppercase !== false);
  setValue("pin-stroke-color", style.stroke_fill || "#111111");
  setValue("pin-stroke-width", style.stroke_width || 0);
  setValue("pin-shadow-color", style.shadow_fill || "#111111");
  setChecked("pin-badge-enabled", !!style.badge_enabled);
  setValue("pin-badge-text", style.badge_text || "");
  setValue("pin-badge-font-family", style.badge_font_family || style.font_family || "");
  setValue("pin-badge-bg", style.badge_background || "#ffffff");
  setValue("pin-badge-fill", style.badge_fill || "#111111");
  setValue("pin-badge-border", style.badge_border_color || "#111111");
  setValue("pin-badge-font-size", style.badge_font_size || 34);
  setValue("pin-badge-width", style.badge_width || 450);
  setValue("pin-badge-height", style.badge_height || 56);
  setValue("pin-badge-radius", style.badge_radius || 14);
  setChecked("pin-accent-enabled", !!style.accent_enabled);
  setValue("pin-accent-text", style.accent_text || "");
  setValue("pin-accent-fill", style.accent_fill || "#ffd21a");
  setValue("pin-accent-stroke", style.accent_stroke_fill || "#111111");
  setValue("pin-accent-font-size", style.accent_font_size || 116);
  updateTemplateColorLabels();
}

async function savePinTemplateStyle() {
  const templateId = activePinTemplateId();
  if (!templateId) return toast("Choose a pin template first.");
  const payload = {};
  payload.template_id = templateId;
  const addValue = (field, id) => {
    if (document.getElementById(id)) payload[field] = valOrEmpty(id) || undefined;
  };
  const addNumber = (field, id) => {
    if (document.getElementById(id)) payload[field] = Number(valOrEmpty(id) || 0);
  };
  const addBoolean = (field, id) => {
    if (document.getElementById(id)) payload[field] = checked(id);
  };
  addValue("band_background", "pin-band-color");
  addValue("band_border_color", "pin-band-border-color");
  addNumber("band_border_width", "pin-band-border-width");
  addNumber("band_radius", "pin-band-radius");
  addValue("font_color", "pin-font-color");
  addValue("font_family", "pin-font-family");
  addNumber("font_size_max", "pin-font-size-max");
  addNumber("font_size_min", "pin-font-size-min");
  addNumber("max_lines", "pin-max-lines");
  addNumber("max_words", "pin-max-words");
  addBoolean("uppercase", "pin-uppercase");
  addValue("stroke_fill", "pin-stroke-color");
  addNumber("stroke_width", "pin-stroke-width");
  addValue("shadow_fill", "pin-shadow-color");
  addBoolean("badge_enabled", "pin-badge-enabled");
  addValue("badge_text", "pin-badge-text");
  addValue("badge_font_family", "pin-badge-font-family");
  addValue("badge_background", "pin-badge-bg");
  addValue("badge_fill", "pin-badge-fill");
  addValue("badge_border_color", "pin-badge-border");
  addNumber("badge_font_size", "pin-badge-font-size");
  addNumber("badge_width", "pin-badge-width");
  addNumber("badge_height", "pin-badge-height");
  addNumber("badge_radius", "pin-badge-radius");
  addBoolean("accent_enabled", "pin-accent-enabled");
  addValue("accent_text", "pin-accent-text");
  addValue("accent_fill", "pin-accent-fill");
  addValue("accent_stroke_fill", "pin-accent-stroke");
  addNumber("accent_font_size", "pin-accent-font-size");
  const saveUrl = appState.editingWebsiteId && valOrEmpty("site-pin-template")
    ? `/websites/${encodeURIComponent(appState.editingWebsiteId)}/pin-template-style`
    : `/pin-templates/${encodeURIComponent(templateId)}/style`;
  const savedStyle = await api(saveUrl, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  if (appState.editingWebsiteId) {
    const index = appState.websites.findIndex(w => String(w.id) === String(appState.editingWebsiteId));
    if (index >= 0) {
      appState.websites[index] = {
        ...appState.websites[index],
        pin_template: templateId,
        pin_template_style: payload,
      };
    }
  }
  toast(appState.editingWebsiteId ? "Website template style saved." : "Template saved.");
  const freshBaseUrl = appState.editingWebsiteId
    ? `/websites/${encodeURIComponent(appState.editingWebsiteId)}/pin-template-preview`
    : pinTemplatePreviewUrl();
  const freshUrl = `${freshBaseUrl}?refresh=true&t=${Date.now()}`;
  const img = document.getElementById("pin-template-preview-img");
  const link = document.getElementById("pin-template-preview-link");
  const open = document.getElementById("open-pin-template-preview");
  if (img) img.src = freshUrl;
  if (link) link.href = freshUrl;
  if (open) open.href = freshUrl;
}

function pinTemplateEditorFields() {
  return `
    <div class="template-style-editor template-admin-editor">
      <div class="form-row">
        <label class="color-field"><span>Band background</span><input id="pin-band-color" type="color" value="#ff585d"><code data-value-for="pin-band-color">#ff585d</code></label>
        <label class="color-field"><span>Band border</span><input id="pin-band-border-color" type="color" value="#ffffff"><code data-value-for="pin-band-border-color">#ffffff</code></label>
      </div>
      <div class="form-row">
        <label class="color-field"><span>Font color</span><input id="pin-font-color" type="color" value="#ffffff"><code data-value-for="pin-font-color">#ffffff</code></label>
        <label class="color-field"><span>Text stroke</span><input id="pin-stroke-color" type="color" value="#111111"><code data-value-for="pin-stroke-color">#111111</code></label>
      </div>
      <div class="form-row">
        <label class="field">Font family<input id="pin-font-family" placeholder="Lilita One"></label>
        <label class="field">Shadow color<input id="pin-shadow-color" type="color" value="#111111"></label>
      </div>
      <div class="form-row">
        <label class="field">Max font size<input id="pin-font-size-max" type="number" min="24" max="180"></label>
        <label class="field">Min font size<input id="pin-font-size-min" type="number" min="18" max="120"></label>
      </div>
      <div class="form-row">
        <label class="field">Max lines<input id="pin-max-lines" type="number" min="1" max="4"></label>
        <label class="field">Max words<input id="pin-max-words" type="number" min="1" max="16"></label>
      </div>
      <div class="form-row">
        <label class="field">Stroke width<input id="pin-stroke-width" type="number" min="0" max="12"></label>
        <label class="field">Band border width<input id="pin-band-border-width" type="number" min="0" max="24"></label>
      </div>
      <div class="form-row">
        <label class="field">Band radius<input id="pin-band-radius" type="number" min="0" max="120"></label>
        <label class="field checkbox-field"><input id="pin-uppercase" type="checkbox"> Uppercase title</label>
      </div>
      <hr class="soft-divider">
      <div class="form-row">
        <label class="field checkbox-field"><input id="pin-badge-enabled" type="checkbox"> Show badge</label>
        <label class="field">Badge text<input id="pin-badge-text" placeholder="easy recipe"></label>
      </div>
      <div class="form-row">
        <label class="color-field"><span>Badge background</span><input id="pin-badge-bg" type="color" value="#ffffff"><code data-value-for="pin-badge-bg">#ffffff</code></label>
        <label class="color-field"><span>Badge text color</span><input id="pin-badge-fill" type="color" value="#111111"><code data-value-for="pin-badge-fill">#111111</code></label>
      </div>
      <div class="form-row">
        <label class="color-field"><span>Badge border</span><input id="pin-badge-border" type="color" value="#111111"><code data-value-for="pin-badge-border">#111111</code></label>
        <label class="field">Badge font size<input id="pin-badge-font-size" type="number" min="12" max="90"></label>
      </div>
      <div class="form-row">
        <label class="field">Badge width<input id="pin-badge-width" type="number" min="80" max="900"></label>
        <label class="field">Badge height<input id="pin-badge-height" type="number" min="24" max="140"></label>
      </div>
      <div class="form-row">
        <label class="field">Badge radius<input id="pin-badge-radius" type="number" min="0" max="80"></label>
      </div>
      <hr class="soft-divider">
      <div class="form-row">
        <label class="field checkbox-field"><input id="pin-accent-enabled" type="checkbox"> Show accent text</label>
        <label class="field">Accent text<input id="pin-accent-text" placeholder="Delicious"></label>
      </div>
      <div class="form-row">
        <label class="color-field"><span>Accent color</span><input id="pin-accent-fill" type="color" value="#ffd21a"><code data-value-for="pin-accent-fill">#ffd21a</code></label>
        <label class="color-field"><span>Accent stroke</span><input id="pin-accent-stroke" type="color" value="#111111"><code data-value-for="pin-accent-stroke">#111111</code></label>
      </div>
      <label class="field">Accent font size<input id="pin-accent-font-size" type="number" min="24" max="220"></label>
    </div>
  `;
}

async function renderPinTemplates() {
  appState.pinTemplates = (await api("/pin-templates").catch(() => ({ templates: [] }))).templates || [];
  const options = appState.pinTemplates.map(t => `<option value="${esc(t.id)}">${esc(t.label)}</option>`).join("");
  const current = appState.pinTemplates[0]?.id || "";
  app.innerHTML = `
    <div class="grid wide-left">
      <section class="panel">
        <div class="panel-head"><h2>Template Editor</h2><span class="mini muted">${appState.pinTemplates.length} templates</span></div>
        <div class="panel-body">
          <label class="field">Choose Template</label>
          <select id="template-admin-select">${options}</select>
          ${pinTemplateEditorFields()}
          <div class="toolbar" style="margin-top:14px">
            <button class="btn primary" id="save-template-admin-style">Save Template</button>
            <a class="btn" id="open-pin-template-preview" href="/pin-templates/${encodeURIComponent(current)}/preview" target="_blank" rel="noopener">Open Preview</a>
          </div>
        </div>
      </section>
      <section class="panel">
        <div class="panel-head"><h2>Preview</h2><button class="btn" id="refresh-template-preview">Refresh</button></div>
        <div class="panel-body preview-stage">
          <a id="pin-template-preview-link" href="/pin-templates/${encodeURIComponent(current)}/preview" target="_blank" rel="noopener">
            <img id="pin-template-preview-img" src="/pin-templates/${encodeURIComponent(current)}/preview" alt="Pinterest pin template preview" class="template-preview-large">
          </a>
        </div>
      </section>
    </div>
  `;
  if (current) document.getElementById("template-admin-select").value = current;
  updatePinTemplatePreview();
  document.getElementById("template-admin-select").addEventListener("change", updatePinTemplatePreview);
  document.getElementById("save-template-admin-style").addEventListener("click", savePinTemplateStyle);
  document.getElementById("refresh-template-preview").addEventListener("click", () => {
    const url = `${pinTemplatePreviewUrl()}?refresh=true&t=${Date.now()}`;
    document.getElementById("pin-template-preview-img").src = url;
    document.getElementById("pin-template-preview-link").href = url;
    document.getElementById("open-pin-template-preview").href = url;
  });
  document.querySelectorAll(".template-admin-editor input").forEach(input => input.addEventListener("input", updateTemplateColorLabels));
}

async function saveWebsite() {
  const editingSite = appState.websites.find(w => String(w.id) === String(appState.editingWebsiteId));
  const storedSite = storedWebsiteFor(editingSite);
  const previousBaseUrl = normaliseWebsiteUrl(editingSite?.base_url);
  const payload = {
    name: val("site-name"),
    base_url: val("site-url"),
    site_type: val("site-type") || "wordpress",
    username: val("site-user"),
    publish_endpoint: val("site-publish-endpoint"),
    api_enabled: !!document.getElementById("site-api-enabled")?.checked,
    pin_template: val("site-pin-template"),
    publish_status: val("site-publish-status"),
  };
  const password = payload.site_type === "html_static" ? val("site-api-key") : val("site-pass");
  if (payload.site_type === "html_static") {
    if (password) payload.api_key = password;
  } else if (password || !appState.editingWebsiteId) {
    payload.password = password;
  }

  if (appState.editingWebsiteId) {
    await api(`/websites/${appState.editingWebsiteId}`, { method: "PUT", body: JSON.stringify(payload) });
    if (previousBaseUrl && previousBaseUrl !== normaliseWebsiteUrl(payload.base_url)) {
      forgetWebsite(editingSite);
    }
    rememberWebsite({ ...payload, password: password || storedSite?.password || "" });
    toast("Website updated.");
  } else {
    await api("/websites", { method: "POST", body: JSON.stringify(payload) });
    rememberWebsite({ ...payload, password });
    toast("Website saved.");
  }
  appState.editingWebsiteId = null;
  appState.websiteEditorOpen = false;
  renderWebsites();
}

async function renderApiKeys() {
  const keys = (await api("/api-keys").catch(() => ({ keys: [] }))).keys || [];
  app.innerHTML = `<div class="grid cols-2">${keys.map(k => `
    <section class="panel">
      <div class="panel-head"><h2>${esc(k.service)}</h2>${statusBadge(k.configured ? "configured" : "missing")}</div>
      <div class="panel-body grid">
        <p class="muted">${esc(k.description)}</p>
        <div class="code">${esc(k.env_var)} = ${esc(k.masked || "not set")}</div>
        <input id="key-${k.id}" type="password" placeholder="Paste new value">
        <div class="toolbar"><button class="btn primary" data-key-save="${k.id}">Save</button><button class="btn" data-key-test="${k.id}">Test Connection</button></div>
        <div id="key-result-${k.id}" class="mini muted"></div>
      </div>
    </section>`).join("")}</div>`;
}

async function renderPrompts() {
  const prompts = (await api("/prompts").catch(() => ({ prompts: [] }))).prompts || [];
  app.innerHTML = `<div class="grid cols-2">${prompts.map(p => `
    <section class="panel">
      <div class="panel-head"><h2>${esc(p.name)}</h2><span class="mini muted">${fmtDate(p.updated_at)}</span></div>
      <div class="panel-body">
        <p class="muted">${esc(p.description)}</p>
        <p class="mini muted">Variables: ${(p.variables || []).map(v => `{${esc(v)}}`).join(", ")}</p>
        <textarea id="prompt-${p.id}">${esc(p.content)}</textarea>
        <div class="toolbar" style="margin-top:10px"><button class="btn primary" data-prompt-save="${p.id}">Save</button><button class="btn" data-prompt-test="${p.id}">Test</button><button class="btn" data-prompt-history="${p.id}">History</button></div>
        <div id="prompt-result-${p.id}" class="logbox" style="display:none; min-height:100px"></div>
      </div>
    </section>`).join("")}</div>`;
}

async function renderLogs() {
  const [health, logs] = await Promise.all([api("/status").catch(() => ({})), api("/logs?limit=200").catch(() => ({ logs: [] }))]);
  app.innerHTML = `
    <div class="grid cols-4">
      ${metric("Celery", health.celery_status || "unknown", "worker")}
      ${metric("Redis", health.redis_status || "unknown", "broker")}
      ${metric("Database", health.db_status || "unknown", "SQLite")}
      ${metric("Queued", health.queued_jobs ?? 0, "pending jobs")}
    </div>
    <section class="panel" style="margin-top:16px">
      <div class="panel-head"><h2>Live Logs</h2><button class="btn" id="refresh-logs">Refresh</button></div>
      <div class="panel-body"><div class="logbox">${renderLogLines((logs.logs || []).reverse())}</div></div>
    </section>
  `;
  document.getElementById("refresh-logs").addEventListener("click", renderLogs);
}

function renderLogLines(logs) {
  if (!logs.length) return `<div class="empty">No logs yet.</div>`;
  return logs.map(l => `<div class="log-line log-${esc(l.level)}"><span>${fmtDate(l.created_at)}</span><span>${esc(l.level)}</span><span>${esc(l.service)}</span><span>${esc(l.message)}</span></div>`).join("");
}

async function renderSettings() {
  const [settings, presetsRes] = await Promise.all([
    api("/settings").catch(() => ({ settings: {} })),
    api("/settings/legal-presets").catch(() => ({ presets: {} })),
  ]);
  const s = settings.settings || {};
  const presets = presetsRes.presets || {};

  const PRESET_ORDER = [
    ["content_blog",   "Content Blog Default"],
    ["recipe_blog",    "Recipe Blog Default"],
    ["affiliate_blog", "Affiliate Blog Default"],
    ["health_blog",    "Health Blog Default"],
    ["finance_blog",   "Finance Blog Default"],
    ["tech_blog",      "Tech Blog Default"],
    ["eu_gdpr",        "EU GDPR Default"],
    ["us_standard",    "US Standard Default"],
  ];

  app.innerHTML = `
    <div class="grid cols-2">
      ${settingsPanel("execution", s.execution || {})}
      ${settingsPanel("storage", s.storage || {})}
      ${settingsPanel("notifications", s.notifications || {})}
      ${settingsPanel("security", s.security || {})}
    </div>

    <section class="panel" style="margin-top:16px">
      <div class="panel-head">
        <div><h2>Legal Presets</h2><p class="panel-subtitle">Named presets auto-applied during website generation. Click Edit to customize any preset.</p></div>
      </div>
<div class="panel-body" style="padding:0">
         ${PRESET_ORDER.map(([pid, label]) => `
           <div style="display:flex;align-items:center;justify-content:space-between;padding:14px 24px;border-bottom:1px solid var(--border)">
             <div>
               <strong style="font-size:0.9rem;color:var(--text)">${esc(label)}</strong>
               <p class="mini muted" style="margin-top:2px;color:var(--muted)">${_presetSummary(presets[pid] || {})}</p>
             </div>
             <button class="btn btn-sm" data-edit-preset="${pid}" style="flex-shrink:0;padding:6px 14px;background:rgba(15,23,42,.86);color:var(--text);border:1px solid var(--border);border-radius:7px;font-size:0.78rem;font-weight:600;cursor:pointer">Edit</button>
           </div>`).join("")}
       </div>
    </section>

    <section class="panel danger-zone" style="margin-top:16px">
      <div class="panel-head"><h2>Danger Zone</h2></div>
      <div class="panel-body toolbar">
        <button class="btn danger" data-danger="reset-stats">Reset Stats</button>
        <button class="btn" data-danger="export-data">Export Data</button>
        <button class="btn danger" data-danger="delete-all-jobs">Delete All Jobs</button>
      </div>
    </section>
  `;

  // Wire Edit buttons — reuse the legal modal, but in "preset edit" mode
  document.querySelectorAll("[data-edit-preset]").forEach(btn => {
    btn.addEventListener("click", () => {
      const pid = btn.dataset.editPreset;
      const label = PRESET_ORDER.find(([id]) => id === pid)?.[1] || pid;
      _ensureLegalModal();
      // Override modal title and save behaviour for preset editing
      document.querySelector("#legal-modal-overlay strong").textContent = `Edit: ${label}`;
      document.querySelector("#legal-modal-overlay .mini.muted").textContent = "Changes are saved as the default definition for this preset.";
      _openLegalModal(presets[pid] || {});
// Replace save handler with preset-save version
       const saveBtn = document.getElementById("lm-save");
       const newSave = saveBtn.cloneNode(true);
       saveBtn.parentNode.replaceChild(newSave, saveBtn);
       newSave.textContent = "Save Preset";
       newSave.style.background = "linear-gradient(180deg,var(--purple),var(--cyan))";
       newSave.style.boxShadow = "0 10px 22px rgba(99,102,241,.22)";
       newSave.addEventListener("mouseenter", () => {
         newSave.style.filter = "brightness(1.04)";
       });
       newSave.addEventListener("mouseleave", () => {
         newSave.style.filter = "none";
       });
       newSave.addEventListener("click", async () => {
        _saveLegalModal();
        const payload = { ..._legalModalOverrides };
        try {
          await api(`/settings/legal-presets/${pid}`, { method: "PUT", body: JSON.stringify(payload) });
          toast(`"${label}" preset saved.`);
          _closeLegalModal();
          _legalModalOverrides = {};
          renderSettings();
        } catch (e) {
          toast(e.message || "Save failed.", true);
        }
      });
    });
  });
}

function _presetSummary(preset) {
  const on = [];
  if (preset.uses_analytics)       on.push("analytics");
  if (preset.uses_ads)             on.push("ads");
  if (preset.uses_affiliate_links) on.push("affiliate links");
  if (preset.displays_health_info) on.push("health info");
  if (preset.displays_nutrition_info) on.push("nutrition info");
  if (preset.displays_financial_info) on.push("financial info");
  if (preset.displays_tech_advice) on.push("tech advice");
  if (preset.stores_data_in_eu)    on.push("EU data storage");
  if (preset.has_dpo)              on.push("DPO");
  return on.length ? on.join(", ") : "standard content blog settings";
}

// ── Niche default categories (mirrors backend DEFAULT_NICHE_CATEGORIES) ────
const NICHE_DEFAULT_CATEGORIES = {
  "recipes":         ["Breakfast", "Lunch", "Dinner", "Dessert", "Healthy", "Quick Meals"],
  "health":          ["Wellness", "Nutrition", "Supplements", "Fitness"],
  "fitness":         ["Workouts", "Nutrition", "Weight Loss", "Mindfulness"],
  "finance":         ["Investing", "Budgeting", "Saving", "Credit Cards"],
  "technology":      ["AI", "Software", "Gadgets", "Tutorials"],
  "travel":          ["Destinations", "Tips", "Budget Travel", "Food"],
  "education":       ["Study Tips", "Career", "Online Learning", "Productivity"],
  "general blog":    ["Lifestyle", "Personal", "Reviews", "Tips"],
  "product reviews": ["Electronics", "Home", "Beauty", "Fashion"],
  "business":        ["Entrepreneurship", "Marketing", "Finance", "Productivity"],
};

// Mutable categories state for the chip input
let _builderCategories = [];

function _renderCategoryChips() {
  const container = document.getElementById("builder-cat-chips");
  if (!container) return;
  container.innerHTML = _builderCategories.map((cat, i) =>
    `<span style="display:inline-flex;align-items:center;gap:5px;background:#f0ebe6;border:1px solid #d4c5bb;border-radius:20px;padding:4px 10px;font-size:0.8rem;font-weight:600;color:#3b1a08">
      ${esc(cat)}
      <button type="button" onclick="_removeCategory(${i})" style="background:none;border:none;cursor:pointer;color:#9b7a6a;font-size:0.9rem;padding:0;line-height:1" aria-label="Remove ${esc(cat)}">×</button>
    </span>`
  ).join("");
}

function _addCategory(value) {
  const v = value.trim();
  if (!v || _builderCategories.includes(v)) return;
  _builderCategories.push(v);
  _renderCategoryChips();
}

function _removeCategory(index) {
  _builderCategories.splice(index, 1);
  _renderCategoryChips();
}

function _setNicheCategories(niche) {
  const defaults = NICHE_DEFAULT_CATEGORIES[niche] || NICHE_DEFAULT_CATEGORIES["recipes"];
  _builderCategories = [...defaults];
  _renderCategoryChips();
}

// Maps niche value → preset id (mirrors backend NICHE_TO_PRESET)
const NICHE_TO_PRESET = {
  "recipes": "recipe_blog",
  "health": "health_blog",
  "fitness": "health_blog",
  "finance": "finance_blog",
  "technology": "tech_blog",
  "product reviews": "affiliate_blog",
};

// ── Theme system ──────────────────────────────────────────────────────────────

const PRESET_THEMES = [
  { name: "Warm Editorial",     niche: "recipes",   primary: "#C96A3D", secondary: "#F7F1EB", accent: "#8B4513", background: "#FFFFFF", surface: "#FFF8F3", textPrimary: "#1F1F1F", textSecondary: "#5C5C5C", border: "#E8D8CC" },
  { name: "Sage Healthy",       niche: "health",    primary: "#6B8E6B", secondary: "#F3F8F2", accent: "#4D6B4D", background: "#FFFFFF", surface: "#F3F8F2", textPrimary: "#1A211A", textSecondary: "#526052", border: "#D0E0CE" },
  { name: "Midnight Authority",  niche: "finance",   primary: "#1E3A5F", secondary: "#F5F7FA", accent: "#0F172A", background: "#FFFFFF", surface: "#F5F7FA", textPrimary: "#0F172A", textSecondary: "#475569", border: "#CBD5E1" },
  { name: "Dessert Rose",        niche: "desserts",  primary: "#D9778A", secondary: "#FFF5F7", accent: "#A84F63", background: "#FFFFFF", surface: "#FFF5F7", textPrimary: "#1F1016", textSecondary: "#6B4050", border: "#F0C8D0" },
  { name: "Minimal Charcoal",    niche: "editorial", primary: "#2D2D2D", secondary: "#FAFAFA", accent: "#111111", background: "#FFFFFF", surface: "#F6F6F6", textPrimary: "#111111", textSecondary: "#555555", border: "#E0E0E0" },
];

const NICHE_DEFAULT_THEME = {
  "recipes": "Warm Editorial",
  "desserts": "Dessert Rose",
  "health": "Sage Healthy",
  "fitness": "Sage Healthy",
  "finance": "Midnight Authority",
  "technology": "Midnight Authority",
  "travel": "Minimal Charcoal",
  "education": "Midnight Authority",
  "general blog": "Minimal Charcoal",
  "product reviews": "Minimal Charcoal",
  "business": "Midnight Authority",
};

// Holds the currently selected theme state
let selectedTheme = { ...PRESET_THEMES[0] };
let _activeTheme = selectedTheme;
let _customThemeEditing = false;

function _themeByName(name) {
  return PRESET_THEMES.find(t => t.name === name) || PRESET_THEMES[0];
}

function _setActiveTheme(theme) {
  selectedTheme = { ...theme };
  _activeTheme = selectedTheme;
  _renderThemeCards();
  _renderThemePreview();
}

function _getThemeConfig() {
  return { ..._activeTheme };
}

function _renderThemeCards() {
  const container = document.getElementById("builder-theme-cards");
  if (!container) return;
  container.innerHTML = PRESET_THEMES.map(t => {
    const isActive = _activeTheme.name === t.name && !_customThemeEditing;
    return `<button type="button" class="theme-card${isActive ? " theme-card-active" : ""}"
        data-theme-name="${esc(t.name)}"
        aria-pressed="${isActive ? "true" : "false"}"
        title="${esc(t.name)}">
      <div class="theme-swatch" style="display:flex;gap:3px;margin-bottom:6px">
        <span style="width:18px;height:18px;border-radius:4px;background:${t.primary};display:inline-block"></span>
        <span style="width:18px;height:18px;border-radius:4px;background:${t.accent};display:inline-block"></span>
        <span style="width:18px;height:18px;border-radius:4px;border:1px solid ${t.border};background:${t.surface};display:inline-block"></span>
      </div>
      <div style="font-size:0.75rem;font-weight:700;line-height:1.3;color:var(--text);overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;word-break:break-word;width:100%">${esc(t.name)}</div>
      <div style="font-size:0.67rem;color:var(--muted);margin-top:1px;overflow:hidden;display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;width:100%">${esc(t.niche)}</div>
    </button>`;
  }).join("") +
  `<button type="button" class="theme-card${_customThemeEditing ? " theme-card-active" : ""}"
      data-theme-action="custom"
      aria-pressed="${_customThemeEditing ? "true" : "false"}"
      title="Custom theme">
    <div style="display:flex;gap:3px;margin-bottom:6px">
      <span style="width:18px;height:18px;border-radius:4px;background:linear-gradient(135deg,#f43f5e,#8b5cf6,#06b6d4);display:inline-block"></span>
    </div>
    <div style="font-size:0.75rem;font-weight:700;color:var(--text)">Custom</div>
    <div style="font-size:0.67rem;color:var(--muted);margin-top:1px">pick colors</div>
  </button>`;
}

function _bindThemeCardSelector() {
  const container = document.getElementById("builder-theme-cards");
  if (!container || container.dataset.bound === "true") return;
  container.dataset.bound = "true";
  container.addEventListener("click", (event) => {
    const card = event.target.closest(".theme-card");
    if (!card || !container.contains(card)) return;
    event.preventDefault();
    if (card.dataset.themeAction === "custom") {
      _openCustomTheme();
      return;
    }
    const themeName = card.dataset.themeName;
    if (themeName) _selectPresetTheme(themeName);
  });
}

function _selectPresetTheme(name) {
  _customThemeEditing = false;
  _setActiveTheme(_themeByName(name));
  const panel = document.getElementById("builder-custom-theme-panel");
  if (panel) panel.style.display = "none";
}

function _openCustomTheme() {
  _customThemeEditing = true;
  _renderThemeCards();
  const panel = document.getElementById("builder-custom-theme-panel");
  if (!panel) return;
  panel.style.display = "block";
  // Render color pickers
  const colorFields = [
    ["primary","Primary"],["secondary","Secondary"],["accent","Accent"],
    ["background","Background"],["surface","Surface"],["textPrimary","Text Primary"],
    ["textSecondary","Text Secondary"],["border","Border"],
  ];
  const grid = document.getElementById("builder-custom-color-grid");
  if (grid) {
    grid.innerHTML = colorFields.map(([f, label]) => `
      <div style="display:flex;flex-direction:column;align-items:center;gap:4px">
        <input type="color" id="ct-${f}" value="${_activeTheme[f] || "#000000"}"
          style="width:44px;height:44px;padding:2px;border:1px solid var(--border);border-radius:8px;cursor:pointer;background:none">
        <span style="font-size:0.65rem;color:var(--muted);text-align:center">${label}</span>
      </div>`).join("");
  }
  _renderThemePreview();
}

function _applyCustomTheme() {
  const fields = ["primary","secondary","accent","background","surface","textPrimary","textSecondary","border"];
  const custom = { name: "Custom" };
  fields.forEach(f => {
    const el = document.getElementById(`ct-${f}`);
    custom[f] = el?.value || _activeTheme[f];
  });
  _setActiveTheme(custom);
}

function _renderThemePreview() {
  const preview = document.getElementById("builder-theme-preview");
  if (!preview) return;
  const t = _activeTheme;
  preview.dataset.themeName = t.name || "Preview";
  preview.style.cssText = `
    background:${t.background};border:1px solid ${t.border};border-radius:10px;
    overflow:hidden;font-family:Georgia,serif;transition:all .2s
  `;
  preview.innerHTML = `
    <div style="background:${t.primary};padding:8px 14px;display:flex;align-items:center;justify-content:space-between">
      <strong style="color:#fff;font-size:0.82rem;letter-spacing:-.01em">${esc(_activeTheme.name || "Preview")}</strong>
      <span style="color:rgba(255,255,255,.8);font-size:0.7rem">nav nav nav</span>
    </div>
    <div style="padding:12px 14px;background:${t.surface}">
      <div style="font-size:0.65rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:${t.primary};margin-bottom:4px">Latest Recipe</div>
      <div style="font-size:0.92rem;font-weight:700;color:${t.textPrimary};line-height:1.2;margin-bottom:4px">Homemade Pasta with Sauce</div>
      <div style="font-size:0.72rem;color:${t.textSecondary};line-height:1.4;margin-bottom:8px">A rich and comforting classic made from scratch.</div>
      <div style="display:inline-block;background:${t.primary};color:#fff;font-size:0.68rem;font-weight:700;padding:4px 10px;border-radius:999px">Read Recipe</div>
    </div>
    <div style="padding:6px 14px;border-top:1px solid ${t.border};background:${t.secondary}">
      <span style="font-size:0.65rem;color:${t.textSecondary}">Category &nbsp;·&nbsp; Category &nbsp;·&nbsp; Category</span>
    </div>
  `;
}

function _syncThemeToNiche(niche) {
  if (_customThemeEditing) return;
  const themeName = NICHE_DEFAULT_THEME[niche] || "Warm Editorial";
  _setActiveTheme(_themeByName(themeName));
}

// Holds any field overrides set via the "Customize" modal (preset_id = "custom")
let _legalModalOverrides = {};
// All preset definitions fetched from backend
let _legalPresets = {};

// ── Legal Customization Modal ───────────────────────────────────────────────

function _legalModalHtml() {
  const cb = (id, label) =>
    `<label style="display:flex;align-items:center;gap:7px;font-size:0.85rem;cursor:pointer;min-width:200px;color:var(--text)">
       <input type="checkbox" id="lm-${id}" style="accent-color:var(--purple)"> ${label}
     </label>`;
  return `
    <div id="legal-modal-overlay" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:200;align-items:center;justify-content:center;padding:20px">
      <div style="background:var(--panel);border-radius:14px;box-shadow:0 24px 70px rgba(0,0,0,.42);width:100%;max-width:680px;max-height:90vh;display:flex;flex-direction:column;overflow:hidden;border:1px solid var(--border)">
        <div style="padding:20px 24px 16px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;flex-shrink:0;background:linear-gradient(180deg,rgba(255,255,255,.03),rgba(255,255,255,.012))">
          <div>
            <strong style="font-size:1rem;color:var(--text)">Customize Legal &amp; Privacy</strong>
            <p class="mini muted" style="margin-top:3px;color:var(--muted)">These override the selected preset for this generation only.</p>
          </div>
          <button id="lm-close" style="background:rgba(15,23,42,.86);border:none;border-radius:8px;width:32px;height:32px;font-size:1rem;cursor:pointer;color:var(--text);display:flex;align-items:center;justify-content:center;border:1px solid var(--border)">✕</button>
        </div>
        <div style="padding:20px 24px;overflow-y:auto;flex:1">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px 24px;margin-bottom:18px">
            <div><label class="field" style="margin-bottom:4px">Business Type</label><input id="lm-business_type" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.875rem;background:var(--panel-soft);color:var(--text)" placeholder="content blog"></div>
            <div><label class="field" style="margin-bottom:4px">Country</label><input id="lm-country" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.875rem;background:var(--panel-soft);color:var(--text)" placeholder="United States"></div>
            <div><label class="field" style="margin-bottom:4px">Data Controller Name</label><input id="lm-data_controller_name" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.875rem;background:var(--panel-soft);color:var(--text)" placeholder=""></div>
            <div><label class="field" style="margin-bottom:4px">Data Controller Email</label><input id="lm-data_controller_email" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.875rem;background:var(--panel-soft);color:var(--text)" placeholder="privacy@example.com"></div>
            <div><label class="field" style="margin-bottom:4px">DPO Email</label><input id="lm-dpo_email" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.875rem;background:var(--panel-soft);color:var(--text)" placeholder="dpo@example.com"></div>
            <div><label class="field" style="margin-bottom:4px">Minimum Age</label><input id="lm-minimum_age" type="number" min="1" max="120" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.875rem;background:var(--panel-soft);color:var(--text)" placeholder="13"></div>
            <div><label class="field" style="margin-bottom:4px">Affiliate Programs</label><input id="lm-affiliate_programs" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.875rem;background:var(--panel-soft);color:var(--text)" placeholder="Amazon Associates, ShareASale"></div>
            <div><label class="field" style="margin-bottom:4px">Company Name</label><input id="lm-company_name" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.875rem;background:var(--panel-soft);color:var(--text)" placeholder="Optional"></div>
          </div>
          <p class="field" style="margin-bottom:8px;color:var(--muted)">Data Collection</p>
          <div style="display:flex;flex-wrap:wrap;gap:8px 16px;margin-bottom:16px">
            ${cb("collects_names","Collects names")}
            ${cb("collects_emails","Collects emails")}
            ${cb("collects_ip_addresses","Collects IP addresses")}
            ${cb("uses_contact_forms","Uses contact forms")}
            ${cb("uses_analytics","Uses analytics")}
            ${cb("uses_cookies","Uses cookies")}
            ${cb("uses_newsletter","Uses newsletter")}
            ${cb("allows_comments","Allows comments")}
            ${cb("uses_ads","Uses ads")}
            ${cb("uses_affiliate_links","Uses affiliate links")}
            ${cb("allows_user_content","Allows user content")}
            ${cb("allows_user_generated_content","Allows user-generated content")}
            ${cb("has_user_accounts","Has user accounts")}
            ${cb("sells_products","Sells products")}
            ${cb("publishes_product_reviews","Publishes product reviews")}
            ${cb("links_to_third_party_sites","Links to third-party sites")}
          </div>
          <p class="field" style="margin-bottom:8px;color:var(--muted)">Content &amp; Disclaimers</p>
          <div style="display:flex;flex-wrap:wrap;gap:8px 16px;margin-bottom:16px">
            ${cb("displays_health_info","Displays health info")}
            ${cb("displays_nutrition_info","Displays nutrition info")}
            ${cb("displays_financial_info","Displays financial info")}
            ${cb("displays_tech_advice","Displays tech advice")}
            ${cb("displays_legal_info","Displays legal info")}
            ${cb("has_dpo","Has DPO")}
          </div>
          <p class="field" style="margin-bottom:8px;color:var(--muted)">Legal Basis (GDPR)</p>
          <div style="display:flex;flex-wrap:wrap;gap:8px 16px;margin-bottom:16px">
            ${cb("legal_basis_consent","Consent")}
            ${cb("legal_basis_legitimate_interest","Legitimate interest")}
            ${cb("legal_basis_contract","Contract")}
            ${cb("legal_basis_legal_obligation","Legal obligation")}
            ${cb("stores_data_in_eu","Stores data in EU")}
            ${cb("uses_third_party_processors","Uses third-party processors")}
          </div>
          <p class="field" style="margin-bottom:8px;color:var(--muted)">Page Overrides <span class="mini muted" style="color:var(--muted)">(leave blank to auto-generate)</span></p>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
            <div><label class="field" style="margin-bottom:4px">Privacy Policy</label><textarea id="lm-privacy_policy" style="width:100%;height:80px;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.85rem;resize:vertical;background:var(--panel-soft);color:var(--text)" placeholder="Paste custom privacy policy text…"></textarea></div>
            <div><label class="field" style="margin-bottom:4px">Terms of Use</label><textarea id="lm-terms" style="width:100%;height:80px;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.85rem;resize:vertical;background:var(--panel-soft);color:var(--text)" placeholder="Paste custom terms text…"></textarea></div>
          </div>
          <label class="field" style="margin:10px 0 4px">Disclaimer</label>
          <textarea id="lm-disclaimer" style="width:100%;height:70px;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.85rem;resize:vertical;background:var(--panel-soft);color:var(--text)" placeholder="Paste custom disclaimer…"></textarea>
          <label class="field" style="margin:10px 0 4px">Effective Date</label>
          <input id="lm-effective_date" style="padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.875rem;max-width:220px;background:var(--panel-soft);color:var(--text)" placeholder="May 13, 2026">
        </div>
        <div style="padding:14px 24px;border-top:1px solid var(--border);display:flex;gap:10px;justify-content:flex-end;flex-shrink:0">
          <button id="lm-cancel" style="padding:10px 18px;background:rgba(15,23,42,.86);color:var(--text);border:1px solid var(--border);border-radius:9px;font-size:0.875rem;font-weight:600;cursor:pointer">Cancel</button>
          <button id="lm-save" style="padding:10px 18px;background:linear-gradient(180deg,var(--purple),var(--cyan));color:#fff;border:none;border-radius:9px;font-size:0.875rem;font-weight:600;cursor:pointer;box-shadow:0 10px 22px rgba(99,102,241,.22)">Apply Customization</button>
        </div>
      </div>
    </div>`;
}

function _ensureLegalModal() {
  if (!document.getElementById("legal-modal-overlay")) {
    document.body.insertAdjacentHTML("beforeend", _legalModalHtml());
    const closeBtn = document.getElementById("lm-close");
    const cancelBtn = document.getElementById("lm-cancel");
    const saveBtn = document.getElementById("lm-save");
    
    closeBtn.addEventListener("click", _closeLegalModal);
    cancelBtn.addEventListener("click", _closeLegalModal);
    
    // Close button hover
    closeBtn.addEventListener("mouseenter", () => {
      closeBtn.style.background = "rgba(255,255,255,.08)";
    });
    closeBtn.addEventListener("mouseleave", () => {
      closeBtn.style.background = "rgba(15,23,42,.86)";
    });
    
    document.getElementById("legal-modal-overlay").addEventListener("click", e => {
      if (e.target === document.getElementById("legal-modal-overlay")) _closeLegalModal();
    });
    saveBtn.addEventListener("click", _saveLegalModal);
    
    // Cancel button hover
    cancelBtn.addEventListener("mouseenter", () => {
      cancelBtn.style.background = "rgba(31,41,55,.94)";
      cancelBtn.style.borderColor = "rgba(129,140,248,.28)";
    });
    cancelBtn.addEventListener("mouseleave", () => {
      cancelBtn.style.background = "rgba(15,23,42,.86)";
      cancelBtn.style.borderColor = "var(--border)";
    });
    
    // Save button hover
    saveBtn.addEventListener("mouseenter", () => {
      saveBtn.style.filter = "brightness(1.04)";
    });
    saveBtn.addEventListener("mouseleave", () => {
      saveBtn.style.filter = "none";
    });
  }
}

function _closeLegalModal() {
  document.getElementById("legal-modal-overlay").style.display = "none";
}

function _openLegalModal(presetFields) {
  _ensureLegalModal();
  // Populate fields from presetFields (current preset or saved overrides)
  const src = Object.keys(_legalModalOverrides).length ? _legalModalOverrides : presetFields;
  const textFields = ["business_type","country","data_controller_name","data_controller_email",
    "dpo_email","minimum_age","affiliate_programs","company_name","privacy_policy","terms",
    "disclaimer","effective_date"];
  for (const f of textFields) {
    const el = document.getElementById(`lm-${f}`);
    if (el) el.value = src[f] ?? "";
  }
  const boolFields = ["collects_names","collects_emails","collects_ip_addresses","uses_contact_forms",
    "uses_analytics","uses_cookies","uses_newsletter","allows_comments","uses_ads","uses_affiliate_links",
    "allows_user_content","allows_user_generated_content","has_user_accounts","sells_products",
    "publishes_product_reviews","links_to_third_party_sites","displays_health_info","displays_nutrition_info",
    "displays_financial_info","displays_tech_advice","displays_legal_info","has_dpo",
    "legal_basis_consent","legal_basis_legitimate_interest","legal_basis_contract",
    "legal_basis_legal_obligation","stores_data_in_eu","uses_third_party_processors"];
  for (const f of boolFields) {
    const el = document.getElementById(`lm-${f}`);
    if (el) el.checked = !!src[f];
  }
  document.getElementById("legal-modal-overlay").style.display = "flex";
}

function _saveLegalModal() {
  const textFields = ["business_type","country","data_controller_name","data_controller_email",
    "dpo_email","minimum_age","affiliate_programs","company_name","privacy_policy","terms",
    "disclaimer","effective_date"];
  const boolFields = ["collects_names","collects_emails","collects_ip_addresses","uses_contact_forms",
    "uses_analytics","uses_cookies","uses_newsletter","allows_comments","uses_ads","uses_affiliate_links",
    "allows_user_content","allows_user_generated_content","has_user_accounts","sells_products",
    "publishes_product_reviews","links_to_third_party_sites","displays_health_info","displays_nutrition_info",
    "displays_financial_info","displays_tech_advice","displays_legal_info","has_dpo",
    "legal_basis_consent","legal_basis_legitimate_interest","legal_basis_contract",
    "legal_basis_legal_obligation","stores_data_in_eu","uses_third_party_processors"];
  _legalModalOverrides = {};
  for (const f of textFields) {
    const el = document.getElementById(`lm-${f}`);
    if (el) _legalModalOverrides[f] = f === "minimum_age" ? Number(el.value) || 13 : el.value.trim();
  }
  for (const f of boolFields) {
    const el = document.getElementById(`lm-${f}`);
    if (el) _legalModalOverrides[f] = el.checked;
  }
  // Switch preset selector to "custom"
  const sel = document.getElementById("builder-legal-preset");
  if (sel) sel.value = "custom";
  _updatePresetBadge("custom");
  _closeLegalModal();
}

function _updatePresetBadge(presetId) {
  const badge = document.getElementById("builder-preset-badge");
  if (!badge) return;
  if (presetId === "custom") {
    badge.textContent = "Customized";
    badge.style.color = "var(--purple)";
  } else {
    badge.textContent = "Auto-applied";
    badge.style.color = "var(--muted)";
  }
}

async function renderWebsiteBuilder() {
  _legalModalOverrides = {};
  _legalPresets = await api("/settings/legal-presets").then(r => r.presets).catch(() => ({}));

  app.innerHTML = `
    <div class="grid wide-left">
      <section class="panel">
        <div class="panel-head">
          <div>
            <h2>One Click Website Builder</h2>
            <p class="panel-subtitle">Fill in the essentials and generate a complete website with legal pages in seconds.</p>
          </div>
          <button class="btn primary" id="generate-website">Generate Website</button>
        </div>
        <div class="panel-body">
          <div class="form-row">
            <div><label class="field">Website Name <span class="required">*</span></label><input id="builder-website-name" placeholder="Yara Bites"></div>
            <div><label class="field">Chef / Author Name <span class="required">*</span></label><input id="builder-chef-name" placeholder="Chef Yara"></div>
          </div>
          <div class="form-row" style="margin-top:14px">
            <div><label class="field">Domain</label><input id="builder-domain" placeholder="example.com"></div>
            <div><label class="field">Contact Email</label><input id="builder-contact-email" placeholder="hello@example.com"></div>
          </div>
          <div class="form-row" style="margin-top:14px">
            <div>
              <label class="field">Niche</label>
              <select id="builder-niche-type">
                <option value="recipes" selected>Recipes</option>
                <option value="health">Health</option>
                <option value="fitness">Fitness</option>
                <option value="finance">Finance</option>
                <option value="technology">Technology</option>
                <option value="travel">Travel</option>
                <option value="education">Education</option>
                <option value="general blog">General blog</option>
                <option value="product reviews">Product reviews</option>
                <option value="business">Business</option>
              </select>
            </div>
            <div><label class="field">Country</label><input id="builder-country" placeholder="United States, EU, UK..."></div>
          </div>

          <!-- Categories -->
          <div style="margin-top:18px">
            <label class="field" style="margin-bottom:8px">Categories <span class="mini muted">(auto-suggested from niche, edit freely)</span></label>
            <div id="builder-cat-chips" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;min-height:30px"></div>
            <div style="display:flex;gap:8px">
              <input id="builder-cat-input" placeholder="Add a category…" style="flex:1;padding:7px 11px;border:1px solid #d4c5bb;border-radius:7px;font-size:0.875rem"
                onkeydown="if(event.key==='Enter'){event.preventDefault();_addCategory(this.value);this.value=''}">
              <button type="button" onclick="_addCategory(document.getElementById('builder-cat-input').value);document.getElementById('builder-cat-input').value=''"
                style="padding:7px 14px;background:#f3ede8;color:#3b1a08;border:1px solid #d4c5bb;border-radius:7px;font-size:0.82rem;font-weight:600;cursor:pointer;white-space:nowrap">
                + Add
              </button>
            </div>
          </div>

<!-- Legal Configuration row -->
           <div style="margin-top:18px;padding:14px 16px;background:rgba(15,23,42,.62);border:1px solid var(--border);border-radius:10px;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap">
             <div style="display:flex;align-items:center;gap:12px;flex:1;min-width:220px">
               <div>
                 <label class="field" style="margin-bottom:4px">Legal Configuration</label>
                 <select id="builder-legal-preset" style="padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.875rem;background:var(--panel-soft);min-width:200px;color:var(--text)"><option value="recipe_blog">Recipe Blog Default</option>
                   <option value="content_blog">Content Blog Default</option>
                   <option value="affiliate_blog">Affiliate Blog Default</option>
                   <option value="health_blog">Health Blog Default</option>
                   <option value="finance_blog">Finance Blog Default</option>
                   <option value="tech_blog">Tech Blog Default</option>
                   <option value="eu_gdpr">EU GDPR Default</option>
                   <option value="us_standard">US Standard Default</option>
                   <option value="custom">Custom</option>
                 </select>
               </div>
               <span id="builder-preset-badge" class="mini muted" style="margin-top:18px;color:var(--muted)">Auto-applied</span>
             </div>
<button id="builder-customize-legal" style="padding:8px 16px;background:rgba(15,23,42,.86);color:var(--text);border:1px solid var(--border);border-radius:9px;font-size:0.82rem;font-weight:600;cursor:pointer;white-space:nowrap;flex-shrink:0;box-shadow:0 1px 2px rgba(0,0,0,.18)">
               Customize Advanced Legal Settings
             </button>
          </div>

          <div class="form-row" style="margin-top:18px">
            <div><label class="field">Tagline</label><input id="builder-tagline" placeholder="Simple recipes that work."></div>
            <div><label class="field">Homepage Headline</label><input id="builder-headline" placeholder="Simple Recipes That Work"></div>
          </div>
          <label class="field" style="margin-top:14px">Hero Text</label>
          <textarea id="builder-hero-text" placeholder="Every recipe is tested, practical, and made for real home kitchens."></textarea>
          <label class="field" style="margin-top:14px">About Chef / About Us</label>
          <textarea id="builder-about-text" placeholder="Tell readers who you are, what kind of recipes you publish, and why they can trust your kitchen."></textarea>
          <div class="form-row" style="margin-top:14px">
            <div>
              <label class="field">Chef / Hero Image</label>
              <input id="builder-chef-image" type="file" accept="image/*">
              <p class="mini muted" style="margin:6px 0 0">Used in home, about, and sidebar areas.</p>
            </div>
            <div>
              <label class="field">Website Logo</label>
              <input id="builder-logo-image" type="file" accept="image/*">
              <p class="mini muted" style="margin:6px 0 0">Shown in the site header.</p>
            </div>
          </div>
          <label class="field" style="margin-top:14px">Favicon</label>
          <input id="builder-favicon-image" type="file" accept="image/png,image/jpeg,image/webp,image/gif,image/svg+xml,image/x-icon,image/vnd.microsoft.icon">

<!-- Social Media Links -->
           <details style="margin-top:20px">
             <summary style="cursor:pointer;font-size:0.82rem;font-weight:700;letter-spacing:.4px;color:var(--muted);padding:10px 0;border-top:1px solid var(--border);list-style:none;display:flex;align-items:center;gap:6px;user-select:none">
               ▶ Social Media Links <span class="mini muted" style="font-weight:400;margin-left:4px">(optional — shown in header &amp; footer)</span>
             </summary>
             <div style="padding-top:12px;display:grid;grid-template-columns:1fr 1fr;gap:10px">
               <div><label class="field" style="margin-bottom:3px">📌 Pinterest</label>
                 <input id="builder-social-pinterest" type="url" placeholder="https://pinterest.com/yourprofile" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.85rem;background:var(--panel-soft);color:var(--text)"></div>
               <div><label class="field" style="margin-bottom:3px">📷 Instagram</label>
                 <input id="builder-social-instagram" type="url" placeholder="https://instagram.com/yourhandle" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.85rem;background:var(--panel-soft);color:var(--text)"></div>
               <div><label class="field" style="margin-bottom:3px">📘 Facebook</label>
                 <input id="builder-social-facebook" type="url" placeholder="https://facebook.com/yourpage" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.85rem;background:var(--panel-soft);color:var(--text)"></div>
               <div><label class="field" style="margin-bottom:3px">🐦 X / Twitter</label>
                 <input id="builder-social-twitter" type="url" placeholder="https://x.com/yourhandle" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.85rem;background:var(--panel-soft);color:var(--text)"></div>
               <div><label class="field" style="margin-bottom:3px">🎵 TikTok</label>
                 <input id="builder-social-tiktok" type="url" placeholder="https://tiktok.com/@yourhandle" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.85rem;background:var(--panel-soft);color:var(--text)"></div>
               <div><label class="field" style="margin-bottom:3px">▶ YouTube</label>
                 <input id="builder-social-youtube" type="url" placeholder="https://youtube.com/@yourchannel" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.85rem;background:var(--panel-soft);color:var(--text)"></div>
<div><label class="field" style="margin-bottom:3px">💼 LinkedIn</label>
                  <input id="builder-social-linkedin" type="url" placeholder="https://linkedin.com/in/yourprofile" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.85rem;background:var(--panel-soft);color:var(--text)"></div>
              </div>
            </details>

            <div style="margin-top:16px;padding:12px 14px;background:rgba(15,23,42,.62);border:1px solid var(--border);border-radius:9px">
              <label class="field" style="margin-bottom:4px">Social Icons Placement</label>
              <select id="builder-social-placement" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:9px;font-size:0.875rem;background:var(--panel-soft);color:var(--text)">
                <option value="footer_only">Footer only (default)</option>
                <option value="header_only">Header only</option>
                <option value="both">Both header and footer</option>
                <option value="hidden">Hidden (no icons)</option>
              </select>
              <p class="mini muted" style="margin:6px 0 0;color:var(--muted)">Where to display social media icons on the generated website.</p>
            </div>

          <!-- Website Theme -->
          <div style="margin-top:22px;padding:18px;background:rgba(15,23,42,.52);border:1px solid var(--border);border-radius:12px">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:8px">
              <div>
                <label class="field" style="margin-bottom:0">Website Theme</label>
                <p class="mini muted" style="margin:3px 0 0;color:var(--muted)">Auto-selected from niche. Click any card to override.</p>
              </div>
            </div>
            <div id="builder-theme-cards" style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px"></div>

            <!-- Live preview -->
            <div style="margin-bottom:10px">
              <label class="field" style="margin-bottom:6px;font-size:0.72rem">Live Preview</label>
              <div id="builder-theme-preview" style="border-radius:10px;overflow:hidden;min-height:80px"></div>
            </div>

            <!-- Custom color picker (hidden by default) -->
            <div id="builder-custom-theme-panel" style="display:none;padding-top:14px;border-top:1px solid var(--border)">
              <label class="field" style="margin-bottom:10px">Custom Colors</label>
              <div id="builder-custom-color-grid" style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px"></div>
              <button type="button" onclick="_applyCustomTheme()"
                style="margin-top:12px;padding:7px 16px;background:var(--purple);color:#fff;border:none;border-radius:8px;font-size:0.82rem;font-weight:600;cursor:pointer">
                Apply Custom Colors
              </button>
            </div>
          </div>

            <div id="website-builder-message" class="form-message info" style="margin-top:16px">Fill in the required fields, then hit Generate Website.</div>
        </div>
      </section>
      <section class="panel">
        <div class="panel-head"><h2>Output</h2><span class="mini muted">static preview</span></div>
        <div class="panel-body" id="website-builder-output">
          <div class="empty">No website generated yet.</div>
        </div>
      </section>
    </div>
  `;

  // Auto-select preset and categories based on niche
  const nicheSelect = document.getElementById("builder-niche-type");
  const legalSelect = document.getElementById("builder-legal-preset");

  // Initialize theme
  _customThemeEditing = false;
  _setActiveTheme(_themeByName(NICHE_DEFAULT_THEME[nicheSelect.value] || "Warm Editorial"));
  _bindThemeCardSelector();
  _renderThemeCards();
  _renderThemePreview();

  _setNicheCategories(nicheSelect.value);

  function syncPresetToNiche() {
    const mapped = NICHE_TO_PRESET[nicheSelect.value];
    if (mapped) {
      legalSelect.value = mapped;
      _legalModalOverrides = {};
      _updatePresetBadge(mapped);
    }
    _setNicheCategories(nicheSelect.value);
    _syncThemeToNiche(nicheSelect.value);
  }
  syncPresetToNiche();
  nicheSelect.addEventListener("change", syncPresetToNiche);

  legalSelect.addEventListener("change", () => {
    if (legalSelect.value !== "custom") _legalModalOverrides = {};
    _updatePresetBadge(legalSelect.value);
  });

  document.getElementById("builder-customize-legal").addEventListener("click", () => {
    const currentPreset = _legalPresets[legalSelect.value] || {};
    _openLegalModal(currentPreset);
  });

  document.getElementById("generate-website").addEventListener("click", generateWebsitePreview);
}

function websiteBuilderValue(id) {
  return document.getElementById(id)?.value.trim() || "";
}

function websiteBuilderFile(id) {
  return document.getElementById(id)?.files?.[0] || null;
}

function readWebsiteBuilderImage(id, label) {
  const file = websiteBuilderFile(id);
  if (!file) return Promise.resolve("");
  if (!file.type.startsWith("image/")) {
    return Promise.reject(new Error(`${label} must be an image file.`));
  }
  if (file.size > 5 * 1024 * 1024) {
    return Promise.reject(new Error(`${label} must be 5 MB or smaller.`));
  }
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error(`${label} could not be read.`));
    reader.readAsDataURL(file);
  });
}

async function generateWebsitePreview() {
  const button = document.getElementById("generate-website");
  const message = document.getElementById("website-builder-message");
  const output = document.getElementById("website-builder-output");

  const selectedPreset = document.getElementById("builder-legal-preset")?.value || "content_blog";
  const isCustom = selectedPreset === "custom";

  const payload = {
    website_name: websiteBuilderValue("builder-website-name"),
    chef_name: websiteBuilderValue("builder-chef-name"),
    domain: websiteBuilderValue("builder-domain"),
    contact_email: websiteBuilderValue("builder-contact-email"),
    country: websiteBuilderValue("builder-country"),
    niche_type: websiteBuilderValue("builder-niche-type"),
    tagline: websiteBuilderValue("builder-tagline"),
    headline: websiteBuilderValue("builder-headline"),
    hero_text: websiteBuilderValue("builder-hero-text"),
    about_text: websiteBuilderValue("builder-about-text"),
    legal_preset: isCustom ? "custom" : selectedPreset,
    // When custom, spread all modal overrides as individual fields
    ...(isCustom ? _legalModalOverrides : {}),
    // Categories
    categories: _builderCategories.length ? [..._builderCategories] : undefined,
    // Social links (only include non-empty values)
    social_pinterest: websiteBuilderValue("builder-social-pinterest") || undefined,
    social_instagram: websiteBuilderValue("builder-social-instagram") || undefined,
    social_facebook:  websiteBuilderValue("builder-social-facebook")  || undefined,
    social_twitter:   websiteBuilderValue("builder-social-twitter")   || undefined,
    social_tiktok:    websiteBuilderValue("builder-social-tiktok")    || undefined,
    social_youtube:   websiteBuilderValue("builder-social-youtube")   || undefined,
    social_linkedin:  websiteBuilderValue("builder-social-linkedin")  || undefined,
    // Social placement (footer_only, header_only, both, hidden)
    social_placement: document.getElementById("builder-social-placement")?.value || "footer_only",
    // Theme config — selected preset or custom colors
    theme_config: _getThemeConfig(),
  };
  if (!payload.website_name || !payload.chef_name) {
    message.className = "form-message error";
    message.textContent = "Website name and chef name are required.";
    return;
  }
  button.disabled = true;
  button.textContent = "Generating...";
  message.className = "form-message info";
  message.textContent = "Preparing images...";
  try {
    payload.chef_image = await readWebsiteBuilderImage("builder-chef-image", "Chef image");
    payload.logo_image = await readWebsiteBuilderImage("builder-logo-image", "Website logo");
    payload.favicon_image = await readWebsiteBuilderImage("builder-favicon-image", "Favicon");
    message.textContent = "Generating website files...";
    const result = await api("/website-builder/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    message.className = "form-message success";
    message.textContent = "Website generated successfully.";
    output.innerHTML = `
      <div class="artifact-grid" style="grid-template-columns:1fr">
        <a class="artifact-card" href="${esc(result.preview_url)}" target="_blank">
          <div class="artifact-img" style="display:grid;place-items:center;background:linear-gradient(135deg,#fffaf2,#667a43);color:#253224;font-size:2rem;font-weight:900;">${esc(normalizeSiteName(payload.website_name).slice(0, 1).toUpperCase())}</div>
          <strong>${esc(normalizeSiteName(payload.website_name))}</strong>
          <span class="mini muted">Open website preview</span>
        </a>
      </div>
      <div class="kv-list" style="margin-top:16px">
        <div class="kv"><span class="k">Preview</span><span class="v"><a href="${esc(result.preview_url)}" target="_blank">${esc(result.preview_url)}</a></span></div>
        <div class="kv"><span class="k">Folder</span><span class="v">${esc(result.path)}</span></div>
        <div class="kv"><span class="k">Pages</span><span class="v">${esc((result.pages || []).join(", "))}</span></div>
      </div>
    `;
  } catch (e) {
    message.className = "form-message error";
    message.textContent = e.message || "Website generation failed.";
  } finally {
    button.disabled = false;
    button.textContent = "Generate Website";
  }
}

function settingsPanel(section, data) {
  return `<section class="panel"><div class="panel-head"><h2>${esc(section)}</h2><button class="btn primary" data-settings-save="${esc(section)}">Save</button></div><div class="panel-body"><textarea id="settings-${esc(section)}" class="code">${esc(JSON.stringify(data, null, 2))}</textarea></div></section>`;
}

function val(id) { return document.getElementById(id).value.trim(); }

async function render() {
  clearInterval(appState.timer);
  renderNav();
  setTitle();
  app.innerHTML = `<div class="empty">Loading...</div>`;
  const path = routePath();
  try {
    if (path === "/") await renderDashboard();
    else if (path === "/jobs-page") await renderJobs();
    else if (path === "/new-batch") await renderNewBatch();
    else if (path === "/websites-page") await renderWebsites();
    else if (path === "/website-builder") await renderWebsiteBuilder();
    else if (path === "/api-keys-page") await renderApiKeys();
    else if (path === "/prompts-page") await renderPrompts();
    else if (path === "/logs-page") await renderLogs();
    else if (path === "/settings-page") await renderSettings();
    attachPageEvents();
  } catch (e) {
    app.innerHTML = `<div class="panel"><div class="panel-body"><strong>Unable to load page.</strong><p class="muted">${esc(e.message)}</p></div></div>`;
  }
}

function attachPageEvents() {
  // Most controls are handled by delegated document-level events because tables
  // and detail panes are frequently re-rendered.
}

function startSocket() {
  const dot = document.getElementById("socket-dot");
  const label = document.getElementById("socket-label");
  try {
    const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/jobs`);
    ws.onopen = () => { dot.className = "dot ok"; label.textContent = "Live"; };
    ws.onmessage = event => {
      const data = JSON.parse(event.data);
      appState.stats = data.stats;
      appState.logs = data.logs || [];
    };
    ws.onerror = () => { dot.className = "dot bad"; label.textContent = "Polling"; };
    ws.onclose = () => {
      dot.className = "dot";
      label.textContent = "Polling";
      setTimeout(startSocket, 5000);
    };
  } catch (_) {
    dot.className = "dot";
    label.textContent = "Polling";
  }
}

document.addEventListener("click", async e => {
  const articlePreview = e.target.closest("[data-article-preview]");
  if (articlePreview && e.target.closest("summary")) {
    setTimeout(() => {
      const id = String(articlePreview.dataset.articlePreview || "");
      if (!id) return;
      if (articlePreview.open) appState.openArticlePreviews.add(id);
      else appState.openArticlePreviews.delete(id);
    }, 0);
    return;
  }
  const actionMenu = e.target.closest("[data-action-menu]");
  if (actionMenu) {
    e.preventDefault();
    e.stopPropagation();
    const id = actionMenu.dataset.actionMenu;
    const panel = document.querySelector(`[data-action-menu-panel="${CSS.escape(id)}"]`);
    const isOpen = panel?.classList.contains("open");
    document.querySelectorAll(".action-menu-panel.open").forEach(item => item.classList.remove("open"));
    document.querySelectorAll("[data-action-menu][aria-expanded='true']").forEach(item => item.setAttribute("aria-expanded", "false"));
    if (panel && !isOpen) {
      document.body.appendChild(panel);
      panel.dataset.portalMenu = "true";
      const rect = actionMenu.getBoundingClientRect();
      const menuWidth = 210;
      const menuHeight = 188;
      const spaceBelow = window.innerHeight - rect.bottom;
      const top = spaceBelow >= menuHeight + 16 ? rect.bottom + 8 : rect.top - menuHeight - 8;
      const left = Math.max(12, Math.min(window.innerWidth - menuWidth - 12, rect.right - menuWidth));
      panel.style.setProperty("--menu-top", `${Math.round(Math.max(12, top))}px`);
      panel.style.setProperty("--menu-left", `${Math.round(left)}px`);
      panel.classList.add("open");
      actionMenu.setAttribute("aria-expanded", "true");
    }
    return;
  }
  if (!e.target.closest(".action-menu-panel") && !e.target.closest("[data-action-menu]")) {
    document.querySelectorAll(".action-menu-panel.open").forEach(item => item.classList.remove("open"));
    document.querySelectorAll("[data-action-menu][aria-expanded='true']").forEach(item => item.setAttribute("aria-expanded", "false"));
  }
  if (e.target.closest("[data-job-checkbox]")) {
    const checkbox = e.target.closest("[data-job-checkbox]");
    if (checkbox.checked) {
      appState.selectedJobIds.add(String(checkbox.value));
    } else {
      appState.selectedJobIds.delete(String(checkbox.value));
    }
    updateSelectedJobsCount();
    return;
  }
  const route = e.target.closest("[data-route]");
  if (route) {
    e.preventDefault();
    navigate(route.dataset.route);
    return;
  }
  const job = e.target.closest("[data-job]");
  if (job) return showJob(job.dataset.job);
  const jobButton = e.target.closest("[data-job-action]");
  if (jobButton) return jobAction(jobButton.dataset.jobAction, jobButton.dataset.id);
  const refreshJob = e.target.closest("[data-refresh-job]");
  if (refreshJob) {
    await showJob(refreshJob.dataset.refreshJob);
    return toast("Job steps refreshed.");
  }
  const siteTest = e.target.closest("[data-site-test]");
  if (siteTest) {
    document.querySelectorAll(".action-menu-panel.open").forEach(item => item.classList.remove("open"));
    const res = await api(`/websites/${siteTest.dataset.siteTest}/test`, { method: "POST" });
    return toast(res.message || "Website tested.");
  }
  const siteSyncCategories = e.target.closest("[data-site-sync-categories]");
  if (siteSyncCategories) {
    document.querySelectorAll(".action-menu-panel.open").forEach(item => item.classList.remove("open"));
    siteSyncCategories.disabled = true;
    siteSyncCategories.textContent = "Syncing...";
    try {
      const res = await api(`/websites/${siteSyncCategories.dataset.siteSyncCategories}/sync-categories`, { method: "POST" });
      toast(res.message || "Categories synced.");
      return renderWebsites();
    } catch (error) {
      toast(error.message || "Category sync failed.");
      return;
    }
  }
  const siteEdit = e.target.closest("[data-site-edit]");
  if (siteEdit) {
    document.querySelectorAll(".action-menu-panel.open").forEach(item => item.classList.remove("open"));
    appState.editingWebsiteId = siteEdit.dataset.siteEdit;
    appState.websiteEditorOpen = true;
    return renderWebsites();
  }
  const siteDelete = e.target.closest("[data-site-delete]");
  if (siteDelete) {
    document.querySelectorAll(".action-menu-panel.open").forEach(item => item.classList.remove("open"));
    if (!confirm("Delete this website?")) return;
    const site = appState.websites.find(w => String(w.id) === String(siteDelete.dataset.siteDelete));
    await api(`/websites/${siteDelete.dataset.siteDelete}`, { method: "DELETE" });
    forgetWebsite(site);
    toast("Website deleted.");
    return renderWebsites();
  }
  const keySave = e.target.closest("[data-key-save]");
  if (keySave) {
    const id = keySave.dataset.keySave;
    await api(`/api-keys/${id}`, { method: "PUT", body: JSON.stringify({ value: val(`key-${id}`) }) });
    toast("API key saved.");
    return renderApiKeys();
  }
  const keyTest = e.target.closest("[data-key-test]");
  if (keyTest) {
    const id = keyTest.dataset.keyTest;
    const res = await api(`/api-keys/test/${id}`, { method: "POST" });
    document.getElementById(`key-result-${id}`).textContent = res.message;
    return;
  }
  const promptSave = e.target.closest("[data-prompt-save]");
  if (promptSave) {
    const id = promptSave.dataset.promptSave;
    await api(`/prompts/${id}`, { method: "PUT", body: JSON.stringify({ content: document.getElementById(`prompt-${id}`).value }) });
    return toast("Prompt saved.");
  }
  const promptTest = e.target.closest("[data-prompt-test]");
  if (promptTest) {
    const id = promptTest.dataset.promptTest;
    const res = await api(`/prompts/${id}/test`, { method: "POST", body: JSON.stringify({ keyword: "chocolate cake", website_name: "Demo Site", article_title: "Chocolate Cake", article_content: "Demo article content" }) });
    const box = document.getElementById(`prompt-result-${id}`);
    box.style.display = "block";
    box.textContent = res.output;
    return;
  }
  const promptHistory = e.target.closest("[data-prompt-history]");
  if (promptHistory) {
    const id = promptHistory.dataset.promptHistory;
    const res = await api(`/prompts/${id}/history`);
    const box = document.getElementById(`prompt-result-${id}`);
    box.style.display = "block";
    box.innerHTML = renderLogLines((res.history || []).map(h => ({ created_at: h.created_at, level: "info", service: "history", message: h.content.slice(0, 240) })));
    return;
  }
  const settingsSave = e.target.closest("[data-settings-save]");
  if (settingsSave) {
    const section = settingsSave.dataset.settingsSave;
    await api("/settings", { method: "PUT", body: JSON.stringify({ section, value: JSON.parse(document.getElementById(`settings-${section}`).value) }) });
    return toast("Settings saved.");
  }
  const danger = e.target.closest("[data-danger]");
  if (danger) {
    if (!confirm(`Run ${danger.dataset.danger}?`)) return;
    const res = await api(`/settings/danger/${danger.dataset.danger}`, { method: "POST" });
    toast(res.message || "Action complete.");
    return renderSettings();
  }
});
window.addEventListener("popstate", render);
document.getElementById("refresh-page")?.addEventListener("click", render);
render();
startSocket();
