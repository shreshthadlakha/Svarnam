/* main.js — boot: load dataset.json, hydrate everything from it. Zero hardcoded numbers. */
import { initCharts, syncRem, buildStack, buildWage, buildMsp, buildHeroBar, buildStatTiles, tableFor, cssVar } from './charts.js';
import { wireCalculator } from './calculator.js';
import { wireCsv } from './csv.js';

const $ = (s) => document.querySelector(s);
const TOLA = 11.6638038;

/* ── theme ── */
function initTheme() {
    const saved = localStorage.getItem('svarnam-theme');
    if (saved) document.documentElement.setAttribute('data-theme', saved);
    $('#themeBtn').addEventListener('click', () => {
        const cur = document.documentElement.getAttribute('data-theme')
            || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        const next = cur === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('svarnam-theme', next);
        if (window.__rebuildAll) window.__rebuildAll();
    });
}

/* ── nav menu ── */
function initNav() {
    const btn = $('#menuBtn'), nav = $('#siteNav');
    btn.addEventListener('click', () => {
        const open = nav.classList.toggle('open');
        btn.setAttribute('aria-expanded', String(open));
    });
    nav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
        nav.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
    }));
}

/* ── scroll-in animations ── */
function initScrollAnim() {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.querySelectorAll('.chart-anim').forEach(el => el.classList.add('in-view'));
        return;
    }
    const io = new IntersectionObserver((entries) => {
        entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in-view'); io.unobserve(e.target); } });
    }, { threshold: 0.1 });
    document.querySelectorAll('.chart-anim').forEach(el => io.observe(el));
}

/* ── segmented control ── */
function wireSegControl(data) {
    const annual = $('#segAnnual'), monthly = $('#segMonthly');
    const set = (mode) => {
        annual.setAttribute('aria-pressed', String(mode === 'annual'));
        monthly.setAttribute('aria-pressed', String(mode === 'monthly'));
        buildStack(data, mode);
    };
    annual.addEventListener('click', () => set('annual'));
    monthly.addEventListener('click', () => set('monthly'));
}

/* ── table toggles ── */
function wireTableToggle(btnId, tableId, render) {
    const btn = $(btnId), table = $(tableId);
    btn.addEventListener('click', () => {
        const expanded = btn.getAttribute('aria-expanded') === 'true';
        btn.setAttribute('aria-expanded', String(!expanded));
        table.hidden = expanded;
        if (!expanded && !table.hasChildNodes()) table.appendChild(render());
    });
}

function renderBreaks(breaks) {
    const ul = $('#breakList');
    ul.innerHTML = '';
    breaks.forEach((b, i) => {
        const li = document.createElement('li');
        const chip = document.createElement('span');
        chip.className = 'chip chip-prov';
        chip.textContent = (i + 1) + '. ' + b.date;
        li.appendChild(chip);
        li.appendChild(document.createTextNode(' ' + b.label));
        ul.appendChild(li);
    });
}

function renderEpisodes(episodes) {
    const ul = $('#episodeList');
    ul.innerHTML = '';
    episodes.forEach(e => {
        const li = document.createElement('li');
        const strong = document.createElement('span');
        strong.className = 'episelist-date';
        strong.textContent = e.date + ' — ';
        li.appendChild(strong);
        const sign = e.direction === 'premium' ? '+' : '−';
        if (e.inr_10g_equiv != null) {
            li.appendChild(document.createTextNode(
                `${sign}₹${Math.round(e.inr_10g_equiv).toLocaleString('en-IN')}/10g · `));
        } else {
            li.appendChild(document.createTextNode(`${e.direction} (size not documented) · `));
        }
        li.appendChild(document.createTextNode(e.event));
        ul.appendChild(li);
    });
}

function renderSources(sources) {
    const host = $('#sourcesTable');
    const t = document.createElement('table');
    t.innerHTML = '<caption>Svarnam source registry</caption><thead><tr><th>ID</th><th>Source</th><th>Coverage</th><th>Accessed</th><th>License</th></tr></thead><tbody></tbody>';
    const tb = t.querySelector('tbody');
    sources.forEach(s => {
        const tr = document.createElement('tr');
        const td1 = document.createElement('td');
        const code = document.createElement('code'); code.textContent = s.id; td1.appendChild(code);
        const td2 = document.createElement('td');
        const a = document.createElement('a'); a.href = s.url; a.textContent = s.name; a.target = '_blank'; a.rel = 'noopener';
        td2.appendChild(a);
        const td3 = document.createElement('td'); td3.textContent = s.coverage || '';
        const td4 = document.createElement('td'); td4.textContent = s.accessed || '';
        const td5 = document.createElement('td'); td5.textContent = s.license_note || '';
        tr.append(td1, td2, td3, td4, td5);
        tb.appendChild(tr);
    });
    host.appendChild(t);
}

