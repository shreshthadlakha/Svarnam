# Rupee Gold Stack — Repository & Code Structure

**Version:** 1.0 · **Date:** 21 Nov 2026
**Repo name (working title):** `rupee-gold-stack` · Stack: Python 3.13 pipeline, vanilla JS page

---

## 1. Repository tree

```
rupee-gold-stack/
├── README.md                    # public face: what this is, honesty labels, "data as of", links
├── LICENSE                      # MIT (code)
├── DATA-LICENSE.md              # CC BY 4.0 for dataset.json + charts; third-party source terms summarized
├── DISCLAIMER.md                # model-not-advice text (also rendered in page footer — LAUNCH-KIT §1)
├── docs/                        # copies of this suite: PRD, TECH-DESIGN, CODE-STRUCTURE, PLAN, LAUNCH-KIT
│
├── data/                        # never shipped; git-tracked where size permits, else documented fetch scripts
│   ├── raw/                     # downloaded source files — IMMUTABLE, never hand-edited
│   │   ├── rbi/                 #   t35_gold_annual.xlsx, t133_fx_fy.xlsx, t164…, t132…, t205…, t223…
│   │   ├── lbma/                #   gold_pm_wayback.json, gold_pm_live.json
│   │   ├── goldhub/             #   Gold_price_averages…since_1978.xlsx
│   │   ├── fred/                #   DEXINUS.csv
│   │   ├── wages/               #   WRRI exports (+ AWI if included)
│   │   └── msp/                 #   CACP PDFs + extracted CSVs (stitching worksheets)
│   ├── policy/                  # hand-curated, every row sourced:
│   │   ├── duty_calendar.csv    #   period-keyed duty (specific-rate era AND ad-valorem era)
│   │   ├── breaks.csv           #   the 9 regime breaks
│   │   └── episodes.csv         #   documented premium/discount episodes
│   └── interim/                 # generated — one normalized CSV per series, provenance header + flags
│
├── pipeline/                    # local build system (never deployed)
│   ├── __init__.py
│   ├── units.py                 # constants: oz→g, quintal→kg, FY definition — the ONLY place
│   ├── sources.py               # source registry S01…: name, URL, file, coverage, accessed, license
│   ├── parse_rbi.py             # Handbook Table 35 + Table 133
│   ├── parse_goldhub.py         # Goldhub INR monthly since 1978
│   ├── parse_lbma.py            # LBMA daily JSON (wayback + live merge, dedupe)
│   ├── parse_fred.py            # DEXINUS daily USD/INR
│   ├── parse_wages.py           # WRRI (+ AWI), FY annualization
│   ├── parse_msp.py             # CACP clean table + PDF-archive stitch
│   ├── policy.py                # loads data/policy/*.csv into typed structures
│   ├── derive.py                # decomposition legs + ratio anchors (TECH-DESIGN §4)
│   ├── validate.py              # golden values + reconciliation/source/calendar invariants
│   ├── build.py                 # CLI: python -m pipeline.build → site artifacts
│   ├── report.py                # build_report.txt: row counts, gaps, flags, coverage map
│   └── tests/
│       ├── fixtures/            # trimmed raw-format samples (committed)
│       ├── test_parse_rbi.py    # …one test module per parser
│       ├── test_derive.py       # worked example FY2025-26; calendar selection
│       └── test_validate.py     # invariant behavior incl. intentional failure cases
│
├── site/                        # the only deployed directory (GitHub Pages)
│   ├── index.html               # single page; no hardcoded numbers — renders from dataset.json
│   ├── dataset.json             # build artifact (copied from pipeline output)
│   ├── sources.md               # build artifact (human-readable source table)
│   └── assets/
│       ├── css/main.css
│       ├── js/main.js           # bootstrap: fetch dataset.json, wire selectors, render
│       ├── js/charts.js         # chart builders + regime-break/premium-episode annotation shim
│       ├── js/calculator.js     # FR5 client-side grams calculator
│       ├── js/csv.js            # FR9 client-side CSV export from dataset.json
│       └── vendor/chart.umd.min.js   # pinned Chart.js 4 + SRI hash
│
├── Makefile                     # make build / make update / make serve / make test
├── .github/workflows/
│   ├── ci.yml                   # pytest + blocklist grep gate (PRD A7) on PR
│   └── pages.yml                # deploy site/ on push to main
└── .gitignore                   # data/raw contents (too big/licensed) except checksums; interim; __pycache__
```

