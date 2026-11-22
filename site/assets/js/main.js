/* main.js — boot: load dataset.json once, hydrate everything from it. Zero hardcoded numbers. */
import { initCharts, syncRem, buildFlagship, buildMonthly, buildWage, buildMsp, buildHeroRows, tableFor, TOLA_G } from './charts.js';
import { wireCalculator } from './calculator.js';
import { wireCsv } from './csv.js';

const $ = (s) => document.querySelector(s);

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
        // rupee convention: dealer quotes are converted to ₹/10g at the episode
        // month's average USD/INR (computed at build); the USD quote stays in the
        // source record for provenance.
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
    t.innerHTML = '<caption>Svarnam source registry — every figure resolves to one of these ids</caption><thead><tr><th>ID</th><th>Source</th><th>Coverage</th><th>Accessed</th><th>License note</th></tr></thead><tbody></tbody>';
    const tb = t.querySelector('tbody');
    sources.forEach(s => {
        const tr = document.createElement('tr');
        const td1 = document.createElement('td');
        const code = document.createElement('code');
        code.textContent = s.id;
        td1.appendChild(code);
        const td2 = document.createElement('td');
        const a = document.createElement('a');
        a.href = s.url; a.textContent = s.name; a.target = '_blank'; a.rel = 'noopener';
        td2.appendChild(a);
        const td3 = document.createElement('td'); td3.textContent = s.coverage || '';
        const td4 = document.createElement('td'); td4.textContent = s.accessed || '';
        const td5 = document.createElement('td'); td5.textContent = s.license_note || '';
        tr.append(td1, td2, td3, td4, td5);
        tb.appendChild(tr);
    });
    host.appendChild(t);
}

function renderHeroRows(data) {
    const last = buildHeroRows(data);
    const landed = last.landed_cost;
    const metalShare = (last.metal_fx_leg / landed * 100).toFixed(1);
    // answer line: question-with-answer pairing (dive_01 implication 4)
    $('#answerLine').textContent =
        `Answer: ${metalShare}% of the FY${last.fy} price is metal plus the dollar — the rest is duty, GST and a ${(last.premium_leg / landed * 100).toFixed(1)}% discount.`;
}

function wirePurchasing(data) {
    const occSel = $('#occupationSel');
    const occs = [...new Set(data.derived.gold_per_wageday.map(r => r.occupation))].sort();
    occs.forEach(o => {
        const opt = document.createElement('option');
        opt.value = o; opt.textContent = o;
        occSel.appendChild(opt);
    });
    // default: the longest-span representative occupation (dive_02 rec 7)
    const spans = new Map();
    data.derived.gold_per_wageday.forEach(r => {
        spans.set(r.occupation, (spans.get(r.occupation) || 0) + 1);
    });
    let best = occs[0], bestN = -1;
    spans.forEach((n, o) => { if (n > bestN) { bestN = n; best = o; } });
    occSel.value = best;

    const cropSel = $('#cropSel');
    const crops = [...new Set(data.derived.gold_per_mspkg.map(r => r.crop))];
    crops.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c; opt.textContent = c;
        cropSel.appendChild(opt);
    });
    cropSel.value = 'Wheat';

    const rerunWage = () => {
        const rows = buildWage(data, occSel.value);
        const last = rows[rows.length - 1];
        if (last) {
            const days = TOLA_G / last.grams;
            $('#wageTitle').textContent =
                `One tola costs ${Math.round(days).toLocaleString('en-IN')} days of ${occSel.value} work (${last.fy})`;
        }
        $('#wageTable').innerHTML = '';
        const vis = rows.map(r => ({ fy: r.fy, 'days per tola': (TOLA_G / r.grams).toFixed(0), 'grams per day': r.grams }));
        $('#wageTable').appendChild(tableFor(vis));
    };
    const rerunMsp = () => {
        const rows = buildMsp(data, cropSel.value);
        const last = rows[rows.length - 1];
        if (last) {
            $('#mspTitle').textContent =
                `One tola bought ${Math.round(TOLA_G / last.grams).toLocaleString('en-IN')} kg of ${cropSel.value} (${last.crop_year})`;
        }
        $('#mspTable').innerHTML = '';
        const vis = rows.map(r => ({ crop_year: r.crop_year, 'kg per tola': (TOLA_G / r.grams).toFixed(0), 'grams per kg': r.grams }));
        $('#mspTable').appendChild(tableFor(vis));
    };
    occSel.addEventListener('change', rerunWage);
    cropSel.addEventListener('change', rerunMsp);
    rerunWage(); rerunMsp();
}

async function boot() {
    const res = await fetch('dataset.json');
    if (!res.ok) throw new Error('dataset.json HTTP ' + res.status);
    const data = await res.json();
    window.__RGS = data;

    // freshness split (dive_05 rec 6): data vintage + last review date
    const months = data.derived.decomposition_monthly;
    const wages = data.derived.gold_per_wageday;
    $('#monthlyLast').textContent = months.length ? months[months.length - 1].month : '…';
    $('#dataAsOf2').textContent = data.meta.data_as_of;

    renderBreaks(data.policy.breaks);
    renderEpisodes(data.policy.episodes);
    renderSources(data.sources);

    initCharts(() => {
        buildFlagship(data); buildMonthly(data);
        const occ = $('#occupationSel').value, crop = $('#cropSel').value;
        if (occ) buildWage(data, occ);
        if (crop) buildMsp(data, crop);
    });
    buildFlagship(data);
    buildMonthly(data);
    buildHeroRows(data);
    renderHeroRows(data);
    wirePurchasing(data);
    wireCalculator(data);
    wireCsv(data);
}

boot().catch(err => {
    document.body.classList.add('fatal');
    const el = $('#fatalMsg');
    el.classList.remove('hidden');
    el.textContent = 'The dataset failed to load: ' + err.message + ' — every number on this page renders from dataset.json; without it there is nothing to show.';
    const st = document.createElement('pre');
    st.id = 'fatalStack';
    st.textContent = err.stack || '(no stack)';
    el.after(st);
});