function renderHero(data) {
    const rows = data.derived.decomposition_annual;
    const last = rows[rows.length - 1];
    const landed = last.metal_fx_leg + last.duty_leg + last.gst_leg;
    const fmt = (v) => '₹' + Math.round(v).toLocaleString('en-IN');

    buildHeroBar(data);
    buildStatTiles(data);

    $('#bigPrice').textContent = fmt(last.mumbai_inr_10g);
    $('#bigPriceFy').textContent = last.fy;
    $('#dataAsOf').textContent = data.meta.data_as_of;
    $('#dataAsOf2').textContent = data.meta.data_as_of;
    $('#answerLine')?.remove();
    // the answer is in the hero bar + tiles now, not a separate sentence
}

function wirePurchasing(data) {
    const occSel = $('#occupationSel'), cropSel = $('#cropSel');
    const occs = [...new Set(data.derived.gold_per_wageday.map(r => r.occupation))].sort();
    occs.forEach(o => { const o2 = document.createElement('option'); o2.value = o; o2.textContent = o; occSel.appendChild(o2); });
    const crops = [...new Set(data.derived.gold_per_mspkg.map(r => r.crop))];
    crops.forEach(c => { const o = document.createElement('option'); o.value = c; o.textContent = c; cropSel.appendChild(o); });
    cropSel.value = 'Wheat';

    const rerunWage = () => {
        const rows = buildWage(data, occSel.value);
        const last = rows[rows.length - 1];
        if (last && last.grams > 0) {
            $('#wageTitle').textContent = `One tola costs ${Math.round(TOLA / last.grams).toLocaleString('en-IN')} days of ${occSel.value} work (${last.fy})`;
        }
        wireTableToggle('#wageTableBtn', '#wageTable', () => tableFor(
            rows.map(r => ({ fy: r.fy, 'days per tola': (TOLA / r.grams).toFixed(0), 'grams per day': r.grams }))));
    };
    const rerunMsp = () => {
        const rows = buildMsp(data, cropSel.value);
        const last = rows[rows.length - 1];
        if (last && last.grams > 0) {
            $('#mspTitle').textContent = `One tola bought ${Math.round(TOLA / last.grams).toLocaleString('en-IN')} kg of ${cropSel.value} (${last.crop_year})`;
        }
        wireTableToggle('#mspTableBtn', '#mspTable', () => tableFor(
            rows.map(r => ({ crop_year: r.crop_year, 'kg per tola': (TOLA / r.grams).toFixed(0), 'grams per kg': r.grams }))));
    };
    occSel.addEventListener('change', rerunWage);
    cropSel.addEventListener('change', rerunMsp);
    rerunWage(); rerunMsp();
}

function wireStack(data) {
    $('#segAnnual').addEventListener('click', () => { setSeg(true); buildStack(data, 'annual'); });
    $('#segMonthly').addEventListener('click', () => { setSeg(false); buildStack(data, 'monthly'); });
    function setSeg(annual) {
        $('#segAnnual').setAttribute('aria-pressed', String(annual));
        $('#segMonthly').setAttribute('aria-pressed', String(!annual));
    }
    wireTableToggle('#stackTableBtn', '#stackTable', () => tableFor(
        data.derived.decomposition_annual.map(r => ({
            fy: r.fy, '₹/10g': r.mumbai_inr_10g, metal: r.metal_fx_leg,
            duty: r.duty_leg, gst: r.gst_leg, premium: r.premium_leg,
        }))));
}

async function boot() {
    const res = await fetch('dataset.json');
    if (!res.ok) throw new Error('dataset.json HTTP ' + res.status);
    const data = await res.json();
    window.__RGS = data;

    initTheme();
    initNav();
    initScrollAnim();

    const rebuild = () => {
        buildStack(data, $('#segAnnual').getAttribute('aria-pressed') === 'true' ? 'annual' : 'monthly');
        buildWage(data, $('#occupationSel').value);
        buildMsp(data, $('#cropSel').value);
    };
    initCharts(rebuild);
    window.__rebuildAll = () => {
        syncRem(); rebuild();
    };

    renderHero(data);
    buildStack(data, 'annual');
    buildHeroBar(data);
    buildStatTiles(data);
    wireSegControl(data);
    wirePurchasing(data);
    renderBreaks(data.policy.breaks);
    renderEpisodes(data.policy.episodes);
    renderSources(data.sources);
    wireCalculator(data);
    wireCsv(data);
}

boot().catch(err => {
    document.body.classList.add('fatal');
    const el = $('#fatalMsg');
    if (el) {
        el.classList.remove('hidden');
        el.textContent = 'The dataset failed to load: ' + err.message + ' — every number on this page renders from dataset.json; without it there is nothing to show.';
        const st = document.createElement('pre');
        st.id = 'fatalStack';
        st.textContent = err.stack || '(no stack)';
        el.after(st);
    }
});
