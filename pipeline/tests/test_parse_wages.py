"""Tests for parse_wages.py: fixture behavior + real-file anchors (skipif raw absent)."""

import csv
import re
from pathlib import Path

import pytest

from pipeline import parse_wages

FIXTURE = Path(__file__).parent / "fixtures" / "wrri_raw_sample.csv"
RAW = parse_wages.RAW_PATH
RAW_PRESENT = RAW.is_file()
requires_raw = pytest.mark.skipif(not RAW_PRESENT, reason="data/wages/wrri_raw.csv not present")


def _by_key(rows):
    return {(r["fy"], r["state"], r["occupation_group"], r["occupation"]): r for r in rows}


def _read_raw():
    with RAW.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def _raw_floats(rows, column):
    """Independent numeric filter: float() rejects '@'/'-'/empty cells."""
    values = []
    for row in rows:
        try:
            values.append(float(row[column]))
        except ValueError:
            continue
    return values


def _is_numeric(value):
    """Independent of parse_wages._numeric: float() rejects '@'/'-'/empty."""
    try:
        float(value)
        return True
    except ValueError:
        return False


# --- fixture tests -------------------------------------------------------

def test_fixture_annualization(tmp_path):
    rows = parse_wages.parse(FIXTURE, tmp_path / "wage_annual.csv")
    by = _by_key(rows)

    plough = by[("2006-07", "ANDHRA PRADESH", "Agriculture", "Ploughing")]
    assert plough["inr_day"] == "80.50"          # (79.90 + 81.10) / 2; '-' and '@' skipped
    assert plough["inr_day_female"] == ""        # no numeric female months → empty, not zero
    assert plough["n_months"] == "2"
    assert plough["source_flag"] == "partial-year"

    sowing = by[("2007-08", "ANDHRA PRADESH", "Agriculture", "Sowing")]
    assert sowing["inr_day"] == "61.25"          # (60.00 + 62.50 + 61.25) / 3
    assert sowing["inr_day_female"] == "41.25"   # (40.00 + 42.50) / 2; male count drives n_months
    assert sowing["n_months"] == "3"
    assert sowing["source_flag"] == "partial-year"

    loaders = by[("2013-14", "ANDHRA PRADESH", "Non-Agriculture",
                  "Non-agricultural labourers(including porters, loaders)")]
    assert loaders["inr_day"] == "150.00"        # comma-quoted occupation survives round-trip
    assert loaders["inr_day_female"] == "100.00"
    assert loaders["source_flag"] == "partial-year"

    sweepers = by[("2022-23", "All India", "Non-Agriculture", "Sweeping/cleaning workers")]
    assert sweepers["inr_day"] == "300.00"
    assert sweepers["inr_day_female"] == "250.00"
    assert sweepers["n_months"] == "1"
    assert sweepers["series"] == "WRRI"


def test_fixture_full_year_flag_and_female_independence(tmp_path):
    rows = parse_wages.parse(FIXTURE, tmp_path / "wage_annual.csv")
    weeding = _by_key(rows)[("2008-09", "KERALA", "Agriculture", "Weeding")]
    assert weeding["n_months"] == "12"           # male numeric in all 12 months
    assert weeding["source_flag"] == ""          # full year → no flag
    assert weeding["inr_day"] == "6.50"          # mean(1..12)
    assert weeding["inr_day_female"] == "6.67"   # mean(1,2,4,5,7,8,10,11,12); '-' months skipped


def test_fixture_file_shape(tmp_path):
    out = tmp_path / "wage_annual.csv"
    parse_wages.parse(FIXTURE, out)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "# series: wage_annual"
    assert lines[1].startswith("# source: S06 Labour Bureau")
    assert lines[1].endswith("(accessed 2026-11-21)")
    assert lines[2].startswith("# notes: ") and "Nov-2013" in lines[2]
    assert lines[3].split(",") == parse_wages.COLUMNS


# --- real-file anchors ---------------------------------------------------

@requires_raw
def test_raw_anchor_ap_jan_2006_07_ploughing():
    rows = [r for r in _read_raw()
            if r["year"] == "2006-2007" and r["month"] == "Jan"
            and r["state"] == "ANDHRA PRADESH" and r["group"] == "Agriculture"
            and r["occupation"] == "Ploughing"]
    assert rows, "AP Jan 2006-2007 Ploughing row missing from raw"
    assert float(rows[0]["male"]) == 79.90


@requires_raw
def test_raw_all_india_rows_present():
    assert any(r["state"] == "All India" for r in _read_raw())


@requires_raw
def test_real_annualization_ap_ploughing_fy2006_07(tmp_path):
    raw_rows = [r for r in _read_raw()
                if r["year"] == "2006-2007" and r["state"] == "ANDHRA PRADESH"
                and r["group"] == "Agriculture" and r["occupation"] == "Ploughing"]
    male = _raw_floats(raw_rows, "male")
    assert len(male) == 12

    rows = parse_wages.parse(RAW, tmp_path / "wage_annual.csv")
    row = _by_key(rows)[("2006-07", "ANDHRA PRADESH", "Agriculture", "Ploughing")]
    assert row["n_months"] == "12"
    assert row["source_flag"] == ""
    assert float(row["inr_day"]) == pytest.approx(sum(male) / len(male), abs=0.005)

    # whole-file reconciliation: no male-numeric month lost in annualization
    numeric_male = sum(1 for r in _read_raw() if _is_numeric(r["male"]))
    assert sum(int(r["n_months"]) for r in rows) == numeric_male
    # unique-key count is ~9.5k, far below a naive 97310/12 guess: the raw file
    # repeats ~450 state×occupation rows within each FY's monthly blocks
    assert 5_000 < len(rows) < 20_000
    fy_re = re.compile(r"\d{4}-\d{2}")
    assert all(fy_re.fullmatch(r["fy"]) for r in rows)
    assert any(r["state"] == "All India" for r in rows)


@requires_raw
def test_raw_anchor_ap_jan_2023_24_ploughing_tilling():
    """CONTRACT §Verification anchors — restored during parent reconciliation.
    The original author's search missed it because the occupation label ends
    with ' workers'; row verified present in raw on 2026-11-21."""
    rows = [r for r in _read_raw()
            if r["year"] == "2023-2024" and r["month"] == "Jan"
            and r["state"] == "ANDHRA PRADESH" and r["group"] == "Agriculture"
            and r["occupation"] == "Ploughing/Tilling workers"]
    assert rows, "AP Jan 2023-24 Ploughing/Tilling workers row missing from raw"
    assert float(rows[0]["male"]) == 593.38
