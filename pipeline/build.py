"""Build — CLI entry: python -m pipeline.build
Runs validation first (fails hard), then derives and emits:
  site/dataset.json, site/sources.md, build_report.txt
"""
import csv
import json
import os
import sys
from datetime import datetime, timezone

from . import derive
from . import policy as policy_mod
from . import report as report_mod
from . import sources as sources_mod
from . import validate as validate_mod

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTERIM = os.path.join(ROOT, "data", "interim")
SITE = os.path.join(ROOT, "site")


def _read(name, numeric=()):
    path = os.path.join(INTERIM, name)
    with open(path, encoding="utf-8") as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    rows = list(csv.DictReader(lines))
    out = []
    for r in rows:
        for k in numeric:
            v = (r.get(k) or "").strip()
            r[k] = float(v) if v else None
        out.append(r)
    return out


T164_CSV = "gold_inr_mumbai_monthly_t164.csv"
CONTINUITY_WARN_PCT = 1.0  # T164↔Goldhub overlap tolerance — warn in the report, never fails


def _merge_domestic_monthly(goldhub_rows, t164_rows):
    """S02 merge: pinned Goldhub INR domestic rows are authoritative (flag 'derived',
    passed through unchanged); T164 rows are appended only for months BEYOND the
    last Goldhub month (flag 't164-extension'). Overlap months are never replaced —
    their mean abs percentage diff comes back as a continuity cross-check
    (warn >1%, never fail). Months with no T164 value are never imputed.
    """
    gh_by_month = {r["month"]: r for r in goldhub_rows}
    last_gh = max(gh_by_month, default=None)
    diffs = []
    for t in t164_rows:
        gh = gh_by_month.get(t["month"])
        v = t.get("mumbai_inr_10g")
        g = gh.get("inr_10g_domestic") if gh else None
        if v is not None and g is not None:
            diffs.append((t["month"], abs(v - g) / g * 100.0))
    extension = sorted(
        ({"month": t["month"], "inr_10g_domestic": t["mumbai_inr_10g"],
          "source_flag": "t164-extension"}
         for t in t164_rows
         if t.get("mumbai_inr_10g") is not None and (last_gh is None or t["month"] > last_gh)),
        key=lambda r: r["month"])
    mean = sum(d for _, d in diffs) / len(diffs) if diffs else None
    crosscheck = {
        "last_goldhub_month": last_gh,
        "extension_months": len(extension),
        "overlap_months": len(diffs),
        "overlap_first": diffs[0][0] if diffs else None,
        "overlap_last": diffs[-1][0] if diffs else None,
        "mean_abs_pct_diff": round(mean, 3) if mean is not None else None,
        "warn": mean is not None and mean > CONTINUITY_WARN_PCT,
    }
    return goldhub_rows + extension, crosscheck


def _extend_usd_monthly(usd_rows, lbma_rows):
    """Monthly USD beyond the last Goldhub USD pin = calendar-month means of
    lbma_daily.csv (flag 'lbma-derived'); months with no LBMA day are skipped —
    never imputed. Returns (merged_rows, extension_month_count).
    """
    last = max((r["month"] for r in usd_rows), default=None)
    buckets: dict[str, list] = {}
    for r in lbma_rows:
        if r.get("usd_oz") is None or not r.get("date"):
            continue
        buckets.setdefault(r["date"][:7], []).append(r["usd_oz"])
    extension = [{"month": m, "usd_oz": sum(vs) / len(vs), "source_flag": "lbma-derived"}
                 for m, vs in sorted(buckets.items()) if last is None or m > last]
    return usd_rows + extension, len(extension)


def _merge_notes(t164_rows, domestic_merged, merge_info, usd_rows, usd_merged,
                 usd_ext_months, lbma_available):
    """build_report notes: merged-series coverage, the T164↔Goldhub continuity
    cross-check (warn >1%, never fails) and which monthly series is stale."""
    out = []
    last_pin = merge_info["last_goldhub_month"]
    if t164_rows is None:
        out.append("WARNING: T164 interim missing (gold_inr_mumbai_monthly_t164.csv) — "
                   "gold domestic monthly series stale at %s (last Goldhub pin); "
                   "S02 refresh backfills it" % last_pin)
    else:
        last_t164 = max((r["month"] for r in t164_rows), default=None)
        out.append("gold domestic monthly: Goldhub pin last %s, T164 interim last %s — "
                   "merged series last %s (+%d t164-extension months)"
                   % (last_pin, last_t164,
                      max((r["month"] for r in domestic_merged), default=None),
                      merge_info["extension_months"]))
    if merge_info["overlap_months"]:
        line = ("T164↔Goldhub continuity cross-check: %d overlap months (%s..%s), "
                "mean abs diff %.2f%%"
                % (merge_info["overlap_months"], merge_info["overlap_first"],
                   merge_info["overlap_last"], merge_info["mean_abs_pct_diff"]))
        if merge_info["warn"]:
            out.append("WARNING: " + line + " — above the 1% tolerance (report-only; build continues)")
        else:
            out.append(line + " — within the 1% tolerance")
    else:
        out.append("T164↔Goldhub continuity cross-check: no overlap months between the "
                   "Goldhub pin and the T164 interim — nothing to compare")
    last_usd_pin = max((r["month"] for r in usd_rows), default=None)
    if lbma_available:
        out.append("gold USD monthly: Goldhub pin last %s, merged series last %s "
                   "(+%d lbma-derived months)"
                   % (last_usd_pin, max((r["month"] for r in usd_merged), default=None),
                      usd_ext_months))
    else:
        out.append("WARNING: lbma_daily.csv absent — USD monthly extension unavailable; "
                   "series stale at %s (last Goldhub pin)" % last_usd_pin)
    return out


