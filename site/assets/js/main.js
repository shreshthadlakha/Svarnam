/* main.js — boot: load dataset.json, hydrate the page. Renders ONLY from the dataset. */
import { initCharts, buildHero, buildStack, buildWage, buildMsp, tableFor } from './charts.js';
import { wireCalculator } from './calculator.js';
import { wireCsv, flatten } from './csv.js';

const $ = (s) => document.querySelector(s);

function fill(sel, rows, valueKey, labelFn) {
  const el = $(sel);
  el.innerHTML = '';
  rows.forEach((r, i) => {
    const o = document.createElement('option');
    o.value = r[valueKey];
    o.textContent = labelFn(r, i);
    if (i === 0) o.selected = true;
    el.appendChild(o);
  });
}

function renderSources(sources) {
  const host = $('#sourcesTable');
  const t = document.createElement('table');
  t.innerHTML = '<thead><tr><th>ID</th><th>Source</th><th>Coverage</th><th>Accessed</th><th>License note</th></tr></thead><tbody></tbody>';
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
    const tdFile = document.createElement('td');
    tdFile.textContent = s.file ? 'local: ' + s.file : '';
    tdFile.className = 'muted';
    td2.appendChild(tdFile);
    const td3 = document.createElement('td'); td3.textContent = s.coverage || '';
    const td4 = document.createElement('td'); td4.textContent = s.accessed || '';
    const td5 = document.createElement('td'); td5.textContent = s.license_note || '';
    tr.append(td1, td2, td3, td4, td5);
    tb.appendChild(tr);
  });
  host.appendChild(t);
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
    li.appendChild(document.createTextNode(
      e.usd_per_oz != null ? `${sign}$${e.usd_per_oz}/oz ` : `${e.direction} (size not documented) `));
    li.appendChild(document.createTextNode(' · ' + e.event));
    ul.appendChild(li);
  });
}

function renderBreaks(breaks, decomp) {
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

function wireStack(data) {
  $('#stackMode').addEventListener('change', (ev) => {
    buildStack(data, ev.target.value);
    $('#stackTable').innerHTML = '';
    const rows = ev.target.value === 'annual' ? data.derived.decomposition_annual : data.derived.decomposition_monthly;
    $('#stackTable').appendChild(tableFor(
      rows.map(r => ({ period: r.fy || r.month, '₹/10g': r.mumbai_inr_10g, metal: r.metal_fx_leg, duty: r.duty_leg, gst: r.gst_leg, premium: r.premium_leg }))));
  });
}

function wireSelectors(data) {
  const occSel = $('#occupationSel');
  const occs = [...new Set(data.derived.gold_per_wageday.map(r => r.occupation))].sort();
  occs.forEach((o, i) => {
    const opt = document.createElement('option');
    opt.value = o; opt.textContent = o;
    if (i === 0) opt.selected = true;
    occSel.appendChild(opt);
  });
  const cropSel = $('#cropSel');
  const crops = [...new Set(data.derived.gold_per_mspkg.map(r => r.crop))];
  crops.forEach((c, i) => {
    const opt = document.createElement('option');
    opt.value = c; opt.textContent = c;
    if (i === 0) opt.selected = true;
    cropSel.appendChild(opt);
  });
  const rerunWage = () => {
    buildWage(data, occSel.value);
    $('#wageTable').innerHTML = '';
    const rows = data.derived.gold_per_wageday.filter(r => r.occupation === occSel.value)
      .map(r => ({ fy: r.fy, 'wage ₹/day': r.wage_inr_day, grams: r.grams }));
    $('#wageTable').appendChild(tableFor(rows));
  };
  const rerunMsp = () => {
    buildMsp(data, cropSel.value);
    $('#mspTable').innerHTML = '';
    const rows = data.derived.gold_per_mspkg.filter(r => r.crop === cropSel.value)
      .map(r => ({ crop_year: r.crop_year, 'MSP ₹/kg': r.msp_inr_kg, grams: r.grams }));
    $('#mspTable').appendChild(tableFor(rows));
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

  $('#dataAsOf').textContent = data.meta.data_as_of;
  $('#dataAsOf2').textContent = data.meta.data_as_of;
  renderBreaks(data.policy.breaks);
  renderEpisodes(data.policy.episodes);
  renderSources(data.sources);

  initCharts();
  buildHero(data);
  buildStack(data, 'annual');
  $('#stackTable').appendChild(tableFor(
    data.derived.decomposition_annual.map(r => ({ period: r.fy, '₹/10g': r.mumbai_inr_10g, metal: r.metal_fx_leg, duty: r.duty_leg, gst: r.gst_leg, premium: r.premium_leg }))));
  wireStack(data);
  wireSelectors(data);
  wireCalculator(data);
  wireCsv(flatten(data));

  if (data.meta.provisional) {
    document.title = '[provisional] ' + document.title;
  }
}

boot().catch(err => {
  document.body.classList.add('fatal');
  const el = $('#fatalMsg');
  el.classList.remove('hidden');
  el.textContent = 'The dataset failed to load: ' + err.message + ' — every number on this page renders from dataset.json; without it there is nothing to show.';
});
