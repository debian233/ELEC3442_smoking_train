const els = {
  tbody: document.getElementById('tbody'),

  className: document.getElementById('className'),
  minConf: document.getElementById('minConf'),
  limit: document.getElementById('limit'),
  apply: document.getElementById('apply'),
  toggleRefresh: document.getElementById('toggleRefresh'),

  previewImg: document.getElementById('previewImg'),
  openImage: document.getElementById('openImage'),
  emptyState: document.getElementById('emptyState'),
  previewMeta: document.getElementById('previewMeta'),

  statTotal: document.getElementById('statTotal'),
  statLatest: document.getElementById('statLatest'),
  liveIndicator: document.getElementById('liveIndicator'),
  liveText: document.getElementById('liveText'),
  lastUpdated: document.getElementById('lastUpdated'),
};

let autoRefresh = true;
let timer = null;
let lastSelectedId = null;

/* -------- formatters -------- */
function fmtPct(x) {
  if (x === null || x === undefined) return '';
  return (x * 100).toFixed(1) + '%';
}

function fmtTemp(t) {
  if (t === null || t === undefined) return '';
  const n = Number(t);
  if (!Number.isFinite(n)) return '';
  return n.toFixed(1) + '°C';
}

function fmtLoc(loc) {
  if (!loc) return '';
  const { xc, yc } = loc;
  if (xc === null || xc === undefined || yc === null || yc === undefined) return '';
  const x = Number(xc), y = Number(yc);
  if (!Number.isFinite(x) || !Number.isFinite(y)) return '';
  return `(${x.toFixed(0)}, ${y.toFixed(0)})`;
}

function parseTime(t) {
  if (!t) return null;
  // Accept "YYYY-MM-DD HH:MM:SS" (treat as local) or ISO strings
  const s = typeof t === 'string' ? t.replace(' ', 'T') : t;
  const d = new Date(s);
  return isNaN(d.getTime()) ? null : d;
}

function fmtRelative(t) {
  const d = parseTime(t);
  if (!d) return t || '';
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 5)   return 'just now';
  if (diff < 60)  return `${Math.floor(diff)}s ago`;
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  return `${Math.floor(diff/86400)}d ago`;
}

