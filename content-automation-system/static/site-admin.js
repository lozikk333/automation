const slug = location.pathname.split("/").filter(Boolean)[1] || "";
const apiBase = `/cms/sites/${encodeURIComponent(slug)}`;
const siteBase = `/generated-sites/${encodeURIComponent(slug)}`;
const app = document.getElementById("cms-app");
const titleEl = document.getElementById("cms-title");
const kickerEl = document.getElementById("cms-kicker");

let me = null;
let mediaItems = [];
let categories = [];

document.querySelectorAll("nav a").forEach(a => {
  a.href = `${siteBase}${a.getAttribute("href")}`;
});
const brand = document.querySelector(".cms-brand");
if (brand) brand.href = `${siteBase}/admin`;

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, ch => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[ch]));
}

function toast(message, tone = "ok") {
  let el = document.getElementById("cms-toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "cms-toast";
    document.body.appendChild(el);
  }
  el.className = `cms-toast ${tone}`;
  el.textContent = message;
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.remove("show"), 2600);
  requestAnimationFrame(() => el.classList.add("show"));
}

async function api(path, options = {}) {
  const res = await fetch(`${apiBase}${path}`, {
    credentials: "include",
    headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...options,
  });
  const text = await res.text();
  const data = text && !text.startsWith("email,") ? JSON.parse(text) : text;
  if (res.status === 401) throw new Error("AUTH_REQUIRED");
  if (!res.ok) throw new Error(data.detail || res.statusText);
  return data;
}

async function load(path, renderer) {
  app.innerHTML = `<div class="card empty">Loading...</div>`;
  try {
    await renderer(await api(path));
  } catch (error) {
    if (error.message === "AUTH_REQUIRED") return loginView();
    app.innerHTML = `<div class="card empty"><h2>Could not load</h2><p>${esc(error.message)}</p></div>`;
  }
}

function viewName() {
  const parts = location.pathname.split("/").filter(Boolean);
  const adminIndex = parts.indexOf("admin");
  return adminIndex >= 0 ? (parts[adminIndex + 1] || "dashboard") : "dashboard";
}

function setChrome(label) {
  titleEl.textContent = label;
  kickerEl.textContent = me?.website?.name || "Site Admin";
  document.querySelectorAll("nav a").forEach(a => a.classList.toggle("active", a.dataset.view === viewName()));
}

function empty(label) {
  return `<div class="card empty">${esc(label)}</div>`;
}

function loginView() {
  document.body.className = "login";
  document.body.innerHTML = `
    <form class="editor login-card" id="login-form">
      <div><p id="cms-kicker">Site Owner</p><h1>Sign in</h1><p class="muted">Use the owner account for this generated website.</p></div>
      <label>Email <input name="email" type="email" required autocomplete="email"></label>
      <label>Password <input name="password" type="password" required autocomplete="current-password"></label>
      <button class="primary" type="submit">Sign in</button>
    </form>`;
  document.getElementById("login-form").addEventListener("submit", async event => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const res = await fetch(`${apiBase}/auth/login`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(Object.fromEntries(form)),
    });
    if (!res.ok) return toast("Invalid email or password", "bad");
    location.reload();
  });
}

function go(view) {
  history.pushState({}, "", `${siteBase}/admin${view === "dashboard" ? "" : `/${view}`}`);
  boot();
}

function toolbar({ search = true, status = false, category = false, extra = "" } = {}) {
  return `<div class="toolbar">
    ${search ? `<input id="search" type="search" placeholder="Search">` : ""}
    ${status ? `<select id="status-filter"><option value="">All status</option><option>draft</option><option>published</option><option>archived</option><option>pending</option><option>approved</option><option>spam</option><option>trash</option></select>` : ""}
    ${category ? `<select id="category-filter"><option value="">All categories</option>${categories.map(c => `<option>${esc(c)}</option>`).join("")}</select>` : ""}
    ${extra}
  </div>`;
}

function bindFilters(callback) {
  ["search", "status-filter", "category-filter"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener(id === "search" ? "input" : "change", () => callback());
  });
}

