const els = {
  tbody: document.getElementById('tbody'),

  className: document.getElementById('className'),
  minConf: document.getElementById('minConf'),
  limit: document.getElementById('limit'),
  apply: document.getElementById('apply'),
  toggleRefresh: document.getElementById('toggleRefresh'),

  previewImg: document.getElementById('previewImg'),
  openImage: document.getElementById('openImage'),
};

let autoRefresh = true;
let timer = null;
let lastSelectedId = null;
let lastRowsCache = [];

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

function setImageFromRow(row) {
  if (!row || !row.image_url) {
    els.previewImg.removeAttribute("src");
    els.previewImg.style.display = "none";
    els.openImage.style.display = "none";
    return;
  }

  els.previewImg.src = row.image_url;
  els.previewImg.style.display = "block";

  els.openImage.href = row.image_url;
  els.openImage.style.display = "inline";
}

function renderTable(rows) {
  lastRowsCache = rows || [];

  if (!rows || rows.length === 0) {
    els.tbody.innerHTML = '<tr><td colspan="5" class="muted">No detections found (with current filters).</td></tr>';
    lastSelectedId = null;
    setImageFromRow(null);
    return;
  }

  els.tbody.innerHTML = rows.map(r => {
    const selectedStyle = (r.id === lastSelectedId)
      ? 'style="background: rgba(78,161,255,0.08);"'
      : '';

    return `
      <tr data-id="${r.id}" ${selectedStyle}>
        <td>${r.id ?? ''}</td>
        <td>${r.time ?? ''}</td>
        <td class="right">${fmtPct(r.confidence)}</td>
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
      renderTable(rows); // re-render to highlight selected row
    });
  });

  // If nothing selected yet, select newest row and show its image if available
  if (lastSelectedId === null) {
    lastSelectedId = rows[0].id;
    setImageFromRow(rows[0]);
    renderTable(rows);
    return;
  }

  // If selected row disappeared (filter changed), pick newest
  if (!rows.some(r => r.id === lastSelectedId)) {
    lastSelectedId = rows[0].id;
    setImageFromRow(rows[0]);
    renderTable(rows);
  }
}

async function refreshAll() {
  try {
    const rows = await fetchJSON(buildDetectionsUrl());
    renderTable(rows);
  } catch (e) {
    console.error(e);
    els.tbody.innerHTML = '<tr><td colspan="5" class="muted">Error loading data. Check console.</td></tr>';
  }
}

function startTimer() {
  if (timer) clearInterval(timer);
  timer = setInterval(() => {
    if (autoRefresh) refreshAll();
  }, 2000);
}

els.apply?.addEventListener("click", () => refreshAll());

els.toggleRefresh?.addEventListener("click", () => {
  autoRefresh = !autoRefresh;
  els.toggleRefresh.textContent = autoRefresh ? "Pause" : "Resume";
  if (autoRefresh) refreshAll();
});

refreshAll();
startTimer();