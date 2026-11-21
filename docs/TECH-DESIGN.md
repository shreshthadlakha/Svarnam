# Rupee Gold Stack — Technical Design

**Version:** 1.0 · **Date:** 21 Nov 2026 · **Status:** Approved
**Reads with:** [PRD.md](PRD.md) · [CODE-STRUCTURE.md](CODE-STRUCTURE.md) · KT bundle §3 (verified data spine) and §4 (verified fact base)

---

## 1. Architecture overview

Three components; only the third is deployed.

```
┌───────────────────────────────┐     ┌──────────────────────┐     ┌─────────────────────────┐
│  (a) PIPELINE (local Python)  │ ──▶ │  (b) DATASET ARTIFACT │ ──▶ │ (c) STATIC PAGE         │
│  parsers → normalize →        │     │  dataset.json         │     │  index.html + Chart.js  │
│  derive → validate            │     │  sources.md           │     │  (GitHub Pages)         │
│  never shipped                │     │  build_report.txt     │     │  renders only from JSON │
└───────────────────────────────┘     └──────────────────────┘     └─────────────────────────┘
```

- **(a)** Runs on the dev machine. Reads `data/raw/` (downloaded source files, immutable), writes `data/interim/` (one normalized CSV per series with provenance headers) and emits (b).
- **(b)** The single source of truth. Versioned in git. The page never contains a hardcoded number.
- **(c)** Vanilla HTML/JS. No framework, no backend, no cookies, no analytics.

## 2. Data flow

```
data/raw/{rbi,lbma,goldhub,fred,wages,msp}
        │  parse_* modules (one per source family)
        ▼
data/interim/*.csv          ← one file per series; provenance header comment; flags column
        │  policy.py (hand-curated, sourced constants — duty calendar, breaks, episodes)
        ▼
pipeline/derive.py          ← decomposition legs, ratio anchors (formulas in §4)
        │  validate.py       ← golden values + reconciliation invariants (§8)
        ▼
pipeline/build.py  ──▶  site/dataset.json + site/sources.md + build_report.txt
```

## 3. Pipeline modules (one responsibility each)