async function dashboard() {
  setChrome("Dashboard");
  await load("/summary", async data => {
    app.innerHTML = `
      <div class="grid stats">
        ${[
          ["posts", "Posts"],
          ["pending_comments", "Pending Comments"],
          ["subscribers", "Subscribers"],
          ["media", "Media Items"],
        ].map(([key, label]) => `<article class="card stat"><span>${label}</span><strong>${esc(data[key])}</strong></article>`).join("")}
      </div>
      <div class="quick-actions">
        <button class="primary" data-go="posts">New post</button>
        <button data-go="media">Upload media</button>
        <button data-go="settings">Site settings</button>
        <a class="btn" href="${siteBase}/" target="_blank" rel="noopener">View site</a>
      </div>
      <div class="split">
        <section class="card"><h2>Recent Activity</h2>${data.activity?.length ? data.activity.map(a => `<p><strong>${esc(a.action)}</strong> ${esc(a.message)}<br><span class="muted">${esc(a.created_at)}</span></p>`).join("") : empty("No activity yet.")}</section>
        <section class="card"><h2>Latest Comments</h2>${data.latest_comments?.length ? data.latest_comments.map(c => `<p>${esc(c.content)}<br><span class="muted">${esc(c.author_name)} - ${esc(c.status)}</span></p>`).join("") : empty("No comments yet.")}</section>
      </div>
      <section class="card"><h2>Latest Subscribers</h2>${data.latest_subscribers?.length ? data.latest_subscribers.map(s => `<p>${esc(s.email)} <span class="muted">${esc(s.created_at)}</span></p>`).join("") : empty("No subscribers yet.")}</section>`;
    app.querySelectorAll("[data-go]").forEach(btn => btn.onclick = () => go(btn.dataset.go));
  });
}

async function loadShared() {
  const [catData, mediaData] = await Promise.all([
    api("/categories").catch(() => ({ categories: [] })),
    api("/media").catch(() => ({ items: [] })),
  ]);
  categories = catData.categories || [];
  mediaItems = mediaData.items || [];
}

function mediaOptions(selected) {
  return `<option value="">No featured image</option>${mediaItems.map(item => `<option value="${item.id}" ${String(selected || "") === String(item.id) ? "selected" : ""}>${esc(item.original_filename || item.filename)}</option>`).join("")}`;
}

function tagString(item) {
  return Array.isArray(item.tags) ? item.tags.join(", ") : (item.tags || "");
}

function contentEditor(item = {}, kind = "posts") {
  const isPost = kind === "posts";
  return `
    <form class="editor" data-editor="${kind}" data-id="${item.id || ""}">
      <div class="row">
        <label>Title <input name="title" value="${esc(item.title || "")}" required></label>
        <label>Slug <input name="slug" value="${esc(item.slug || "")}" placeholder="auto-generated"></label>
      </div>
      <div class="row">
        <label>Status <select name="status">${["draft", "published", "archived"].map(v => `<option value="${v}" ${item.status === v ? "selected" : ""}>${v}</option>`).join("")}</select></label>
        ${isPost ? `<label>Category <select name="category"><option value="">Uncategorized</option>${categories.map(c => `<option ${item.category === c ? "selected" : ""}>${esc(c)}</option>`).join("")}</select></label>` : `<span></span>`}
      </div>
      ${isPost ? `<div class="row"><label>Tags <input name="tags" value="${esc(tagString(item))}" placeholder="tag one, tag two"></label><label>Featured image <select name="featured_media_id">${mediaOptions(item.featured_media_id)}</select></label></div>` : ""}
      ${isPost ? `<label>Excerpt <input name="excerpt" value="${esc(item.excerpt || "")}"></label>` : ""}
      <label>Content <textarea name="content">${esc(item.content || "")}</textarea></label>
      ${isPost ? `<div class="row"><label>SEO title <input name="seo_title" value="${esc(item.seo_title || "")}"></label><label>Meta description <input name="meta_description" value="${esc(item.meta_description || "")}"></label></div>` : ""}
      <div class="form-actions"><button class="primary" type="submit">Save</button><button type="button" data-cancel>Cancel</button></div>
    </form>`;
}

