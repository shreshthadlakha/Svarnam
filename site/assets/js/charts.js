/* charts.js — theme-aware Chart.js builders + annotation shims.
   Colours read from CSS tokens at render time; the theme toggle triggers rebuildAll.
   Classic script (no ES modules) so the page also works opened directly from disk
   (file://), where the browser blocks module scripts. API: window.SvarnamCharts. */
(() => {
const $ = (s) => document.querySelector(s);
let CHARTS = {};

function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function chartTheme() {
    return {
        ink: cssVar('--ink'),
        ink2: cssVar('--ink-2'),
        ink3: cssVar('--ink-3'),
        line: cssVar('--line'),
        lineStrong: cssVar('--line-strong'),
        surface: cssVar('--surface'),
        gold: cssVar('--c-metal'),
        rust: cssVar('--c-duty'),
        green: cssVar('--c-gst'),
        residualHatch: cssVar('--residual-hatch'),
        residualInk: cssVar('--ink-3'),
    };
}

function hatchPattern(inkColour) {
    const c = document.createElement('canvas');
    c.width = 8; c.height = 8;
    const ctx = c.getContext('2d');
    ctx.strokeStyle = inkColour;
    ctx.lineWidth = 1.2;
    ctx.globalAlpha = 0.55;
    ctx.beginPath();
    ctx.moveTo(0, 8); ctx.lineTo(8, 0);
    ctx.moveTo(-2, 2); ctx.lineTo(2, -2);
    ctx.moveTo(6, 10); ctx.lineTo(10, 6);
    ctx.stroke();
    return ctx.createPattern(c, 'repeat');
}

/* --- regime-break shim: dashed rules + numbered flags -------------------- */
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
            ctx.strokeStyle = cssVar('--residual-hatch');
            ctx.globalAlpha = 0.7;
            ctx.setLineDash([4, 3]);
            ctx.lineWidth = 1.2;
            ctx.beginPath();
            ctx.moveTo(px, area.top);
            ctx.lineTo(px, area.bottom);
            ctx.stroke();
            ctx.setLineDash([]);
            ctx.globalAlpha = 1;
            const by = area.top + 11;
            ctx.beginPath();
            ctx.arc(px, by, 9, 0, Math.PI * 2);
            ctx.fillStyle = cssVar('--ink-3');
            ctx.fill();
            ctx.strokeStyle = cssVar('--surface');
            ctx.lineWidth = 1.4;
            ctx.stroke();
            ctx.fillStyle = cssVar('--surface');
            ctx.font = 'bold 10px ' + cssVar('--font-ui').split(',')[0] + ', system-ui';
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
        const key = mode === 'monthly' ? b.date.slice(0, 7) : fyOfDate(b.date);
        const idx = idxOf.get(key);
        if (idx !== undefined) marks.push({ index: idx, n: n + 1 });
    });
    return marks;
}

