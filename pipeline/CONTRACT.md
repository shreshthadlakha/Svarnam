# Interim CSV contract (parsers → derive)

Every parser emits ONE file per series into `data/interim/`. Rules (CODE-STRUCTURE §2):

1. First lines are `#` provenance comments: `# series: <name>`, `# source: <S-id> <name> (accessed <date>)`, `# notes: <method/flags>`. Then the CSV header row, then data rows.
2. `source_flag` is the honesty channel. Vocabulary: `` (empty = clean), `interpolated`, `stitched`, `regime-official-fx`, `source-break`, `lagged`, `partial-year`, `recommended-only`, `derived`.
3. `null`/unknown = empty cell — never zero, never silently imputed.
4. Dates ISO `YYYY-MM-DD`; months `YYYY-MM`; financial years `YYYY-YY` (e.g. `1985-86`).
5. Constants come from `pipeline/units.py` ONLY (troy oz = 31.1034768 g; quintal = 100 kg).
6. Parsers are pure readers: no network calls, no edits to `data/raw/`.

## Files and exact columns

| File | Columns | Producer |
|---|---|---|
| `gold_inr_annual.csv` | `fy,mumbai_inr_10g,london_usd_oz,london_converted_inr_10g,spread_inr,source_flag` | parse_rbi (T_35; 41 rows FY1985-86→2025-26) |
| `fx_annual.csv` | `fy,usdinr_avg,usdinr_endyear,regime_flag` | parse_rbi (T_133; 40 rows FY1986-87→2025-26; regime_flag: `official` (1986-87..1991-92), `lerms` (1992-93), `fedai-market` (1993-94..2011-12), `rbi-ref` (2012-13..2017-18), `fbil` (2018-19..)) |
| `lbma_daily.csv` | `date,usd_oz,source_flag` | parse_lbma (merged wayback+live, deduped; flag `live`/`wayback`) |
| `fx_daily.csv` | `date,usdinr,source_flag` | parse_fred (DEXINUS; `.` rows skipped) |
| `gold_usd_monthly.csv` | `month,usd_oz,source_flag` | parse_goldhub (Monthly_Avg USD column, 1978-01→2026-10; `#N/A` skipped) |
| `gold_inr_domestic_monthly.csv` | `month,inr_10g_domestic,source_flag` | parse_goldhub (INR column ÷ OZ × 10 — byte-verified as the Indian DOMESTIC price, Oct 2005→2026-10; flag `derived`) |
| `wage_annual.csv` | `fy,state,occupation_group,occupation,series,inr_day,inr_day_female,n_months,source_flag` | parse_wages (WRRI raw → FY means over numeric months only; fy normalized `2006-07`; flag `partial-year` when n_months<12) |
| `msp_annual.csv` | `crop,crop_year,inr_quintal,source_flag` | parse_msp (CACP /Home/MSP fixed-table; crop-year as published; rabi MY = crop year + 1) |

## Verification anchors (parsers must reproduce exactly)

- T35: FY1985-86 = 2125.47 / 327.75; FY2025-26 = 118420.90 / 3937.86
- T133: FY1986-87 avg = 12.7782; FY1990-91 avg = **17.9428** (not 17.9427 — file is truth); FY2025-26 avg = 88.3071
- LBMA: first row 1968-04-01 = 37.70; last row 2026-09-25; merged total = 14,691 unique dates
- DEXINUS: first 1973-01-02 = 8.02; last 2026-11-13 = 94.24; 14,054 data lines of which 13,501 numeric (missing days are '.')
- Goldhub: USD 1978-01 = 207.83 (n=586); INR first 2005-10 = 21584.0711/oz (n=253) → 6939.44 ₹/10g via units (the 6939.42 stated earlier was hand-rounding — units.py is truth). Layout truth (verified by probe 2026-11-21): the date sits in the unlabeled column C (one LEFT of the 'USD' header label) and each currency's values sit directly under its own label column — do NOT apply a blanket +1 offset; locate columns by header name and verify against the anchors
- WRRI: AP Jan 2006-2007 Ploughing = 79.90; AP Jan 2023-2024 Ploughing/Tilling = 593.38; 97,310 raw rows
- MSP: wheat crop-year 2024-25 = 2425; 2025-26 = 2585; paddy common 2025-26 = 2369; tur 2026-27 fixed = 8450
