"""Smoke tests for the automated quarterly-refresh mechanism (pipeline/refresh.py).

Brief coverage: the dry-run plan lists all 5 automatable sources + the Goldhub
skip note; .gitignore pins the two Goldhub-derived interims; refresh.yml parses
as YAML and carries the quarterly cron + workflow_dispatch.
"""
import os
import re
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # same bootstrap as pipeline/refresh.py (PYTHONSAFEPATH machines)

from pipeline import refresh  # noqa: E402


def test_dry_run_plan_lists_all_source_steps():
    plan = refresh.build_plan("dry-run")
    text = refresh.render_plan(plan, "dry-run")
    for needle in ("FRED", "LBMA", "CACP", "WRRI", "RBI"):  # the 5 automatable sources
        assert needle in text
    assert "T35" in text and "T133" in text and "T164" in text  # both Handbook tables planned
    assert {s["id"] for s in plan} == {"S05", "S09", "S08", "S06", "S01", "S04", "S02", "S03"}


def test_dry_run_plan_has_explicit_goldhub_skip():
    plan = {s["id"]: s for s in refresh.build_plan("dry-run")}
    goldhub = plan["S03"]
    assert goldhub["action"] == "skip"
    assert "login-gated" in goldhub["note"]
    assert "annual spine unaffected" in goldhub["note"]


def test_gitignore_pins_goldhub_derived_interims():
    with open(os.path.join(ROOT, ".gitignore"), encoding="utf-8") as f:
        text = f.read()
    assert "!data/interim/gold_usd_monthly.csv" in text
    assert "!data/interim/gold_inr_domestic_monthly.csv" in text


def test_refresh_workflow_parses_with_cron_and_dispatch():
    with open(os.path.join(ROOT, ".github", "workflows", "refresh.yml"), encoding="utf-8") as f:
        text = f.read()
    assert re.search(r"cron:\s*['\"]0 6 1 \* \*['\"]", text)
    assert "workflow_dispatch" in text
    assert "jobs:" in text and "steps:" in text
    try:
        import yaml
    except ImportError:
        pytest.skip("PyYAML not installed — cron/dispatch/structure asserted textually above")
    cfg = yaml.safe_load(text)
    triggers = cfg.get("on") if isinstance(cfg.get("on"), dict) else cfg.get(True)
    assert isinstance(triggers, dict)
    assert triggers["schedule"][0]["cron"] == "0 6 1 * *"
    assert "workflow_dispatch" in triggers


def test_pinned_goldhub_provenance_date_readable():
    pinned = refresh.pinned_goldhub_date()
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", pinned) or pinned == "unknown"