function initCharts(rebuildAll) {
    if (!window.Chart) return;
    window.Chart.register(regimeMarks);
    window.Chart.defaults.font.family = `"${cssVar('--font-ui').split(',')[0].trim()}", Inter, system-ui, sans-serif`;
    window.Chart.defaults.color = cssVar('--ink-2');
    syncRem();
    if (rebuildAll) {
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

function syncRem() {
    if (!window.Chart) return;
    const rem = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
    window.Chart.defaults.font.size = Math.round(rem * 0.75);
}

function baseTooltip(rows) {
    const th = chartTheme();
    return {
        backgroundColor: th.surface,
        titleColor: th.ink,
        bodyColor: th.ink2,
        borderColor: th.lineStrong,
        borderWidth: 1,
        borderRadius: 12,
        padding: 14,
        callbacks: {
            title: (items) => rows[items[0].dataIndex]?.fy || rows[items[0].dataIndex]?.month || items[0].label,
            label: (c) => '',
            afterBody: (items) => {
                const idx = items[0].dataIndex;
                const r = rows[idx];
                if (!r) return [];
                const fmt = (v) => '₹' + Math.round(v).toLocaleString('en-IN');
                return [
                    `metal + FX  ${fmt(r.metal_fx_leg)}`,
                    `duty         ${fmt(r.duty_leg)}`,
                    `GST          ${fmt(r.gst_leg)}`,
                    `landed cost  ${fmt(r.landed_cost)}`,
                    `published    ${fmt(r.mumbai_inr_10g)}`,
                    `premium      ${r.premium_pct >= 0 ? '+' : ''}${r.premium_pct}%`,
                ];
            },
        },
        displayColors: false,
    };
}

/* --- flagship: 41-year stacked decomposition (hero section) --------------- */
function buildStack(data, mode) {
    const rows = mode === 'annual'
        ? data.derived.decomposition_annual
        : data.derived.decomposition_monthly;
    const th = chartTheme();
    const labels = rows.map(r => r.fy || r.month);
    const hatch = hatchPattern(th.residualHatch);
    const mk = (field, label, color, extra) => ({
        label, data: rows.map(r => r[field]), backgroundColor: color,
        borderColor: cssVar('--surface'), borderWidth: 1, stack: 's',
        ...extra,
    });
    const ds = [
        mk('metal_fx_leg', 'metal + FX', th.gold),
        mk('duty_leg', 'duty', th.rust),
        mk('gst_leg', 'GST', th.green),
        mk('premium_leg', 'residual (hatched)', hatch),
    ];
    if (CHARTS.stack) CHARTS.stack.destroy();
    CHARTS.stack = new window.Chart($('#stackChart'), {
        type: 'bar',
        data: { labels, datasets: ds },
        options: {
            responsive: true, maintainAspectRatio: false,
            animation: { duration: 300, easing: 'ease-out' },
            plugins: {
                legend: { position: 'top', labels: { font: { size: 12 }, color: th.ink2, boxWidth: 14, boxHeight: 14, borderRadius: 2 } },
                tooltip: baseTooltip(rows),
            },
            scales: {
                x: {
                    stacked: true,
                    grid: { display: false },
                    border: { color: th.line },
                    ticks: { maxRotation: 45, minRotation: 0, autoSkip: mode === 'annual' ? false : true, maxTicksLimit: mode === 'annual' ? 41 : 25, font: { size: 11 }, color: th.ink3 },
                },
                y: {
                    stacked: true,
                    grid: { color: th.line, lineWidth: (c) => (c.tick && c.tick.value === 0) ? 1.4 : 0.5 },
                    border: { display: false },
                    ticks: { maxTicksLimit: 6, callback: (v) => '₹' + (+v).toLocaleString('en-IN'), color: th.ink3, font: { size: 12 } },
                },
            },
        },
    });
    CHARTS.stack.$regimeMarks = marksForLabels(labels, data.policy.breaks, mode);
}

/* --- wage: days of work per tola ------------------------------------------ */
function buildWage(data, occupation) {
    const th = chartTheme();
    const rows = data.derived.gold_per_wageday
        .filter(r => r.occupation === occupation)
        .sort((a, b) => a.fy.localeCompare(b.fy));
    const days = rows.map(r => (r.grams && r.grams > 0) ? 11.6638038 / r.grams : null);
    const reclassIdx = rows.findIndex(r => r.fy === '2014-15');
    if (CHARTS.wage) CHARTS.wage.destroy();
    CHARTS.wage = new window.Chart($('#wageChart'), {
        type: 'line',
        data: {
            labels: rows.map(r => r.fy),
            datasets: [{
                label: `days of ${occupation} work per tola`,
                data: days,
                borderColor: th.gold, pointBackgroundColor: th.gold,
                pointRadius: 3, borderWidth: 2.5, tension: 0.2,
            }],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: cssVar('--surface'), titleColor: cssVar('--ink'),
                    bodyColor: cssVar('--ink-2'), borderColor: cssVar('--line-strong'),
                    borderWidth: 1, borderRadius: 12, padding: 12, displayColors: false,
                    callbacks: { label: (c) => `${Math.round(+c.parsed.y).toLocaleString('en-IN')} days of work per tola` },
                },
            },
            scales: {
                x: { grid: { display: false }, border: { color: th.line }, ticks: { font: { size: 11 }, color: th.ink3, maxRotation: 45 } },
                y: { beginAtZero: true, grid: { color: th.line }, border: { display: false }, ticks: { maxTicksLimit: 6, callback: (v) => v.toLocaleString('en-IN') + ' d', color: th.ink3, font: { size: 12 } } },
            },
        },
    });
    // end label: latest value
    const lastMeta = CHARTS.wage.getDatasetMeta(0);
    const lastEl = lastMeta.data[lastMeta.data.length - 1];
    if (lastEl && days[days.length - 1] != null) {
        drawEndLabel(CHARTS.wage, lastEl.x, lastEl.y, Math.round(days[days.length - 1]).toLocaleString('en-IN') + ' d', th.gold);
    }
    // reclassification annotation
    if (reclassIdx > 0) {
        drawAnnotation(CHARTS.wage, reclassIdx, 'Nov 2013: occupations reclassified', th.ink3);
    }
    return rows;
}