| Module | Responsibility | Input → output |
|---|---|---|
| `sources.py` | Registry of every source: id (S01…), name, URL, local file, coverage, access date, license note. RBI entries record **edition + table number** (they drift between editions) | — → `SOURCES` dict |
| `parse_rbi.py` | Handbook **Table 35** (Mumbai ₹/10g annual FY1985-86→; London $/oz; RBI's own converted ₹ column + spread) and **Table 133** (USD/INR FY annual, FY1986-87→, with regime notes). Handles the known XLSX layout quirks | `data/raw/rbi/*.xlsx` → interim CSVs |
| `parse_goldhub.py` | WGC Goldhub averages: monthly USD from 1978-01; **INR column = Indian domestic price, Oct 2005→** (byte-verified vs T35 FY averages ±0.06% — treat as domestic-monthly, NOT world-INR; enables monthly decomposition 2005-10→) | `data/raw/goldhub/*.xlsx` → interim |
| `parse_lbma.py` | LBMA Gold Price PM daily JSON: merge Wayback historical copy (1968-04-01→2023-09-01) with live tail; dedupe on date; keep source-flag per row | `data/raw/lbma/*.json` → interim |
| `parse_fred.py` | DEXINUS daily USD/INR from 1973-01-02 | `data/raw/fred/*.csv` → interim |
| `parse_wages.py` | WRRI monthly (20 states, occupations; official DB 2006-07→2023-24) + optional AWI district annual (1950-51→, lag-flagged); annualize to FY averages; Das-Usami extension if used (flag: break at Nov 2013) | `data/raw/wages/*` → interim |
| `parse_msp.py` | CACP MSP: clean table (2010-11→) + PDF archive stitching (1982-83→, gap 1985-86 flagged); wheat/rice/tur minimum; crop-year labels | `data/raw/msp/*` → interim |
| `policy.py` | Hand-curated, every row sourced: duty calendar (period-keyed, specific-rate era 1990-2011 AND ad-valorem era 2012→; see KT §4.1 for the verified table), GST from 2017-07-01, 9 regime breaks, premium episodes, SGB arc | `data/policy/*.csv` → policy dict |
| `derive.py` | Decomposition + ratios (§4). Duty is selected per period from the calendar — **never a single constant** | interim + policy → derived tables |
| `validate.py` | §8 golden values + invariants; build fails hard on any mismatch | derived → pass/fail |
| `build.py` | CLI entry (`python -m pipeline.build`): emit `site/dataset.json`, `site/sources.md`, `build_report.txt` (row counts, gaps, flags) | — → artifacts |
| `units.py` | The one place for constants: troy oz = 31.1034768 g; quintal = 100 kg; FY = Apr–Mar | — |

## 4. Model specification

### 4.1 Decomposition (an identity, not a model)

For each FY (or month where available):

```
metal_fx_leg  = (london_usd_oz / 31.1034768) × 10 × usdinr          # ₹ per 10g at world price + official FX
duty_leg      = metal_fx_leg × d(t)                                  # d(t) from the duty calendar at t
gst_leg       = (metal_fx_leg + duty_leg) × 0.03                     # GST compounds on duty-paid value (from 2017-07-01)
landed_cost   = metal_fx_leg + duty_leg + gst_leg
premium_leg   = mumbai_inr_10g − landed_cost                         # signed; negative = discount
```

- Before GST (pre-Jul 2017): `gst_leg = 0` (the tool's stack starts at duty; earlier local VAT/excise layers are not reconstructable cleanly — noted in sources).
- Specific-rate duty era (1990–2011): duty leg is computed from ₹/10g constants directly (e.g., ₹300/10g in 2010 ≈ 1.08% ad-valorem equivalent — recorded, not assumed).
- **Intra-FY changes (time-weighting rule, fixed at design time):** for any FY containing k duty-calendar periods, that FY's duty leg uses the day-weighted average `d̄ = Σ(dᵢ·daysᵢ)/Σ(daysᵢ)`; the same rule covers the GST leg switching on mid-FY2017-18 (0 before 1 Jul 2017, 0.03 after). The premium residual absorbs rounding, so the reconciliation invariant (§8.2) holds for transition FYs (2012-13, 2013-14, 2017-18, 2019-20, 2021-22, 2022-23, 2024-25) — golden values for those FYs must be computed with this rule, never an end-FY rate.
- Pre-March-1993 FX is the official rate; the chart annotates it ("official FX regime" band). Pre-1990 is **not modeled** (GCA prohibition; annotate only).
- **All-in import wedge** for display: `(1+d)×1.03 − 1` → 18.45% at 15% duty, 9.18% at 6% — shown in the policy card, not as a chart element.

**Worked example — FY2025-26** (golden check): London avg $3,937.86/oz, FX 88.3071, Mumbai ₹118,420.90/10g, duty in effect = 6% (the 15% re-hike of 13 May 2026 falls in FY2026-27 — the calendar must get this right):

```
metal_fx_leg = (3937.86 / 31.1034768) × 10 × 88.3071 = ₹111,801.33
duty_leg     = ₹6,708.08    (6%)
gst_leg      = ₹3,555.28    (3% on duty-paid value)
landed_cost  = ₹122,064.69
premium_leg  = −₹3,643.79   → premium_pct ≈ −2.99%
```

Check: 111,801.33 + 6,708.08 + 3,555.28 − 3,643.79 = 118,420.90 ✓ (machine-verified 21 Nov 2026 — never retype golden values by hand; generate them from the files). Shares of the Mumbai price: metal+FX 94.4%, duty 5.7%, GST 3.0%, premium −3.1%. (Approximate to rounding; validate.py enforces the ±0.5% reconciliation.)

### 4.2 Ratio anchors

```
gold_per_wageday(fy) = wage_inr_day(fy, occupation) / (mumbai_inr_10g / 10)        # grams of gold one day's wage buys
gold_per_mspkg(yr)   = (msp_inr_quintal(yr, crop) / 100) / (mumbai_inr_10g / 10)   # grams of gold one kg of crop buys
```

- Wage annualization: FY average of monthly WRRI values; label occupation + state (default: all-India aggregate as published; AWI adds district depth later).
- MSP year = crop year as published by CACP (Kharif/Rabi marketing year); wheat/rice/tur in V1.
- No CPI deflation anywhere in V1: ratios are already real comparisons; the decomposition is nominal by design (it is a price *accounting*). CPI-deflated gold = V2 candidate (MoSPI CPI).

### 4.3 FX spine normalization

- FY1985-86: Table 133 starts FY1986-87 — use Table 35's own London-converted ₹ column for 1985-86, flag the source; cross-check T35-implied FX against T133 from FY1986-87 onward (validation, not replacement).
- Daily FRED DEXINUS is the market-rate overlay for narrative charts only; V1 decomposition uses annual averages.

## 5. `dataset.json` schema (v1)

```jsonc
{
  "meta": { "generated": "ISO8601", "generator_version": "1.0", "provisional": true,
             "data_as_of": "2026-11-21", "repo": "rupee-gold-stack" },
  "sources": [ { "id": "S01", "name": "RBI Handbook of Statistics on the Indian Economy 2025-26, Table 35",
                 "url": "...", "coverage": "FY1985-86..FY2025-26", "accessed": "2026-11-20",
                 "license_note": "public sector reuse with attribution" } ],
  "series": {
    "gold_inr_annual":  [ { "fy": "FY1985-86", "mumbai_inr_10g": 2125.47, "london_usd_oz": 327.75,
                             "source": "S01", "flags": [] } ],
    "gold_usd_monthly": [ { "month": "1978-01", "usd_oz": null, "source": "S03", "flags": [] } ],
    "fx_annual":        [ { "fy": "FY1986-87", "usdinr_avg": 12.7782, "regime": "official",
                             "source": "S04", "flags": [] } ],
    "wage_annual":      [ { "fy": "FY2006-07", "state": "ALL-INDIA", "occupation": "…", "series": "WRRI",
                             "inr_day": null, "source": "S06", "flags": [] } ],
    "msp_annual":       [ { "crop": "wheat", "crop_year": "1982-83", "inr_quintal": null,
                             "source": "S08", "flags": ["stitched"] } ]
  },
  "policy": {
    "duty_calendar": [ { "from": "1990-06-06", "to": "1992-02-29", "type": "specific",
                          "inr_10g": 250, "source": "S10" },
                        { "from": "2026-05-13", "to": null, "type": "advalorem",
                          "bcd": 0.10, "aidc": 0.05, "source": "S12" } ],
    "gst":     { "from": "2017-07-01", "rate": 0.03, "base": "duty_paid_value", "source": "S11" },
    "breaks":  [ { "date": "1990-06-06", "label": "Gold Control Act repealed — pre-1991 price not free-market",
                   "source": "S10" } ],
    "episodes":[ { "date": "2013-12-15", "usd_oz": 160, "direction": "premium",
                   "event": "80:20 import restriction", "source": "S13" } ]
  },
  "derived": {
    "decomposition_annual": [ { "fy": "FY2025-26", "mumbai_inr_10g": 118420.90,
                                "metal_fx_leg": 111805.9, "duty_leg": 6708.4, "gst_leg": 3554.4,
                                "premium_leg": -3647.8, "premium_pct": -2.99,
                                "duty_in_effect": 0.06, "flags": [] } ],
    "gold_per_wageday": [ { "fy": "…", "occupation": "…", "grams": null, "source": "S06" } ],
    "gold_per_mspkg":   [ { "crop_year": "…", "crop": "wheat", "grams": null, "source": "S08" } ]
  }
}
```

Schema rules: every row carries `source`; `flags` is the honesty channel (`stitched`, `interpolated`, `regime-official-fx`, `source-break`, `lagged`); unknown values are `null` — never zero, never imputed silently.

## 6. Page design

- **Stack:** one `index.html` + vanilla ES-module JS + **Chart.js 4 vendored** (`vendor/chart.umd.min.js`, pinned + SRI). Chosen over ECharts for weight (~65 KB gz vs ~350 KB) — sufficient for stacked columns and lines. A ~80-line custom annotation plugin draws regime-break markers and premium-episode callouts (Chart.js has no built-in annotation without the paid-style plugin; the shim is deterministic and testable). If annotation needs outgrow the shim, ECharts is the documented fallback.
- **Charts:** (1) decomposition = stacked columns, signed premium segment; (2–3) ratio lines with selectable occupation/crop; (4) optional monthly USD overlay line, toggled off by default.
- **Renderer discipline:** the page reads `dataset.json` and nothing else; the FR5 calculator is pure client-side arithmetic.
- **Performance budget:** total < 500 KB (PRD A5) — dataset ~40 KB, Chart.js ~210 KB min, CSS+JS+HTML < 60 KB, fonts: system stack only (no webfonts).
- **A11y:** charts get descriptive `aria-label`s + a "view data as table" link per chart (the CSV/table fallback doubles as the accessibility path).

## 7. Hosting & deployment

- **Vercel (chosen by owner, 2026-11-22):** static deploy of `/site` only — `vercel.json` pins `outputDirectory: site` (docs/, pipeline/, data/ are never served), sets `Cache-Control: must-revalidate` on `dataset.json`/`sources.md` (fresh data on every visit) and `immutable` on the vendored Chart.js. Flow: connect the GitHub repo on vercel.com → every push to main redeploys → **the monthly auto-refresh commit redeploys the site automatically** (Vercel watches the repo; no Vercel-side cron needed). Hobby plan is free for this non-commercial project.
- Alternative kept: GitHub Pages via `.github/workflows/pages.yml` — switched to `workflow_dispatch`-only so it never auto-runs against a non-enabled Pages repo. Either host, never both live without choosing a canonical URL.
- No server, no env vars, no secrets, no analytics in V1. If ever wanted, privacy-preserving only — decision deferred.
- Repo: `rupee-gold-stack`. License: **MIT for code, CC BY 4.0 for dataset & charts** (rationale in LAUNCH-KIT §4).

## 8. Testing strategy

1. **Golden values** (from verified spot checks, KT §4.5): FY1985-86 ₹2,125.47 / $327.75; FY1991-92 ₹4,297.63; FY2024-25 ₹75,841.87 / $2,584.53; FY2025-26 ₹118,420.90 / $3,937.86; FX FY1990-91 17.9428; LBMA first row 1968-04-01 $37.70; FRED DEXINUS start 1973-01-02; FY2025-26 decomposition within ±0.5% (§4.1).
2. **Reconciliation invariant:** for every year, |metal+FX + duty + GST + premium − Mumbai| ≤ 0.5% of Mumbai.
3. **Source-completeness invariant:** every emitted row has a source id present in `sources.py`; every source id resolves to a URL + access date.
4. **Calendar invariant:** decomposition for any date uses exactly one duty-calendar row; overlap/gap ⇒ build fails.
5. **CI blocklist gate:** grep of the tag-stripped visible copy of `site/` (HTML tags/attributes removed, `assets/vendor/` excluded) for the advice-language blocklist (PRD A7) — `target="_blank"` and `event.target` must not trip it.
6. **Parser fixtures:** committed trimmed samples of each raw file format; parser unit tests run against fixtures (raw files stay out of unit tests — too big/licensed).

## 9. Update procedure (see LAUNCH-KIT §5 for the runbook)

`python -m pipeline.build` regenerates everything from `data/raw/` + `data/policy/`. A new RBI Handbook edition = drop the new XLSX, update `sources.py` edition+table numbers, re-run, review `build_report.txt` diff. A duty change = one new `duty_calendar` row with its notification source. The page never needs a code change for data updates.