async function contentList(kind, page = 1) {
  await loadShared();
  setChrome(kind === "posts" ? "Posts" : "Pages");
  const render = async () => {
    const search = encodeURIComponent(document.getElementById("search")?.value || "");
    const status = encodeURIComponent(document.getElementById("status-filter")?.value || "");
    const category = encodeURIComponent(document.getElementById("category-filter")?.value || "");
    const data = await api(`/${kind}?search=${search}&status=${status}&category=${category}&page=${page}&page_size=10`);
    document.getElementById("table-slot").innerHTML = data.items.length ? `
      <table><thead><tr><th>Title</th><th>Status</th>${kind === "posts" ? "<th>Category</th>" : ""}<th>Slug</th><th>Updated</th><th></th></tr></thead><tbody>
      ${data.items.map(item => `<tr>
        <td>${esc(item.title)}${kind === "posts" && item.excerpt ? `<br><span class="muted">${esc(item.excerpt)}</span>` : ""}</td>
        <td><span class="status">${esc(item.status)}</span></td>${kind === "posts" ? `<td>${esc(item.category || "-")}</td>` : ""}
        <td>${esc(item.slug)}</td><td>${esc(item.updated_at)}</td>
        <td class="actions"><button data-edit="${item.id}">Edit</button>${kind === "posts" ? ` <button data-duplicate="${item.id}">Duplicate</button>` : ""} <button class="danger" data-delete="${item.id}">Delete</button></td>
      </tr>`).join("")}</tbody></table>
      <div class="pagination"><button ${data.page <= 1 ? "disabled" : ""} data-page="${data.page - 1}">Previous</button><span>Page ${data.page} of ${data.pages}</span><button ${data.page >= data.pages ? "disabled" : ""} data-page="${data.page + 1}">Next</button></div>` : empty(`No ${kind} found.`);
    bindContentActions(kind, data.items);
  };
  app.innerHTML = `${toolbar({ status: true, category: kind === "posts", extra: `<button class="primary" id="new-item">New ${kind === "posts" ? "Post" : "Page"}</button>` })}
    ${kind === "posts" ? `<form class="editor compact" id="categories-form"><label>Categories <input name="categories" value="${esc(categories.join(", "))}"></label><button>Save categories</button></form>` : ""}
    <div id="editor-slot"></div><div id="table-slot"></div>`;
  bindFilters(render);
  document.getElementById("new-item").onclick = () => bindEditor({}, kind);
  const catForm = document.getElementById("categories-form");
  if (catForm) catForm.onsubmit = async event => {
    event.preventDefault();
    const next = new FormData(event.currentTarget).get("categories").split(",").map(v => v.trim()).filter(Boolean);
    await api("/categories", { method: "PUT", body: JSON.stringify({ categories: next }) });
    toast("Categories saved");
    contentList("posts");
  };
  await render();
}

function bindContentActions(kind, items) {
  app.querySelectorAll("[data-edit]").forEach(btn => btn.onclick = () => bindEditor(items.find(item => String(item.id) === btn.dataset.edit), kind));
  app.querySelectorAll("[data-delete]").forEach(btn => btn.onclick = async () => {
    if (!confirm("Delete this item?")) return;
    await api(`/${kind}/${btn.dataset.delete}`, { method: "DELETE" });
    toast("Deleted");
    contentList(kind);
  });
  app.querySelectorAll("[data-duplicate]").forEach(btn => btn.onclick = async () => {
    await api(`/posts/${btn.dataset.duplicate}/duplicate`, { method: "POST" });
    toast("Post duplicated");
    contentList("posts");
  });
  app.querySelectorAll("[data-page]").forEach(btn => btn.onclick = () => contentList(kind, Number(btn.dataset.page)));
}

