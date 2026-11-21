<div align="center">

# Svarnam

### What a tola of gold is actually made of.

**Metal · Dollar · Duty · GST · Premium** — India's rupee gold price, decomposed
from public data alone. FY1985-86 → today.

[![CI](https://github.com/{user}/svarnam/actions/workflows/ci.yml/badge.svg)](https://github.com/{user}/svarnam/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/code_license-MIT-blue.svg)](LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/data_license-CC_BY_4.0-lightgrey.svg)](DATA-LICENSE.md)
[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
![Model not advice](https://img.shields.io/badge/model--not--advice-%E2%9C%94-8a9a5b)

**[Live site](https://svarnam.vercel.app)** · [Dataset](site/dataset.json) · [Source registry](site/sources.md) · [Disclaimer](DISCLAIMER.md)

*Screenshot placeholder — drop a full-page capture here after first deploy.*

</div>

---

## Table of contents

- [Why this exists](#why-this-exists)
- [What's inside](#whats-inside)
- [How the numbers are made](#how-the-numbers-are-made)
- [Quickstart](#quickstart)
- [Updating the data](#updating-the-data)
- [Project structure](#project-structure)
- [Data sources](#data-sources)
- [Testing](#testing)
- [Roadmap](#roadmap)
- [FAQ](#faq)
- [Contributing](#contributing)
- [Credits & prior art](#credits--prior-art)
- [License](#license)
- [Disclaimer](#disclaimer)

## Why this exists

Every Indian has seen the chart: ₹18 per 10g in 1925 → ₹1.5 lakh today. None of
those charts say what the price is actually **made of**.

Svarnam decomposes the published Mumbai rupee gold price into four legs —

| Leg | What it captures |
|---|---|
| **Metal + FX** | London gold price × the US dollar |
| **Duty** | India's customs duty (a story of its own: 15% → 6% → 15% inside two years) |
| **GST** | 3% on the duty-paid value, since July 2017 |
| **Premium** | The signed residual — dealer premiums above landed cost, grey-market discounts below it |

— and then measures what gold *buys*: **grams per wage-day** (rural wages, 40
occupations) and **grams per MSP-kilogram** (official food prices). It is an
accounting identity, not a valuation model: the premium is displayed, never
judged. No forecasts, no targets, no recommendations — by design.

## What's inside

- **Hero decomposition** of the latest financial year with per-leg shares
- **41-year stacked decomposition** (FY1985-86 → FY2025-26) plus a **253-month view** (2005-10 → 2026-10)
- **9 annotated regime breaks** — Gold Control Act repeal, NRI scheme, FX unification, the 2000-01 source break, ad-valorem switch, 80:20 restriction, GST, the duty cycle, the SGB arc
- **15 documented premium/discount episodes** (Reuters "Asia Gold" dealer quotes, +$160/oz in Dec 2013 → −$207/oz in May 2026)
- **Grams per wage-day** across 40 occupations (Labour Bureau WRRI, 2006-07 → 2023-24)
- **Grams per MSP-kg** for wheat, paddy and tur (CACP, crop years 2010-11 →)
- **Client-side calculator** — your daily wage, in grams; nothing leaves the browser
- **Full CSV export** and a source registry where every number links to its provider, access date and license
- A **Sovereign Gold Bonds context card** — the scheme the government shut down because gold's rise made its own gold-linked borrowing too expensive

## How the numbers are made

For every period (an accounting identity — no assumptions, no fitted parameters):

```text
metal+FX leg = London $/oz ÷ 31.1034768 × 10 × USD/INR
duty leg     = day-weighted customs duty from the sourced calendar
               (specific ₹/10g era 1990-2011; BCD + AIDC + SWS ad-valorem era 2012→)
GST leg      = 3% on the duty-paid value from 1 Jul 2017 (day-weighted at the boundary)
landed cost  = metal+FX + duty + GST
premium leg  = Mumbai price − landed cost        (signed; a discount renders below baseline)
```

Ratio anchors: `grams per wage-day = wage ÷ (₹10g ÷ 10)` and
`grams per MSP-kg = (MSP ÷ 100) ÷ (₹10g ÷ 10)`.

The build is **validated, not trusted**:

- Golden values are pinned to the source files (never retyped) and checked on every build
- Every period must reconcile: the four legs sum back to the published price within ±0.5%
- The duty calendar must cover every day 1968→present with exactly one row — overlaps or gaps fail the build
- T35-implied FX is cross-checked against the official FX series (divergences are documented, not silenced)
- Every emitted row carries a source id, and `site/sources.md` renders the full registry with URLs, access dates and license notes

## Quickstart

Prerequisites: **Python 3.13+**, `pip`, and (optionally) GNU Make.

```bash
git clone https://github.com/{user}/svarnam.git
cd svarnam
python -m pip install pandas openpyxl lxml pytest

python -m pipeline.build     # validate → derive → emit site/dataset.json + sources.md
python -m pytest pipeline/tests -q
```

Then open `site/index.html` via any static server (it fetches `dataset.json`):

```bash
python -m http.server 8000 --directory site    # → http://localhost:8000
```

GNU Make users: `make build` · `make test` · `make serve` · `make refresh`.

The repo ships with **pinned baseline interims**, so the build works on a fresh
clone even before any raw data is downloaded — the validation suite treats a
missing raw file as a hard failure and tells you which one.

## Updating the data

**Automatic.** A scheduled GitHub Actions workflow
([`.github/workflows/refresh.yml`](.github/workflows/refresh.yml)) runs on the
1st of every month: it re-fetches FRED, LBMA (latest Wayback capture), the CACP
MSP feed, the WRRI wage tables and the RBI Handbook tables, re-parses, rebuilds
`dataset.json`, and commits the result — your host redeploys from that commit.
RBI edition changes are auto-discovered from the Handbook index.

By hand: `make refresh` (local, atomic `.bak`-protected replaces, per-source
report in `refresh_report.txt`). A failed fetch never corrupts anything —
staleness is flagged, never hidden.

A human is only needed for two cases: Goldhub's login-gated monthly domestic
series (optional backfill — the site stays current without it), and if RBI ever
redesigns their site structure (the refresh says so loudly).

## Project structure

```text
svarnam/
├── pipeline/          # build system (never deployed)
│   ├── parse_*.py     #   one parser per source family (RBI, LBMA, FRED, Goldhub, wages, MSP)
│   ├── policy.py      #   sourced duty calendar, regime breaks, premium episodes
│   ├── derive.py      #   decomposition legs + ratio anchors
│   ├── validate.py    #   golden values + invariants (build fails hard)
│   ├── build.py       #   emits site/dataset.json + sources.md + build_report.txt
│   ├── blocklist_check.py  # advice-language gate on the page copy
│   └── tests/         #   fixtures + golden-value + invariant tests
├── site/              # the only deployed directory
│   ├── index.html     #   renders exclusively from dataset.json — zero hardcoded numbers
│   ├── assets/        #   css, js (charts + annotation shim, calculator, CSV export), vendored Chart.js
│   ├── dataset.json   #   the single source of truth for the page
│   └── sources.md     #   the rendered source registry
├── data/              # raw downloads (gitignored + checksummed) · policy CSVs · pinned interims (all in git)
├── vercel.json        # static deploy config: serves site/ only, cache headers
└── build_report.txt   # validation ledger of the last build
```

## Data sources

| ID | Source | Used for |
|---|---|---|
| S01/S02/S04 | RBI Handbook of Statistics (Tables 35, 164, 133) | Mumbai ₹/10g, USD/INR, monthly gold |
| S03 | WGC Goldhub averages | Monthly USD (1978→), monthly domestic ₹ (2005-10→) |
| S05 | FRED DEXINUS (Fed H.10) | Daily USD/INR overlay, 1973→ |
| S06/S07 | Labour Bureau WRRI · DES AWI | Rural wages, 20 states · district wage history |
| S08 | CACP | Minimum Support Prices, crop years 2010-11→ (+ archive to 1982-83) |
| S09 | LBMA Gold Price PM | Free-market USD gold, 1968-04 → (Wayback-sourced) |
| S10–S15 | CBIC notifications via referencer.in, WGC analyses, Reuters, PIB | Duty calendar, GST, regime breaks, premium episodes, SGB arc |

Full registry with URLs, access dates and license notes:
[site/sources.md](site/sources.md). Raw downloads are checksummed
(`data/rbi/SHA256SUMS.txt`).

## Testing

- **Golden values** pinned to the source files — a transcribed digit fails the build (this caught a real one: FX 17.9428, not 17.9427)
- **Reconciliation invariant** — legs must sum back to the published price within ±0.5%, every period
- **Calendar invariant** — exactly one duty row per day, 1968 → present
- **Corruption tests** — the validator is tested against deliberately corrupted data
- **CI** — pytest plus an advice-language gate that scans the page copy on every push

## Roadmap

- **v1.1** — MSP deep history: OCR of the 1982-83 → 2010-11 archive compendiums
- **v2** — state-wise layer (WRRI covers 20 states), CEDA mandi prices, CPI-deflated overlay
- **v3** — multi-asset extension: the same identity for silver, real estate, equities

## FAQ

**Is this investment advice?** No. It decomposes published prices and compares
them with public statistics. No forecasts, no targets, no recommendations.

**Why annual?** The deepest honest history is annual (RBI Table 35,
FY1985-86 →). Monthly resolution (2005-10 →) is included and extends itself at
each refresh.

**Can I use the data?** Yes — [CC BY 4.0](DATA-LICENSE.md) with attribution;
underlying sources keep their own terms.

## Contributing

The most valuable contribution is a **data correction**: open an issue with the
source and the number. Corrections are logged publicly in
`site/sources.md` — building trust is the point of this project.

## Credits & prior art

- Genre inspiration: [Nate Lorenzen's *Gold Standard*](https://lorenzen.ai/tools/gold-standard/) — the honest-labels framing is a deliberate nod
- Prior art: Roy Jastram, *The Golden Constant* (England/US); WGC Qaurum
- Data: Reserve Bank of India, LBMA/ICE, World Gold Council, Labour Bureau,
  CACP, FRED, Reuters' "Asia Gold" reporting
- The colonial-era *Prices and Wages in India* yearbooks (1870s–1940s) — the
  deep-history unlock for a future version

## License

Code: [MIT](LICENSE) · Dataset & charts: [CC BY 4.0](DATA-LICENSE.md) ·
Underlying sources keep their own terms (summarized in [DATA-LICENSE.md](DATA-LICENSE.md)).

## Disclaimer

**Model, not advice.** This page decomposes published gold prices and compares
them with public wage and support-price statistics. It contains no forecasts,
no price targets, and no recommendation to buy, sell, or avoid anything. Every
number links to its public source; if a source revises, we revise.
