"""Tests for pipeline.parse_msp (S08 CACP MSP -> msp_annual.csv).

data/raw/msp/msp_table.html is the /json.json response that the CACP
/Home/MSP page renders client-side into its "Minimum Support / Fair &
Remunerative Prices (Crop Year)" table, so the committed fixture
msp_sample.html is a trimmed sample of that artifact: every row of the
four tracked crops exactly as fetched, placeholder years with '-'
prices included.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import parse_msp  # noqa: E402

FIXTURE = HERE / "fixtures" / "msp_sample.html"
REAL = HERE.parent.parent / "data" / "raw" / "msp" / "msp_table.html"


def _rows(path: Path) -> list[dict[str, object]]:
    return parse_msp.parse_msp(path.read_text(encoding="utf-8"))


def _find(rows: list[dict[str, object]], crop: str, crop_year: str) -> dict[str, object]:
    return next(r for r in rows if r["crop"] == crop and r["crop_year"] == crop_year)


@pytest.mark.skipif(not FIXTURE.exists(), reason="fixture msp_sample.html missing")
class TestFixture:
    """Anchors and structure against the trimmed committed sample."""

    def test_wheat_anchors(self) -> None:
        rows = _rows(FIXTURE)
        assert _find(rows, "Wheat", "2024-25")["inr_quintal"] == 2425
        assert _find(rows, "Wheat", "2025-26")["inr_quintal"] == 2585

    def test_paddy_common_2025_26(self) -> None:
        assert _find(_rows(FIXTURE), "Paddy Common", "2025-26")["inr_quintal"] == 2369

    def test_tur_2026_27_is_fixed_price(self) -> None:
        row = _find(_rows(FIXTURE), "Tur (Arhar)", "2026-27")
        assert row["inr_quintal"] == 8450
        assert row["source_flag"] == ""  # taken from the Fixed column

    def test_placeholder_years_dropped_and_crops_exact(self) -> None:
        rows = _rows(FIXTURE)
        assert {r["crop"] for r in rows} == set(parse_msp.CROPS)
        assert not [r for r in rows if r["crop_year"] == "2027-28"]  # '-' placeholders skipped
        assert all(r["source_flag"] in ("", "recommended-only") for r in rows)

    def test_coverage_2010_11_through_2026_27(self) -> None:
        for crop in parse_msp.CROPS:
            years = [r["crop_year"] for r in _rows(FIXTURE) if r["crop"] == crop]
            assert years == sorted(years)
            assert len(years) == 17  # 18 published crop years minus the 2027-28 placeholder
            assert years[0] == "2010-11" and years[-1] == "2026-27"


class TestUnit:
    """Parser mechanism on small synthetic inputs."""

    def test_crop_year_label(self) -> None:
        assert parse_msp.crop_year_label(2010) == "2010-11"
        assert parse_msp.crop_year_label(2024) == "2024-25"
        assert parse_msp.crop_year_label(2027) == "2027-28"

    def test_recommended_only_fallback(self) -> None:
        raw = json.dumps(
            [{"seasonname": "Rabi Crops", "commodityname": "Wheat",
              "financialyear": 2024, "reco_price": "1234", "fixed_price": "-"}]
        )
        assert parse_msp.parse_msp(raw) == [
            {"crop": "Wheat", "crop_year": "2024-25",
             "inr_quintal": 1234, "source_flag": "recommended-only"}
        ]

    def test_both_cells_empty_is_skipped(self) -> None:
        raw = json.dumps(
            [{"seasonname": "Rabi Crops", "commodityname": "Wheat",
              "financialyear": 2027, "reco_price": "-", "fixed_price": ""}]
        )
        assert parse_msp.parse_msp(raw) == []

    def test_fixed_column_wins_over_recommended(self) -> None:
        raw = json.dumps(
            [{"seasonname": "Kharif Crops", "commodityname": "Tur (Arhar)",
              "financialyear": 2026, "reco_price": "8000", "fixed_price": "8450"}]
        )
        row = parse_msp.parse_msp(raw)[0]
        assert row["inr_quintal"] == 8450
        assert row["source_flag"] == ""


@pytest.mark.skipif(not REAL.exists(), reason="data/raw/msp/msp_table.html not fetched")
class TestRealFile:
    """Contract anchors against the full fetched artifact."""

    def test_wheat_anchors(self) -> None:
        rows = _rows(REAL)
        assert _find(rows, "Wheat", "2024-25")["inr_quintal"] == 2425
        assert _find(rows, "Wheat", "2025-26")["inr_quintal"] == 2585

    def test_paddy_common_2025_26(self) -> None:
        assert _find(_rows(REAL), "Paddy Common", "2025-26")["inr_quintal"] == 2369

    def test_tur_2026_27_fixed(self) -> None:
        row = _find(_rows(REAL), "Tur (Arhar)", "2026-27")
        assert row["inr_quintal"] == 8450
        assert row["source_flag"] == ""

    def test_row_count_and_coverage(self) -> None:
        rows = _rows(REAL)
        assert len(rows) == 68
        assert {r["crop"] for r in rows} == set(parse_msp.CROPS)
        assert not [r for r in rows if r["crop_year"] == "2027-28"]


def test_write_csv_provenance(tmp_path: Path) -> None:
    rows = [{"crop": "Wheat", "crop_year": "2024-25", "inr_quintal": 2425, "source_flag": ""}]
    out = tmp_path / "msp_annual.csv"
    parse_msp.write_csv(rows, out)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "# series: msp_annual"
    assert lines[1] == "# source: S08 CACP MSP (accessed 2026-11-21)"
    assert "crop-year as published by CACP" in lines[2]
    assert "rabi marketing year = crop year + 1 (wheat)" in lines[2]
    assert lines[3] == "crop,crop_year,inr_quintal,source_flag"
