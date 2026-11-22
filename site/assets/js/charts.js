/* charts.js — Chart.js builders + annotation shims. Okabe-Ito hues; marks use the
   luminance-darkened variants (#B26A00 / #00805C) that pass WCAG 1.4.11 3:1 on paper. */

const $ = (s) => document.querySelector(s);
let CHARTS = {};

export const TOLA_G = 11.6638038; // 1 tola = 11.6638038 g (display-level constant)
const PALETTE = { metal: '#B26A00', duty: '#D55E00', gst: '#00805C', premium: '#0072B2' };

export function syncRem() {
    if (!window.Chart) return;
    const rem = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
    window.Chart.defaults.font.size = Math.round(rem * 0.75);
}

/* --- regime-break shim: dashed lines + numbered badges ------------------- */
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
            const px = px0 + (used[Math.round(px0 / 10)] || 0) * 10;
            used[Math.round(px0 / 10)] = (used[Math.round(px0 / 10)] || 0) + 1;
            ctx.save();
            ctx.strokeStyle = 'rgba(107,91,46,.8)';
            ctx.setLineDash([4, 3]);
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(px, area.top);
            ctx.lineTo(px, area.bottom);
            ctx.stroke();
            ctx.setLineDash([]);
            const by = area.top + 11;
            ctx.beginPath();
            ctx.arc(px, by, 9, 0, Math.PI * 2);
            ctx.fillStyle = '#6b5b2e';
            ctx.fill();
            ctx.strokeStyle = '#faf7ef';
            ctx.lineWidth = 1.4;
            ctx.stroke();
            ctx.fillStyle = '#fff';
            ctx.font = `bold ${Math.round(10)}px system-ui`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(String(m.n), px, by);
            ctx.restore();
        });
    },
};

/* --- flagship end-labels: the 4 legs labelled at the last column --------- */
const endLabels = {
    id: 'endLabels',
    afterDatasetsDraw(chart) {
        const cfg = chart.$endLabels;
        if (!cfg) return;
        const { ctx, chartArea: area, scales: { x, y } } = chart;
        const last = chart.data.labels.length - 1;
        if (last < 0) return;
        const px0 = x.getPixelForValue(last);
        if (!isFinite(px0)) return;
        const d = chart.data.datasets.map(ds => ds.data[last] || 0);
        const mids = [
            d[0] / 2,
            d[0] + d[1] / 2,
            d[0] + d[1] + d[2] / 2,
            d[0] + d[1] + d[2] + d[3] / 2,
        ];
        let pxs = mids.map(v => y.getPixelForValue(v));
        // enforce minimum 16px separation (sliver legs cluster)
        for (let i = 1; i < pxs.length; i++) {
            if (pxs[i] - pxs[i - 1] < 16) pxs[i] = pxs[i - 1] + 16;
        }
        const names = ['metal + FX', 'duty', 'GST', 'premium'];
        const cols = [PALETTE.metal, PALETTE.duty, PALETTE.gst, PALETTE.premium];
        ctx.save();
        ctx.font = '600 11px system-ui';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        names.forEach((name, i) => {
            const px = Math.min(pxs[i], area.bottom - 8);
            ctx.fillStyle = cols[i];
            ctx.fillText(name, area.right + 6, px);
        });
        ctx.restore();
    },
};

