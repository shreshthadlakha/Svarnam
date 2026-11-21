"""Parse S03 WGC Goldhub monthly averages xlsx -> interim CSVs.

Raw layout quirk (byte-verified against data/rbi/goldhub_averages_since_1978.xlsx):
sheet 'Monthly_Avg' carries its currency labels on row 6 (D='USD', ..., J='INR'),
but the date column is unlabeled: data rows start on row 7 with the month date one
column LEFT of the 'USD' label (C), and every value sits directly under its own
label (USD at D, INR at J) - i.e. +1 relative to the unlabeled date column.
Verified anchors: D7 = 207.83 (1978-01-31); J340 = 21584.0711 (2005-10-31).
'#N/A' cells are skipped - never emitted as values.

Outputs (pipeline/CONTRACT.md):
  data/interim/gold_usd_monthly.csv           month,usd_oz,source_flag
  data/interim/gold_inr_domestic_monthly.csv  month,inr_10g_domestic,source_flag
"""
from __future__ import annotations

import csv
import sys
from datetime import date, datetime
from pathlib import Path

import openpyxl

if __package__ in (None, ""):  # allow `python pipeline/parse_goldhub.py` from anywhere
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.units import inr_oz_to_inr_10g  # noqa: E402  (CONTRACT rule 5)

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_XLSX = REPO_ROOT / "data" / "rbi" / "goldhub_averages_since_1978.xlsx"
OUT_DIR = REPO_ROOT / "data" / "interim"

SHEET = "Monthly_Avg"
HEADER_ROW = 6  # byte-verified: label row; data starts on row 7, shifted +1
LABELS = ("USD", "INR")
SOURCE_ID = "S03 WGC Goldhub averages xlsx (INR from 1978)"
ACCESS_DATE = "2026-11-21"

USD_SERIES = "gold_usd_monthly"
USD_COLUMNS = ("month", "usd_oz", "source_flag")
USD_FLAG = ""  # CONTRACT vocabulary: empty = clean
USD_NOTES = "Monthly_Avg USD column, USD per troy-oz; #N/A cells skipped"

INR_SERIES = "gold_inr_domestic_monthly"
INR_COLUMNS = ("month", "inr_10g_domestic", "source_flag")
INR_FLAG = "derived"
INR_NOTES = (
    "INR/oz column converted to INR/10g via pipeline.units.inr_oz_to_inr_10g; "
    "Indian DOMESTIC price (verified vs RBI T35 within +/-0.06%), NOT world-INR; "
    "#N/A cells skipped"
)

Row = tuple[str, float, str]


def _header_columns(ws: "openpyxl.worksheet.worksheet.Worksheet") -> dict[str, int]:
    """Locate 'USD'/'INR' label columns in the header row (by name, not position)."""
    label_col: dict[str, int] = {}
    for col in range(1, ws.max_column + 1):
        value = ws.cell(HEADER_ROW, col).value
        if isinstance(value, str):
            label = value.strip()
            if label in LABELS and label not in label_col:
                label_col[label] = col
    missing = [label for label in LABELS if label not in label_col]
    if missing:
        raise ValueError(f"{SHEET}: header row {HEADER_ROW} has no {missing} label")
    return {
        "date": label_col["USD"] - 1,  # quirk: unlabeled date column left of 'USD'
        "usd": label_col["USD"],  # quirk: values sit directly under their labels
        "inr": label_col["INR"],
    }


def _month(value: object) -> str | None:
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return f"{value.year:04d}-{value.month:02d}"
    return None


def _numeric(value: object) -> float | None:
    """Numbers only: '#N/A', blanks and None are skipped, never emitted."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def parse_goldhub(path: Path = SOURCE_XLSX) -> tuple[list[Row], list[Row]]:
    """Return (usd_rows, inr_rows); each row is (month, value, source_flag)."""
    workbook = openpyxl.load_workbook(path, data_only=True)
    if SHEET not in workbook.sheetnames:
        raise ValueError(f"{path}: sheet {SHEET!r} not found in {workbook.sheetnames}")
    ws = workbook[SHEET]
    cols = _header_columns(ws)
    usd_rows: list[Row] = []
    inr_rows: list[Row] = []
    for row in ws.iter_rows(min_row=HEADER_ROW + 1, values_only=True):
        month = _month(row[cols["date"] - 1]) if len(row) >= cols["date"] else None
        if month is None:
            continue
        usd = _numeric(row[cols["usd"] - 1]) if len(row) >= cols["usd"] else None
        if usd is not None:
            usd_rows.append((month, usd, USD_FLAG))
        inr = _numeric(row[cols["inr"] - 1]) if len(row) >= cols["inr"] else None
        if inr is not None:
            inr_rows.append((month, round(inr_oz_to_inr_10g(inr), 4), INR_FLAG))
    return usd_rows, inr_rows


def write_csv(
    path: Path, series: str, columns: tuple[str, ...], rows: list[Row], notes: str
) -> int:
    """Write one interim CSV with CONTRACT provenance header; returns data-row count."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(f"# series: {series}\n")
        fh.write(f"# source: {SOURCE_ID} (accessed {ACCESS_DATE})\n")
        fh.write(f"# notes: {notes}\n")
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(rows)
    return len(rows)


def main() -> int:
    usd_rows, inr_rows = parse_goldhub()
    n_usd = write_csv(OUT_DIR / f"{USD_SERIES}.csv", USD_SERIES, USD_COLUMNS, usd_rows, USD_NOTES)
    n_inr = write_csv(OUT_DIR / f"{INR_SERIES}.csv", INR_SERIES, INR_COLUMNS, inr_rows, INR_NOTES)
    print(f"{USD_SERIES}.csv: {n_usd} rows ({usd_rows[0][0]}..{usd_rows[-1][0]})")
    print(f"{INR_SERIES}.csv: {n_inr} rows ({inr_rows[0][0]}..{inr_rows[-1][0]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
