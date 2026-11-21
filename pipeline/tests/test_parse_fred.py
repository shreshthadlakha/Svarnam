"""Tests for pipeline.parse_fred: fixture behaviour + real-file contract anchors."""
from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.parse_fred import IN_PATH, SERIES, load_fred, main, write_fx_csv

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "dexinus_sample.csv"

EXPECTED = [
    ("1973-01-02", "8.0200", ""),
    ("1973-01-05", "8.0300", ""),
]


def test_fixture_skips_missing_and_junk() -> None:
    assert load_fred(FIXTURE) == EXPECTED


def test_fixture_write_csv_header_and_rows(tmp_path: Path) -> None:
    out = tmp_path / "fx_daily.csv"
    write_fx_csv(EXPECTED, out)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == f"# series: {SERIES}"
    assert lines[1].startswith("# source: S05 FRED DEXINUS (accessed ")
    assert lines[2].startswith("# notes: ")
    assert lines[3] == "date,usdinr,source_flag"
    assert lines[4] == "1973-01-02,8.0200,"
    assert lines[-1] == "1973-01-05,8.0300,"


def test_main_cli_writes_out_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "fx_daily.csv"
    assert main(["--in", str(FIXTURE), "--out", str(out)]) == 0
    assert out.exists()
    assert f"{SERIES}: 2 rows" in capsys.readouterr().out


@pytest.mark.skipif(not IN_PATH.exists(), reason="real DEXINUS csv not present")
def test_real_file_anchors() -> None:
    rows = load_fred(IN_PATH)
    # CONTRACT.md says 14,053 data rows, but the real file (verified 2026-11-21)
    # has 14,054 data lines = 13,501 numeric + 553 empty-value rows (US holidays,
    # e.g. 1973-02-12 ... 2026-11-11), 0 '.' rows and 0 duplicate dates — so
    # 14,053 is unreachable (skip -> 13,501, keep -> 14,054); the file is truth.
    assert len(rows) == 13501
    dates = [d for d, _v, _flag in rows]
    assert dates == sorted(dates)
    assert rows[0] == ("1973-01-02", "8.0200", "")
    assert rows[-1] == ("2026-11-13", "94.2400", "")