/* --- flagship callouts: two load-bearing moments ------------------------- */
const CALLOUTS = [
    { fy: '2013-14', text: '80:20 curbs: premiums to +$160/oz' },
    { fy: '2024-25', text: 'Duty cut → discounts' },
];
const calloutsPlugin = {
    id: 'callouts',
    afterDatasetsDraw(chart) {
        const cfg = chart.$callouts;
        if (!cfg) return;
        const { ctx, chartArea: area, scales: { x, y } } = chart;
        const labels = chart.data.labels;
        cfg.forEach(c => {
            const idx = labels.indexOf(c.fy);
            if (idx < 0) return;
            const px = x.getPixelForValue(idx);
            if (!isFinite(px) || px < area.left || px > area.right) return;
            const total = chart.data.datasets.reduce((s, ds) => s + (ds.data[idx] || 0), 0);
            const topPx = y.getPixelForValue(total);
            ctx.save();
            ctx.strokeStyle = 'rgba(34,33,29,.45)';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(px, topPx - 4);
            ctx.lineTo(px, topPx - 22);
            ctx.stroke();
            ctx.fillStyle = '#22211d';
            ctx.font = '600 11px system-ui';
            ctx.textAlign = px > area.right - 110 ? 'right' : 'center';
            ctx.fillText(c.text, px, topPx - 28);
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

export function initCharts(rebuildAll) {
    if (!window.Chart) return;
    window.Chart.register(regimeMarks, endLabels, calloutsPlugin);
    window.Chart.defaults.font.family = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
    window.Chart.defaults.color = '#22211d';
    syncRem();
    if (rebuildAll) {
        // rebuild charts when the user's base font size changes (rem scaling)
        const probe = document.createElement('div');
        probe.style.cssText = 'position:absolute;height:1em;width:0;visibility:hidden';
        document.body.appendChild(probe);
        let last = probe.getBoundingClientRect().height;
        const ro = new ResizeObserver(() => {
            const h = probe.getBoundingClientRect().height;
            if (Math.abs(h - last) > 0.5) { last = h; syncRem(); rebuildAll(); }
        });
        ro.observe(probe);
    }
}

/* --- flagship: 41-year stacked decomposition (the hero) ------------------- */
export function buildFlagship(data) {
    const rows = data.derived.decomposition_annual;
    const labels = rows.map(r => r.fy);
    const mk = (field, label, color) => ({
        label, data: rows.map(r => r[field]), backgroundColor: color,
        borderColor: '#faf7ef', borderWidth: 1, stack: 's', order: 2,
    });
    const ds = [
        mk('metal_fx_leg', 'metal + FX', PALETTE.metal),
        mk('duty_leg', 'duty', PALETTE.duty),
        mk('gst_leg', 'GST', PALETTE.gst),
        mk('premium_leg', 'premium (signed)', PALETTE.premium),
    ];
    if (CHARTS.flagship) CHARTS.flagship.destroy();
    CHARTS.flagship = new window.Chart($('#flagshipChart'), {
        type: 'bar',
        data: { labels, datasets: ds },
        options: {
            responsive: true, maintainAspectRatio: false,
            layout: { padding: { right: 92 } },
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ₹${(+c.raw).toLocaleString('en-IN')}` } },
            },
            scales: {
                x: { stacked: true, ticks: { maxRotation: 90, minRotation: 45, autoSkip: false, font: { size: 10 } } },
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
    CHARTS.flagship.$regimeMarks = marksForLabels(labels, data.policy.breaks, 'annual');
    CHARTS.flagship.$endLabels = true;
    CHARTS.flagship.$callouts = CALLOUTS;
}

/* --- monthly picture ------------------------------------------------------ */
export function buildMonthly(data) {
    const rows = data.derived.decomposition_monthly;
    const labels = rows.map(r => r.month);
    const mk = (field, label, color) => ({
        label, data: rows.map(r => r[field]), backgroundColor: color,
        borderColor: '#faf7ef', borderWidth: 1, stack: 's',
    });
    const ds = [
        mk('metal_fx_leg', 'metal + FX', PALETTE.metal),
        mk('duty_leg', 'duty', PALETTE.duty),
        mk('gst_leg', 'GST', PALETTE.gst),
        mk('premium_leg', 'premium (signed)', PALETTE.premium),
    ];
    if (CHARTS.monthly) CHARTS.monthly.destroy();
    CHARTS.monthly = new window.Chart($('#monthlyChart'), {
        type: 'bar',
        data: { labels, datasets: ds },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { font: { size: 11 } } },
                tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ₹${(+c.raw).toLocaleString('en-IN')} (${c.dataset.label === 'premium (signed)' ? '' : ''}${(+c.raw).toFixed(0)})` } },
            },
            scales: {
                x: {
                    stacked: true,
                    ticks: {
                        callback: (v, i) => (labels[i] && labels[i].endsWith('-01')) ? labels[i].slice(0, 4) : '',
                        autoSkip: false, maxRotation: 0, font: { size: 10 },
                    },
                },
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
    CHARTS.monthly.$regimeMarks = marksForLabels(labels, data.policy.breaks, 'monthly');
}

/* --- purchasing: per-tola units (FT-style rescale) ------------------------ */
export function buildWage(data, occupation) {
    const rows = data.derived.gold_per_wageday
        .filter(r => r.occupation === occupation)
        .sort((a, b) => a.fy.localeCompare(b.fy));
    const daysPerTola = rows.map(r => (r.grams && r.grams > 0) ? TOLA_G / r.grams : null);
    if (CHARTS.wage) CHARTS.wage.destroy();
    CHARTS.wage = new window.Chart($('#wageChart'), {
        type: 'line',
        data: {
            labels: rows.map(r => r.fy),
            datasets: [{
                label: `days of ${occupation} work per tola`,
                data: daysPerTola,
                borderColor: PALETTE.metal, pointBackgroundColor: PALETTE.metal,
                tension: 0.15, pointRadius: 2.5, borderWidth: 2.5,
            }],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: (c) => `${(+c.parsed.y).toLocaleString('en-IN', { maximumFractionDigits: 0 })} days of work per tola` } },
            },
            scales: { y: { beginAtZero: true, ticks: { callback: (v) => v.toLocaleString('en-IN') + ' d' } } },
        },
    });
    return rows;
}

export function buildMsp(data, crop) {
    const rows = data.derived.gold_per_mspkg
        .filter(r => r.crop === crop)
        .sort((a, b) => a.crop_year.localeCompare(b.crop_year));
    const kgPerTola = rows.map(r => (r.grams && r.grams > 0) ? TOLA_G / r.grams : null);
    if (CHARTS.msp) CHARTS.msp.destroy();
    CHARTS.msp = new window.Chart($('#mspChart'), {
        type: 'line',
        data: {
            labels: rows.map(r => r.crop_year),
            datasets: [{
                label: `kg of ${crop} per tola`,
                data: kgPerTola,
                borderColor: PALETTE.gst, pointBackgroundColor: PALETTE.gst,
                tension: 0.15, pointRadius: 2.5, borderWidth: 2.5,
            }],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: (c) => `${(+c.parsed.y).toLocaleString('en-IN', { maximumFractionDigits: 0 })} kg per tola` } },
            },
            scales: { y: { beginAtZero: true, ticks: { callback: (v) => v.toLocaleString('en-IN') + ' kg' } } },
        },
    });
    return rows;
}

