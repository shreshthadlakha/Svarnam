/* charts.js — Chart.js builders + the regime-break annotation shim (deterministic, no plugins needed). */

const $ = (s) => document.querySelector(s);
let CHARTS = {};

/* Okabe-Ito palette — designed for colour-vision-deficiency safety. */
const PALETTE = { metal: '#E69F00', duty: '#D55E00', gst: '#009E73', premium: '#0072B2' };

/* --- annotation shim -----------------------------------------------------
   Dashed vertical lines + numbered badges (1–9) for regime breaks.
   The numbers map to the numbered list rendered under each chart.
   marks: [{index (category index), n}] — staggered on collision. */
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
            const px = px0 + (used[Math.round(px0 / 9)] || 0) * 9;
            used[Math.round(px0 / 9)] = (used[Math.round(px0 / 9)] || 0) + 1;
            ctx.save();
            ctx.strokeStyle = 'rgba(107,91,46,.8)';
            ctx.setLineDash([4, 3]);
            ctx.beginPath();
            ctx.moveTo(px, area.top);
            ctx.lineTo(px, area.bottom);
            ctx.stroke();
            ctx.setLineDash([]);
            const by = area.top + 10;
            ctx.beginPath();
            ctx.arc(px, by, 8, 0, Math.PI * 2);
            ctx.fillStyle = '#6b5b2e';
            ctx.fill();
            ctx.strokeStyle = '#faf7ef';
            ctx.lineWidth = 1.2;
            ctx.stroke();
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 9px system-ui';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(String(m.n), px, by);
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

function marksForLabels(labels, breaks, mode) {
    const idxOf = new Map(labels.map((l, i) => [l, i]));
    const marks = [];
    breaks.forEach((b, n) => {
        // FY labels ("1985-86") and month labels ("2026-10") are BOTH 7 chars with a
        // dash — never guess the basis from label shape; the caller passes the mode.
        const key = mode === 'monthly' ? b.date.slice(0, 7) : fyOfDate(b.date);
        const idx = idxOf.get(key);
        if (idx !== undefined) marks.push({ index: idx, n: n + 1 });
    });
    return marks;
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
    const mk = (field, label, color) => ({
        label, data: rows.map(r => r[field]), backgroundColor: color,
        borderColor: '#faf7ef', borderWidth: 1,
        stack: 's', order: 2,
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
                y: {
                    stacked: true,
                    grid: {
                        color: (c) => (c.tick && c.tick.value === 0) ? '#8a8576' : '#eee7d6',
                        lineWidth: (c) => (c.tick && c.tick.value === 0) ? 1.4 : 0.5,
                    },
                    ticks: { callback: (v) => '₹' + (+v).toLocaleString('en-IN') },
                },
            },
        },
    });
    CHARTS.stack.$regimeMarks = marksForLabels(labels, data.policy.breaks, mode);
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
                borderColor: PALETTE.metal, backgroundColor: 'rgba(230,159,0,.15)',
                fill: true, tension: 0.15, pointRadius: 2.5,
            }],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'top' }, tooltip: { callbacks: { label: (c) => `${c.parsed.y} g` } } },
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
                borderColor: PALETTE.gst, backgroundColor: 'rgba(0,158,115,.15)',
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
