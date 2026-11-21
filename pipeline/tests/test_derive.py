"""Derive tests — the machine-verified FY2025-26 worked example + era behaviour."""
import datetime as dt
import os

import pytest

from pipeline import derive, policy, units

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="module")
def calendar():
    return policy.load_duty_calendar()


def test_fy_bounds():
    d1, d2 = units.fy_bounds("1985-86")
    assert (d1, d2) == (dt.date(1985, 4, 1), dt.date(1986, 3, 31))
    d1, d2 = units.fy_bounds("1999-00")
    assert (d1, d2) == (dt.date(1999, 4, 1), dt.date(2000, 3, 31))


def test_worked_example_fy2025_26(calendar):
    """TECH-DESIGN §4.1, machine-verified 2026-11-21. London 3937.86, FX 88.3071, duty 6%, GST 3%."""
    legs = derive.period_legs(
        units.usd_oz_to_inr_10g(3937.86, 88.3071),
        dt.date(2025, 4, 1), dt.date(2026, 3, 31), calendar)
    assert legs["metal_fx_leg"] == pytest.approx(111801.33, abs=0.02)
    assert legs["duty_leg"] == pytest.approx(6708.08, abs=0.02)
    assert legs["gst_leg"] == pytest.approx(3555.28, abs=0.02)
    assert legs["landed_cost"] == pytest.approx(122064.69, abs=0.05)


def test_specific_era_partial_fy(calendar):
    """FY1990-91: prohibition until 1990-06-05, then ₹250/10g specific → day-weighted."""
    legs = derive.period_legs(0.0, dt.date(1990, 4, 1), dt.date(1991, 3, 31), calendar)
    # 66 days at 0 (Apr 1 - Jun 5), 299 days at 250 → mean = 250*299/365 ≈ 204.66
    assert legs["duty_leg"] == pytest.approx(250 * 299 / 365, abs=0.5)


def test_gst_transition_fy2017_18(calendar):
    """FY2017-18: GST 0 for Apr-Jun, 3% after Jul 1 — day-weighted, not step."""
    metal = 30000.0
    legs = derive.period_legs(metal, dt.date(2017, 4, 1), dt.date(2018, 3, 31), calendar)
    # duty era is flat 10% here → duty = 3000; gst ≈ 0.03*(33000)*273/365 ≈ 7412
    assert legs["duty_leg"] == pytest.approx(3000.0, abs=1.0)
    assert legs["gst_leg"] == pytest.approx(0.03 * 33000 * 273 / 365, abs=5.0)


def test_swat_specific_vs_advalorem(calendar):
    """FY2019-20 duty = 13.75% effective (BCD 12.5 + SWS 1.25), day-weighted full FY."""
    metal = 40000.0
    legs = derive.period_legs(metal, dt.date(2019, 4, 1), dt.date(2020, 3, 31), calendar)
    # Apr 1–Jul 5: 10% row (96 days); Jul 6–Mar 31: 13.75% (269 days)
    expect = (0.10 * 96 + 0.1375 * 269) / 365 * metal
    assert legs["duty_leg"] == pytest.approx(expect, abs=2.0)


def test_ratio_math():
    mumbai = 118420.90
    wage = 400.0
    grams = wage / (mumbai / 10.0)
    assert grams == pytest.approx(0.033777, abs=1e-5)
    msp_kg = 2585.0 / 100.0
    assert msp_kg / (mumbai / 10.0) == pytest.approx(0.002183, abs=1e-6)
