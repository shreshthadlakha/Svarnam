"""Validator behaviour tests — golden values catch corruption (fail-hard path)."""
import pytest

from pipeline import validate


def test_validate_interims_real_files():
    """Runs against the real interim files when present (repo build)."""
    try:
        problems, stats, notes = validate.validate_interims()
    except validate.ValidationError as e:
        pytest.skip("interims not built yet: %s" % e)
    assert not problems, problems


def test_golden_value_catches_corruption(monkeypatch, tmp_path):
    """Corrupting a golden value must surface as a problem (A2 invariant)."""
    import os
    d = tmp_path
    rows = ["fy,mumbai_inr_10g,london_usd_oz,london_converted_inr_10g,spread_inr,source_flag",
            "1985-86,2125.47,327.75,1289.76,835.71,",
            "1991-92,4297.63,357.40,2841.07,1456.55,",
            "2024-25,75841.87,2584.53,70315.41,5526.46,",
            "2025-26,118420.90,3937.86,112381.86,6039.04,"]
    (d / "gold_inr_annual.csv").write_text("\n".join(rows), encoding="utf-8")
    (d / "fx_annual.csv").write_text(
        "fy,usdinr_avg,usdinr_endyear,regime_flag\n"
        "1986-87,12.7777,12.8882,official\n"
        "1991-92,24.4737,31.2256,official\n"
        "2024-25,84.5756,85.5814,fbil\n"
        "2025-26,88.3071,94.6543,fbil\n", encoding="utf-8")
    for name in ("lbma_daily.csv", "fx_daily.csv", "gold_usd_monthly.csv",
                 "gold_inr_domestic_monthly.csv", "msp_annual.csv", "wage_annual.csv"):
        (d / name).write_text("", encoding="utf-8")
    monkeypatch.setattr(validate, "INTERIM", str(d))
    problems, stats, notes = validate.validate_interims()
    assert any("1986-87 golden mismatch" in s for s in problems), problems
    assert any("interim file missing or empty" in s for s in problems), problems


def test_ci_mode_tolerates_missing_lbma(monkeypatch, tmp_path):
    """CI baseline: the raw LBMA feed is never pinned (licensing) — its absence is a
    note, not a failure; every other missing file still fails the build."""
    import os
    d = tmp_path
    rows = ["fy,mumbai_inr_10g,london_usd_oz,london_converted_inr_10g,spread_inr,source_flag",
            "1985-86,2125.47,327.75,1289.76,835.71,",
            "1991-92,4297.63,357.40,2841.07,1456.55,",
            "2024-25,75841.87,2584.53,70315.41,5526.46,",
            "2025-26,118420.90,3937.86,112381.86,6039.04,"]
    (d / "gold_inr_annual.csv").write_text("\n".join(rows), encoding="utf-8")
    (d / "fx_annual.csv").write_text(
        "fy,usdinr_avg,usdinr_endyear,regime_flag\n"
        "1986-87,12.7782,12.8882,official\n"
        "1991-92,24.4737,31.2256,official\n"
        "2024-25,84.5756,85.5814,fbil\n"
        "2025-26,88.3071,94.6543,fbil\n", encoding="utf-8")
    for name in ("fx_daily.csv", "gold_usd_monthly.csv", "gold_inr_domestic_monthly.csv",
                 "msp_annual.csv", "wage_annual.csv"):
        (d / name).write_text("", encoding="utf-8")
    # lbma_daily.csv deliberately absent
    monkeypatch.setattr(validate, "INTERIM", str(d))
    problems, stats, notes = validate.validate_interims(ci_mode=True)
    assert not any("lbma_daily" in s for s in problems), problems
    assert any("lbma_daily" in s for s in notes), notes
    assert any("interim file missing or empty" in s for s in problems), problems