function bindEditor(item, kind) {
  const slot = document.getElementById("editor-slot");
  slot.innerHTML = contentEditor(item, kind);
  slot.querySelector("[data-cancel]").onclick = () => slot.innerHTML = "";
  slot.querySelector("form").onsubmit = async event => {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = Object.fromEntries(new FormData(form));
    payload.tags = String(payload.tags || "").split(",").map(v => v.trim()).filter(Boolean);
    payload.featured_media_id = payload.featured_media_id ? Number(payload.featured_media_id) : null;
    const id = form.dataset.id;
    await api(`/${kind}${id ? `/${id}` : ""}`, { method: id ? "PUT" : "POST", body: JSON.stringify(payload) });
    toast("Saved");
    contentList(kind);
  };
}

async function comments() {
  setChrome("Comments");
  app.innerHTML = `${toolbar({ search: true, status: true })}<div id="table-slot"></div>`;
  const render = async () => {
    const search = encodeURIComponent(document.getElementById("search")?.value || "");
    const status = encodeURIComponent(document.getElementById("status-filter")?.value || "");
    const data = await api(`/comments?search=${search}&status=${status}`);
    document.getElementById("table-slot").innerHTML = data.items.length ? `<table><thead><tr><th>Commenter</th><th>Comment</th><th>Post</th><th>Status</th><th></th></tr></thead><tbody>
      ${data.items.map(item => `<tr><td>${esc(item.author_name)}<br><span class="muted">${esc(item.author_email)}<br>${esc(item.created_at)}</span></td><td>${esc(item.content)}${item.reply ? `<p class="reply">Reply: ${esc(item.reply)}</p>` : ""}</td><td>${esc(item.post_title || "-")}</td><td><span class="status">${esc(item.status)}</span></td><td class="actions">${["approved", "pending", "spam", "trash"].map(s => `<button data-id="${item.id}" data-status="${s}">${s}</button>`).join(" ")}<button data-reply="${item.id}">Reply</button><button class="danger" data-delete="${item.id}">Delete</button></td></tr>`).join("")}
    </tbody></table>` : empty("No comments found.");
    app.querySelectorAll("[data-status]").forEach(btn => btn.onclick = async () => {
      await api(`/comments/${btn.dataset.id}`, { method: "PUT", body: JSON.stringify({ status: btn.dataset.status }) });
      toast("Comment updated");
      render();
    });
    app.querySelectorAll("[data-reply]").forEach(btn => btn.onclick = async () => {
      const reply = prompt("Reply to this comment");
      if (reply === null) return;
      await api(`/comments/${btn.dataset.reply}`, { method: "PUT", body: JSON.stringify({ status: "approved", reply }) });
      toast("Reply saved");
      render();
    });
    app.querySelectorAll("[data-delete]").forEach(btn => btn.onclick = async () => {
      if (!confirm("Delete this comment?")) return;
      await api(`/comments/${btn.dataset.delete}`, { method: "DELETE" });
      toast("Comment deleted");
      render();
    });
  };
  bindFilters(render);
  render();
}

async function subscribers() {
  setChrome("Subscribers");
  app.innerHTML = `${toolbar({ extra: `<button id="export-csv">Export CSV</button>` })}<form class="editor compact" id="subscriber-form"><div class="row"><label>Email <input name="email" type="email" required></label><label>Name <input name="name"></label></div><button class="primary">Add subscriber</button></form><div id="table-slot"></div>`;
  const render = async () => {
    const search = encodeURIComponent(document.getElementById("search")?.value || "");
    const data = await api(`/subscribers?search=${search}`);
    document.getElementById("table-slot").innerHTML = data.items.length ? `<table><thead><tr><th>Email</th><th>Name</th><th>Status</th><th>Source</th><th>Date</th><th></th></tr></thead><tbody>${data.items.map(item => `<tr><td>${esc(item.email)}</td><td>${esc(item.name)}</td><td>${esc(item.status)}</td><td>${esc(item.source)}</td><td>${esc(item.created_at)}</td><td><button class="danger" data-delete="${item.id}">Delete</button></td></tr>`).join("")}</tbody></table>` : empty("No subscribers found.");
    app.querySelectorAll("[data-delete]").forEach(btn => btn.onclick = async () => {
      if (!confirm("Delete this subscriber?")) return;
      await api(`/subscribers/${btn.dataset.delete}`, { method: "DELETE" });
      toast("Subscriber deleted");
      render();
    });
  };
  bindFilters(render);
  document.getElementById("export-csv").onclick = () => location.href = `${apiBase}/subscribers/export`;
  document.getElementById("subscriber-form").onsubmit = async event => {
    event.preventDefault();
    await api("/subscribers", { method: "POST", body: JSON.stringify(Object.fromEntries(new FormData(event.currentTarget))) });
    event.currentTarget.reset();
    toast("Subscriber saved");
    render();
  };
  render();
}

