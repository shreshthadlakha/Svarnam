# Svarnam — Master Knowledge Transfer

**Version:** 1.0 · **Date of record:** 21 November 2026
**Status:** APPROVED TO BUILD (GO verdict delivered 20 Nov 2026). V1 design locked. Nothing built yet — data spine verified, ~half the data already downloaded.
**Purpose:** Self-contained corpus for resuming this project in any fresh session, on any machine, or with a collaborator. Read top-to-bottom; nothing else is assumed.

---

## 0. 60-second orientation

**What:** "Svarnam" — an interactive, static, single-page web tool that measures what one gram of gold buys in India against the real economy, and decomposes the domestic rupee gold price into its four legs: **metal** (global spot) + **dollar** (USD/INR) + **tax** (customs duty + GST) + **local premium/discount** (residual).

**Inspiration:** Nate Lorenzen's "Gold Standard" tool at https://lorenzen.ai/tools/gold-standard/ (US model: gold vs. cow + farmland anchors → fair value $2,921 vs. spot $3,628 = +24.2% "monetary premium"; honest provisional labels; editable assumptions; CSV download). His tool is a founder credibility artifact, not a business — and has **zero detectable circulation** (verified: no HN/Reddit/LinkedIn/X hits as of 20 Nov 2026).

**Why India, why now:** No India-specific version of this genre exists anywhere (verified across ~15 searches — prior art is Jastram's *The Golden Constant*, England/US only; WGC Qaurum 2020; the US tool itself). India's viral gold genre is 100-year price-history charts (price-only, no real-economy layer). And the story is live news: **gold import duty was re-hiked from 6% to 15% on 13 May 2026**, the grey market is active (discounts >$200/oz), and the government discontinued Sovereign Gold Bonds (Feb 2025) because its own gold-linked borrowing got too expensive. The tool answers the question Indians are asking right now: *why is gold ~₹1.18 lakh/10g?*

**Who builds:** Solo indie developer (India-based), owner of this workspace. Fits the established goals: resume weight + LinkedIn reach, "money, transparently modeled" brand coherence with the Money-Desk idea. Sequencing rule: **Tessera's ship gate stands** — this project's page build slots after Tessera ships (or as one deliberate weekend between projects); data-fetch work can run anytime in background.

**Build cost:** 2–3 weekends. **Money cost:** ₹0 (Vercel Hobby hosting, free data, no API keys).

---

## 1. Decision trail (how we got here)

1. **20 Nov 2026, earlier:** User saw the Lorenzen tool and asked "can we build something like this for India?" First-pass verdict: don't clone cow/land anchors (India lacks century-long national series); redirect to the rupee-gold premium decomposition, where India's data is strong.
2. **20 Nov 2026:** User pasted two independent external analyses ("guy 1", "guy 2"). Guy 1 = critic (heuristic verdict, data caveats, "India version would be weaker"). Guy 2 = architect (6 indicators, 3 valuation layers, state-wise layer, multi-asset platform vision, research-before-code). A six-track verification wave (subagents) checked every assertion against primary sources.
3. **Wave verdict — resolves the guys' disagreement:** India version is **stronger than guy 1 assumed** (wage/MSP/policy/FX data verified rich) and **narrower than guy 2 assumed** (livestock and land are verifiably dead as historical series). Both guys misattributed the wage series to the Labour Bureau — it is the Agri Ministry's DES series (Agricultural Wages in India); Labour Bureau's series is Wage Rates in Rural India.
4. **GO decision with locked V1 scope** (see §2). Full evidence in `research/dive_01.md … dive_06.md` (workspace evidence archive).

Compressed guy verdicts (design rationale):
- **Guy 1 (critic):** right that the original is a heuristic, not a valuation model (chosen equilibrium ratios, 70/100 cow years interpolated, in-sample R²). Wrong that "India version would be weaker" — he compared India's worst anchors against the US tool's best, and missed that the policy decomposition is the product.
- **Guy 2 (architect):** right on sources (RBI Handbook, CEDA — both verified hands-on) and owner of the single best idea: the **state-wise layer** (V2). Wrong on scope: a 6-month institution plan kills a solo shipper; "methodology before code" is how such projects die politely; his dashboard mock used "illustrative data" — the one sin that would destroy the honesty moat.

---

## 2. Product definition (V1 — LOCKED)

### 2.1 The pitch line
> How much of today's ₹1.18 lakh / 10g of gold is metal, how much is the dollar, how much is tax, and how much is fear — and what has a day's wage, or a kilo of wheat, actually bought in gold over 40–75 years?

### 2.2 Page anatomy (single static page + one JSON dataset)
1. **Hero:** current decomposition bar (metal / dollar / tax / premium) + headline ratio ("1 day's MGNREGA wage = X grams" style)
2. **Decomposition chart:** stacked lines/areas of the four legs, 1985-86 → present (annual)
3. **Purchasing-power charts (2):** grams of gold per wage-day; grams of gold per MSP-kg (wheat, rice, tur selectable)
4. **Regime-break annotation layer** on every chart (see §4.3)
5. **Methodology + full source table** (every series, every break, every assumption)
6. **CSV download** of the dataset
7. **Honesty labels** throughout (provisional, interpolated portions, source breaks, in-sample disclosure) — this is the genre's moat; copying Lorenzen's honesty framing is deliberate

### 2.3 The decomposition math
- **Metal leg:** LBMA Gold Price PM, USD/oz. Unit conversion: 1 troy oz = 31.1034768 g.
- **Dollar leg:** USD/INR (market-determined from 1 Mar 1993; official rate before — annotate).
- **Landed cost:** spot × FX × (1 + duty) × (1 + GST 3%). Note GST compounds on the duty-paid value, so all-in tax wedge = (1+d)×1.03 − 1. At 15% duty: ≈18.45%. At 6% duty: ≈9.18%.
- **Local premium (residual):** domestic Mumbai price − landed cost. Documented episodes: +$160/oz (Dec 2013, 80:20 restrictions), +$112/oz (Jan 2026, duty-hike bets), −$207/oz (May 2026, grey-market discount post-re-hike). Reuters "Asia Gold" quotes these vs. official landed prices — read sign conventions carefully.
- **Ratio anchors:** grams of gold per wage-day (WRRI/AWI series ÷ gold ₹/g); grams per MSP-kg (MSP ₹/quintal ÷ 100 ÷ gold ₹/g).
- **NO forward price targets, no probability-weighted scenarios** — SEBI research-analyst / finfluencer territory. Educational/model framing only.

### 2.4 Explicit exclusions (with reasons, so nobody re-litigates)
- **Livestock anchor:** DEAD — no price series exists in India (verified: NSS 70th round = counts; BAHS 2025 = production/GVA, zero price tables; NDDB = milk prices only; e-pashuhaat = ~632 spot listings). At most a static "today" factoid.
- **Agri-land anchor (history):** DEAD — no national transaction series (verified). ISALPI starts Jan 2019, 6 states, ask-prices. Snapshot module at most.
- **Housing:** weak (RBI HPI city 2010-11→; NHB RESIDEX 2007→ valuation-based). V2/V3 module.
- **State-wise layer:** V2 — verified feasible on wage + mandi-food anchors (WRRI covers 20 states incl. Punjab/UP/Tamil Nadu; CEDA mandi data is district-level).
- **Multi-asset platform ("Indian Real Economy Valuation Index": rupee, real estate, silver, equities):** V3 north star, not V1.

---

## 3. Verified data spine (the heart of this document)

All "verified hands-on" items were downloaded/checked on 20 Nov 2026; the remaining acquisitions (wages, MSP archive, Goldhub, FRED) completed 21 Nov 2026. Local copies in `data/rbi/` (plus `data/wages/`, `data/msp/`, `data/policy/`).

| # | Dataset | Source | Coverage | Verdict | Local copy |
|---|---|---|---|---|---|
| 1a | **RBI Handbook of Statistics on the Indian Economy 2025-26, Table 35** — Mumbai gold ₹/10g + London $/oz + spread, annual | https://rbi.org.in/Scripts/AnnualPublications.aspx?head=Handbook%20of%20Statistics%20on%20Indian%20Economy (direct XLSX on rbidocs.rbi.org.in) | **FY 1985-86 → FY 2025-26 (41 obs)** | ✅ Usable — the primary INR gold spine. Source break 1999-2000/2000-01 (BBA/PTI era vs. IBJA/press era — RBI's own comparability note) | `data/rbi/t35_gold_annual.xlsx` (+ .pdf) |
| 1b | RBI Table 164 — monthly gold | same Handbook | Apr 2022 → Apr 2026 only (history rotates out each edition) | Partial | `data/rbi/t164_gold_monthly.xlsx` |
| 1c | WGC Goldhub — gold price averages in 13 currencies incl. INR (monthly/quarterly/annual) | https://www.gold.org/goldhub/data/gold-prices — file `Gold_price_averages_in_a_range_of_currencies_since_1978.xlsx` | **BYTE-VERIFIED 21 Nov 2026:** monthly USD from 1978-01 (586 rows); **INR column = Oct 2005 → Oct 2026 only (253 months) and it is the Indian DOMESTIC price** — FY averages match RBI T35 Mumbai within ±0.06% (FY2013-14 −0.00%, FY2021-22 +0.04%, FY2025-26 +0.06%); NOT the world price in rupees (world-INR differs 8–22% = tax wedge + local premium) | ✅ Usable — monthly domestic series enables **monthly-resolution decomposition 2005-10→** (duty changes visible at monthly granularity). World-price INR overlay must be DERIVED: LBMA monthly × USD/INR monthly (1973→, both on disk). Login-gated (see traps) | `data/rbi/goldhub_averages_since_1978.xlsx` (+ `goldhub_page.html`) |
| 2a | **LBMA Gold Price PM, USD** — daily free-market series | https://prices.lbma.org.uk/json/gold_pm.json (live endpoint 403s non-browser agents) | **1968-04-01 → present** (Wayback copy verified: first row 1968-04-01 = $37.70; snapshot ends 2023-09-01) | ✅ Usable as the global series; needs a live fetch for the 2023→2026 tail. Licensing note: IBA enforces terms on redistribution of deep history — display derived model outputs, not the raw feed | `data/rbi/gold_pm_wb.json` (Wayback history) + `gold_pm_live.json` (live tail to 2026-09-25) |
| 2b | Pre-1968 USD gold | NMA historical table https://nma.org/resources/historical-gold-prices-1833-to-present | 1833 → 1967 official prices ($35 from 1934; $38 in 1972, $42.22 in 1973) | Anchor only — not a market price. Flag as such | — |
| 3a | **RBI Handbook FX, Table 133** — USD/INR FY annual avg + end-year | same Handbook page | **FY 1986-87 → FY 2025-26** (official rates till 1991-92; FEDAI indicative from 1992-93; RBI ref rates from May 2012; FBIL from Jul 2018) | ✅ Usable; official-vs-market era documented in-table | `data/rbi/t133_fx_fy.xlsx` (+ T132/T205/T223; daily overlay `dexinus_daily.csv`, 1973→) |
| 3b | FRED DEXINUS — daily USD/INR (Fed H.10 NY noon rate) | https://fred.stlouisfed.org/data/DEXINUS | **1973-01-02 → present** | ✅ Usable free daily overlay (NY market rate, not RBI official); CLI/browser-agent downloads time out — download manually in your own browser | `data/rbi/dexinus_daily.csv` |
| 3c | Pre-1993 parallel premium | Cerra & Saxena, IMF Staff Papers 2002 https://www.imf.org/external/pubs/ft/staffp/2002/03/pdf/cerra.pdf — LPARALLEL series 1978Q1–1993Q4 (in-paper, not downloadable) | quarterly | Documented; series needs Reinhart–Rogoff/IMF PAR datasets (to-verify) | — |
| 4a | **WRRI — Wage Rates in Rural India** (Labour Bureau) — monthly, 20 states (incl. Punjab, UP, Tamil Nadu), ~25 occupations, sex-disaggregated | Labour Bureau official DB (source links in dive_02.md) | Official DB **2006-07 → 2023-24**; collection since 1986; Das-Usami compiled series extends 1998-99 → 2022-23 (break at Nov 2013 reclassification) | ✅ **Best anchor.** Raw extraction DONE 21 Nov 2026: 97,310 rows = 18 FYs × 12 months × 21 states (incl. All-India) × ~40 occupation labels. Caveats: Jul–Dec 2022-23 not yet in the DB; 2013-14 present but partial (old-scheme-only months Jul–Oct — correction to dive_02's January-only observation); non-numeric cells are only `@`/`-` markers | `data/wages/wrri_raw.csv` + extractor `data/wages/_wrri_extract.py` |
| 4b | **AWI — Agricultural Wages in India** (DES, Agri Ministry — NOT Labour Bureau) — district-level, 21 states | dive_02.md has source | **Since 1950-51**, publication lag 2–3 yrs | ✅ Optional deep-history extension (recommended) — 2023-24 volume downloaded 21 Nov 2026 (18.4 MB, valid PDF) | `data/wages/AWI-2023-24.pdf` |
| 4c | RBI Handbook Tables 112-115 (state wages, men, ~2014→2024); MGNREGA notified rates (state-wise annual, FY 2016-17→2025-26); ASI (no ready long series, 16-mo lag) | same Handbook; nrega portal | as stated | Supporting | — |
| 5a | **MSP — Minimum Support Prices** | Official CACP table https://cacp.da.gov.in/Home/MSP (updated 30.09.2026): crop years **2010-11 → 2027-28**, all 22 crops | Clean era: 2010-11→ | ✅ Usable | — |
| 5b | MSP deep archive — CACP "Price Policy" report PDFs | CACP report archive | **MY 1982-83 → 2024-25** (PDF annexures; manual stitching; 1985-86 volume absent) | Downloaded 21 Nov 2026, 32/32 OK: 26 archive compendiums 1982-83→2010-11 (JBIG2 scans — OCR required) + 6 born-digital reports (text-layer MSP-history annexures incl. kharif 2024-25 / rabi 2024-25). Rabi MY 2011-12 gap healable via archive "crops sown 2010-11". Full 76-URL manifest: `data/msp/_urls.csv` | `data/msp/` (~230 MB) |
| 6 | **CEDA Agri-Market Data Portal** (Centre for Economic Data & Analysis, Ashoka University) — mandi prices | https://ceda.ashoka.edu.in (portal; details in dive_03.md) | **2001 → present**; 300+ commodities, 2,700+ mandis; monthly; national/state/**district**; cleaned + API | ✅ Excellent — V2 state-wise layer | — |
| 7 | DEAD anchors (verified): livestock prices (nothing anywhere), agri-land national series (nothing; ISALPI = monthly index Jan 2019=100→, ask prices, 6 states AP/KA/MH/TN/TG/UP; ICRISAT village transactions 1975→ non-national; NSS AIDIS decadal self-reports 1991/2003/2013/2019), housing (RBI HPI quarterly transaction-based, city 2010-11→, all-India ~2013-14→; NHB RESIDEX 2007→, 50 cities, valuation-based) | dives 03/04 | — | ❌ history; snapshot factoids only | — |
| 8 | Pre-1990 domestic gold premium | **No reliable series found** (two search rounds). Ban era (GCA 1968–6 Jun 1990): domestic price not free-market; India was the world's largest illicit gold market in the 1980s (consumption 50t in 1980 → 175t in 1985, incl. smuggled) | — | Regime break: annotate, do not model pre-1990 as market data | — |

### Data-access traps (learned the hard way — do not rediscover)
- Goldhub file download 403s non-browser agents → use a real browser session.
- LBMA prices JSON 403s non-browser agents → Wayback Machine copies work (`web.archive.org/web/2020id_/…`).
- IBJA (ibjarates.com): free depth ≈ 30 days; full history behind a paid official API with undisclosed depth. **Do not build on IBJA history.**
- RBI DBIE (data.rbi.org.in) is a JS single-page app — not scriptable from CLI; treat as manual-browser fallback.
- Handbook table numbers drift between editions (gold table was T38 in the 2024-25 edition, T35 in 2025-26). Always cite edition + table number together.
- The monthly gold/FX tables in the current edition are shallow (2022→); history rotates out each edition. Older editions are the only free path to long monthly RBI series.
- agriwelfare portal (MSP alternative) is bot-blocked.
- **Goldhub downloads now require a free registered account** (verified 21 Nov 2026: file page says "You must be logged in to download this file"), and the login form is gated by **Cloudflare Turnstile** — which silently fails in the agent's embedded browser (no challenge iframe ever renders, `cf-turnstile-response` stays empty, button stays disabled even after reset + fresh reload + 15 s wait). Login + download must be done in the owner's own browser; after sign-in the direct file URL downloads immediately. Wayback has zero good captures of the xlsx (all 403). Skip-or-buy decision: the INR monthly overlay can be derived as LBMA monthly avg × USD/INR monthly avg — both series are now on disk.
- **prices.lbma.org.uk now Cloudflare-blocks this machine entirely — even a real browser session** (verified 21 Nov 2026). Working route: Wayback capture 2026-09-28 → saved as `data/rbi/gold_pm_live.json` (1968-04-01 → 2026-09-25, 14,691 rows). Tail beyond Sep 2026: later Wayback captures or Goldhub averages after account registration.
- **FRED (fred.stlouisfed.org) is unreachable from this machine's automated routes** (CLI and the agent's browser both timed out, 21 Nov 2026) — but it downloads fine in the owner's own browser: the user saved it manually as `data/rbi/dexinus_daily.csv` (14,055 rows, 1973-01-02 → 2026-11-13, ₹8.02 → ₹94.24). Verified on disk same day. Update route = manual browser download.
- 1 troy oz = 31.1034768 g — put the constant in one place in code.
- The rural-wages DB is a plain PHP multi-select POST (`survey_year[]`, `survey_month[]`, `state_id[]`, `occupation_code[]`), responses capped at 5,000 rows — scripted month × 2-year-group queries work fine with no captcha; extractor saved at `data/wages/_wrri_extract.py` (rerun annually for each new FY).

---

## 4. Verified fact base (cheat-sheet with citations)

### 4.1 Duty path 1990 → 2026 (the tax leg) — verified end-to-end, one source per row in dive_05.md
| Period | Effective customs duty on standard gold |
|---|---|
| ≤ 6 Jun 1990 | **Prohibited** (Gold Control Act 1968; black market) |
| Jun 1990 → 2011 | Specific-rate era: ₹250/10g (1990) → ₹450 NRI channel (Mar 1992) → ₹220 (1994) → ₹250 (1998) → ₹400 (Jan 1999) → ₹250 (Mar 2001) → ₹100 standard (2003) → ₹200 (Jul 2009) → ₹300 (Feb 2010 ≈ 1.08% ad-valorem equivalent) |
| 17 Jan 2012 | 2% (ad-valorem switch) → 4% (Mar 2012) → 6% (Jan 2013) → 8% (Jun 2013) → **10% (13 Aug 2013)** + RBI 80:20 import restriction (Jul 2013–28 Nov 2014) |
| 2014–2018 | 10% flat |
| Jul 2019 | BCD 12.5% (≈13.75% with SWS) |
| Feb 2021 | 7.5% BCD + 2.5% AIDC + 0.75% SWS = **10.75%** |
| Feb 2022 | 10% BCD + 5% AIDC = **15%** |
| 24 Jul 2024 | 5% BCD + 1% AIDC = **6%** (sharpest cut on record; lowest since Jun 2013) |
| **13 May 2026** | **Re-hiked to 15%** (10% BCD + 5% AIDC) — CURRENT as of 21 Nov 2026. Context: FX pressure; FY26 gold imports a record $71.98 bn. Reuters: https://www.reuters.com/world/india/india-raises-import-tariffs-gold-silver-government-order-says-2026-05-12 |

- **GST:** 3% on gold value since 1 Jul 2017 (3% IGST at import on duty-paid value; 5% on making charges). All-in import wedge = (1+duty)×1.03 − 1 → **≈18.45% today** (vs ≈9.18% under the 6% regime).
- **WGC elasticity (for calibration, regime-dependent):** −1% duty ⇒ ~+3 t/yr long-run consumer demand; the 2024 cut (+9 pts) ⇒ +50t+ H2 2024 demand.

### 4.2 FX regime (the dollar leg)
Official rate till 1991-92 → LERMS dual rate 40:60 (Mar 1992) → **unified market-determined rate from 1 Mar 1993**. July 1991 devaluation of 18-19%. Reference rates: ₹17.94/$ (FY1990-91) → ₹24.47 (FY1991-92) → ₹31.37 (FY1993-94) → ₹88.31 (FY2025-26).

### 4.3 Regime breaks to annotate on every chart (fixed list)
1. Gold Control Act 1968 (possession limits, black market) — repeal 6 Jun 1990; pre-1991 domestic price not free-market
2. NRI/passenger import scheme Mar 1992 (5 kg, ₹450/10g; 10 kg from Jan 1997)
3. FX unification Mar 1993
4. Source break 1999-2000/2000-01 (RBI's own comparability note)
5. Ad-valorem duty switch Jan 2012
6. 80:20 restriction Jul 2013–Nov 2014 (premium +$160/oz Dec 2013)
7. GST 3% Jul 2017
8. Duty cycle: 15% (2022) → 6% (Jul 2024) → 15% (May 2026)
9. SGB: launched 5 Nov 2015 (₹2,684/g) → last tranche 21 Feb 2024 (₹6,263/g) → discontinued, confirmed 1 Feb 2025 (₹1.12 lakh-crore liability on ~132t outstanding)

### 4.4 Documented premium/discount episodes (Reuters "Asia Gold" dealer quotes vs. official landed prices)
Dec 2013 **+$160/oz** (80:20) · Oct/Dec 2024 −$8 · Sep 2025 +$7 (festive) · Oct 2025 −$12 · Dec 2025 −$34 · **Jan 2026 +$112 (duty-hike bets)** · **May 2026 −$207 (grey market post-re-hike)** · Jun 2026 grey-market discounts >$200, smuggling revival, illegal imports projected >100t in 2026 · Jul 2026 −$56 official channel. Pattern: restrictions/duty spikes → premiums + grey market; liberalisations → discounts. May 2026 is the mirror image of Jul 2024.

### 4.5 Gold price spot checks (from Table 35 — sanity anchors for the pipeline)
FY1985-86: ₹2,125.47/10g ($327.75/oz) · FY1991-92: ₹4,297.63 · FY2024-25: ₹75,841.87 ($2,584.53) · FY2025-26: ₹118,420.90 ($3,937.86). India viral-chart numbers for the launch post: ~₹18/10g (1925) → ₹18.75 (1930s) → ₹89 (1947) → ₹1.33k (1980) → ₹1.4-1.5 lakh (2026), CAGR ~9.06%.

### 4.6 SGB punchline (the most quotable fact in the project)
Launched 5 Nov 2015 to shift household demand from physical gold (first tranche ₹2,684/g, 2.75% interest). 67 tranches, ~147t issued. Last tranche 21 Feb 2024. Government discontinued the scheme (announced Jul 2024 budget, confirmed 1 Feb 2025 — Economic Affairs Secretary: "a rather fairly high-cost borrowing for the government… the government has chosen not to follow that path") because gold's rise made its own gold-linked borrowing prohibitively expensive. **The premium is so real the sovereign stopped selling its instrument.**

### 4.7 Novelty & prior art (verified 20 Nov 2026 — dive_06.md)
- **No India-specific gold purchasing-power reconstruction or interactive tool exists** (searched academic, blogs/Substack, finTwit-style, Reddit, platforms). Novelty claim: TRUE for the India-localized build.
- Closest prior art ranked: 1) Lorenzen's tool (US-only; the genre template) · 2) WGC Qaurum / Gold Valuation Model (Jan 2020; macro decomposition, not purchasing-power anchors) · 3) Jastram, *The Golden Constant* (England/US) · 4) MeasuringWorth India rupee measures (1916-1948 window surfaced) · 5) India's viral 100-year price charts (price-only, no real-economy comparator) and Reddit pattern threads.
- Academic precedents worth citing in methodology: Kazak 2025 (rice/flour-per-gold ratios, ScienceDirect); rupee gold-standard monetary history (Balachandran 2008: rupee nominally gold-standard from 1898; ~11.30016 troy grains fine gold per rupee).
- **Future depth unlock:** colonial official yearbooks *"Prices and Wages in India"* (1870s–1940s) exist — a genuinely deep Indian reconstruction is possible in a later version. Neither external analysis spotted this.

### 4.8 Attention calibration (distribution truth)
The Lorenzen tool has **zero detectable circulation** → the valuation-model genre does NOT self-distribute. India's price-history genre demonstrably goes viral. Launch = ride the viral price-chart format as the hero, tool as the interactive exhibit underneath, May-2026 duty re-hike as the news peg, SGB punchline as the memorable quote.

---

## 5. Build plan (2–3 weekends)

### Stack
- Python 3.13 (bundled on the machine) + `pip install pandas openpyxl` (xlsx parsing; lxml for any HTML scraping)
- Static page: plain HTML + one chart library (ECharts or Chart.js via CDN) — zero build step, zero backend
- Hosting: **Vercel Hobby (chosen by owner, 22 Nov 2026)** — static deploy of `site/` only via `vercel.json` (`outputDirectory: site`; docs/pipeline/data never served); connects to the GitHub repo and **auto-redeploys on every push, including the monthly auto-refresh commit**. Alternative kept: GitHub Pages (pages.yml, workflow_dispatch only). Repo name: `svarnam`.
- A real browser for the two bot-protected downloads (agent's browser_tool can do these)

### Weekend 1 — data pipeline
1. Browser-fetch: WGC Goldhub averages xlsx (confirm INR column truly spans 1978→) + live LBMA gold_pm.json (2023→2026 tail)
2. Download WRRI wage series (Labour Bureau portal; links in dive_02.md) + AWI annual series (optional but recommended)
3. Digitize MSP: clean table 2010-11→ direct; CACP PDF archive 1982-83→ stitched (wheat, rice, tur minimum)
4. Transcribe duty table + premium episodes + breaks from dive_05.md into structured data
5. Build the splice: RBI T35 (primary, annual) + Goldhub INR monthly (sub-annual resolution, after depth check); compute decomposition legs + ratio anchors; emit `dataset.json` + `sources.md` (every series, every break, every assumption, every URL)

### Weekend 2 — the page
Hero decomposition bar; stacked decomposition chart; two purchasing-power charts with crop/occupation selectors; regime-break annotation layer (§4.3 list is the fixed spec); methodology + source table; CSV download; honesty labels.

### Weekend 3 — polish + launch
Mobile pass; minimal editable assumptions (e.g., "how many grams should a day's wage buy — you decide"); disclaimers (model, not advice; sources; provisional labels); the LinkedIn launch post (price-chart hero + interactive exhibit + May 2026 news peg + SGB punchline).

### `dataset.json` sketch
```
{ "gold_inr_annual": [{fy, mumbai_10g, london_usd_oz, source_flag}],
  "fx": [{fy, usdinr_avg, regime_flag}],
  "duty": [{from, to, bcd, aidc, other, note}],
  "premium_episodes": [{date, usd_per_oz, sign, event, source}],
  "wages": [{fy_or_month, state, occupation, inr_day, series_flag}],
  "msp": [{crop, year, inr_quintal}],
  "breaks": [{date, label}],
  "derived": {metal_leg, dollar_leg, tax_leg, premium_leg, grams_per_wageday, grams_per_mspkg} }
```

---

## 6. Guardrails (fixed constraints — do not negotiate at build time)
1. **No forward price targets, no probability-weighted scenarios, no buy/sell framing.** SEBI research-analyst regulations + finfluencer crackdown. Educational/data-journalism framing only.
2. **Honesty labels mandatory** (provisional, interpolated portions, source breaks, in-sample). This is the genre's moat and the brand.
3. **Licensing:** deep LBMA history carries ICE Benchmark Administration terms — display derived model outputs, not the raw licensed feed; note it in the source table.
4. **Never use "illustrative" fake data anywhere in the real product** (guy 2's mock did this; it would destroy credibility).
5. Keep the Lorenzen tool credited as inspiration (genre etiquette + it's just decent).

---

## 7. Sequencing & next actions (ordered)

**Sequencing override (owner decision, 21-22 Nov 2026):** the Tessera ship-gate rule is lifted for this project — Svarnam launches first, codebase fully separated from Tessera (S:\ untouched). Quarterly cadence replaced by **monthly automation** (refresh.yml + vercel.json; zero manual updates).

Status (all ☑ done, 21-22 Nov 2026):
1. ☑ Goldhub xlsx + live LBMA tail fetched (owner browser + Wayback)
2. ☑ WRRI extracted (97,310 rows) + AWI volume downloaded
3. ☑ MSP clean-era table parsed + deep archive downloaded (OCR = V1.1)
4. ☑ Pipeline → dataset.json (41 FY + 253 months, all invariants PASS)
5. ☑ Page built + verified live in browser (97/97 tests, A7 gate in CI)
6. ☑ Monthly auto-refresh + Vercel config committed

Remaining (owner executes, ~20 min):
1. ☐ Create GitHub repo `svarnam`, push master
2. ☐ Connect Vercel (LAUNCH-KIT §4) → live URL → smoke test + phone A8 check
3. ☐ Trigger Actions → quarterly-refresh → Run workflow once → confirm the refresh commit + Vercel auto-redeploy
4. ☐ LinkedIn launch per LAUNCH-KIT §2; delete the throwaway Goldhub account

---

## 8. Artifact map (where everything lives)

**This workspace:**
- `docs/Svarnam-Knowledge-Transfer.md` — this document
- `docs/PRD.md` · `docs/TECH-DESIGN.md` · `docs/CODE-STRUCTURE.md` · `docs/PLAN.md` · `docs/LAUNCH-KIT.md` — the approved build doc suite (build-accuracy corrections applied 21 Nov 2026: ratio formulas, golden values, worked example, paths, duty time-weighting, grep-gate scoping)
- `docs/Svarnam-Conversation-Transcript.md` — verbatim decision-trail transcript
- `research/dive_01.md` … `dive_06.md` — the six verification tracks (gold/FX sources, wages, MSP/mandi/livestock, land/housing, policy timeline, novelty)
- `data/rbi/` — RBI Handbook tables (T35/T133/T164/T132/T205/T223) + LBMA (Wayback + live tail) + Goldhub averages + DEXINUS + `SHA256SUMS.txt`
- `data/wages/` — `wrri_raw.csv` (97,310 rows, extracted 21 Nov 2026) + `AWI-2023-24.pdf` + extractor script
- `data/msp/` — 26 deep-history archive compendiums (1982-83→2010-11, OCR needed) + 6 born-digital reports + full URL manifest
- `data/policy/` — `duty_calendar.csv` / `breaks.csv` / `episodes.csv` (every row sourced, validated)
- `pipeline/` — the build system (parsers → derive → validate → build), all tests green
- `site/` — index.html + charts + calculator + CSV export; renders ONLY from `dataset.json`; deployed on Vercel (`vercel.json`: outputDirectory=site, cache headers)
- `site/dataset.json` + `site/sources.md` + `build_report.txt` — v1 build output: 41 FY decomposition (1985-86→2025-26) + 253 monthly (2005-10→2026-10) + ratio anchors, all invariants PASS (2026-11-22)

**Portability:** copy `docs/` + `research/` + `data/` together. That is the whole project state.

---

## 9. Context the next session also needs (one paragraph)
Owner profile: solo indie developer in India; shipped LightClip (local-first video tool, on GitHub/LinkedIn); active project Tessera (offline document-conversion desktop app, Rust+Tauri, at S:\Tessera — its own KT bundle exists: Master-Knowledge-Transfer.md in C:\Users\shres\Downloads). Queued idea: local-first AI money-desk for cross-border PayPal freelancers (idea pack in the same Downloads folder). This gold project is the third workstream and the designated "first post-Tessera artifact." Communication preference: non-obvious strategic answers over ranked tables; big-software-scale ambitions; pushes back on niche-and-already-done pitches. This project passed that bar because the India-localized build is verified novel and the policy decomposition is a story dimension the US original doesn't have.

---

*End of transfer document. If any fact here needs re-verification, the six dive files contain the original URLs and evidence tiers — check there before re-searching.*
