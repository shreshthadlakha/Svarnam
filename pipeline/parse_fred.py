"""Parse FRED DEXINUS daily USD/INR into data/interim/fx_daily.csv.

Input: data/rbi/dexinus_daily.csv, header observation_date,DEXINUS.
Rows whose observation is '.' or empty are missing observations — skipped.
Output layout per pipeline/CONTRACT.md; source_flag stays empty (clean),
the honesty channel per CONTRACT.md rule 2.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_PATH = ROOT / "data" / "rbi" / "dexinus_daily.csv"
OUT_PATH = ROOT / "data" / "interim" / "fx_daily.csv"

SERIES = "fx_daily"
SOURCE = "S05 FRED DEXINUS (accessed 2026-11-21)"
NOTES = "daily USD/INR (DEXINUS); '.'/empty observations skipped; empty flag = clean"

Row = tuple[str, str, str]


def load_fred(path: Path | str) -> list[Row]:
    """Read DEXINUS daily CSV; drop missing ('.'/empty) and non-numeric rows."""
    rows: list[Row] = []
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            date = (row.get("observation_date") or "").strip()
            raw = (row.get("DEXINUS") or "").strip()
            if not date or raw in ("", "."):
                continue
            try:
                float(raw)
            except ValueError:
                continue
            rows.append((date, raw, ""))
    return rows


def write_fx_csv(rows: list[Row], out_path: Path | str) -> None:
    """Provenance header + CSV per CONTRACT.md rule 1."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# series: {SERIES}",
        f"# source: {SOURCE}",
        f"# notes: {NOTES}",
        "date,usdinr,source_flag",
    ]
    lines += [f"{d},{v},{flag}" for d, v, flag in rows]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Parse DEXINUS into interim CSV")
    p.add_argument("--in", dest="inp", type=Path, default=IN_PATH)
    p.add_argument("--out", type=Path, default=OUT_PATH)
    a = p.parse_args(argv)
    rows = load_fred(a.inp)
    if not rows:
        raise SystemExit("no valid DEXINUS rows parsed")
    write_fx_csv(rows, a.out)
    print(f"{SERIES}: {len(rows)} rows; first {rows[0][0]}={rows[0][1]}; last {rows[-1][0]}={rows[-1][1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
