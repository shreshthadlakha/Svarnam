# Rupee Gold Stack — Product Requirements Document (PRD)

**Version:** 1.0 · **Date:** 21 Nov 2026 · **Status:** Approved for build
**Companion docs:** [TECH-DESIGN.md](TECH-DESIGN.md) · [CODE-STRUCTURE.md](CODE-STRUCTURE.md) · [PLAN.md](PLAN.md) · [LAUNCH-KIT.md](LAUNCH-KIT.md) · KT bundle: `docs/Rupee-Gold-Stack-Knowledge-Transfer.md`

---

## 1. One-liner

A static, honest, single-page web tool that decomposes India's rupee gold price into **metal + dollar + tax + local premium**, and measures what gold actually buys against **daily wages and food prices** — FY1985-86 to today.

## 2. Problem statement

1. Every Indian has seen "gold all-time high" charts (₹18/10g in 1925 → ~₹1.5 lakh in 2026). **None** show what the price is made of, or what it buys in real terms. India's gold content is price-only.
2. 2024–2026 made the tax leg chaotic and newsworthy: duty 15% → 6% (Jul 2024) → **15% again (13 May 2026)**; the all-in import wedge went ~9.2% → ~18.45% overnight; grey-market discounts exceeded $200/oz; smuggling revival projected >100 t for 2026.
3. The sovereign stopped selling its own gold-linked instrument (SGB discontinued, Feb 2025) because gold's rise made the borrowing too expensive.
4. Verified novelty (dive_06): **no India-specific gold purchasing-power reconstruction or interactive tool exists.** Prior art: Jastram's *The Golden Constant* (England/US), WGC Qaurum (2020, macro decomposition), the Lorenzen tool (US-only, zero circulation).

## 3. Audience

| # | Persona | Need | Success for them |
|---|---|---|---|
| P1 | LinkedIn/finTwit reader — retail investor, gold buyer, finance professional | Understand the price in 30 seconds on a phone | Sees the four legs of today's price; shares it |
| P2 | Checker — journalist, analyst, quant | Verify, not just view | Clicks every number to its named source; downloads the CSV |
| P3 | Owner (solo dev) | Credibility artifact + reach | The launch post rides the viral price-chart genre; the tool is the exhibit underneath |

## 4. Goals

- **G1** Make the invisible legs of the rupee gold price visible and quantified, 1985-86 → today.
- **G2** Every number on the page traceable to a named public source with URL and access date — the honesty moat.
- **G3** Ship in 2–3 weekends, ₹0 cost, zero backend, fully offline-capable page.
- **G4** Distribution built-in: launch post format (price-chart hero) matches the genre that demonstrably travels in India.

## 5. Non-goals (locked — do not re-litigate at build time)

| # | Non-goal | Reason |
|---|---|---|
| N1 | Forward price targets, probability-weighted scenarios, buy/sell language | SEBI research-analyst regulations + finfluencer crackdown; advice-shaped framing is the project's one existential legal risk |
| N2 | Fair-value scoring / "gold is over- or undervalued" verdicts | That requires *chosen* equilibrium assumptions — the exact flaw guy 1 correctly identified in the original. V1's decomposition is an **accounting identity**, not a valuation opinion; the premium residual is displayed, never judged |
| N3 | Livestock / agricultural-land / housing historical anchors | Verified dead as data (KT §3): no series exists. At most static "today" factoids in a later version |
| N4 | State-wise layer; multi-asset platform ("Real Economy Valuation Index") | V2 and V3 respectively — data readiness verified, scope discipline required |
| N5 | Backend, accounts, tracking, real-time prices | Static + annual/monthly official averages only; no cookies, no analytics in V1 |
| N6 | Daily-frequency long history for India | Doesn't exist free (IBJA paywalled); annual RBI spine + monthly Goldhub overlay is the honest maximum |

## 6. Functional requirements

