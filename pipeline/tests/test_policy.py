"""Policy loader tests — calendar invariants + duty anchors (PRD A-invariants)."""
import datetime as dt
import os

import pytest

from pipeline import policy

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="module")
def calendar():
    return policy.load_duty_calendar()


def test_calendar_single_coverage(calendar):
    span, problems = policy.check_calendar(calendar)
    assert not problems, problems
    assert span > 13000  # 1968-09-01 → present


def test_duty_anchors(calendar):
    assert policy.row_for(calendar, dt.date(2013, 8, 13))["bcd"] == pytest.approx(0.10)
    assert policy.row_for(calendar, dt.date(2022, 6, 1))["bcd"] == pytest.approx(0.10)
    assert policy.row_for(calendar, dt.date(2022, 6, 1))["aidc"] == pytest.approx(0.05)
    row24 = policy.row_for(calendar, dt.date(2024, 8, 1))
    assert row24["bcd"] + (row24["aidc"] or 0) == pytest.approx(0.06)
    row26 = policy.row_for(calendar, dt.date(2026, 11, 21))
    assert row26["bcd"] + (row26["aidc"] or 0) == pytest.approx(0.15)
    assert row26["to"] is None  # open row


def test_prohibition_era(calendar):
    row = policy.row_for(calendar, dt.date(1985, 6, 1))
    assert row["type"] == "prohibition"


def test_gst_boundary(calendar):
    assert policy.row_for(calendar, dt.date(2017, 6, 30))["gst_rate"] == 0.0
    assert policy.row_for(calendar, dt.date(2017, 7, 1))["gst_rate"] == pytest.approx(0.03)


def test_breaks_and_episodes():
    breaks = policy.load_breaks()
    assert len(breaks) == 9
    assert breaks[0]["date"] == dt.date(1990, 6, 6)
    eps = policy.load_episodes()
    assert len(eps) == 15
    dec13 = next(e for e in eps if e["date"] == dt.date(2013, 12, 1))
    assert dec13["usd_per_oz"] == 160 and dec13["direction"] == "premium"


def test_exact_one_open_row(calendar):
    assert sum(1 for r in calendar if r["to"] is None) == 1
