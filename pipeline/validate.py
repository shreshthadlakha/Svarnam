"""Validate — golden values + invariants. Build fails hard on any mismatch.

Golden values are read-from-file truths (PRD A2 / TECH-DESIGN §8), never
hand-retyped numbers: FX 17.9428 is the T_133 cell, the FY2025-26 legs are the
machine-verified worked example (TECH-DESIGN §4.1).
"""
import csv
import os

from . import policy as policy_mod
from . import units

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTERIM = os.path.join(ROOT, "data", "interim")


class ValidationError(AssertionError):
    pass


def _read_interim(name):
    """Rows or None when the file is missing/empty (reported as a problem, never a crash)."""
    path = os.path.join(INTERIM, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    rows = list(csv.DictReader(lines))
    return rows or None


def _num(v):
    v = (v or "").strip()
    return float(v) if v else None


def _check(cond, msg, problems):
    if not cond:
        problems.append(msg)


def validate_interims():
    p = []

    def need(name):
        rows = _read_interim(name)
        if rows is None:
            p.append("interim file missing or empty: %s" % name)
        return rows

    stats = {}

    # --- RBI T35 gold annual ---
    g_rows = need("gold_inr_annual.csv")
    g = {r["fy"]: r for r in g_rows} if g_rows else {}
    for fy, mum, lon in (("1985-86", 2125.47, 327.75), ("1991-92", 4297.63, None),
                         ("2024-25", 75841.87, 2584.53), ("2025-26", 118420.90, 3937.86)):
        if fy not in g:
            p.append("gold_inr_annual: missing FY row %s" % fy)
            continue
        _check(abs(float(g[fy]["mumbai_inr_10g"]) - mum) < 0.005, "T35 %s golden mismatch" % fy, p)
        if lon is not None:
            _check(abs(float(g[fy]["london_usd_oz"]) - lon) < 0.005, "T35 %s London golden mismatch" % fy, p)
    if g_rows:
        _check(len(g) == 41, "T35 rows = %d, expected 41" % len(g), p)
    stats["gold_annual_rows"] = len(g)

    # --- RBI T133 FX annual ---
    fx_rows = need("fx_annual.csv")
    fx = {r["fy"]: r for r in fx_rows} if fx_rows else {}
    for fy, val in (("1986-87", 12.7782), ("1990-91", 17.9428), ("2025-26", 88.3071)):
        if fy not in fx:
            p.append("fx_annual: missing FY row %s" % fy)
            continue
        _check(abs(float(fx[fy]["usdinr_avg"]) - val) < 0.00005,
               "T133 %s golden mismatch (file truth %.4f)" % (fy, val), p)
    if fx_rows:
        _check(len(fx) == 40, "T133 rows = %d, expected 40" % len(fx), p)
    stats["fx_annual_rows"] = len(fx)

    # --- LBMA daily ---
    lb = need("lbma_daily.csv")
    stats["lbma_rows"] = len(lb) if lb else 0
    if lb:
        _check(lb[0]["date"] == "1968-04-01" and abs(float(lb[0]["usd_oz"]) - 37.70) < 0.005,
               "LBMA first row anchor mismatch", p)
        _check(lb[-1]["date"] == "2026-09-25", "LBMA last row != 2026-09-25", p)
        _check(len(lb) == 14691, "LBMA rows = %d, expected 14691" % len(lb), p)

    # --- FRED DEXINUS daily ---
    fd = need("fx_daily.csv")
    stats["fx_daily_rows"] = len(fd) if fd else 0
    if fd:
        _check(fd[0]["date"] == "1973-01-02" and abs(float(fd[0]["usdinr"]) - 8.02) < 0.005,
               "DEXINUS first anchor mismatch", p)
        _check(fd[-1]["date"] == "2026-11-13", "DEXINUS last row != 2026-11-13", p)

    # --- Goldhub monthly USD ---
    um_rows = need("gold_usd_monthly.csv")
    um = {r["month"]: r for r in um_rows} if um_rows else {}
    stats["usd_monthly_rows"] = len(um)
    if um_rows:
        _check(abs(float(um["1978-01"]["usd_oz"]) - 207.83) < 0.005, "Goldhub USD 1978-01 anchor mismatch", p)
        _check(len(um) == 586, "Goldhub USD months = %d, expected 586" % len(um), p)

    # --- Goldhub INR domestic monthly (byte-verified column) ---
    dm_rows = need("gold_inr_domestic_monthly.csv")
    dm = {r["month"]: r for r in dm_rows} if dm_rows else {}
    stats["inr_domestic_monthly_rows"] = len(dm)
    if dm_rows:
        _check("2005-10" in dm, "Goldhub INR domestic missing 2005-10", p)
        if "2005-10" in dm:
            _check(abs(float(dm["2005-10"]["inr_10g_domestic"]) - units.inr_oz_to_inr_10g(21584.0711)) < 0.01,
                   "Goldhub INR 2005-10 anchor mismatch", p)
        _check(len(dm) == 253, "Goldhub INR domestic months = %d, expected 253" % len(dm), p)

    # --- MSP annual ---
    ms_rows = need("msp_annual.csv")
    ms = {(r["crop"], r["crop_year"]): r for r in ms_rows} if ms_rows else {}
    stats["msp_rows"] = len(ms)
    if ms_rows:
        for crop, cy, val in (("Wheat", "2024-25", 2425.0), ("Wheat", "2025-26", 2585.0),
                              ("Paddy Common", "2025-26", 2369.0), ("Tur (Arhar)", "2026-27", 8450.0)):
            key = (crop, cy)
            if key in ms and ms[key]["inr_quintal"]:
                _check(abs(float(ms[key]["inr_quintal"]) - val) < 0.5,
                       "MSP anchor %s %s = %s, expected %s" % (crop, cy, ms[key]["inr_quintal"], val), p)
            else:
                p.append("MSP anchor missing: %s %s" % (crop, cy))

    # --- Wages annualized ---
    wa = need("wage_annual.csv")
    stats["wage_rows"] = len(wa) if wa else 0
    if wa:
        ai = [r for r in wa if r["fy"] == "2006-07" and r["state"].upper().startswith("ALL INDIA")]
        _check(len(ai) > 0, "wage_annual: no ALL-INDIA FY2006-07 rows", p)
        ap = [r for r in wa if r["fy"] == "2006-07" and r["state"] == "ANDHRA PRADESH"
              and r["occupation"] == "Ploughing" and r["occupation_group"] == "Agriculture"]
        if ap:
            _check(ap[0]["n_months"] == "12", "wage FY2006-07 AP Ploughing n_months != 12", p)

    return p, stats


def validate_calendar():
    cal = policy_mod.load_duty_calendar()
    span, problems = policy_mod.check_calendar(cal)
    return span, problems, cal


def validate_decomposition(decomp, label_kind="fy"):
    """Reconciliation invariant: |sum of legs − mumbai| ≤ 0.5% of mumbai, every period."""
    p = []
    for r in decomp:
        key = r.get("fy") or r.get("month")
        total = (r["metal_fx_leg"] + r["duty_leg"] + r["gst_leg"] + r["premium_leg"])
        mumbai = r["mumbai_inr_10g"]
        diff = abs(total - mumbai)
        if diff > 0.005 * mumbai:
            p.append("%s %s reconciliation off by %.2f (%.3f%%)" % (label_kind, key, diff, diff / mumbai * 100))
        if r["mumbai_inr_10g"] in (None, 0):
            p.append("%s %s mumbai missing/zero" % (label_kind, key))
    return p


def validate_fy2526_worked_example(decomp_annual):
    """Exact legs of the machine-verified worked example (TECH-DESIGN §4.1)."""
    expected = {"metal_fx_leg": 111801.33, "duty_leg": 6708.08, "gst_leg": 3555.28,
                "landed_cost": 122064.69, "premium_leg": -3643.79, "usdinr": 88.3071}
    p = []
    row = next((r for r in decomp_annual if r["fy"] == "2025-26"), None)
    if row is None:
        return ["FY2025-26 decomposition row missing"]
    for k, v in expected.items():
        if abs(row[k] - v) > 0.02:
            p.append("FY2025-26 %s = %.4f, expected %.4f" % (k, row[k], v))
    return p


def validate_fx_crosscheck(gold_annual, fx_annual, tolerance_pct=1.0):
    """TECH-DESIGN §4.3: T35-implied FX vs T133 — validation, not replacement.

    Documented exceptions (sourced, not silent): FY1991-92 straddles the
    July-1991 18-19% devaluation step change (RBI RC&F), so T35's London
    conversion basis diverges from the annual average rate by ~1.03%.
    """
    exceptions = {
        "1991-92": "FY1991-92 straddles the July-1991 devaluation step change; "
                   "T35 London-conversion basis diverges from annual average rate — documented divergence",
    }
    p = []
    notes = []
    fx = {r["fy"]: float(r["usdinr_avg"]) for r in fx_annual}
    for g in gold_annual:
        fy = g["fy"]
        conv, usd = _num(g.get("london_converted_inr_10g")), _num(g.get("london_usd_oz"))
        if fy not in fx or not conv or not usd:
            continue
        implied = conv / (usd / units.TROY_OZ_GRAMS * 10.0)
        diff = (implied - fx[fy]) / fx[fy] * 100.0
        if fy in exceptions:
            notes.append("FX cross-check %s diverges %+.2f%% — %s" % (fy, diff, exceptions[fy]))
        elif abs(diff) > tolerance_pct:
            p.append("FX cross-check %s: T35-implied %.4f vs T133 %.4f (%+.2f%%)" % (fy, implied, fx[fy], diff))
        elif abs(diff) > 0.3:
            notes.append("FX cross-check %s diverges %+.2f%% (within tolerance; noted)" % (fy, diff))
    return p, notes


def run_all(decomp_annual=None, decomp_monthly=None):
    """Full validation. Returns (problems, notes, stats). problems non-empty = FAIL."""
    problems, notes = [], []
    p, stats = validate_interims()
    problems += p
    span, cal_problems, cal = validate_calendar()
    problems += cal_problems
    stats["calendar_span_days"] = span
    if decomp_annual is not None:
        problems += validate_decomposition(decomp_annual, "fy")
        problems += validate_fy2526_worked_example(decomp_annual)
        ga = _read_interim("gold_inr_annual.csv")
        fa = _read_interim("fx_annual.csv")
        if ga and fa:
            p, n = validate_fx_crosscheck(ga, fa)
            problems += p
            notes += n
    if decomp_monthly is not None:
        problems += validate_decomposition(decomp_monthly, "month")
    return problems, notes, stats


if __name__ == "__main__":
    probs, notes, stats = run_all()
    import json
    print(json.dumps({"problems": probs, "notes": notes, "stats": stats}, indent=2))
