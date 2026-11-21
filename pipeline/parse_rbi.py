"""Parse RBI Handbook annual tables into interim CSVs (see pipeline/CONTRACT.md).

T_35 (data/rbi/t35_gold_annual.xlsx) -> data/interim/gold_inr_annual.csv
T_133 (data/rbi/t133_fx_fy.xlsx)     -> data/interim/fx_annual.csv
T_164 (data/rbi/t164_gold_monthly.xlsx) -> data/interim/gold_inr_mumbai_monthly_t164.csv

Sheet layout (all tables): title row 2; header rows 3-5; column-number row 6;
data rows start at row 7. T_35/T_133 continue while column B holds a YYYY-YY
label; T_164 groups monthly rows under FY-block labels in column B (months
Apr-Mar, an Average row per block) until the notes tail. Parsers are pure readers: no network calls, no edits to
data/raw/ (CONTRACT rule 6); unknown cells stay empty, never zero (rule 3).
"""
from __future__ import annotations

import csv
import re
from collections.abc import Iterator
from pathlib import Path

import openpyxl
from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

REPO_ROOT = Path(__file__).resolve().parents[1]

T35_PATH = REPO_ROOT / "data" / "rbi" / "t35_gold_annual.xlsx"
T133_PATH = REPO_ROOT / "data" / "rbi" / "t133_fx_fy.xlsx"
GOLD_OUT = REPO_ROOT / "data" / "interim" / "gold_inr_annual.csv"
FX_OUT = REPO_ROOT / "data" / "interim" / "fx_annual.csv"
T164_PATH = REPO_ROOT / "data" / "rbi" / "t164_gold_monthly.xlsx"
T164_OUT = REPO_ROOT / "data" / "interim" / "gold_inr_mumbai_monthly_t164.csv"

GOLD_HEADER: list[str] = [
    "fy",
    "mumbai_inr_10g",
    "london_usd_oz",
    "london_converted_inr_10g",
    "spread_inr",
    "source_flag",
]
FX_HEADER: list[str] = ["fy", "usdinr_avg", "usdinr_endyear", "regime_flag"]
T164_HEADER: list[str] = ["month", "mumbai_inr_10g", "source_flag"]

GOLD_PROVENANCE: list[str] = [
    "# series: gold_inr_annual",
    "# source: S01 RBI Handbook 2025-26 Table 35 (accessed 2026-11-20)",
    "# notes: FY averages; source break 1999-2000/2000-01",
]
FX_PROVENANCE: list[str] = [
    "# series: fx_annual",
    "# source: S04 RBI Handbook 2025-26 Table 133 (accessed 2026-11-20)",
    "# notes: usdinr_avg = period average; usdinr_endyear = end-year rate;"
    " regime eras per sheet notes: official 1986-87..1991-92, lerms 1992-93,"
    " fedai-market 1993-94..2011-12, rbi-ref 2012-13..2017-18, fbil 2018-19..",
]
T164_PROVENANCE: list[str] = [
    "# series: gold_inr_mumbai_monthly_t164",
    "# source: S02 RBI Handbook 2025-26 Table 164 (accessed 2026-11-21)",
    "# notes: monthly averages, Mumbai \u20b9/10g (column C); FY blocks run Apr-Mar"
    " (Apr-Dec = block start year, Jan-Mar = start year + 1); Average rows"
    " skipped; months with no published value stay empty, never imputed",
]

YEAR_RE = re.compile(r"^\d{4}-\d{2}$")

# (flag, first FY start year, last FY start year); fbil is open-ended per CONTRACT.
REGIME_ERAS: tuple[tuple[str, int, int], ...] = (
    ("official", 1986, 1991),
    ("lerms", 1992, 1992),
    ("fedai-market", 1993, 2011),
    ("rbi-ref", 2012, 2017),
    ("fbil", 2018, 9999),
)


def regime_flag(fy: str) -> str:
    """Regime era label for a YYYY-YY label, keyed by the FY start year."""
    start = int(fy[:4])
    for name, lo, hi in REGIME_ERAS:
        if lo <= start <= hi:
            return name
    return ""


def _cell(ws: Worksheet, row: int, col: int) -> object:
    value = ws.cell(row=row, column=col).value
    if isinstance(value, str):
        return value.strip()
    return value


def _numeric(value: object) -> object:
    """Numeric strings lose thousands separators; non-numeric truth passes through."""
    if isinstance(value, str):
        try:
            return float(value.replace(",", ""))
        except ValueError:
            return value
    return value