| ID | Requirement |
|---|---|
| FR1 | **Hero decomposition**: current-FY bar showing metal / dollar / duty / GST / premium as ₹/10g with percentages |
| FR2 | **Decomposition chart**: stacked columns of Mumbai ₹/10g by FY (1985-86 → latest), segments = metal+FX base, duty leg, GST leg, premium residual (signed — negative premium renders as a below-baseline "discount" segment) |
| FR3 | **Ratio chart A — gold per wage-day**: annual; occupation selectable (WRRI series); optional AWI 1950-51 deep-history toggle |
| FR4 | **Ratio chart B — gold per MSP-kg**: crop selectable (wheat / rice / tur) |
| FR5 | **Custom calculator** (client-side only): user enters own daily wage → grams-equivalent output; no data leaves the browser |
| FR6 | **Regime-break annotations**: the fixed 9-break list (KT §4.3) rendered as dated markers on every time chart |
| FR7 | **Premium episodes timeline**: documented episodes (+$160/oz Dec'13, +$112/oz Jan'26, −$207/oz May'26 grey market, etc.) as callouts, each with its source link |
| FR8 | **Source table**: every series with name, URL, coverage window, access date, license note; every chart element carries its source ID on hover |
| FR9 | **CSV download**: full dataset, generated client-side from dataset.json |
| FR10 | **Honesty labels**: "provisional", "annual averages", "source break 2000-01" style markers on affected chart segments; footer disclaimer (text fixed in LAUNCH-KIT §1) |
| FR11 | **Responsive**: fully usable at 360 px width (LinkedIn traffic is overwhelmingly mobile) |
| FR12 | **SGB context card**: the launch–Feb 2024–discontinuation arc with citations, as static copy |

## 7. Content requirements

- **C1** `dataset.json` is the single source of truth; the page renders only from it — zero hardcoded numbers in HTML.
- **C2** English; ₹ formatting; lakh/crore notation in prose, plain numerals in charts.
- **C3** Tone: data journalism. No investment calls to action anywhere.

## 8. Acceptance criteria (each one checkable)

| ID | Criterion |
|---|---|
| A1 | Every displayed number resolves to a source ID present in `sources.md` |
| A2 | Golden values render correctly: FY1985-86 Mumbai ₹2,125.47/10g; FY1991-92 ₹4,297.63; FY2024-25 ₹75,841.87 ($2,584.53/oz); FY2025-26 ₹118,420.90 ($3,937.86/oz); FX FY1990-91 = 17.9428 (read from the file, not retyped); LBMA first row 1968-04-01 = $37.70 |
| A3 | Decomposition reconciles per year: metal+FX + duty + GST + premium = Mumbai price within ±0.5% |
| A4 | All 9 regime breaks (KT §4.3) annotated |
| A5 | Total page weight < 500 KB; loads < 2 s on 4G; works offline after load (chart lib vendored, not CDN) |
| A6 | CSV download matches dataset.json exactly |
| A7 | CI grep gate passes: zero occurrences of blocklisted advice language ("target", "forecast", "will reach", "should buy", "expect") in the tag-stripped visible copy of site/ (assets/vendor/ excluded — `target="_blank"` and `event.target` don't trip the gate) |
| A8 | 360 px check: no horizontal scroll outside charts, charts legible |

## 9. Success metrics

- **S1** Launch post reach ≥ 3× owner's median post reach; ≥ 1 re-share by a finance creator with > 10k followers.
- **S2** ≥ 25 repo stars in the first month (soft signal).
- **S3** ≥ 1 external citation (post, newsletter, article links the tool).
- **S4** Zero factual corrections required publicly — the true KPI of the honesty moat.

## 10. Risks & mitigations

| ID | Risk | Mitigation |
|---|---|---|
| R1 | Upstream data revisions (RBI revisions; MSP archive stitching errors) | Dataset versioning + "accessed on" dates + golden-value spot checks + 3-random-years manual verification per MSP crop |
| R2 | LBMA/ICE licensing on deep daily history | Display derived model outputs only; note terms in source table; fallback = WGC Goldhub averages |
| R3 | Misread as investment advice | Fixed disclaimer text; A7 CI gate; tone rules (C3) |
| R4 | Staleness | Update runbook (LAUNCH-KIT §5); "data as of" stamp on hero |
| R5 | RBI Handbook table-number drift across editions | `sources.py` records edition + table number together |
| R6 | Single-maintainer bus factor | KT bundle + this doc suite make the project portable by design |
