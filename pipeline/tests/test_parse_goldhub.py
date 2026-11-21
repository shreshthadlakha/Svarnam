"""Tests for pipeline.parse_goldhub: fixture quirk, real anchors, emitted CSVs.

Run from the repo root:  python -m pytest pipeline/tests/test_parse_goldhub.py -q
"""
import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.parse_goldhub import (  # noqa: E402
    ACCESS_DATE,
    INR_COLUMNS,
    INR_FLAG,
    INR_NOTES,
    INR_SERIES,
    SOURCE_ID,
    USD_COLUMNS,
    USD_FLAG,
    USD_NOTES,
    USD_SERIES,
    parse_goldhub,
    write_csv,
)
from pipeline.units import inr_oz_to_inr_10g  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "goldhub_fixture.xlsx"
REAL_XLSX = ROOT / "data" / "rbi" / "goldhub_averages_since_1978.xlsx"
USD_CSV = ROOT / "data" / "interim" / "gold_usd_monthly.csv"
INR_CSV = ROOT / "data" / "interim" / "gold_inr_domestic_monthly.csv"

# Trimmed raw-format sample: header labels on row 6 (D='USD', J='INR'); the date
# column is unlabeled, one left of 'USD' (C); values sit under their own labels.
FIXTURE_ROWS = [  # (date, USD cell, INR cell) exactly as laid out in the raw quirk
    (datetime(1978, 1, 31), 207.83, "#N/A"),
    (datetime(1978, 2, 28), "#N/A", "#N/A"),
    (datetime(1978, 3, 31), 191.19, "#N/A"),
    (datetime(2005, 9, 30), 470.75, "#N/A"),
    (datetime(2005, 10, 31), 469.6, 21584.0711),
    (datetime(2005, 11, 30), 485.25, 21700.5),
]


@pytest.fixture(scope="session", autouse=True)
def fixture_xlsx() -> Path:
    """Build the trimmed raw-format fixture xlsx (rebuilt each session; openpyxl only)."""
    import openpyxl

    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Monthly_Avg"
    ws["A1"] = "Gold Price Averages in various periods (trimmed fixture)"
    ws["D6"] = "USD"  # header labels sit on row 6 (date column C is unlabeled)
    ws["J6"] = "INR"
    for offset, (day, usd, inr) in enumerate(FIXTURE_ROWS):
        row = 7 + offset
        ws.cell(row, 3, day)  # unlabeled date column, left of the 'USD' label
        ws.cell(row, 4, usd)  # USD directly under its own label (D)
        ws.cell(row, 10, inr)  # INR directly under its own label (J)
    wb.save(FIXTURE)
    return FIXTURE


def _read_interim(path: Path) -> tuple[list[str], list[list[str]]]:
    """Strip '#' provenance lines; return (csv_header, data_rows)."""
    lines = [
        ln
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln and not ln.startswith("#")
    ]
    return lines[0].split(","), [ln.split(",") for ln in lines[1:]]


def test_fixture_rows_with_quirk() -> None:
    usd_rows, inr_rows = parse_goldhub(FIXTURE)
    assert [r[0] for r in usd_rows] == [
        "1978-01", "1978-03", "2005-09", "2005-10", "2005-11",
    ]  # 1978-02 USD '#N/A' skipped
    assert usd_rows[0] == ("1978-01", 207.83, USD_FLAG)
    assert usd_rows[2] == ("2005-09", 470.75, USD_FLAG)
    assert [r[0] for r in inr_rows] == ["2005-10", "2005-11"]  # pre-2005-10 INR '#N/A' skipped
    assert inr_rows[0] == (
        "2005-10", pytest.approx(round(inr_oz_to_inr_10g(21584.0711), 4), abs=1e-9), INR_FLAG,
    )
    assert inr_rows[1][1] == pytest.approx(round(inr_oz_to_inr_10g(21700.5), 4), abs=1e-9)
    assert all(isinstance(r[1], float) for r in usd_rows + inr_rows)  # no '#N/A' leaked


