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
    wage_annual = _read("wage_annual.csv", numeric=("inr_day", "inr_day_female", "n_months"))
    for w in wage_annual:
        if w["n_months"] is not None:
            w["n_months"] = int(w["n_months"])
    msp_annual = _read("msp_annual.csv", numeric=("inr_quintal",))

    decomp_annual = derive.decomposition_annual(gold_annual, fx_annual, cal)
    decomp_monthly = derive.decomposition_monthly(domestic_monthly, usd_monthly, fx_daily, cal)
    wage_all_india = [w for w in wage_annual if w["state"].upper().startswith("ALL INDIA")]
    ratios_wage = derive.gold_per_wageday(decomp_annual, wage_all_india)
    ratios_msp = derive.gold_per_mspkg(decomp_annual, msp_annual)

    problems, notes, stats = validate_mod.run_all(decomp_annual, decomp_monthly, ci_mode=ci_mode)
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
            "repo": "rupee-gold-stack",
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
