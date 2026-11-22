/* csv.js — FR9: client-side CSV export, generated from dataset.json only.
   Classic script so the page also works opened directly from disk; exposes window.SvarnamCsv. */
(() => {
function esc(v) {
  if (v == null) return '';
  const s = String(Array.isArray(v) ? v.join('|') : (typeof v === 'object' ? JSON.stringify(v) : v));
  return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

function rowsToCsv(rows) {
  if (!rows || !rows.length) return '(no rows)\n';
  const keys = Object.keys(rows[0]);
  return keys.join(',') + '\n' + rows.map(r => keys.map(k => esc(r[k])).join(',')).join('\n') + '\n';
}

function toCsv(data) {
  const out = [];
  out.push('# svarnam dataset export');
  out.push('# generated: ' + data.meta.generated + ' | data_as_of: ' + data.meta.data_as_of + ' | provisional: ' + data.meta.provisional);
  out.push('');
  for (const [name, rows] of Object.entries(data.series)) {
    out.push('### series: ' + name);
    out.push(rowsToCsv(rows));
  }
  for (const [name, rows] of Object.entries(data.derived)) {
    out.push('### derived: ' + name);
    out.push(rowsToCsv(rows));
  }
  for (const [name, rows] of Object.entries(data.policy)) {
    out.push('### policy: ' + name);
    out.push(rowsToCsv(rows));
  }
  out.push('### sources');
  out.push(rowsToCsv(data.sources.map(s => ({ id: s.id, name: s.name, url: s.url, coverage: s.coverage, accessed: s.accessed, license_note: s.license_note }))));
  return out.join('\n');
}

/* flatten is used by main.js to keep a single reference for the export. */
function flatten(data) {
  return data;
}

function wireCsv(data) {
  const download = () => {
    const blob = new Blob([toCsv(data)], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'svarnam-dataset.csv';
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 800);
  };
  ['csvBtn', 'csvBtnFooter'].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.addEventListener('click', (e) => { e.preventDefault(); download(); });
  });
}

window.SvarnamCsv = { wireCsv };
})();
