"""Policy loader — hand-curated, sourced CSVs → typed structures.

data/policy/duty_calendar.csv columns:
  from_date,to_date,type,channel,bcd_or_inr_10g,aidc,sws,gst_rate,note,source_ref
type: prohibition | specific | advalorem; channel: standard (modeled) | nri_baggage (auxiliary).
to_date is INCLUSIVE last day in force; empty = open (still in force).
gst_rate lives on the duty row that is in force (0.03 from 2017-07-01; empty before).
"""
import csv
import datetime as dt
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _rows(path):
    with open(path, encoding="utf-8") as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    return list(csv.DictReader(lines))


def _d(s):
    return dt.date.fromisoformat(s) if s else None


def load_duty_calendar(path=None):
    """Standard-channel rows only, sorted by from_date. Each row:
    {from, to, type, inr_10g, bcd, aidc, sws, gst_rate, note, source_ref}"""
    path = path or os.path.join(ROOT, "data", "policy", "duty_calendar.csv")
    out = []
    for r in _rows(path):
        if r.get("channel", "standard").strip() != "standard":
            continue  # nri_baggage rows are auxiliary, not the modeled rate
        def _num(key):
            v = (r.get(key) or "").strip()
            return float(v) if v else None
        out.append({
            "from": _d(r["from_date"]),
            "to": _d(r["to_date"]),
            "type": r["type"].strip(),
            "inr_10g": _num("bcd_or_inr_10g") if r["type"].strip() == "specific" else None,
            "bcd": _num("bcd_or_inr_10g") if r["type"].strip() == "advalorem" else None,
            "aidc": _num("aidc"),
            "sws": _num("sws"),
            "gst_rate": _num("gst_rate") or 0.0,
            "note": r.get("note", ""),
            "source_ref": r.get("source_ref", ""),
        })
    out.sort(key=lambda x: x["from"])
    return out


def load_breaks(path=None):
    path = path or os.path.join(ROOT, "data", "policy", "breaks.csv")
    return [{"date": _d(r["date"]), "label": r["label"], "source_ref": r["source_ref"]}
            for r in _rows(path)]


def load_episodes(path=None):
    path = path or os.path.join(ROOT, "data", "policy", "episodes.csv")
    out = []
    for r in _rows(path):
        v = (r.get("usd_per_oz") or "").strip()
        out.append({"date": _d(r["date"]),
                    "usd_per_oz": float(v) if v else None,
                    "direction": r["direction"].strip(),
                    "event": r["event"], "source_ref": r["source_ref"]})
    return out


def row_for(calendar, d: dt.date):
    """Exactly one standard row containing d (inclusive), else ValueError."""
    hits = [r for r in calendar if r["from"] <= d and (r["to"] is None or d <= r["to"])]
    if len(hits) != 1:
        raise ValueError("duty calendar: %d rows cover %s (invariant 4 violated)" % (len(hits), d))
    return hits[0]


def check_calendar(calendar):
    """Single-coverage invariant over the whole span; returns (span_days, problems)."""
    problems = []
    d = min(r["from"] for r in calendar)
    last = max((r["to"] for r in calendar if r["to"] is not None), default=None)
    span = 0
    while last is None or d <= last:
        try:
            row_for(calendar, d)
        except ValueError as e:
            problems.append(str(e))
            if len(problems) > 5:
                break
        span += 1
        d += dt.timedelta(days=1)
    return span, problems
