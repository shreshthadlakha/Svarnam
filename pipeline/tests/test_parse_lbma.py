"""Tests for pipeline.parse_lbma: fixture behaviour + real-file contract anchors."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.parse_lbma import (
    LIVE_PATH,
    SERIES,
    WB_PATH,
    load_lbma,
    main,
    write_lbma_csv,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "lbma_fixtures.json"

EXPECTED = [
    ("2000-01-03", 283.0, "live"),  # live row wins the dedupe over wayback 282.5
    ("2000-01-04", 279.7, "wayback"),  # wayback-only date survives
    ("2000-01-05", 285.4, "live"),  # wayback USD null -> skipped, live row kept
    ("2000-01-07", 286.1, "live"),  # live-only date
]


def _materialize(tmp_path: Path) -> tuple[Path, Path]:
    """Write fixture arrays as raw-format JSON files the parser reads."""
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    wb = tmp_path / "gold_pm_wb_sample.json"
    live = tmp_path / "gold_pm_live_sample.json"
    wb.write_text(json.dumps(data["wayback"]), encoding="utf-8")
    live.write_text(json.dumps(data["live"]), encoding="utf-8")
    return wb, live


def test_fixture_merge_dedupe_sort_flags(tmp_path: Path) -> None:
    wb, live = _materialize(tmp_path)
    assert load_lbma(wb, live) == EXPECTED


def test_fixture_write_csv_header_and_rows(tmp_path: Path) -> None:
    out = tmp_path / "lbma_daily.csv"
    write_lbma_csv(EXPECTED, out)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == f"# series: {SERIES}"
    assert lines[1].startswith("# source: S09 LBMA Gold Price PM JSON (accessed ")
    assert lines[2].startswith("# notes: ")
    assert lines[3] == "date,usd_oz,source_flag"
    assert lines[4] == "2000-01-03,283.00,live"
    assert lines[-1] == "2000-01-07,286.10,live"


def test_main_cli_writes_out_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    wb, live = _materialize(tmp_path)
    out = tmp_path / "lbma_daily.csv"
    assert main(["--wb", str(wb), "--live", str(live), "--out", str(out)]) == 0
    assert out.exists()
    assert f"{SERIES}: 4 unique dates" in capsys.readouterr().out


@pytest.mark.skipif(
    not (WB_PATH.exists() and LIVE_PATH.exists()),
    reason="real LBMA JSON files not present",
)
def test_real_file_anchors() -> None:
    rows = load_lbma(WB_PATH, LIVE_PATH)
    assert len(rows) == 14691  # CONTRACT.md: merged total = 14,691 unique dates
    dates = [d for d, _usd, _flag in rows]
    assert dates == sorted(dates)
    assert len(set(dates)) == len(dates)
    assert {flag for _d, _usd, flag in rows} <= {"live", "wayback"}
    assert rows[0][0] == "1968-04-01"
    assert rows[0][1] == pytest.approx(37.70)
    assert rows[-1][0] == "2026-09-25"
    assert rows[-1][1] == pytest.approx(4261.05)