def test_write_csv_provenance(tmp_path: Path) -> None:
    usd_rows, _ = parse_goldhub(FIXTURE)
    out = tmp_path / "gold_usd_monthly.csv"
    n = write_csv(out, USD_SERIES, USD_COLUMNS, usd_rows, USD_NOTES)
    assert n == 5
    text = out.read_text(encoding="utf-8")
    assert text.splitlines()[0] == "# series: gold_usd_monthly"
    assert text.splitlines()[1] == f"# source: {SOURCE_ID} (accessed {ACCESS_DATE})"
    assert text.splitlines()[2].startswith("# notes:")
    columns, rows = _read_interim(out)
    assert columns == list(USD_COLUMNS)
    assert rows[0][:2] == ["1978-01", "207.83"]
    assert rows[0][2] == USD_FLAG


@pytest.mark.skipif(not REAL_XLSX.exists(), reason="real goldhub xlsx not present")
def test_real_usd_anchors() -> None:
    usd_rows, _ = parse_goldhub(REAL_XLSX)
    assert len(usd_rows) == 586
    assert usd_rows[0] == ("1978-01", pytest.approx(207.83), USD_FLAG)
    assert usd_rows[-1][0] == "2026-10"
    months = [r[0] for r in usd_rows]
    assert months == sorted(months) and len(set(months)) == len(months)
    assert all(r[2] == USD_FLAG for r in usd_rows)


@pytest.mark.skipif(not REAL_XLSX.exists(), reason="real goldhub xlsx not present")
def test_real_inr_anchors() -> None:
    _, inr_rows = parse_goldhub(REAL_XLSX)
    assert len(inr_rows) == 253
    assert inr_rows[0][0] == "2005-10"
    assert inr_rows[0][1] == pytest.approx(round(inr_oz_to_inr_10g(21584.0711), 4), abs=1e-9)
    assert inr_rows[0][1] == pytest.approx(6939.44, abs=0.01)  # units-based; CONTRACT text says 6939.42
    assert inr_rows[-1][0] == "2026-10"
    assert all(r[2] == INR_FLAG for r in inr_rows)
    months = [r[0] for r in inr_rows]
    assert months == sorted(months) and len(set(months)) == len(months)


@pytest.mark.skipif(not USD_CSV.exists(), reason="gold_usd_monthly.csv not built yet")
def test_emitted_usd_csv() -> None:
    text = USD_CSV.read_text(encoding="utf-8")
    assert text.splitlines()[0] == "# series: gold_usd_monthly"
    assert text.splitlines()[1] == f"# source: {SOURCE_ID} (accessed {ACCESS_DATE})"
    assert text.splitlines()[2].startswith("# notes:")
    data_lines = [ln for ln in text.splitlines() if ln and not ln.startswith("#")]
    assert all("#N/A" not in ln for ln in data_lines)  # '#N/A' never emitted as a value
    columns, rows = _read_interim(USD_CSV)
    assert columns == list(USD_COLUMNS)
    assert len(rows) == 586
    assert rows[0] == ["1978-01", "207.83", USD_FLAG]
    assert rows[-1][0] == "2026-10"
    assert all(r[2] == USD_FLAG for r in rows)


@pytest.mark.skipif(not INR_CSV.exists(), reason="gold_inr_domestic_monthly.csv not built yet")
def test_emitted_inr_csv() -> None:
    text = INR_CSV.read_text(encoding="utf-8")
    assert text.splitlines()[0] == "# series: gold_inr_domestic_monthly"
    assert text.splitlines()[1] == f"# source: {SOURCE_ID} (accessed {ACCESS_DATE})"
    assert "DOMESTIC" in text.splitlines()[2] and "NOT world-INR" in text.splitlines()[2]
    data_lines = [ln for ln in text.splitlines() if ln and not ln.startswith("#")]
    assert all("#N/A" not in ln for ln in data_lines)  # '#N/A' never emitted as a value
    columns, rows = _read_interim(INR_CSV)
    assert columns == list(INR_COLUMNS)
    assert len(rows) == 253
    assert rows[0][0] == "2005-10" and rows[0][2] == INR_FLAG
    assert float(rows[0][1]) == pytest.approx(round(inr_oz_to_inr_10g(21584.0711), 4), abs=1e-9)
    assert rows[-1][0] == "2026-10"
    assert all(r[2] == INR_FLAG for r in rows)
    assert INR_NOTES.startswith("INR/oz column converted")