def _year_rows(ws: Worksheet) -> Iterator[tuple[int, str]]:
    """Yield (row, fy) for the data block: rows 7+ while column B is a YYYY-YY label.

    The block ends at the first non-empty, non-year row after data began
    (blank rows inside the block are tolerated); notes rows are never read.
    """
    started = False
    for row in range(7, ws.max_row + 1):
        fy = _cell(ws, row, 2)
        if isinstance(fy, str) and YEAR_RE.match(fy):
            started = True
            yield row, fy
        elif started and any(_cell(ws, row, col) is not None for col in range(1, 7)):
            return


def _sheet(wb: Workbook, name: str) -> Worksheet:
    if name not in wb.sheetnames:
        raise ValueError(f"sheet {name!r} not found; sheets={wb.sheetnames}")
    return wb[name]


def parse_gold(path: str | Path = T35_PATH) -> list[dict[str, object]]:
    """T_35 rows: B=fy, C=Mumbai INR/10g, D=London USD/oz, E=converted INR/10g, F=spread."""
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = _sheet(wb, "T_35")
    return [
        {
            "fy": fy,
            "mumbai_inr_10g": _numeric(_cell(ws, row, 3)),
            "london_usd_oz": _numeric(_cell(ws, row, 4)),
            "london_converted_inr_10g": _numeric(_cell(ws, row, 5)),
            "spread_inr": _numeric(_cell(ws, row, 6)),
            "source_flag": "",
        }
        for row, fy in _year_rows(ws)
    ]


def parse_fx(path: str | Path = T133_PATH) -> list[dict[str, object]]:
    """T_133 rows: B=fy, E=USD period average, F=end-year rate; regime_flag per CONTRACT."""
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = _sheet(wb, "T_133")
    return [
        {
            "fy": fy,
            "usdinr_avg": _numeric(_cell(ws, row, 5)),
            "usdinr_endyear": _numeric(_cell(ws, row, 6)),
            "regime_flag": regime_flag(fy),
        }
        for row, fy in _year_rows(ws)
    ]


T164_MONTHS: dict[str, int] = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _month_rows(ws: Worksheet) -> Iterator[tuple[int, str]]:
    """Yield (row, YYYY-MM) for T_164 data rows.

    Column B holds FY-block labels (2022-23) that start a block, then month
    names Apr..Mar; Average rows and the notes tail are skipped. Apr-Dec map
    to the block start year, Jan-Mar to start year + 1 (Indian FY).
    """
    fy_start: int | None = None
    for row in range(7, ws.max_row + 1):
        label = _cell(ws, row, 2)
        if isinstance(label, str) and YEAR_RE.match(label):
            fy_start = int(label[:4])
        elif (fy_start is not None and isinstance(label, str)
              and label[:3].lower() in T164_MONTHS):
            month = T164_MONTHS[label[:3].lower()]
            yield row, "%d-%02d" % (fy_start if month >= 4 else fy_start + 1, month)


def parse_t164(path: str | Path = T164_PATH) -> list[dict[str, object]]:
    """T_164 monthly rows: B=fy/month labels, C=Mumbai INR/10g monthly average.

    Unknown cells stay empty (CONTRACT rule 3); source_flag t164 marks the source.
    """
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = _sheet(wb, "T_164")
    rows: list[dict[str, object]] = []
    for row, month in _month_rows(ws):
        value = _numeric(_cell(ws, row, 3))
        rows.append({
            "month": month,
            "mumbai_inr_10g": value if isinstance(value, (int, float)) else None,
            "source_flag": "t164",
        })
    return rows


def _fmt(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return repr(value)
    return str(value)


def write_csv(
    path: Path,
    provenance: list[str],
    header: list[str],
    rows: list[dict[str, object]],
) -> int:
    """Write provenance comment lines, the header row, then data rows. Returns row count."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        for line in provenance:
            handle.write(line + "\n")
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        for row in rows:
            writer.writerow([_fmt(row.get(col)) for col in header])
    return len(rows)


def main() -> None:
    gold_rows = parse_gold()
    fx_rows = parse_fx()
    n_gold = write_csv(GOLD_OUT, GOLD_PROVENANCE, GOLD_HEADER, gold_rows)
    t164_rows = parse_t164()
    n_fx = write_csv(FX_OUT, FX_PROVENANCE, FX_HEADER, fx_rows)
    n_t164 = write_csv(T164_OUT, T164_PROVENANCE, T164_HEADER, t164_rows)
    print(f"wrote {GOLD_OUT.relative_to(REPO_ROOT)}: {n_gold} data rows")
    print(f"wrote {FX_OUT.relative_to(REPO_ROOT)}: {n_fx} data rows")
    print(f"wrote {T164_OUT.relative_to(REPO_ROOT)}: {n_t164} data rows")


if __name__ == "__main__":
    main()
