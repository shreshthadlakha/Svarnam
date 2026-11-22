/* calculator.js — FR5: pure client-side grams conversion. No network, no storage.
   Classic script so the page also works opened directly from disk; exposes window.SvarnamCalc. */
(() => {
const $ = (s) => document.querySelector(s);

function wireCalculator(data) {
  const rows = data.derived.decomposition_monthly;
  const latestMonthly = rows.length ? rows[rows.length - 1].mumbai_inr_10g : null;
  const pricePerGram = latestMonthly != null ? latestMonthly / 10 : null;

  const priceInput = $('#calcPrice');
  const wageInput = $('#calcWage');
  const out = $('#calcOut');
  const note = $('#calcNote');

  if (pricePerGram) {
    priceInput.value = Math.round(pricePerGram);
    note.textContent = `Gold side uses the latest monthly domestic average: ₹${latestMonthly.toLocaleString('en-IN')}/10g (Goldhub, flagged in the dataset). Wage side is whatever you type — we compare, we do not advise.`;
  } else {
    note.textContent = 'Monthly price unavailable — type a gold price per gram to compare.';
  }

  const compute = () => {
    const wage = parseFloat(wageInput.value);
    const price = parseFloat(priceInput.value);
    if (!isFinite(wage) || !isFinite(price) || wage <= 0 || price <= 0) {
      out.textContent = '—';
      return;
    }
    const grams = wage / price;
    out.textContent = `${grams.toFixed(4)} g`;
  };
  wageInput.addEventListener('input', compute);
  priceInput.addEventListener('input', compute);
  compute();
}

window.SvarnamCalc = { wireCalculator };
})();
