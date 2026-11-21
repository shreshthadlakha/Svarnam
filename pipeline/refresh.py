"""Automated quarterly refresh for the Rupee Gold Stack.

One command re-fetches every automatable source, validates + atomically replaces
the raw file on disk (previous version kept as .bak), re-runs all parsers
in-process, then runs pipeline.build and writes refresh_report.txt
(fetched/kept/skipped per source + build result + dataset size).

Modes
    python pipeline/refresh.py             local refresh (network + existing raw files)
    python pipeline/refresh.py --dry-run   print the plan only — fetches nothing,
                                           touches no raw file, runs no build
    python pipeline/refresh.py --ci        fresh-checkout mode: data/ may be absent
                                           except the committed pinned interims
                                           (data/interim/gold_usd_monthly.csv,
                                            data/interim/gold_inr_domestic_monthly.csv)

What stays manual
    - S03 Goldhub: login-gated download -> the fetch is always skipped. When the
      raw xlsx is missing (CI), the pinned Goldhub-derived interim CSVs are reused
      as-is ("pinned Goldhub-derived interims reused, last pinned <date>").
    - A new RBI Handbook edition drifts table numbers + file URLs -> fetch emits a
      WARNING ("new Handbook edition - owner must update sources.py") and the
      refresh continues with committed interims. Never silent.

Parsers stay pure readers (CONTRACT rule 6): all fetching lives in refresh_*()
functions here, so importing this module never touches the network.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from typing import Callable

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)  # bootstrap: PYTHONSAFEPATH machines break `python -m pipeline.*`

from pipeline import build as build_mod  # noqa: E402
from pipeline import parse_fred, parse_goldhub, parse_lbma, parse_msp, parse_rbi, parse_wages  # noqa: E402

INTERIM = os.path.join(ROOT, "data", "interim")
REPORT_PATH = os.path.join(ROOT, "refresh_report.txt")
GOLDHUB_XLSX = str(parse_goldhub.SOURCE_XLSX)
WRRI_SCRIPT = os.path.join(ROOT, "data", "wages", "_wrri_extract.py")
WRRI_RAW = str(parse_wages.RAW_PATH)

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXINUS"
LBMA_JSON_URL = "https://prices.lbma.org.uk/json/gold_pm.json"
LBMA_CDX_URL = ("https://web.archive.org/cdx/search/cdx"
                "?url=prices.lbma.org.uk/json/gold_pm.json&output=json&filter=statuscode:200&limit=-1")
MSP_URL = "https://cacp.da.gov.in/json.json"

# RBI Handbook 2025-26 edition — direct XLSX links, edition-pinned like the table
# numbers (paths drift between editions). UNVERIFIED: no network run was made
# while writing this file. If the first real run reports a WARNING here, the
# owner updates this dict and pipeline/sources.py for the new edition.
RBI_EDITION_URLS = {
    "t35_gold_annual.xlsx": "https://rbi.org.in/Documents/HS-2025-26/T_35.xlsx",
    "t133_fx_fy.xlsx": "https://rbi.org.in/Documents/HS-2025-26/T_133.xlsx",
}

HTTP_TIMEOUT = 120
WRRI_TIMEOUT = 1800  # WRRI "full" POSTs month x year-group queries; allow 30 min


# ---------------------------------------------------------------- validators

def validate_xlsx(data: bytes) -> None:
    if data[:4] != b"PK\x03\x04":
        raise ValueError("not a valid XLSX (missing ZIP magic)")


def _validate_json_bytes(data: bytes) -> object:
    parsed = json.loads(data.decode("utf-8-sig"))
    if not parsed:
        raise ValueError("JSON payload is empty")
    return parsed


def validate_msp_json(data: bytes) -> None:
    _validate_json_bytes(data)


def validate_lbma_json(data: bytes) -> None:
    parsed = _validate_json_bytes(data)
    if not isinstance(parsed, dict) or len(parsed) < 1000:
        raise ValueError("LBMA payload is not the full-history dict "
                         "(%d entries)" % (len(parsed) if isinstance(parsed, dict) else -1))


def validate_fred_csv(data: bytes) -> None:
    first = data.decode("utf-8-sig", "replace").splitlines()[0] if data else ""
    if "DEXINUS" not in first:
        raise ValueError("FRED CSV header lacks DEXINUS: %r" % first[:120])


def validate_wrri_csv(path: str) -> None:
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = [next(f, "") for _ in range(2)]
    if len(lines) < 2 or "," not in lines[0] or not lines[1].strip():
        raise ValueError("WRRI raw CSV lacks header/data rows")


# ------------------------------------------------------------ atomic replace

def atomic_replace(target: str, data: bytes, validate: Callable[[bytes], None]) -> None:
    """Write <target>.new, validate it, back the previous file up to .bak, swap."""
    target = str(target)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    tmp = target + ".new"
    with open(tmp, "wb") as f:
        f.write(data)
    try:
        with open(tmp, "rb") as f:
            validate(f.read())
        if os.path.exists(target):
            with open(target, "rb") as src, open(target + ".bak", "wb") as dst:
                dst.write(src.read())
        os.replace(tmp, target)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def http_get(url: str) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (rupee-gold-stack quarterly refresh)"})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return resp.read()


def pinned_goldhub_date() -> str:
    """Accessed date from the provenance header of a pinned Goldhub interim CSV."""
    for name in ("gold_usd_monthly.csv", "gold_inr_domestic_monthly.csv"):
        path = os.path.join(INTERIM, name)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if not line.startswith("#"):
                        break
                    m = re.search(r"\(accessed\s+(\d{4}-\d{2}-\d{2})", line)
                    if m:
                        return m.group(1)
    return "unknown"


# --------------------------------------------------------------------- plan

def build_plan(mode: str = "local") -> list[dict]:
    pinned = pinned_goldhub_date()
    return [
        {"id": "S05", "name": "FRED DEXINUS (daily USD/INR)", "action": "fetch+parse",
         "url": FRED_URL, "target": str(parse_fred.IN_PATH),
         "validate": "CSV header contains DEXINUS",
         "parser": "pipeline.parse_fred.main", "note": ""},
        {"id": "S09", "name": "LBMA Gold Price PM (daily, via Wayback CDX)", "action": "fetch+parse",
         "url": LBMA_JSON_URL, "target": str(parse_lbma.LIVE_PATH),
         "validate": "JSON full-history dict (>=1000 dates)",
         "parser": "pipeline.parse_lbma.main (wb+live merge)",
         "note": "CDX query: latest 200-status capture -> web.archive.org/web/<ts>id_/ fetch; "
                 "data/rbi/gold_pm_wb.json merged when present (CI fallback: live capture alone)"},
        {"id": "S08", "name": "CACP MSP feed", "action": "fetch+parse",
         "url": MSP_URL, "target": str(parse_msp.RAW_PATH),
         "validate": "JSON parse", "parser": "pipeline.parse_msp.main", "note": ""},
        {"id": "S06", "name": "Labour Bureau WRRI (rural wages)", "action": "subprocess+parse",
         "url": "https://www.labourbureau.gov.in/rural-wages", "target": WRRI_RAW,
         "validate": "CSV header + data rows",
         "parser": "data/wages/_wrri_extract.py full -> pipeline.parse_wages.main", "note": ""},
        {"id": "S01", "name": "RBI Handbook T35 (gold annual)", "action": "fetch+parse",
         "url": RBI_EDITION_URLS["t35_gold_annual.xlsx"], "target": str(parse_rbi.T35_PATH),
         "validate": "XLSX ZIP magic", "parser": "pipeline.parse_rbi.parse_gold",
         "note": "HTTP failure -> WARNING 'new Handbook edition - owner must update sources.py'; "
                 "committed interims kept (never silent)"},
        {"id": "S04", "name": "RBI Handbook T133 (FX annual)", "action": "fetch+parse",
         "url": RBI_EDITION_URLS["t133_fx_fy.xlsx"], "target": str(parse_rbi.T133_PATH),
         "validate": "XLSX ZIP magic", "parser": "pipeline.parse_rbi.parse_fx",
         "note": "same edition-drift WARNING path as T35"},
        {"id": "S03", "name": "WGC Goldhub averages since 1978", "action": "skip",
         "url": "https://www.gold.org/goldhub/data/gold-prices",
         "target": "data/interim/gold_usd_monthly.csv + gold_inr_domestic_monthly.csv (pinned)",
         "validate": "n/a (no fetch)",
         "parser": "pipeline.parse_goldhub.main only when the local raw xlsx exists",
         "note": "SKIP: login-gated download; annual spine unaffected — pinned derived "
                 "interims reused, last pinned %s" % pinned},
    ]


def render_plan(plan: list[dict], mode: str) -> str:
    out = ["refresh plan (mode: %s)" % mode, ""]
    for s in plan:
        out.append("[%s] %s — %s" % (s["id"], s["name"], s["action"]))
        out.append("    url:      %s" % s["url"])
        out.append("    target:   %s" % s["target"])
        out.append("    validate: %s" % s["validate"])
        out.append("    parser:   %s" % s["parser"])
        if s["note"]:
            out.append("    note:     %s" % s["note"])
    return "\n".join(out)


# ------------------------------------------------------------- fetch/parse

def _result(out: list, sid: str, name: str, status: str, detail: str = "") -> None:
    out.append((sid, name, status, detail))


def refresh_fred(out: list, warnings: list) -> None:
    fetched = False
    try:
        data = http_get(FRED_URL)
        atomic_replace(parse_fred.IN_PATH, data, validate_fred_csv)
        fetched = True
        parse_fred.main([])
        _result(out, "S05", "FRED DEXINUS (daily USD/INR)", "FETCHED+PARSED",
                "%d bytes -> fx_daily.csv" % len(data))
    except Exception as exc:
        if fetched:
            _result(out, "S05", "FRED DEXINUS", "FETCHED, PARSE FAILED",
                    "%s: %s (fx_daily.csv kept from previous run)" % (type(exc).__name__, exc))
        else:
            _result(out, "S05", "FRED DEXINUS", "KEPT",
                    "fetch failed: %s: %s — fx_daily.csv kept" % (type(exc).__name__, exc))
            warnings.append("WARNING: S05 FRED fetch failed (%s: %s) — continuing with "
                            "committed fx_daily.csv (never silent)" % (type(exc).__name__, exc))


def refresh_lbma(out: list, warnings: list) -> None:
    fetched = False
    try:
        cdx = json.loads(http_get(LBMA_CDX_URL).decode("utf-8"))
        if not cdx:
            raise RuntimeError("CDX returned no captures")
        ts = cdx[-1][1]  # last row = most recent capture; filter=statuscode:200 already applied
        capture_url = "https://web.archive.org/web/%sid_/%s" % (ts, LBMA_JSON_URL)
        data = http_get(capture_url)
        atomic_replace(parse_lbma.LIVE_PATH, data, validate_lbma_json)
        fetched = True
        wb = parse_lbma.WB_PATH if os.path.exists(parse_lbma.WB_PATH) else parse_lbma.LIVE_PATH
        parse_lbma.main(["--wb", str(wb), "--live", str(parse_lbma.LIVE_PATH)])
        _result(out, "S09", "LBMA Gold Price PM (Wayback capture)", "FETCHED+PARSED",
                "capture %s, %d bytes -> lbma_daily.csv%s"
                % (ts, len(data),
                   "" if os.path.exists(parse_lbma.WB_PATH)
                   else " (history gold_pm_wb.json absent — live capture parsed alone)"))
    except Exception as exc:
        if fetched:
            _result(out, "S09", "LBMA Gold Price PM", "FETCHED, PARSE FAILED",
                    "%s: %s (lbma_daily.csv kept from previous run)" % (type(exc).__name__, exc))
        else:
            _result(out, "S09", "LBMA Gold Price PM", "KEPT",
                    "fetch failed: %s: %s — lbma_daily.csv kept" % (type(exc).__name__, exc))
            warnings.append("WARNING: S09 LBMA fetch failed (%s: %s) — continuing with "
                            "committed lbma_daily.csv (never silent)" % (type(exc).__name__, exc))


def refresh_msp(out: list, warnings: list) -> None:
    fetched = False
    try:
        data = http_get(MSP_URL)
        atomic_replace(parse_msp.RAW_PATH, data, validate_msp_json)
        fetched = True
        parse_msp.main([])
        _result(out, "S08", "CACP MSP feed", "FETCHED+PARSED",
                "%d bytes -> msp_annual.csv" % len(data))
    except Exception as exc:
        if fetched:
            _result(out, "S08", "CACP MSP feed", "FETCHED, PARSE FAILED",
                    "%s: %s (msp_annual.csv kept from previous run)" % (type(exc).__name__, exc))
        else:
            _result(out, "S08", "CACP MSP feed", "KEPT",
                    "fetch failed: %s: %s — msp_annual.csv kept" % (type(exc).__name__, exc))
            warnings.append("WARNING: S08 MSP fetch failed (%s: %s) — continuing with "
                            "committed msp_annual.csv (never silent)" % (type(exc).__name__, exc))


def refresh_wrri(out: list, warnings: list) -> None:
    parsed = False
    try:
        proc = subprocess.run([sys.executable, WRRI_SCRIPT, "full"], capture_output=True,
                              text=True, timeout=WRRI_TIMEOUT, cwd=os.path.dirname(WRRI_SCRIPT))
        if proc.returncode != 0:
            raise RuntimeError("extractor rc=%d: %s" % (proc.returncode, (proc.stderr or "")[-300:]))
        validate_wrri_csv(WRRI_RAW)
        parse_wages.main()
        parsed = True
        _result(out, "S06", "WRRI rural wages (subprocess 'full')", "FETCHED+PARSED",
                "wrri_raw.csv regenerated -> wage_annual.csv")
    except Exception as exc:
        if parsed:
            _result(out, "S06", "WRRI rural wages", "FETCHED, PARSE FAILED",
                    "%s: %s (wage_annual.csv kept from previous run)" % (type(exc).__name__, exc))
        else:
            _result(out, "S06", "WRRI rural wages", "KEPT",
                    "subprocess/fetch failed: %s: %s — wage_annual.csv kept"
                    % (type(exc).__name__, exc))
            warnings.append("WARNING: S06 WRRI refresh failed (%s: %s) — continuing with "
                            "committed wage_annual.csv (never silent)" % (type(exc).__name__, exc))


def refresh_rbi(out: list, warnings: list) -> None:
    tables = (
        ("S01", "RBI Handbook T35 (gold annual)", "t35_gold_annual.xlsx", parse_rbi.T35_PATH),
        ("S04", "RBI Handbook T133 (FX annual)", "t133_fx_fy.xlsx", parse_rbi.T133_PATH),
    )
    for sid, name, fname, target in tables:
        try:
            data = http_get(RBI_EDITION_URLS[fname])
            atomic_replace(target, data, validate_xlsx)
            _result(out, sid, name, "FETCHED",
                    "%d bytes -> %s" % (len(data), os.path.basename(str(target))))
        except Exception as exc:
            had = os.path.exists(target)
            _result(out, sid, name, "KEPT" if had else "MISSING",
                    "fetch failed: %s: %s%s" % (type(exc).__name__, exc,
                                                "" if had else " (no raw file on disk)"))
            warnings.append(
                "WARNING: %s fetch failed (%s: %s) — new Handbook edition - owner must update "
                "sources.py; continuing with %s (never silent)"
                % (sid, type(exc).__name__, exc,
                   "committed interims" if had else "committed interims (raw file absent — CI build may fail on a missing interim)"))
    # parse whichever tables are on disk (fetch may have updated one and not the other)
    if os.path.exists(parse_rbi.T35_PATH):
        try:
            rows = parse_rbi.parse_gold(parse_rbi.T35_PATH)
            parse_rbi.write_csv(parse_rbi.GOLD_OUT, parse_rbi.GOLD_PROVENANCE,
                                parse_rbi.GOLD_HEADER, rows)
            _result(out, "S01", "parse_rbi.parse_gold", "PARSED",
                    "%d rows -> gold_inr_annual.csv" % len(rows))
        except Exception as exc:
            _result(out, "S01", "parse_rbi.parse_gold", "PARSE FAILED",
                    "%s: %s (gold_inr_annual.csv kept)" % (type(exc).__name__, exc))
    if os.path.exists(parse_rbi.T133_PATH):
        try:
            rows = parse_rbi.parse_fx(parse_rbi.T133_PATH)
            parse_rbi.write_csv(parse_rbi.FX_OUT, parse_rbi.FX_PROVENANCE,
                                parse_rbi.FX_HEADER, rows)
            _result(out, "S04", "parse_rbi.parse_fx", "PARSED",
                    "%d rows -> fx_annual.csv" % len(rows))
        except Exception as exc:
            _result(out, "S04", "parse_rbi.parse_fx", "PARSE FAILED",
                    "%s: %s (fx_annual.csv kept)" % (type(exc).__name__, exc))


def refresh_goldhub(out: list, _warnings: list) -> None:
    _result(out, "S03", "WGC Goldhub averages since 1978", "SKIP (fetch)",
            "login-gated download; annual spine unaffected")
    if os.path.exists(GOLDHUB_XLSX):
        try:
            parse_goldhub.main()
            _result(out, "S03", "parse_goldhub (local raw xlsx)", "PARSED",
                    "Goldhub-derived interims regenerated from %s" % GOLDHUB_XLSX)
        except Exception as exc:
            _result(out, "S03", "parse_goldhub (local raw xlsx)", "PARSE FAILED",
                    "%s: %s (pinned interims kept)" % (type(exc).__name__, exc))
    else:
        pinned = pinned_goldhub_date()
        msg = "pinned Goldhub-derived interims reused, last pinned %s" % pinned
        print(msg)
        _result(out, "S03", "parse_goldhub (raw xlsx absent — CI)", "PINNED REUSED", msg)


def run_fetches() -> tuple[list, list]:
    out: list = []
    warnings: list = []
    refresh_fred(out, warnings)
    refresh_lbma(out, warnings)
    refresh_msp(out, warnings)
    refresh_wrri(out, warnings)
    refresh_rbi(out, warnings)
    refresh_goldhub(out, warnings)
    return out, warnings


# ------------------------------------------------------------------- build

def run_build() -> tuple[str, str]:
    try:
        build_mod.build(write=True)
    except SystemExit as exc:
        return "BUILD FAILED", str(exc)
    except Exception as exc:
        return "BUILD FAILED", "%s: %s" % (type(exc).__name__, exc)
    path = os.path.join(ROOT, "site", "dataset.json")
    size = os.path.getsize(path) if os.path.exists(path) else 0
    return "BUILD OK", "site/dataset.json %s bytes" % f"{size:,}"


# ------------------------------------------------------------------ report

def render_report(mode: str, plan: list[dict], results: list | None, warnings: list | None,
                  build_status: str, build_detail: str) -> str:
    lines = ["Rupee Gold Stack — quarterly refresh report",
             "mode: %s    generated: %s"
             % (mode, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
             "", "== plan ==", render_plan(plan, mode), ""]
    if results is None:
        lines += ["== results ==",
                  "NOT EXECUTED — dry-run: no network calls, no raw files written, "
                  "no .new/.bak created, no build run.", ""]
    else:
        lines.append("== results (fetched / kept / skipped per source) ==")
        for sid, name, status, detail in results:
            lines.append("%s  %-44s %-22s %s" % (sid, name, status, detail))
        lines += ["", "== warnings =="]
        lines.extend(warnings if warnings else ["(none)"])
        lines.append("")
    lines.append("== build ==")
    lines.append("%s%s" % (build_status, (" — " + build_detail) if build_detail else ""))
    ds = os.path.join(ROOT, "site", "dataset.json")
    size = os.path.getsize(ds) if os.path.exists(ds) else 0
    lines += ["", "== dataset size ==",
              "site/dataset.json: %s bytes%s"
              % (f"{size:,}", "" if results is not None else " (unchanged — dry-run)")]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Rupee Gold Stack — automated quarterly refresh")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true",
                   help="print the plan, fetch nothing, run no build")
    g.add_argument("--ci", action="store_true",
                   help="fresh-checkout mode: data/ may be absent except the pinned interims")
    args = p.parse_args(argv)
    mode = "ci" if args.ci else ("dry-run" if args.dry_run else "local")

    plan = build_plan(mode)
    print(render_plan(plan, mode))

    if mode == "dry-run":
        results = warnings = None
        build_status, build_detail = "NOT RUN (dry-run)", "no build executed; dataset.json untouched"
    else:
        results, warnings = run_fetches()
        build_status, build_detail = run_build()

    report = render_report(mode, plan, results, warnings, build_status, build_detail)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print("\nrefresh_report.txt written -> %s" % os.path.relpath(REPORT_PATH, ROOT))
    return 0 if build_status in ("BUILD OK", "NOT RUN (dry-run)") else 1


if __name__ == "__main__":
    raise SystemExit(main())
