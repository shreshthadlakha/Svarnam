"""Tests for the S02 T164 monthly extension: parser, build merge, RBI discovery.

Fixture tests always run (CI). Real-workbook / real-interim tests are skipped
when data/rbi/t164_gold_monthly.xlsx or the parsed interim CSV is absent.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

PIPELINE_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = PIPELINE_DIR.parent
sys.path.insert(0, str(REPO_DIR))  # package imports: pipeline.build / pipeline.refresh

import parse_rbi as pr  # noqa: E402  (flat import, mirrors test_parse_rbi.py)
from pipeline import build as build_mod  # noqa: E402
from pipeline import refresh as refresh_mod  # noqa: E402

FIXTURES = PIPELINE_DIR / "tests" / "fixtures"
T164_FIX = FIXTURES / "t164_sample.xlsx"
INDEX_FIX = FIXTURES / "rbi_handbook_index_sample.html"
T164_REAL = REPO_DIR / "data" / "rbi" / "t164_gold_monthly.xlsx"
T164_CSV_REAL = REPO_DIR / "data" / "interim" / "gold_inr_mumbai_monthly_t164.csv"
DOM_REAL = REPO_DIR / "data" / "interim" / "gold_inr_domestic_monthly.csv"


def _approx(actual: object, expected: float) -> None:
    if actual is None:
        pytest.fail(f"expected {expected!r}, got None")
    assert actual == pytest.approx(expected, rel=1e-12)


# --- parser: fixture workbook (real T_164 layout, FY2025-26 + partial FY2026-27) ---


def test_t164_fixture_months_flags() -> None:
    rows = pr.parse_t164(T164_FIX)
    assert len(rows) == 13  # 12 months of FY2025-26 + Apr of FY2026-27; Average rows skipped
    assert [r["month"] for r in rows] == [
        "2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09",
        "2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04",
    ]
    assert all(r["source_flag"] == "t164" for r in rows)
    assert list(rows[0].keys()) == pr.T164_HEADER


def test_t164_fixture_spot_values() -> None:
    rows = pr.parse_t164(T164_FIX)
    by_month = {r["month"]: r["mumbai_inr_10g"] for r in rows}
    _approx(by_month["2025-04"], 93091.21)
    _approx(by_month["2025-10"], 121907.67)
    _approx(by_month["2026-01"], 145946.9)
    _approx(by_month["2026-04"], 149927.3)


def test_t164_provenance_header() -> None:
    assert pr.T164_PROVENANCE[0] == "# series: gold_inr_mumbai_monthly_t164"
    assert pr.T164_PROVENANCE[1].startswith(
        "# source: S02 RBI Handbook 2025-26 Table 164 (accessed ")
    assert pr.T164_PROVENANCE[2].startswith("# notes: ")


def test_t164_csv_writer_shape(tmp_path: Path) -> None:
    rows = pr.parse_t164(T164_FIX)
    out = tmp_path / "gold_inr_mumbai_monthly_t164.csv"
    assert pr.write_csv(out, pr.T164_PROVENANCE, pr.T164_HEADER, rows) == 13
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "# series: gold_inr_mumbai_monthly_t164"
    assert lines[3] == ",".join(pr.T164_HEADER)
    data = list(csv.DictReader([ln for ln in lines if not ln.startswith("#")]))
    assert data[0]["month"] == "2025-04"
    assert data[0]["source_flag"] == "t164"
    assert float(data[-1]["mumbai_inr_10g"]) == pytest.approx(149927.3, rel=1e-12)


# --- parser: real workbook (skipped when absent, e.g. CI without data/raw) ---


@pytest.mark.skipif(not T164_REAL.exists(),
                    reason="real T_164 workbook not present; CI runs fixtures only")
class TestRealT164:
    def test_row_count_and_span(self) -> None:
        rows = pr.parse_t164(T164_REAL)
        assert len(rows) == 49  # 2022-04 .. 2026-04 (the FY2026-27 block holds Apr only)
        assert rows[0]["month"] == "2022-04"
        assert rows[-1]["month"] == "2026-04"

    def test_spot_values_vs_probed_sheet(self) -> None:
        rows = pr.parse_t164(T164_REAL)
        by_month = {r["month"]: r["mumbai_inr_10g"] for r in rows}
        _approx(by_month["2022-04"], 52022.53)
        _approx(by_month["2025-10"], 121907.67)
        _approx(by_month["2026-04"], 149927.3)


@pytest.mark.skipif(not T164_CSV_REAL.exists(),
                    reason="parsed T164 interim not present yet")
class TestRealT164Interim:
    def test_provenance_and_rows(self) -> None:
        lines = T164_CSV_REAL.read_text(encoding="utf-8").splitlines()
        assert lines[0] == "# series: gold_inr_mumbai_monthly_t164"
        assert lines[1].startswith("# source: S02 RBI Handbook 2025-26 Table 164 (accessed ")
        data = list(csv.DictReader([ln for ln in lines if not ln.startswith("#")]))
        assert len(data) == 49
        assert data[0]["month"] == "2022-04"
        assert float(data[0]["mumbai_inr_10g"]) == pytest.approx(52022.53, rel=1e-12)


# --- build.py merge: synthetic Goldhub + T164 frames ---


def _dom(month: str, value: float) -> dict:
    return {"month": month, "inr_10g_domestic": value, "source_flag": "derived"}


def _t164(month: str, value: float) -> dict:
    return {"month": month, "mumbai_inr_10g": value, "source_flag": "t164"}


def test_merge_goldhub_authoritative_t164_extension() -> None:
    goldhub = [_dom("2026-01", 100.0), _dom("2026-02", 110.0), _dom("2026-03", 120.0)]
    t164 = [_t164("2026-01", 100.5), _t164("2026-02", 111.0),
            _t164("2026-04", 130.0), _t164("2026-05", 140.0)]
    merged, cc = build_mod._merge_domestic_monthly(goldhub, t164)
    assert [r["month"] for r in merged] == [
        "2026-01", "2026-02", "2026-03", "2026-04", "2026-05"]
    assert [r["source_flag"] for r in merged] == [
        "derived", "derived", "derived", "t164-extension", "t164-extension"]
    assert merged[0]["inr_10g_domestic"] == 100.0  # overlap months keep the Goldhub value
    assert merged[3]["inr_10g_domestic"] == 130.0
    assert cc["last_goldhub_month"] == "2026-03"
    assert cc["overlap_months"] == 2
    expected_mean = ((100.5 - 100.0) / 100.0 * 100.0 + (111.0 - 110.0) / 110.0 * 100.0) / 2
    assert cc["mean_abs_pct_diff"] == pytest.approx(expected_mean, abs=1e-3)
    assert cc["warn"] is False
    assert cc["extension_months"] == 2


def test_merge_overlap_never_replaced_warn_above_one_pct() -> None:
    goldhub = [_dom("2026-01", 100.0)]
    merged, cc = build_mod._merge_domestic_monthly(goldhub, [_t164("2026-01", 103.0)])
    assert merged == goldhub  # overlap month is never replaced, nothing appended
    assert cc["warn"] is True
    assert cc["mean_abs_pct_diff"] == pytest.approx(3.0, abs=1e-9)


def test_merge_missing_t164_interim_is_pure_goldhub() -> None:
    goldhub = [_dom("2026-01", 100.0)]
    merged, cc = build_mod._merge_domestic_monthly(goldhub, [])
    assert merged == goldhub
    assert cc["overlap_months"] == 0 and cc["extension_months"] == 0
    assert cc["mean_abs_pct_diff"] is None and cc["warn"] is False


def test_usd_extension_lbma_monthly_means() -> None:
    usd = [{"month": "2026-01", "usd_oz": 4000.0, "source_flag": ""}]
    lbma = [{"date": "2026-01-05", "usd_oz": 99999.0, "source_flag": "live"},  # inside pin: ignored
            {"date": "2026-02-02", "usd_oz": 4000.0, "source_flag": "live"},
            {"date": "2026-02-03", "usd_oz": 4010.0, "source_flag": "live"},
            {"date": "2026-02-04", "usd_oz": 4020.0, "source_flag": "live"}]
    merged, n = build_mod._extend_usd_monthly(usd, lbma)
    assert n == 1
    assert merged[0]["source_flag"] == "" and merged[0]["usd_oz"] == 4000.0
    assert merged[1]["month"] == "2026-02" and merged[1]["source_flag"] == "lbma-derived"
    assert merged[1]["usd_oz"] == pytest.approx(4010.0, abs=1e-9)


def test_usd_extension_months_without_lbma_are_skipped() -> None:
    usd = [{"month": "2026-02", "usd_oz": 4010.0, "source_flag": "lbma-derived"}]
    lbma = [{"date": "2026-04-01", "usd_oz": 4100.0, "source_flag": "live"}]
    merged, n = build_mod._extend_usd_monthly(usd, lbma)
    assert n == 1
    assert [r["month"] for r in merged] == ["2026-02", "2026-04"]  # 2026-03 gap: skipped, never imputed


def test_decomposition_monthly_carries_extension_flags() -> None:
    from pipeline import derive
    from pipeline import policy as policy_mod
    dom = [{"month": "2026-01", "inr_10g_domestic": 100.0, "source_flag": "derived"},
           {"month": "2026-02", "inr_10g_domestic": 130.0, "source_flag": "t164-extension"}]
    usd = [{"month": "2026-02", "usd_oz": 4000.0, "source_flag": "lbma-derived"}]
    fx = [{"date": "2026-02-05", "usdinr": 90.0}]
    out = derive.decomposition_monthly(dom, usd, fx, policy_mod.load_duty_calendar())
    assert [r["month"] for r in out] == ["2026-02"]  # 2026-01 lacks usd/fx -> skipped, never imputed
    assert out[0]["flags"] == ["goldhub-domestic", "fred-h10-fx", "t164-extension", "lbma-derived"]


# --- refresh.py: RBI index discovery (pure function + saved HTML fixture) ---


def test_discovery_matches_fixture_hrefs() -> None:
    urls = refresh_mod.discover_rbi_urls(INDEX_FIX.read_text(encoding="utf-8"))
    assert set(urls) == {"35", "133", "164"}
    assert urls["164"] == "https://rbi.org.in/Documents/HS-2025-26/T_164T_HBIE202526A1B2.XLSX"
    assert urls["133"] == "https://rbi.org.in/Documents/HS-2025-26/T_133T_HBIE202526A1B2.XLSX"
    assert urls["35"] == "https://rbi.org.in/Documents/HS-2025-26/T_35T_HBIE202526A1B2.XLSX"


def test_discovery_first_edition_wins() -> None:
    urls = refresh_mod.discover_rbi_urls(INDEX_FIX.read_text(encoding="utf-8"))
    assert "202425" not in urls["35"]  # newest edition first: first match per table wins


def test_discovery_no_match_returns_empty() -> None:
    assert refresh_mod.discover_rbi_urls(
        "<html><a href=\"/x/y.XLSX\">t</a></html>", tables=("164",)) == {}


def test_plan_includes_t164_entry() -> None:
    plan = {s["id"]: s for s in refresh_mod.build_plan("local")}
    assert plan["S02"]["parser"] == "pipeline.parse_rbi.parse_t164"
    assert plan["S02"]["target"].endswith("t164_gold_monthly.xlsx")


# --- real merge sanity (skipped when real interims are absent) ---


@pytest.mark.skipif(not (T164_CSV_REAL.exists() and DOM_REAL.exists()),
                    reason="real interims not present; CI runs fixtures only")
class TestRealMerge:
    def test_goldhub_pin_still_leads(self) -> None:
        goldhub = build_mod._read("gold_inr_domestic_monthly.csv", numeric=("inr_10g_domestic",))
        t164 = build_mod._read(build_mod.T164_CSV, numeric=("mumbai_inr_10g",))
        merged, cc = build_mod._merge_domestic_monthly(goldhub, t164)
        assert cc["overlap_months"] == 49      # T164 2022-04..2026-04 all inside the pin
        assert cc["extension_months"] == 0     # pin ends 2026-10 > T164 last month
        assert len(merged) == len(goldhub)
        assert merged[-1]["month"] == "2026-10"
        assert merged[0]["source_flag"] == "derived"
        assert cc["mean_abs_pct_diff"] is not None
