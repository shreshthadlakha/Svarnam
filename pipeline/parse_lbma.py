"""Parse LBMA Gold Price PM daily JSON into data/interim/lbma_daily.csv.

Inputs: data/rbi/gold_pm_wb.json (Wayback history) + data/rbi/gold_pm_live.json
(live feed), both JSON lists of rows like {"is_cms_locked": 0, "d": "YYYY-MM-DD",
"v": [usd_oz, gbp_oz, eur_oz]}. Merge both, dedupe on date preferring the live
row, skip rows whose USD value (v[0]) is null or a string. Output layout and
honesty flags per pipeline/CONTRACT.md.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WB_PATH = ROOT / "data" / "rbi" / "gold_pm_wb.json"
LIVE_PATH = ROOT / "data" / "rbi" / "gold_pm_live.json"
OUT_PATH = ROOT / "data" / "interim" / "lbma_daily.csv"

SERIES = "lbma_daily"
SOURCE = "S09 LBMA Gold Price PM JSON (accessed 2026-11-21)"
NOTES = (
    "LBMA Gold Price PM USD/oz; merged wayback+live, dedupe preferring live; "
    "USD null/string rows skipped; source_flag live/wayback"
)

Row = tuple[str, float, str]


def usd_of(row: dict) -> float | None:
    """USD/oz from v[0]; None when missing, null or a non-numeric string."""
    v = row.get("v")
    if not isinstance(v, list) or not v:
        return None
    usd = v[0]
    if isinstance(usd, bool) or not isinstance(usd, (int, float)):
        return None
    return float(usd)


def load_lbma(wb_path: Path | str, live_path: Path | str) -> list[Row]:
    """Merge the two JSON sources; the later (live) pass overwrites wayback."""
    merged: dict[str, tuple[float, str]] = {}
    for path, flag in ((Path(wb_path), "wayback"), (Path(live_path), "live")):
        rows = json.loads(Path(path).read_text(encoding="utf-8"))
        for row in rows:
            date, usd = row.get("d"), usd_of(row)
            if not date or usd is None:
                continue
            merged[date] = (usd, flag)
    return [(d, usd, flag) for d, (usd, flag) in sorted(merged.items())]


def write_lbma_csv(rows: list[Row], out_path: Path | str) -> None:
    """Provenance header + CSV per CONTRACT.md rule 1."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# series: {SERIES}",
        f"# source: {SOURCE}",
        f"# notes: {NOTES}",
        "date,usd_oz,source_flag",
    ]
    lines += [f"{d},{usd:.2f},{flag}" for d, usd, flag in rows]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Merge LBMA PM JSON into interim CSV")
    p.add_argument("--wb", type=Path, default=WB_PATH)
    p.add_argument("--live", type=Path, default=LIVE_PATH)
    p.add_argument("--out", type=Path, default=OUT_PATH)
    a = p.parse_args(argv)
    rows = load_lbma(a.wb, a.live)
    if not rows:
        raise SystemExit("no valid LBMA rows parsed")
    write_lbma_csv(rows, a.out)
    print(
        f"{SERIES}: {len(rows)} unique dates; "
        f"first {rows[0][0]}={rows[0][1]:.2f}; last {rows[-1][0]}={rows[-1][1]:.2f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
