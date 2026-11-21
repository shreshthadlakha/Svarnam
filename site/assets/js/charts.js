/* charts.js — Chart.js builders + the regime-break annotation shim (deterministic, no plugins needed). */

const $ = (s) => document.querySelector(s);
let CHARTS = {};

const PALETTE = { metal: '#b8860b', duty: '#b0413e', gst: '#5e8c61', premium: '#3f5f8a' };

/* --- annotation shim -----------------------------------------------------
   Draws dashed vertical lines + rotated labels for regime breaks.
   marks: [{index (category index), label, color}] — staggered on collision. */
const regimeMarks = {
  id: 'regimeMarks',
  afterDatasetsDraw(chart) {
    const marks = chart.$regimeMarks;
    if (!marks || !marks.length) return;
    const { ctx, chartArea: area, scales: { x } } = chart;
    if (!x) return;
    const used = {};
    marks.forEach(m => {
      const px0 = x.getPixelForValue(m.index);
      if (!isFinite(px0) || px0 < area.left - 20 || px0 > area.right + 20) return;
      const px = px0 + (used[Math.round(px0 / 8)] || 0) * 7;
      used[Math.round(px0 / 8)] = (used[Math.round(px0 / 8)] || 0) + 1;
      ctx.save();
      ctx.strokeStyle = 'rgba(107,91,46,.75)';
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      ctx.moveTo(px, area.top);
      ctx.lineTo(px, area.bottom);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = '#6b5b2e';
      ctx.font = '10px system-ui';
      ctx.translate(px + 2, area.top + 2);
      ctx.rotate(Math.PI / 2);
      ctx.fillText(m.label, 0, 8);
      ctx.restore();
    });
  },
};

function fyOfDate(iso) {
  const d = iso.split('-');
  const y = +d[0], m = +d[1];
  const y1 = m >= 4 ? y : y - 1;
  return `${y1}-${String((y1 + 1) % 100).padStart(2, '0')}`;
}

function marksForLabels(labels, breaks) {
  const idxOf = new Map(labels.map((l, i) => [l, i]));
  const marks = [];
  breaks.forEach(b => {
    const key = labels[0].includes('-') && labels[0].length === 7 ? b.date.slice(0, 7) : fyOfDate(b.date);
    const idx = idxOf.get(key);
    if (idx !== undefined) marks.push({ index: idx, label: b.date + ' ' + shortLabel(b.label) });
  });
  return marks;
}

function shortLabel(label) {
  const map = [
    ['Gold Control Act', 'GCA repealed'],
    ['NRI', 'NRI scheme'],
    ['FX unified', 'FX unified'],
    ['source break', 'RBI source break'],
    ['ad valorem', 'ad-valorem switch'],
    ['80:20', '80:20 restriction'],
    ['GST', 'GST 3%'],
    ['duty cycle', 'duty cycle 15-6-15'],
    ['Sovereign', 'SGB arc'],
  ];
  for (const [k, v] of map) if (label.toLowerCase().includes(k.toLowerCase())) return v;
  return label.slice(0, 26);
}

export function initCharts() {
  if (window.Chart) {
    window.Chart.register(regimeMarks);
    window.Chart.defaults.font.family = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
    window.Chart.defaults.color = '#22211d';
  }
}