async function media() {
  setChrome("Media");
  app.innerHTML = `${toolbar()}<form class="editor compact" id="upload-form"><div class="row"><label>Upload image <input name="file" type="file" accept="image/*" required></label><label>Alt text <input name="alt_text"></label></div><button class="primary">Upload</button></form><div id="media-slot"></div>`;
  const render = async () => {
    const search = encodeURIComponent(document.getElementById("search")?.value || "");
    const data = await api(`/media?search=${search}`);
    document.getElementById("media-slot").innerHTML = data.items.length ? `<div class="grid media-grid">${data.items.map(item => `<article class="card"><img src="${siteBase}/${esc(item.url)}" alt="${esc(item.alt_text)}"><p>${esc(item.original_filename || item.filename)}</p><div class="actions"><button data-copy="${siteBase}/${esc(item.url)}">Copy URL</button><button class="danger" data-delete="${item.id}">Delete</button></div></article>`).join("")}</div>` : empty("No media uploaded yet.");
    app.querySelectorAll("[data-copy]").forEach(btn => btn.onclick = async () => {
      await navigator.clipboard.writeText(location.origin + btn.dataset.copy);
      toast("URL copied");
    });
    app.querySelectorAll("[data-delete]").forEach(btn => btn.onclick = async () => {
      if (!confirm("Delete this media item?")) return;
      await api(`/media/${btn.dataset.delete}`, { method: "DELETE" });
      toast("Media deleted");
      render();
    });
  };
  bindFilters(render);
  document.getElementById("upload-form").onsubmit = async event => {
    event.preventDefault();
    await api("/media", { method: "POST", body: new FormData(event.currentTarget) });
    event.currentTarget.reset();
    toast("Media uploaded");
    render();
  };
  render();
}

function settingsFields(settings) {
  const simple = ["site_title", "tagline", "logo_url", "favicon_url", "theme", "primary_color", "typography", "seo_title", "seo_description", "analytics_id"];
  return `${simple.map(key => `<label>${esc(key.replaceAll("_", " "))}<input name="${key}" value="${esc(settings[key] || "")}"></label>`).join("")}
    <div class="row"><label>Newsletter <select name="newsletter_enabled"><option value="true">Enabled</option><option value="false" ${settings.newsletter_enabled === false ? "selected" : ""}>Disabled</option></select></label><label>Comments <select name="comments_enabled"><option value="true">Enabled</option><option value="false" ${settings.comments_enabled === false ? "selected" : ""}>Disabled</option></select></label></div>
    <label>Header menu <input name="header_menu" value="${esc((settings.header_menu || []).join(", "))}"></label>
    <label>Footer content <textarea name="footer_content">${esc(settings.footer_content || "")}</textarea></label>
    <label>Social links JSON <textarea name="social_links">${esc(JSON.stringify(settings.social_links || {}, null, 2))}</textarea></label>
    <label>Custom header code <textarea name="custom_header_code">${esc(settings.custom_header_code || "")}</textarea></label>
    <label>Custom footer code <textarea name="custom_footer_code">${esc(settings.custom_footer_code || "")}</textarea></label>`;
}