/* --- MSP: kg per tola ------------------------------------------------------ */
function buildMsp(data, crop) {
    const th = chartTheme();
    const rows = data.derived.gold_per_mspkg
        .filter(r => r.crop === crop)
        .sort((a, b) => a.crop_year.localeCompare(b.crop_year));
    const kg = rows.map(r => (r.grams && r.grams > 0) ? 11.6638038 / r.grams : null);
    if (CHARTS.msp) CHARTS.msp.destroy();
    CHARTS.msp = new window.Chart($('#mspChart'), {
        type: 'line',
        data: {
            labels: rows.map(r => r.crop_year),
            datasets: [{
                label: `kg of ${crop} per tola`,
                data: kg,
                borderColor: th.gold, pointBackgroundColor: th.gold,
                pointRadius: 3, borderWidth: 2.5, tension: 0.2,
            }],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: cssVar('--surface'), titleColor: cssVar('--ink'),
                    bodyColor: cssVar('--ink-2'), borderColor: cssVar('--line-strong'),
                    borderWidth: 1, borderRadius: 12, padding: 12, displayColors: false,
                    callbacks: { label: (c) => `${Math.round(+c.parsed.y).toLocaleString('en-IN')} kg per tola` },
                },
            },
            scales: {
                x: { grid: { display: false }, border: { color: th.line }, ticks: { font: { size: 11 }, color: th.ink3, maxRotation: 45 } },
                y: { beginAtZero: true, grid: { color: th.line }, border: { display: false }, ticks: { maxTicksLimit: 6, callback: (v) => v.toLocaleString('en-IN') + ' kg', color: th.ink3, font: { size: 12 } } },
            },
        },
    });
    const lastMeta = CHARTS.msp.getDatasetMeta(0);
    const lastEl = lastMeta.data[lastMeta.data.length - 1];
    if (lastEl && kg[kg.length - 1] != null) {
        drawEndLabel(CHARTS.msp, lastEl.x, lastEl.y, Math.round(kg[kg.length - 1]).toLocaleString('en-IN') + ' kg', th.gold);
    }
    return rows;
}

/* --- end label + annotation helpers --------------------------------------- */
function drawEndLabel(chart, x, y, text, colour) {
    const { ctx, chartArea: area } = chart;
    ctx.save();
    ctx.font = '600 12px ' + cssVar('--font-ui').split(',')[0] + ', Inter, sans-serif';
    ctx.fillStyle = colour;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, x + 8, Math.min(Math.max(y, area.top + 8), area.bottom - 8));
    ctx.restore();
}