/* --- hero: current-FY decomposition ------------------------------------- */
export function buildHero(data) {
  const rows = data.derived.decomposition_annual;
  const last = rows[rows.length - 1];
  const landed = last.landed_cost;
  const segs = [
    { k: 'metal + FX', v: last.metal_fx_leg, c: PALETTE.metal },
    { k: 'duty', v: last.duty_leg, c: PALETTE.duty },
    { k: 'GST', v: last.gst_leg, c: PALETTE.gst },
    { k: last.premium_leg >= 0 ? 'premium' : 'discount', v: Math.abs(last.premium_leg), c: PALETTE.premium },
  ];
  new window.Chart($('#heroChart'), {
    type: 'bar',
    data: {
      labels: [''],
      datasets: segs.map(s => ({
        label: s.k, data: [s.v], backgroundColor: s.c, borderColor: '#fff', borderWidth: 1,
        barPercentage: 0.62, categoryPercentage: 1,
      })),
    },
    options: {
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ₹${(+c.raw).toLocaleString('en-IN')}` } },
      },
      scales: { x: { stacked: true, ticks: { callback: (v) => '₹' + (+v).toLocaleString('en-IN') } }, y: { stacked: true, display: false } },
    },
  });
  const host = $('#heroStats');
  host.innerHTML = '';
  host.appendChild(stat(`₹${last.mumbai_inr_10g.toLocaleString('en-IN')}`, `Mumbai ₹/10g · ${last.fy}`));
  segs.forEach(s => {
    const pct = (s.v / landed * 100);
    const el = stat(`${pct >= 0 ? '' : '−'}${Math.abs(pct).toFixed(1)}%`, s.k);
    if (s.k === 'discount' || s.k === 'premium' && last.premium_leg < 0) el.classList.add('neg');
    host.appendChild(el);
  });
}

function stat(v, k) {
  const d = document.createElement('div');
  d.className = 'stat';
  const vv = document.createElement('div'); vv.className = 'v'; vv.textContent = v;
  const kk = document.createElement('div'); kk.className = 'k'; kk.textContent = k;
  d.append(vv, kk);
  return d;
}

/* --- stacked decomposition (annual | monthly) ---------------------------- */
export function buildStack(data, mode) {
  const rows = mode === 'annual'
    ? data.derived.decomposition_annual
    : data.derived.decomposition_monthly;
  const labels = rows.map(r => r.fy || r.month);
  const mk = (field, label, color, extra) => ({
    label, data: rows.map(r => r[field]), backgroundColor: color,
    stack: 's', order: 2, ...extra,
  });
  const ds = [
    mk('metal_fx_leg', 'metal + FX', PALETTE.metal),
    mk('duty_leg', 'duty', PALETTE.duty),
    mk('gst_leg', 'GST', PALETTE.gst),
    mk('premium_leg', 'premium (signed)', PALETTE.premium),
  ];
  if (CHARTS.stack) CHARTS.stack.destroy();
  CHARTS.stack = new window.Chart($('#stackChart'), {
    type: 'bar',
    data: { labels, datasets: ds },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ₹${(+c.raw).toLocaleString('en-IN')}` } },
      },
      scales: {
        x: { stacked: true, ticks: { maxRotation: 90, minRotation: 70, autoSkip: true, maxTicksLimit: mode === 'annual' ? 41 : 30, font: { size: 9 } } },
        y: { stacked: true, ticks: { callback: (v) => '₹' + (+v).toLocaleString('en-IN') } },
      },
    },
  });
  CHARTS.stack.$regimeMarks = marksForLabels(labels, data.policy.breaks);
}

/* --- wage ratio ---------------------------------------------------------- */
export function buildWage(data, occupation) {
  const rows = data.derived.gold_per_wageday
    .filter(r => r.occupation === occupation)
    .sort((a, b) => a.fy.localeCompare(b.fy));
  if (CHARTS.wage) CHARTS.wage.destroy();
  CHARTS.wage = new window.Chart($('#wageChart'), {
    type: 'line',
    data: {
      labels: rows.map(r => r.fy),
      datasets: [{
        label: `grams of gold per wage-day — ${occupation}`,
        data: rows.map(r => r.grams),
        borderColor: PALETTE.metal, backgroundColor: 'rgba(184,134,11,.15)',
        fill: true, tension: 0.15, pointRadius: 2.5,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'top' }, tooltip: { callbacks: { label: (c) => `${c.parsed.y} g · ₹${c.dataset.raw && ''}` } } },
      scales: { y: { beginAtZero: true, ticks: { callback: (v) => v + ' g' } } },
    },
  });
}

/* --- MSP ratio ----------------------------------------------------------- */
export function buildMsp(data, crop) {
  const rows = data.derived.gold_per_mspkg
    .filter(r => r.crop === crop)
    .sort((a, b) => a.crop_year.localeCompare(b.crop_year));
  if (CHARTS.msp) CHARTS.msp.destroy();
  CHARTS.msp = new window.Chart($('#mspChart'), {
    type: 'line',
    data: {
      labels: rows.map(r => r.crop_year),
      datasets: [{
        label: `grams of gold per MSP-kg — ${crop}`,
        data: rows.map(r => r.grams),
        borderColor: PALETTE.gst, backgroundColor: 'rgba(94,140,97,.15)',
        fill: true, tension: 0.15, pointRadius: 2.5,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'top' } },
      scales: { y: { beginAtZero: true, ticks: { callback: (v) => v + ' g' } } },
    },
  });
}

/* --- accessibility: data tables ------------------------------------------ */
export function tableFor(rows) {
  if (!rows.length) return document.createTextNode('No rows.');
  const t = document.createElement('table');
  const keys = Object.keys(rows[0]);
  const thead = document.createElement('thead');
  const htr = document.createElement('tr');
  keys.forEach(k => { const th = document.createElement('th'); th.textContent = k; htr.appendChild(th); });
  thead.appendChild(htr);
  const tbody = document.createElement('tbody');
  rows.forEach(r => {
    const tr = document.createElement('tr');
    keys.forEach(k => { const td = document.createElement('td'); td.textContent = r[k] ?? ''; tr.appendChild(td); });
    tbody.appendChild(tr);
  });
  t.append(thead, tbody);
  return t;
}