async function settings() {
  setChrome("Settings");
  await load("/settings", async data => {
    app.innerHTML = `<form class="editor" id="settings-form">${settingsFields(data.settings)}<button class="primary">Save settings</button></form>`;
    document.getElementById("settings-form").onsubmit = async event => {
      event.preventDefault();
      const payload = Object.fromEntries(new FormData(event.currentTarget));
      payload.newsletter_enabled = payload.newsletter_enabled === "true";
      payload.comments_enabled = payload.comments_enabled === "true";
      payload.header_menu = payload.header_menu.split(",").map(v => v.trim()).filter(Boolean);
      try { payload.social_links = JSON.parse(payload.social_links || "{}"); } catch (_) { return toast("Social links must be valid JSON", "bad"); }
      await api("/settings", { method: "PUT", body: JSON.stringify(payload) });
      toast("Settings saved");
      settings();
    };
  });
}

async function users() {
  setChrome("Users");
  await load("/users/profile", async data => {
    app.innerHTML = `<div class="split"><form class="editor" id="profile-form"><h2>Profile</h2><label>Email <input name="email" type="email" value="${esc(data.owner.email)}"></label><label>Display name <input name="display_name" value="${esc(data.owner.display_name)}"></label><button class="primary">Save profile</button></form><form class="editor" id="password-form"><h2>Change Password</h2><label>Current password <input name="current_password" type="password"></label><label>New password <input name="new_password" type="password"></label><button class="primary">Change password</button></form></div>`;
    document.getElementById("profile-form").onsubmit = async event => {
      event.preventDefault();
      await api("/users/profile", { method: "PUT", body: JSON.stringify(Object.fromEntries(new FormData(event.currentTarget))) });
      toast("Profile saved");
    };
    document.getElementById("password-form").onsubmit = async event => {
      event.preventDefault();
      await api("/users/password", { method: "PUT", body: JSON.stringify(Object.fromEntries(new FormData(event.currentTarget))) });
      event.currentTarget.reset();
      toast("Password changed");
    };
  });
}

async function domains() {
  setChrome("Domains");
  await load("/domains", async data => {
    app.innerHTML = `<form class="editor" id="domains-form"><p class="muted">Current generated URL: ${esc(data.base_url)}</p><label>Custom domain <input name="custom_domain" value="${esc(data.custom_domain)}"></label><label>Subdomain <input name="subdomain" value="${esc(data.subdomain)}"></label><label>SSL status <select name="ssl_status"><option>managed</option><option ${data.ssl_status === "pending" ? "selected" : ""}>pending</option><option ${data.ssl_status === "connected" ? "selected" : ""}>connected</option></select></label><button class="primary">Save domain settings</button></form>`;
    document.getElementById("domains-form").onsubmit = async event => {
      event.preventDefault();
      await api("/domains", { method: "PUT", body: JSON.stringify(Object.fromEntries(new FormData(event.currentTarget))) });
      toast("Domain settings saved");
    };
  });
}

async function appearance() {
  setChrome("Appearance");
  await load("/appearance", async data => {
    const a = data.appearance || {};
    app.innerHTML = `<form class="editor" id="appearance-form"><div class="row"><label>Theme <select name="theme">${["Warm Editorial", "Sage Healthy", "Midnight Authority", "Dessert Rose", "Minimal Charcoal"].map(t => `<option ${a.theme === t ? "selected" : ""}>${t}</option>`).join("")}</select></label><label>Primary color <input name="primary_color" type="color" value="${esc(a.primary_color || "#2f6b4f")}"></label></div><label>Typography <input name="typography" value="${esc(a.typography || "System Sans")}"></label><label>Logo URL <input name="logo_url" value="${esc(a.logo_url || "")}"></label><label>Favicon URL <input name="favicon_url" value="${esc(a.favicon_url || "")}"></label><label>Header menu <input name="header_menu" value="${esc((a.header_menu || []).join(", "))}"></label><label>Footer content <textarea name="footer_content">${esc(a.footer_content || "")}</textarea></label><button class="primary">Save appearance</button></form>`;
    document.getElementById("appearance-form").onsubmit = async event => {
      event.preventDefault();
      const payload = Object.fromEntries(new FormData(event.currentTarget));
      payload.header_menu = payload.header_menu.split(",").map(v => v.trim()).filter(Boolean);
      await api("/appearance", { method: "PUT", body: JSON.stringify(payload) });
      toast("Appearance saved");
    };
  });
}

