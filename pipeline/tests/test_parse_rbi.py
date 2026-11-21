"""Tests for pipeline/parse_rbi.py.

Fixture tests always run (CI). Real-workbook tests are skipped when the
data/rbi/*.xlsx sources are absent, so CI (fixtures only) still passes.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import openpyxl
import pytest

PIPELINE_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = PIPELINE_DIR.parent
sys.path.insert(0, str(PIPELINE_DIR))

import parse_rbi as pr  # noqa: E402

FIXTURES = PIPELINE_DIR / "tests" / "fixtures"
T35_FIX = FIXTURES / "t35_sample.xlsx"
T133_FIX = FIXTURES / "t133_sample.xlsx"
T35_REAL = REPO_DIR / "data" / "rbi" / "t35_gold_annual.xlsx"
T133_REAL = REPO_DIR / "data" / "rbi" / "t133_fx_fy.xlsx"


def _approx(actual: object, expected: float) -> None:
    """Anchor assertion: None is always a failure, numbers compare near-exactly."""
    if actual is None:
        pytest.fail(f"expected {expected!r}, got None")
    assert actual == pytest.approx(expected, rel=1e-12)


def _approx_pair(actual: object, expected: object) -> None:
    """Two-sided cell comparison: both None passes, mismatched None fails."""
    if actual is None or expected is None:
        assert actual is None and expected is None
    else:
        assert actual == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize(
    ("fy", "expected"),
    [
        ("1985-86", ""),  # before the first regime era
        ("1986-87", "official"),
        ("1991-92", "official"),
        ("1992-93", "lerms"),
        ("1993-94", "fedai-market"),
        ("2011-12", "fedai-market"),
        ("2012-13", "rbi-ref"),
        ("2017-18", "rbi-ref"),
        ("2018-19", "fbil"),
        ("2025-26", "fbil"),
    ],
)
def test_regime_flag_eras(fy: str, expected: str) -> None:
    assert pr.regime_flag(fy) == expected


# --- gold fixture (T_35 layout, 4 data rows) ---


def test_gold_fixture_row_count_and_columns() -> None:
    rows = pr.parse_gold(T35_FIX)
    assert len(rows) == 4
    assert list(rows[0].keys()) == pr.GOLD_HEADER
    assert [row["fy"] for row in rows] == ["1985-86", "1986-87", "1991-92", "2025-26"]


def test_gold_fixture_contract_anchors() -> None:
    rows = pr.parse_gold(T35_FIX)
    _approx(rows[0]["mumbai_inr_10g"], 2125.47)
    _approx(rows[0]["london_usd_oz"], 327.75)
    _approx(rows[-1]["mumbai_inr_10g"], 118420.90)
    _approx(rows[-1]["london_usd_oz"], 3937.86)


def test_gold_fixture_matches_fixture_workbook() -> None:
    rows = pr.parse_gold(T35_FIX)
    ws = openpyxl.load_workbook(T35_FIX, data_only=True)["T_35"]
    by_fy: dict[str, int] = {}
    for r in range(7, ws.max_row + 1):
        value = ws.cell(r, 2).value
        if isinstance(value, str) and pr.YEAR_RE.match(value.strip()):
            by_fy[value.strip()] = r
    for row in rows:
        r = by_fy[str(row["fy"])]
        _approx_pair(row["mumbai_inr_10g"], ws.cell(r, 3).value)
        _approx_pair(row["london_usd_oz"], ws.cell(r, 4).value)
        _approx_pair(row["london_converted_inr_10g"], ws.cell(r, 5).value)
        _approx_pair(row["spread_inr"], ws.cell(r, 6).value)
        assert row["source_flag"] == ""


def test_gold_provenance_header() -> None:
    assert pr.GOLD_PROVENANCE[0] == "# series: gold_inr_annual"
    assert pr.GOLD_PROVENANCE[1].startswith("# source: S01 ")
    assert "(accessed 2026-11-20)" in pr.GOLD_PROVENANCE[1]
    assert pr.GOLD_PROVENANCE[2].startswith("# notes: ")


def test_gold_csv_writer_shape(tmp_path: Path) -> None:
    rows = pr.parse_gold(T35_FIX)
    out = tmp_path / "gold_inr_annual.csv"
    assert pr.write_csv(out, pr.GOLD_PROVENANCE, pr.GOLD_HEADER, rows) == 4
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "# series: gold_inr_annual"
    assert lines[3] == ",".join(pr.GOLD_HEADER)
    body = [ln for ln in lines if not ln.startswith("#")]  # [0] is the header row
    data = list(csv.DictReader(body))
    assert data[0]["fy"] == "1985-86"
    assert float(data[0]["mumbai_inr_10g"]) == pytest.approx(2125.47, rel=1e-12)
    assert float(data[-1]["london_usd_oz"]) == pytest.approx(3937.86, rel=1e-12)
    assert data[0]["source_flag"] == ""


# --- fx fixture (T_133 layout, 4 data rows) ---


def test_fx_fixture_rows_regimes_anchors() -> None:
    rows = pr.parse_fx(T133_FIX)
    assert len(rows) == 4
    assert list(rows[0].keys()) == pr.FX_HEADER
    assert [row["fy"] for row in rows] == ["1986-87", "1991-92", "1992-93", "2025-26"]
    assert [row["regime_flag"] for row in rows] == ["official", "official", "lerms", "fbil"]
    _approx(rows[0]["usdinr_avg"], 12.7782)
    _approx(rows[-1]["usdinr_avg"], 88.3071)


def test_fx_fixture_matches_fixture_workbook() -> None:
    rows = pr.parse_fx(T133_FIX)
    ws = openpyxl.load_workbook(T133_FIX, data_only=True)["T_133"]
    by_fy: dict[str, int] = {}
    for r in range(7, ws.max_row + 1):
        value = ws.cell(r, 2).value
        if isinstance(value, str) and pr.YEAR_RE.match(value.strip()):
            by_fy[value.strip()] = r
    for row in rows:
        r = by_fy[str(row["fy"])]
        _approx_pair(row["usdinr_avg"], ws.cell(r, 5).value)
        _approx_pair(row["usdinr_endyear"], ws.cell(r, 6).value)


def test_fx_provenance_header() -> None:
    assert pr.FX_PROVENANCE[0] == "# series: fx_annual"
    assert pr.FX_PROVENANCE[1].startswith("# source: S04 ")
    assert "(accessed 2026-11-20)" in pr.FX_PROVENANCE[1]
    assert pr.FX_PROVENANCE[2].startswith("# notes: ")


def test_fx_csv_writer_shape(tmp_path: Path) -> None:
    rows = pr.parse_fx(T133_FIX)
    out = tmp_path / "fx_annual.csv"
    assert pr.write_csv(out, pr.FX_PROVENANCE, pr.FX_HEADER, rows) == 4
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[3] == ",".join(pr.FX_HEADER)
    body = [ln for ln in lines if not ln.startswith("#")]  # [0] is the header row
    data = list(csv.DictReader(body))
    assert data[1]["fy"] == "1991-92" and data[1]["regime_flag"] == "official"
    assert data[2]["fy"] == "1992-93" and data[2]["regime_flag"] == "lerms"
    assert float(data[0]["usdinr_avg"]) == pytest.approx(12.7782, rel=1e-12)
    assert float(data[-1]["usdinr_avg"]) == pytest.approx(88.3071, rel=1e-12)


# --- real workbooks (skipped when absent, e.g. CI without data/raw) ---


@pytest.mark.skipif(not T35_REAL.exists(), reason="real T_35 workbook not present; CI runs fixtures only")
class TestRealT35:
    def test_row_count_and_fy_span(self) -> None:
        rows = pr.parse_gold(T35_REAL)
        assert len(rows) == 41
        assert rows[0]["fy"] == "1985-86"
        assert rows[-1]["fy"] == "2025-26"

    def test_contract_anchors(self) -> None:
        rows = pr.parse_gold(T35_REAL)
        _approx(rows[0]["mumbai_inr_10g"], 2125.47)
        _approx(rows[0]["london_usd_oz"], 327.75)
        _approx(rows[-1]["mumbai_inr_10g"], 118420.90)
        _approx(rows[-1]["london_usd_oz"], 3937.86)


@pytest.mark.skipif(not T133_REAL.exists(), reason="real T_133 workbook not present; CI runs fixtures only")
class TestRealT133:
    def test_row_count_and_fy_span(self) -> None:
        rows = pr.parse_fx(T133_REAL)
        assert len(rows) == 40
        assert rows[0]["fy"] == "1986-87"
        assert rows[-1]["fy"] == "2025-26"

    def test_contract_anchors(self) -> None:
        by_fy = {str(row["fy"]): row for row in pr.parse_fx(T133_REAL)}
        _approx(by_fy["1986-87"]["usdinr_avg"], 12.7782)
        _approx(by_fy["1990-91"]["usdinr_avg"], 17.9428)
        _approx(by_fy["2025-26"]["usdinr_avg"], 88.3071)

    def test_regime_eras_covered(self) -> None:
        rows = pr.parse_fx(T133_REAL)
        by_fy = {str(row["fy"]): row for row in rows}
        assert by_fy["1986-87"]["regime_flag"] == "official"
        assert by_fy["1991-92"]["regime_flag"] == "official"
        assert by_fy["1992-93"]["regime_flag"] == "lerms"
        assert by_fy["2012-13"]["regime_flag"] == "rbi-ref"
        assert by_fy["2018-19"]["regime_flag"] == "fbil"
        assert {row["regime_flag"] for row in rows} == {
            "official",
            "lerms",
            "fedai-market",
            "rbi-ref",
            "fbil",
        }
