# Rupee Gold Stack — Launch Kit

**Version:** 1.0 · **Date:** 21 Nov 2026
Everything here is ready-to-paste. Nothing in this file may drift from PRD guardrails (N1/N2, A7).

---

## 1. Compliance text pack (fixed wording)

**Page footer disclaimer (verbatim):**
> **Model, not advice.** This page decomposes published gold prices and compares them with public wage and support-price statistics. It contains no forecasts, no price targets, and no recommendation to buy, sell, or avoid anything. Every number links to its public source; if a source revises, we revise. Data as of {date}.

**README disclaimer (verbatim):**
> This project is data journalism, not investment research. It shows accounting decompositions of published prices and long-run purchasing-power ratios. It does not predict prices and does not constitute investment advice under any jurisdiction, including SEBI's research-analyst framework.

**LinkedIn post closing line (verbatim):**
> Sources for every number are on the page; the CSV is downloadable. No forecasts here — just the arithmetic the headlines skip.

## 2. LinkedIn launch post (skeleton + hook options)

Structure (price-chart hero → twist → tool → punchline → link):
1. **Hook:** one of —
   - **H1 (chart):** "₹18 in 1925. ₹1.5 lakh today. You've seen this chart. Here's the one nobody's made." → [same chart, but each year split into metal / dollar / tax / premium]
   - **H2 (news peg):** "In July 2024 India cut gold import duty to 6%. In May 2026 it hiked it back to 15%. Here's what that did to the price you pay — decomposed."
   - **H3 (question):** "₹1.18 lakh per 10 grams. How much of that is gold, how much is the dollar, how much is Delhi, and how much is fear? I built a tool that answers it — 40 years of data."
2. **Three findings** (from the decomposition — fill from dataset after M2; candidates: metal+FX share ~94% in FY2025-26; the duty leg's 2022→2024→2026 round trip; India often trading *below* landed cost = the discount/grey-market story).
3. **SGB punchline:** "The government launched Sovereign Gold Bonds at ₹2,684/g in 2015, sold 67 tranches, then discontinued the scheme in 2025 — because gold rising ₹1.12 lakh-crore made its own borrowing too expensive. The premium is so real the sovereign stopped selling its instrument."
4. **Wage line:** one ratio stat (e.g., "X grams of gold = one day's wage in 1990 vs Y today" — compute from dataset, do not estimate).
5. **Closing:** the LAUNCH-KIT §1 LinkedIn line + link. No hashtags beyond 2–3 (finance/India).

Format: first image = the decomposed price chart (mobile-legible); second = wage chart; third = source-table screenshot (the trust shot). Carousel or single image + link in comment (LinkedIn algorithm choice at post time).

## 3. README skeleton (repo public face)

```markdown
# Rupee Gold Stack
What is ₹1.18 lakh / 10g of gold made of? Metal, dollar, tax, fear — decomposed, FY1985-86 → today.

- Live tool: https://{user}.github.io/rupee-gold-stack/
- [Data sources](site/sources.md) · [Download CSV](…) · [Methodology](docs/TECH-DESIGN.md)
- **Model, not advice** (see DISCLAIMER.md) · no forecasts, no targets — by design
- Built from public data only: RBI Handbook, LBMA, WGC Goldhub, Labour Bureau, CACP, FRED
- Status: {data_as_of} · Regime breaks annotated · provisional labels everywhere
```

## 4. Repo setup checklist

- [ ] Create repo `rupee-gold-stack` (public)
- [ ] `LICENSE` = MIT (code) — chosen over GPL: a data-journalism artifact wants maximum reuse; Tessera stays GPL, different product class
- [ ] `DATA-LICENSE.md` = CC BY 4.0 for `dataset.json` + charts; summarize third-party terms (LBMA/ICE display note, RBI public-sector reuse with attribution)
- [ ] `DISCLAIMER.md` = §1 text
- [ ] Enable GitHub Pages (workflow deploy from `site/`)
- [ ] CI: pytest + blocklist grep gate
- [ ] Branch protection off (solo), but CI required on main

## 5. Update runbook

| Trigger | Action |
|---|---|
| New RBI Handbook edition (annual, ~Jul-Aug) | Drop new XLSX into `data/raw/rbi/`; update `sources.py` **edition + table number** (they drift — was T38, now T35); `make build`; review `build_report.txt` diff; commit |
| Duty/GST change (budget or notification) | Add ONE row to `data/policy/duty_calendar.csv` with notification URL; `make build`; the decomposition updates itself |
| Wage data refresh (WRRI annual) | Replace export, re-run |
| MSP revision | Replace clean-table rows; re-run; note revisions in flags |
| Source revision discovered | Fix, re-run, and log the correction in `sources.md` changelog — public corrections build the trust moat (PRD S4) |
| Anything else | If it needs code changes in `site/`, it's a design smell — data updates must never touch page code |

## 6. V2/V3 backlog (locked out of v1 — PRD N4)

**V2 (post-launch, each independently shippable):**
- State-wise layer: WRRI has 20 states (Punjab vs UP vs Tamil Nadu wage ratios) — the guy-2 idea, verified feasible
- CEDA mandi prices (2001→, district-level, API): food anchor beyond MSP + state granularity
- ISALPI agri-land snapshot (2019→, 6 states, ask prices) as a static factoid card
- CPI-deflated gold (MoSPI CPI) as an overlay metric
- Housing snapshot (RBI HPI city indices 2010-11→)

**V3 north star:** "Indian Real Economy Valuation Index" — same framework for rupee, real estate, silver, equities (gold first, per the locked sequencing).

**Deep-history unlock (research stage):** colonial official yearbooks *Prices and Wages in India* (1870s–1940s) — a genuinely long Indian reconstruction nobody has published; treat as its own mini-project.

## 7. Open items carried from research (to close during M1)

1. ✅ CLOSED 21 Nov 2026: Goldhub xlsx downloaded; INR column verified **Oct 2005→Oct 2026 = Indian domestic price** (FY averages match RBI T35 within ±0.06%); monthly USD runs 1978-01→. World-price INR overlay is derived (LBMA × DEXINUS, 1973→)
2. Live LBMA JSON tail 2023→2026 (one browser fetch — agent can do)
3. WRRI export mechanics (portal workflow — agent attempts, owner fallback)
4. MSP archive stitching worksheets (owner-assisted)
5. (Non-blocking) RBI Reference Rate Archive earliest date; DBIE catalog; Reinhart–Rogoff parallel-rate series for the pre-1993 premium overlay