function drawAnnotation(chart, idx, text, colour) {
    const meta = chart.getDatasetMeta(0);
    const el = meta.data[idx];
    if (!el) return;
    const { ctx, chartArea: area } = chart;
    ctx.save();
    ctx.strokeStyle = colour;
    ctx.globalAlpha = 0.5;
    ctx.setLineDash([3, 3]);
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(el.x, area.top);
    ctx.lineTo(el.x, area.bottom);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.globalAlpha = 1;
    ctx.font = '10px ' + cssVar('--font-ui').split(',')[0] + ', system-ui';
    ctx.fillStyle = colour;
    ctx.textAlign = 'center';
    ctx.fillText(text, el.x, area.top + 12);
    ctx.restore();
}

/* --- accessibility: data tables ------------------------------------------- */
function tableFor(rows) {
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

/* --- hero bar (HTML/CSS, landed-cost base) --------------------------------- */
function buildHeroBar(data) {
    const rows = data.derived.decomposition_annual;
    const last = rows[rows.length - 1];
    const landed = last.metal_fx_leg + last.duty_leg + last.gst_leg;
    const mumbai = last.mumbai_inr_10g;
    const total = Math.max(landed, mumbai);
    const shares = {
        metal: last.metal_fx_leg / total * 100,
        duty: last.duty_leg / total * 100,
        gst: last.gst_leg / total * 100,
    };
    const markerPct = mumbai / total * 100;
    const bar = $('#heroBar');
    if (!bar) return last;
    $('#segMetal').style.setProperty('--w', shares.metal + '%');
    $('#segDuty').style.setProperty('--w', shares.duty + '%');
    $('#segGst').style.setProperty('--w', shares.gst + '%');
    const marker = $('#heroMarker');
    marker.style.left = markerPct + '%';
    const hatch = $('#heroHatch');
    if (mumbai < landed) {
        // discount: hatch between marker and bar end
        hatch.style.left = markerPct + '%';
        hatch.style.width = (100 - markerPct) + '%';
        hatch.style.display = 'block';
    } else if (mumbai > landed) {
        // premium: hatch between bar end and marker
        const landedPct = landed / total * 100;
        hatch.style.left = landedPct + '%';
        hatch.style.width = (markerPct - landedPct) + '%';
        hatch.style.display = 'block';
    } else {
        hatch.style.display = 'none';
    }
    // animate
    requestAnimationFrame(() => requestAnimationFrame(() => bar.classList.add('loaded')));
    return last;
}

/* --- stat tiles -------------------------------------------------------------- */
function buildStatTiles(data) {
    const rows = data.derived.decomposition_annual;
    const last = rows[rows.length - 1];
    const landed = last.metal_fx_leg + last.duty_leg + last.gst_leg;
    const th = chartTheme();
    const host = $('#statTiles');
    if (!host) return last;
    host.innerHTML = '';
    const items = [
        { name: 'metal + FX', v: last.metal_fx_leg, c: th.gold, hatch: false },
        { name: 'customs duty', v: last.duty_leg, c: th.rust, hatch: false },
        { name: 'GST', v: last.gst_leg, c: th.green, hatch: false },
        { name: 'premium', v: last.premium_leg, c: th.residualInk, hatch: true },
    ];
    items.forEach(it => {
        const share = (it.v / landed * 100);
        const d = document.createElement('div');
        d.className = 'stat-tile' + (it.hatch ? ' residual' : '');
        d.style.setProperty('--tile-c', it.c);
        const num = document.createElement('div');
        num.className = 'num';
        num.textContent = `${share >= 0 ? '' : '−'}${Math.abs(share).toFixed(1)}%`;
        const lbl = document.createElement('div');
        lbl.className = 'lbl';
        lbl.textContent = it.name;
        d.append(num, lbl);
        host.appendChild(d);
    });
    return last;
}

window.SvarnamCharts = { cssVar, initCharts, syncRem, buildStack, buildWage, buildMsp, buildHeroBar, buildStatTiles, tableFor };
})();
