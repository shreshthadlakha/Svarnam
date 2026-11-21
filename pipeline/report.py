"""Build report — row counts, coverage, gaps, flags (build_report.txt)."""
from datetime import date


def render(meta, stats, decomp_annual, decomp_monthly, ratios, problems, notes):
    L = []
    L.append("SVARNAM — BUILD REPORT")
    L.append("generated: %s   data_as_of: %s   generator: %s" % (
        meta["generated"], meta["data_as_of"], meta["generator_version"]))
    L.append("validation: %s" % ("PASS — zero problems" if not problems else "FAIL (%d problems)" % len(problems)))
    L.append("")
    L.append("== interim row counts ==")
    for k, v in stats.items():
        L.append("  %-26s %s" % (k, v))
    L.append("")
    L.append("== decomposition coverage ==")
    if decomp_annual:
        L.append("  annual : %s → %s  (%d FYs)" % (decomp_annual[0]["fy"], decomp_annual[-1]["fy"], len(decomp_annual)))
        L.append("  monthly: %s → %s  (%d months)" % (decomp_monthly[0]["month"], decomp_monthly[-1]["month"], len(decomp_monthly)))
        neg = sum(1 for r in decomp_annual if r["premium_leg"] < 0)
        L.append("  annual premium negative (discount) in %d of %d FYs" % (neg, len(decomp_annual)))
    L.append("")
    L.append("== ratio anchors ==")
    if ratios.get("wage"):
        first = ratios["wage"][0]
        L.append("  gold_per_wageday: %d rows (state=%s), FYs %s→%s, occupations=%d" % (
            len(ratios["wage"]), first["state"], min(r["fy"] for r in ratios["wage"]),
            max(r["fy"] for r in ratios["wage"]), len({r["occupation"] for r in ratios["wage"]})))
    if ratios.get("msp"):
        L.append("  gold_per_mspkg: %d rows, crops=%s" % (
            len(ratios["msp"]), sorted({r["crop"] for r in ratios["msp"]})))
    L.append("")
    L.append("== known gaps & data notes (documented, not silent) ==")
    for g in [
        "MSP archive: 1985-86 volume absent everywhere; rabi MY 2011-12 healable via archive compendium (crop-year 2010-11 table column covers it)",
        "MSP deep history 1982-83→2010-11 needs OCR (archive PDFs are JBIG2 scans) — V1 ships clean era 2010-11→; deep era = V1.1",
        "WRRI: 2022-23 Jul–Dec not yet published upstream; 2013-14 partial (old-scheme-only months Jul–Oct); occupation labels break at Nov 2013 (no official linking factor)",
        "Monthly decomposition starts 2005-10 (Goldhub INR domestic column start) — annual spine covers 1985-86→",
        "Monthly metal leg = Goldhub USD monthly × DEXINUS H.10 NY market rate (not RBI official) — annual decomposition uses RBI T133 official/notes-flagged series",
        "LBMA live capture ends 2026-09-25; months after that covered by Goldhub USD monthly to 2026-10 — daily tail top-up is a runbook task",
        "FY1985-86 FX: T133 starts FY1986-87 — T35's own London-converted column used, flag t35-implied-fx",
        "Goldhub INR column = Indian DOMESTIC price (byte-verified vs T35 ±0.06%), NOT world price in rupees",
    ]:
        L.append("  - " + g)
    if notes:
        L.append("")
        L.append("== tolerance notes ==")
        for n in notes:
            L.append("  - " + n)
    if problems:
        L.append("")
        L.append("== VALIDATION PROBLEMS (build fails) ==")
        for pr in problems:
            L.append("  ! " + pr)
    L.append("")
    L.append("Reporting day: %s" % date.today().isoformat())
    return "\n".join(L) + "\n"