## 2. Data-flow contract between layers

```
data/raw/*  ──parse_*──▶  data/interim/*.csv  ──derive──▶  derived tables  ──build──▶  site/dataset.json
                                   ▲                                              (only deployed surface)
data/policy/*.csv ──policy.py──┘
```

Rules:
1. `raw/` is immutable; re-downloads replace whole files, never patches.
2. Every `interim/*.csv` carries a provenance header:
   ```
   # series: gold_inr_annual
   # source: S01 RBI Handbook 2025-26 Table 35 (accessed 2026-11-20)
   # notes: FY averages; source break 1999-2000/2000-01
   fy,mumbai_inr_10g,london_usd_oz,flags
   ```
3. `site/` contains **only** build outputs + static assets; no page logic may read any other data source.
4. Policy tables are hand-curated and reviewable in git — the duty change of 13 May 2026 is one CSV row with its notification URL, not code.

## 3. Source-ID scheme

| ID | Source |
|---|---|
| S01 | RBI Handbook 2025-26 Table 35 (gold annual) — cite edition + table number |
| S02 | RBI Handbook Table 164 (gold monthly, short) |
| S03 | WGC Goldhub averages xlsx (INR from 1978) |
| S04 | RBI Handbook Table 133 (FX annual) |
| S05 | FRED DEXINUS |
| S06 | Labour Bureau WRRI |
| S07 | DES Agricultural Wages in India (AWI) |
| S08 | CACP MSP (clean table + archive) |
| S09 | LBMA Gold Price PM JSON |
| S10 | Gold Control Act repeal + customs notification history (referencer.in compilation) |
| S11 | GST 3% (Jul 2017) references |
| S12 | May 2026 re-hike (Reuters + notification 15/2026 coverage) |
| S13 | Reuters "Asia Gold" premium episodes (dated list in dive_05) |
| S14 | WGC duty analyses (2021, 2024) |
| S15 | SGB arc (PIB/RBI/Moneycontrol/Wikipedia) |

Full URLs and access dates live in `pipeline/sources.py` (single registry) and render into `site/sources.md`.

## 4. Conventions

- **Python:** 3.13, type hints everywhere, `pytest`, no dependencies beyond `pandas`, `openpyxl`, `lxml` (stdlib for the rest). Every parser module ≤ ~200 lines; one parser per source family; no cross-parser imports.
- **JS:** ES modules, no framework, no build step; functions take (data, options) and return chart configs — charts.js stays declarative; annotation shim is the only stateful code.
- **Numbers:** `null` = unknown; `flags` = the honesty channel; no silent imputation anywhere. Indian-format rendering (₹, lakh/crore) happens only at display time in JS.
- **Git:** `main` deployable; feature branches; commit message convention `area: change` (e.g., `pipeline: stitch MSP 1996-97 rice from CACP archive`). Data diffs reviewed like code diffs.
- **Secrets:** none exist; the project has no keys by design.

## 5. What lives where (project workspace vs repo)

| Item | Workspace (now) | Repo (at M0) |
|---|---|---|
| KT bundle | `docs/Rupee-Gold-Stack-Knowledge-Transfer.md` | summarized into README + docs/ |
| Doc suite | `docs/PRD.md`, `TECH-DESIGN.md`, `CODE-STRUCTURE.md`, `PLAN.md`, `LAUNCH-KIT.md` | copied into `docs/` |
| Dive evidence | `research/dive_01–06.md` | distilled into sources.py + docs (raw dives stay in workspace) |
| Downloaded data | `data/rbi/*` (+ `data/wages/`, `data/msp/`, `data/policy/`) | moved to `data/raw/{rbi,lbma,goldhub,fred,wages,msp}/` at M0 |
| Policy tables | dive_05 tables | transcribed to `data/policy/*.csv` |
