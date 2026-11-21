"""Derive — decomposition legs (an identity, not a model) + ratio anchors.

TECH-DESIGN §4: metal_fx_leg + duty_leg + gst_leg = landed_cost;
premium_leg = mumbai − landed_cost (signed; negative = discount).
Duty/GST are day-weighted within the period from the sourced calendar
(TECH-DESIGN §4.1 time-weighting rule) — never a single end-period constant.
"""
import datetime as dt
import statistics
from collections import defaultdict

from . import policy as policy_mod
from . import units


def _make_lookup(calendar):
    def lookup(d):
        row = policy_mod.row_for(calendar, d)
        if row["type"] == "prohibition":
            duty = 0.0
        elif row["type"] == "specific":
            duty = row["inr_10g"]
        elif row["type"] == "advalorem":
            # effective rate = BCD + AIDC + SWS (empty components = nil for that
            # row per the sourced calendar notes, e.g. "SWS nil on gold")
            duty = (row["bcd"] + (row["aidc"] or 0.0) + (row["sws"] or 0.0)) * metal_holder[0]
        else:
            raise ValueError("unknown duty type %r" % row["type"])
        return duty, row["gst_rate"]
    metal_holder = [0.0]

    def with_metal(m):
        metal_holder[0] = m
        return lookup
    return with_metal


def period_legs(metal_fx_inr10g: float, d1: dt.date, d2: dt.date, calendar):
    """Day-weighted duty/gst legs over [d1, d2] at a constant period metal_fx."""
    lookup_fn = _make_lookup(calendar)(metal_fx_inr10g)
    total = units.days_between(d1, d2)
    duty_sum = gst_sum = 0.0
    d = d1
    while d <= d2:
        duty_i, gst_i = lookup_fn(d)
        duty_sum += duty_i
        gst_sum += gst_i * (metal_fx_inr10g + duty_i)
        d += dt.timedelta(days=1)
    duty_leg = duty_sum / total
    gst_leg = gst_sum / total
    landed = metal_fx_inr10g + duty_leg + gst_leg
    return {"metal_fx_leg": metal_fx_inr10g, "duty_leg": duty_leg,
            "gst_leg": gst_leg, "landed_cost": landed}


def decomposition_annual(gold_annual, fx_annual, calendar):
    """FY decomposition on the RBI spine. Returns list of rows (rounded 2dp)."""
    fx = {r["fy"]: r for r in fx_annual}
    out = []
    for g in gold_annual:
        fy = g["fy"]
        d1, d2 = units.fy_bounds(fy)
        london = g["london_usd_oz"]
        if fy in fx:
            rate = fx[fy]["usdinr_avg"]
            fx_flag = ""
        else:
            # T133 starts FY1986-87 — FY1985-86 uses T35's own converted column
            rate = g["london_converted_inr_10g"] / (london / units.TROY_OZ_GRAMS * 10.0)
            fx_flag = "t35-implied-fx"
        metal_fx = units.usd_oz_to_inr_10g(london, rate)
        legs = period_legs(metal_fx, d1, d2, calendar)
        premium = g["mumbai_inr_10g"] - legs["landed_cost"]
        out.append({
            "fy": fy, "mumbai_inr_10g": g["mumbai_inr_10g"], "london_usd_oz": london,
            "usdinr": round(rate, 4), "metal_fx_leg": round(legs["metal_fx_leg"], 2),
            "duty_leg": round(legs["duty_leg"], 2), "gst_leg": round(legs["gst_leg"], 2),
            "landed_cost": round(legs["landed_cost"], 2),
            "premium_leg": round(premium, 2),
            "premium_pct": round(premium / legs["landed_cost"] * 100.0, 2),
            "flags": sorted(f for f in (fx_flag, g.get("source_flag", "")) if f),
        })
    return out


def decomposition_monthly(domestic_monthly, usd_monthly, fx_daily, calendar):
    """Monthly decomposition on the verified domestic series (2005-10→).

    metal = Goldhub monthly USD avg × DEXINUS monthly avg (market rate, H.10);
    mumbai = Goldhub INR domestic column in ₹/10g (verified vs T35 ±0.06%).
    """
    fx_m = defaultdict(list)
    for r in fx_daily:
        fx_m[r["date"][:7]].append(r["usdinr"])
    usd = {r["month"]: r for r in usd_monthly}
    out = []
    for g in domestic_monthly:
        m = g["month"]
        u = usd.get(m)
        if u is None or u["usd_oz"] is None or m not in fx_m or not fx_m[m]:
            continue
        rate = statistics.fmean(fx_m[m])
        metal_fx = units.usd_oz_to_inr_10g(u["usd_oz"], rate)
        y, mo = int(m[:4]), int(m[5:7])
        d1 = dt.date(y, mo, 1)
        d2 = dt.date(y + (mo == 12), (mo % 12) + 1, 1) - dt.timedelta(days=1)
        legs = period_legs(metal_fx, d1, d2, calendar)
        mumbai = g["inr_10g_domestic"]
        premium = mumbai - legs["landed_cost"]
        out.append({
            "month": m, "mumbai_inr_10g": mumbai, "london_usd_oz": u["usd_oz"],
            "usdinr": round(rate, 4), "metal_fx_leg": round(legs["metal_fx_leg"], 2),
            "duty_leg": round(legs["duty_leg"], 2), "gst_leg": round(legs["gst_leg"], 2),
            "landed_cost": round(legs["landed_cost"], 2),
            "premium_leg": round(premium, 2),
            "premium_pct": round(premium / legs["landed_cost"] * 100.0, 2),
            "flags": ["goldhub-domestic", "fred-h10-fx"]
                     + [f for f in (g.get("source_flag"), u.get("source_flag"))
                        if f in ("t164-extension", "lbma-derived")],
        })
    return out


def gold_per_wageday(decomp_annual, wage_annual, state="ALL INDIA"):
    """grams of gold one day's wage buys = wage_inr_day / (mumbai/10)."""
    mum = {r["fy"]: r["mumbai_inr_10g"] for r in decomp_annual}
    out = []
    for w in wage_annual:
        if w["state"].upper() != state.upper() or not w["inr_day"]:
            continue
        fy = w["fy"]
        if fy not in mum:
            continue
        grams = w["inr_day"] / (mum[fy] / 10.0)
        out.append({"fy": fy, "occupation": w["occupation"],
                    "state": w["state"], "wage_inr_day": w["inr_day"],
                    "grams": round(grams, 4), "n_months": w["n_months"],
                    "source": "S06", "flags": [f] if (f := w.get("source_flag", "")) else []})
    return out


def gold_per_mspkg(decomp_annual, msp_annual):
    """grams of gold one kg of crop buys = (msp/100) / (mumbai/10); crop year joined to same-label FY."""
    mum = {r["fy"]: r["mumbai_inr_10g"] for r in decomp_annual}
    out = []
    for r in msp_annual:
        cy = r["crop_year"]
        if cy not in mum or not r["inr_quintal"]:
            continue
        kg = units.quintal_to_kg(r["inr_quintal"])
        grams = kg / (mum[cy] / 10.0)
        out.append({"crop_year": cy, "crop": r["crop"], "msp_inr_kg": round(kg, 4),
                    "grams": round(grams, 6), "source": "S08",
                    "flags": [f] if (f := r.get("source_flag", "")) else []})
    return out