def build(write=True, ci_mode=False):
    cal = policy_mod.load_duty_calendar()
    breaks = policy_mod.load_breaks()
    episodes = policy_mod.load_episodes()

    gold_annual = _read("gold_inr_annual.csv", numeric=("mumbai_inr_10g", "london_usd_oz",
                                                        "london_converted_inr_10g", "spread_inr"))
    fx_annual = _read("fx_annual.csv", numeric=("usdinr_avg", "usdinr_endyear"))
    fx_daily = _read("fx_daily.csv", numeric=("usdinr",))
    usd_monthly = _read("gold_usd_monthly.csv", numeric=("usd_oz",))
    domestic_monthly = _read("gold_inr_domestic_monthly.csv", numeric=("inr_10g_domestic",))
    # S02 T164 monthly extension (parsed by refresh.py): optional — fresh CI
    # checkouts carry only the pinned Goldhub interims until the first refresh.
    t164_path = os.path.join(INTERIM, T164_CSV)
    t164_monthly = _read(T164_CSV, numeric=("mumbai_inr_10g",)) if os.path.exists(t164_path) else None
    lbma_path = os.path.join(INTERIM, "lbma_daily.csv")
    lbma_daily = _read("lbma_daily.csv", numeric=("usd_oz",)) if os.path.exists(lbma_path) else None
    wage_annual = _read("wage_annual.csv", numeric=("inr_day", "inr_day_female", "n_months"))
    for w in wage_annual:
        if w["n_months"] is not None:
            w["n_months"] = int(w["n_months"])
    msp_annual = _read("msp_annual.csv", numeric=("inr_quintal",))

    decomp_annual = derive.decomposition_annual(gold_annual, fx_annual, cal)
    domestic_merged, merge_info = _merge_domestic_monthly(domestic_monthly, t164_monthly or [])
    usd_merged, usd_ext_months = _extend_usd_monthly(usd_monthly, lbma_daily or [])
    decomp_monthly = derive.decomposition_monthly(domestic_merged, usd_merged, fx_daily, cal)
    wage_all_india = [w for w in wage_annual if w["state"].upper().startswith("ALL INDIA")]
    ratios_wage = derive.gold_per_wageday(decomp_annual, wage_all_india)
    ratios_msp = derive.gold_per_mspkg(decomp_annual, msp_annual)

    problems, notes, stats = validate_mod.run_all(decomp_annual, decomp_monthly, ci_mode=ci_mode)
    notes = notes + _merge_notes(t164_monthly, domestic_merged, merge_info,
                                 usd_monthly, usd_merged, usd_ext_months,
                                 lbma_daily is not None)
    if problems:
        txt = report_mod.render({"generated": "FAILED", "data_as_of": "FAILED",
                                 "generator_version": "1.0"}, stats, decomp_annual,
                                decomp_monthly, {"wage": ratios_wage, "msp": ratios_msp},
                                problems, notes)
        os.makedirs(SITE, exist_ok=True)
        with open(os.path.join(ROOT, "build_report.txt"), "w", encoding="utf-8") as f:
            f.write(txt)
        raise SystemExit("BUILD FAILED — %d validation problems (see build_report.txt)" % len(problems))

    dataset = {
        "meta": {
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "generator_version": "1.0",
            "provisional": True,
            "data_as_of": "2026-11-21",
            "repo": "svarnam",
        },
        "sources": [{"id": k, **v} for k, v in sorted(sources_mod.SOURCES.items())],
        "series": {
            # slimmed for the A5 page-weight budget: the raw monthly USD/domestic
            # series and the all-India wage matrix are NOT emitted — their values
            # already live inside decomposition_monthly / gold_per_wageday rows.
            # Full series stay in data/interim/ (and ride the quarterly refresh).
            "gold_inr_annual": gold_annual,
            "fx_annual": fx_annual,
            "msp_annual": msp_annual,
        },
        "policy": {
            "duty_calendar": [{**r, "from": r["from"].isoformat(), "to": r["to"].isoformat() if r["to"] else None}
                              for r in cal],
            "breaks": [{**b, "date": b["date"].isoformat()} for b in breaks],
            "episodes": [{**e, "date": e["date"].isoformat()} for e in episodes],
        },
        "derived": {
            "decomposition_annual": decomp_annual,
            "decomposition_monthly": decomp_monthly,
            "gold_per_wageday": ratios_wage,
            "gold_per_mspkg": ratios_msp,
        },
    }
    report_txt = report_mod.render(dataset["meta"], stats, decomp_annual, decomp_monthly,
                                   {"wage": ratios_wage, "msp": ratios_msp}, problems, notes)
    if write:
        os.makedirs(SITE, exist_ok=True)
        with open(os.path.join(SITE, "dataset.json"), "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, separators=(",", ":"))
        with open(os.path.join(SITE, "sources.md"), "w", encoding="utf-8") as f:
            f.write(sources_mod.render_sources_md())
        with open(os.path.join(ROOT, "build_report.txt"), "w", encoding="utf-8") as f:
            f.write(report_txt)
    return dataset, report_txt


def main():
    dataset, report_txt = build()
    size = os.path.getsize(os.path.join(SITE, "dataset.json"))
    print("BUILD OK — dataset.json %.1f KB, %d annual + %d monthly decomposition rows" % (
        size / 1024.0, len(dataset["derived"]["decomposition_annual"]),
        len(dataset["derived"]["decomposition_monthly"])))
    print(report_txt.split("== known gaps")[0])


if __name__ == "__main__":
    main()