/* --- hero decomposition rows ---------------------------------------------- */
export function buildHeroRows(data) {
    const rows = data.derived.decomposition_annual;
    const last = rows[rows.length - 1];
    const host = $('#decompRows');
    if (!host) return last;
    const items = [
        { name: 'metal + FX', v: last.metal_fx_leg, c: PALETTE.metal },
        { name: 'customs duty', v: last.duty_leg, c: PALETTE.duty },
        { name: 'GST', v: last.gst_leg, c: PALETTE.gst },
        { name: 'premium (signed)', v: last.premium_leg, c: PALETTE.premium },
    ];
    const landed = last.landed_cost;
    host.innerHTML = '';
    items.forEach(it => {
        const share = (it.v / landed * 100);
        const d = document.createElement('div');
        d.className = 'drow';
        const left = document.createElement('span');
        const dot = document.createElement('span');
        dot.className = 'dot'; dot.style.background = it.c;
        left.append(dot, document.createTextNode(it.name));
        const right = document.createElement('span');
        right.innerHTML = `₹${Math.abs(it.v).toLocaleString('en-IN', { maximumFractionDigits: 0 })} <span class="share">· ${share >= 0 ? '' : '−'}${Math.abs(share).toFixed(1)}%${it.v < 0 ? ' below landed cost' : ''}</span>`;
        d.append(left, right);
        host.appendChild(d);
    });
    return last;
}

/* --- accessibility: data tables ------------------------------------------- */
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