function fmtAbsTime(t) {
  const d = parseTime(t);
  if (!d) return '';
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function confClass(c) {
  if (c === null || c === undefined) return '';
  if (c < 0.5)  return 'low';
  if (c < 0.75) return 'mid';
  return 'high';
}

function escapeHtml(s) {
  if (s === null || s === undefined) return '';
  return String(s).replace(/[&<>"']/g, c => ({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }[c]));
}

/* -------- fetch -------- */
async function fetchJSON(url) {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

function buildDetectionsUrl() {
  const params = new URLSearchParams();
  params.set("limit", els.limit.value);

  const cls = (els.className?.value || "").trim();
  if (cls) params.set("class_name", cls);

  const mc = (els.minConf?.value || "").trim();
  if (mc) params.set("min_conf", mc);

  return "/api/detections?" + params.toString();
}

/* -------- preview -------- */
function setImageFromRow(row) {
  if (!row || !row.image_url) {
    els.previewImg.removeAttribute("src");
    els.previewImg.style.display = "none";
    els.openImage.style.display = "none";
    els.emptyState.style.display = "block";
    els.previewMeta.innerHTML = "";
    return;
  }

  els.previewImg.src = row.image_url;
  els.previewImg.style.display = "block";
  els.emptyState.style.display = "none";

  els.openImage.href = row.image_url;
  els.openImage.style.display = "inline-block";

  const meta = [
    ['ID', row.id ?? '–'],
    ['Class', row.class_name ? `<span class="badge ${escapeHtml(row.class_name)}">${escapeHtml(row.class_name)}</span>` : '–'],
    ['Confidence', fmtPct(row.confidence) || '–'],
    ['Temperature', fmtTemp(row.temperature) || '–'],
    ['Time', row.time ? escapeHtml(row.time) : '–'],
    ['Location', fmtLoc(row.location) || '–'],
  ];
  els.previewMeta.innerHTML = meta.map(([k,v]) =>
    `<div class="metaItem"><span class="metaLabel">${k}</span><span class="metaValue">${v}</span></div>`
  ).join('');
}

/* -------- table -------- */
function renderTable(rows) {
  if (!rows || rows.length === 0) {
    els.tbody.innerHTML = '<tr><td colspan="6" class="muted">No detections found (with current filters).</td></tr>';
    lastSelectedId = null;
    setImageFromRow(null);
    return;
  }

  els.tbody.innerHTML = rows.map(r => {
    const sel = (r.id === lastSelectedId) ? 'selected' : '';
    const cls = r.class_name ? `<span class="badge ${escapeHtml(r.class_name)}">${escapeHtml(r.class_name)}</span>` : '';
    const pct = (r.confidence ?? 0) * 100;
    const cc = confClass(r.confidence);
    const conf = r.confidence === null || r.confidence === undefined ? '' : `
      <div class="confCell">
        <div class="confBar"><div class="confFill ${cc}" style="width:${Math.min(100,Math.max(0,pct)).toFixed(1)}%"></div></div>
        <span class="confText">${fmtPct(r.confidence)}</span>
      </div>`;

    return `
      <tr class="${sel}" data-id="${r.id}">
        <td>${r.id ?? ''}</td>
        <td class="timeCell"><span class="rel">${escapeHtml(fmtRelative(r.time))}</span><span class="abs">${escapeHtml(fmtAbsTime(r.time))}</span></td>
        <td>${cls}</td>
        <td>${conf}</td>
        <td class="right">${fmtTemp(r.temperature)}</td>
        <td>${fmtLoc(r.location)}</td>
      </tr>
    `;
  }).join("");

  els.tbody.querySelectorAll("tr").forEach(tr => {
    tr.addEventListener("click", () => {
      const id = Number(tr.getAttribute("data-id"));
      const row = rows.find(x => x.id === id);
      lastSelectedId = id;
      setImageFromRow(row);
      // just toggle classes instead of full re-render
      els.tbody.querySelectorAll("tr").forEach(x => x.classList.remove('selected'));
      tr.classList.add('selected');
    });
  });

  // If nothing selected yet, select newest row
  if (lastSelectedId === null) {
    lastSelectedId = rows[0].id;
    setImageFromRow(rows[0]);
    const first = els.tbody.querySelector("tr");
    if (first) first.classList.add('selected');
    return;
  }

  // If selected row disappeared (filter changed), pick newest
  if (!rows.some(r => r.id === lastSelectedId)) {
    lastSelectedId = rows[0].id;
    setImageFromRow(rows[0]);
    const first = els.tbody.querySelector("tr");
    if (first) first.classList.add('selected');
  }
}

/* -------- stats -------- */
async function refreshStats() {
  try {
    const s = await fetchJSON("/api/stats");
    if (els.statTotal) els.statTotal.textContent = (s.total_detections ?? 0).toLocaleString();
    if (els.statLatest) {
      els.statLatest.textContent = s.latest ? fmtRelative(s.latest.time) : '–';
      els.statLatest.title = s.latest?.time || '';
    }
  } catch (e) {
    // silent
  }
}

/* -------- main refresh -------- */
async function refreshAll() {
  try {
    const rows = await fetchJSON(buildDetectionsUrl());
    renderTable(rows);
    if (els.lastUpdated) {
      els.lastUpdated.textContent = 'Updated ' + new Date().toLocaleTimeString();
    }
  } catch (e) {
    console.error(e);
    els.tbody.innerHTML = '<tr><td colspan="6" class="muted">Error loading data. Check console.</td></tr>';
  }
  refreshStats();
}

function startTimer() {
  if (timer) clearInterval(timer);
  timer = setInterval(() => {
    if (autoRefresh) refreshAll();
  }, 2000);
}

/* -------- wire up -------- */
els.apply?.addEventListener("click", () => refreshAll());

els.className?.addEventListener("change", () => refreshAll());
els.limit?.addEventListener("change", () => refreshAll());
els.minConf?.addEventListener("keydown", (e) => { if (e.key === "Enter") refreshAll(); });

els.toggleRefresh?.addEventListener("click", () => {
  autoRefresh = !autoRefresh;
  els.toggleRefresh.textContent = autoRefresh ? "Pause" : "Resume";
  els.liveIndicator?.classList.toggle('paused', !autoRefresh);
  if (els.liveText) els.liveText.textContent = autoRefresh ? "Live" : "Paused";
  if (autoRefresh) refreshAll();
});

refreshAll();
startTimer();
