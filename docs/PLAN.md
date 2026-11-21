# Rupee Gold Stack — Execution Plan

**Version:** 1.0 · **Date:** 21 Nov 2026 · **Owner:** solo dev
**Standing rule:** Tessera's ship gate (friend-Mac session + real .pub/.msg) is untouched — M0–M3 may run anytime in background; M4–M5 (page + launch) slot after Tessera ships or as one deliberate weekend.

---

## 1. Milestones

### M0 — Repo bootstrap (0.5 day, anytime)
- Create `rupee-gold-stack` repo; MIT + CC BY 4.0 + DISCLAIMER files; directory tree per CODE-STRUCTURE §1; CI stub; Pages workflow stub.
- Move `data/rbi/*` → `data/raw/rbi/` with checksums (workspace layout corrected 21 Nov 2026 — downloads live in `data/rbi/`).
- **Exit:** tree exists, `make test` runs (empty), Pages serves a placeholder.

### M1 — Data acquisition (0.5–1 day, anytime; partially agent-doable)
| # | Task | Who | Notes |
|---|---|---|---|
| 1.1 | ✅ DONE 21 Nov 2026: Goldhub xlsx downloaded by owner (login-gated; Turnstile blocks the agent browser) — INR column byte-verified: **Oct 2005→Oct 2026 and = Indian domestic price** (NOT 1978, NOT world-INR); monthly USD from 1978-01 | owner + agent verify | see KT §3 row 1c for the full verified verdict |
| 1.2 | Browser-fetch live LBMA `gold_pm.json` (2023-09→2026 tail); merge with Wayback copy | agent (browser) | licensing note recorded |
| 1.3 | Download WRRI exports (Labour Bureau portal) | agent + owner fallback | links pinned in dive_02 |
| 1.4 | (Optional, recommended) AWI annual series | agent | deep-history toggle |
| 1.5 | Collect CACP MSP archive PDFs 1982-83→ (wheat/rice/tur) | owner (portal is bot-blocked for bulk) | clean table 2010-11→ direct |
- **Exit:** `data/raw/` complete + checksummed; `sources.py` lists every file with URL + access date; Goldhub depth question answered in writing.

### M2 — Pipeline core: decomposition (1 day, anytime) — ✅ DONE 21 Nov 2026
- `parse_rbi` (T35 + T133), `parse_goldhub`, `parse_lbma`, `parse_fred`, `units`, `sources`, `policy` (transcribe dive_05 duty table + breaks + episodes), `derive`, `validate`, `build`.
- **Exit:** `site/dataset.json` v0.1 with decomposition FY1985-86→FY2025-26; all golden values pass; reconciliation invariant passes; `build_report.txt` shows zero unexplained gaps. (Tessera-critical: none of this touches S:\.)

### M3 — Ratio anchors (0.5 day, after M1 wage/MSP data lands) — ✅ DONE 21 Nov 2026 (clean-era MSP; deep-era = V1.1)
- `parse_wages`, `parse_msp`; ratio series; flags (`stitched`, `lagged`, `break-2013` where applicable).
- **Exit:** gold-per-wage-day (WRRI era) + gold-per-MSP-kg computed and validated; AWI extension either in or explicitly deferred to V2.

### M4 — The page (1 day, after Tessera gate / deliberate weekend)
- `index.html` + charts + annotation shim + source table + CSV export + honesty labels + SGB card; mobile pass.
- **Exit:** PRD acceptance criteria A1–A8 all pass (grep gate in CI).

### M5 — Launch (0.5 day, after M4)
- README final; LAUNCH-KIT §2 LinkedIn post (pick hook, add screenshots); publish; pin repo link.
- **Exit:** post live; repo public; "data as of" stamp correct.

### M6 — Post-launch cadence (ongoing, ~1 h/quarter)
- Update runbook (LAUNCH-KIT §5): new Handbook edition → re-run; duty change → one calendar row; log corrections publicly if any (S4 metric).

## 2. Dependency graph

```
M0 ─▶ M1 ─▶ M2 ─▶ M3 ─▶ M4 ─▶ M5 ─▶ M6
      │            ▲
      └─ MSP PDFs ─┘ (owner-assisted; M3 blocked only by this)
```

M2 (decomposition) is fully unblocked the moment M1.1–1.2 close. M3 waits on wages (1.3) and MSP (1.5). M4–M5 respect the Tessera gate.

## 3. Effort & cost

- Total: **2.5–3 weekends** (~18–22 focused hours). Agent can close M1.1–1.3 and draft M2 parsers.
- Cost: ₹0 — GitHub Pages, free data, vendored Chart.js, no keys.

## 4. Risk register (execution-specific)

| Risk | Impact | Mitigation |
|---|---|---|
| WRRI portal export is clunky/multi-file | M3 slips | fall back to Das-Usami compiled series 1998-99→2022-23 (flag the Nov-2013 break) |
| MSP PDF stitching is tedious | M3 slips | V1 ships with clean-era (2010-11→) ratios; deep-era ratios land in v1.1 — the decomposition chart (M2) carries the launch either way |
| Goldhub INR column shallower than metadata claims | M2 monthly overlay drops | annual-only V1 is fully viable (T35 spine); monthly = enhancement |
| LBMA live JSON blocked even in browser session | M2 tail gap | WGC Goldhub averages as the global series (1978→); document |
| Scope creep toward "fair value" scoring | honesty moat dies | PRD N2 is locked; PR dies with it |

## 5. Definition of done (whole project v1)

PRD §8 acceptance criteria all pass + launch post published + update runbook committed. Anything beyond = V2 backlog (LAUNCH-KIT §6), not scope creep.