async function integrations() {
  setChrome("Integrations");
  await load("/integrations", async data => {
    const i = data.integrations || {};
    app.innerHTML = `<form class="editor" id="integrations-form">${["mailchimp", "resend", "google_analytics", "meta_pixel"].map(key => `<label>${esc(key.replaceAll("_", " "))}<input name="${key}" value="${esc(i[key] || "")}"></label>`).join("")}<button class="primary">Save integrations</button></form>`;
    document.getElementById("integrations-form").onsubmit = async event => {
      event.preventDefault();
      await api("/integrations", { method: "PUT", body: JSON.stringify(Object.fromEntries(new FormData(event.currentTarget))) });
      toast("Integrations saved");
    };
  });
}

async function analytics() {
  setChrome("Analytics");
  await load("/analytics", async data => {
    const bars = data.page_views?.map(d => `<div class="bar"><span>${esc(d.day)}</span><strong style="width:${Math.max(2, Number(d.views) * 16)}px"></strong><em>${esc(d.views)}</em></div>`).join("") || "";
    app.innerHTML = `<div class="split"><section class="card"><h2>Page Views</h2>${bars || empty("No page views tracked yet.")}</section><section class="card"><h2>Top Posts</h2>${data.top_posts?.length ? data.top_posts.map(p => `<p>${esc(p.title)} <span class="muted">${esc(p.views)} views</span></p>`).join("") : empty("No top posts yet.")}</section></div><div class="split"><section class="card"><h2>Traffic Sources</h2>${data.traffic_sources?.length ? data.traffic_sources.map(s => `<p>${esc(s.source)} <strong>${esc(s.visits)}</strong></p>`).join("") : empty("No traffic sources yet.")}</section><section class="card"><h2>Growth</h2><p>Subscribers: ${esc(data.subscriber_growth?.reduce((n, x) => n + Number(x.subscribers || 0), 0) || 0)}</p><p>Comments: ${esc(data.comments_activity?.reduce((n, x) => n + Number(x.comments || 0), 0) || 0)}</p></section></div>`;
  });
}

async function backupRestore() {
  setChrome("Backup");
  app.innerHTML = `<div class="split"><section class="card"><h2>Backup Website Data</h2><button class="primary" id="download-backup">Download JSON backup</button></section><section class="card"><h2>Restore Backup</h2><textarea id="restore-json" placeholder="Paste backup JSON"></textarea><button id="restore-backup">Restore settings</button></section></div>`;
  document.getElementById("download-backup").onclick = async () => {
    const data = await api("/backup");
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${slug}-backup.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  };
  document.getElementById("restore-backup").onclick = async () => {
    if (!confirm("Restore settings from this backup?")) return;
    let payload;
    try { payload = JSON.parse(document.getElementById("restore-json").value || "{}"); } catch (_) { return toast("Invalid JSON", "bad"); }
    await api("/backup/restore", { method: "POST", body: JSON.stringify(payload) });
    toast("Backup restored");
  };
}

async function boot() {
  const logout = document.getElementById("logout");
  if (logout) logout.onclick = async () => {
    await api("/auth/logout", { method: "POST" }).catch(() => {});
    location.reload();
  };
  try {
    me = await api("/auth/me");
  } catch (error) {
    if (error.message === "AUTH_REQUIRED") return loginView();
    throw error;
  }
  const view = viewName();
  if (view === "posts") return contentList("posts");
  if (view === "pages") return contentList("pages");
  if (view === "comments") return comments();
  if (view === "subscribers") return subscribers();
  if (view === "media") return media();
  if (view === "settings") return settings();
  if (view === "analytics") return analytics();
  if (view === "users") return users();
  if (view === "domains") return domains();
  if (view === "appearance") return appearance();
  if (view === "integrations") return integrations();
  if (view === "backup-restore") return backupRestore();
  return dashboard();
}

window.addEventListener("popstate", boot);
boot().catch(error => {
  app.innerHTML = `<div class="card"><h2>Something went wrong</h2><p>${esc(error.message)}</p></div>`;
});
