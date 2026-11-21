"""parse_wages.py — S06 Labour Bureau WRRI monthly wage rates → FY annual means.

Reads ``data/wages/wrri_raw.csv`` (97,310 rows; columns year, month, state,
group, occupation, male, female; non-numeric cells are only '@'/'-') and
annualizes to ``data/interim/wage_annual.csv`` per ``pipeline/CONTRACT.md``:

- fy normalized '2006-2007' → '2006-07';
- one row per (fy, state, occupation_group, occupation);
- inr_day / inr_day_female = mean of NUMERIC month values only — '@', '-'
  and empty cells are skipped entirely, never imputed; a cell stays empty
  when its series has no numeric months (never zero);
- n_months counts the months contributing to inr_day (male series);
  source_flag = 'partial-year' when n_months < 12, else '';
- occupations kept exactly as published — old- and new-scheme labels are
  NOT merged across the Nov-2013 reclassification.

Stdlib csv only; pure reader (no network, no writes to data/raw/).
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "wages" / "wrri_raw.csv"
OUT_PATH = ROOT / "data" / "interim" / "wage_annual.csv"

SERIES = "WRRI"
COLUMNS = [
    "fy", "state", "occupation_group", "occupation", "series",
    "inr_day", "inr_day_female", "n_months", "source_flag",
]

PROVENANCE = [
    "# series: wage_annual",
    "# source: S06 Labour Bureau — Wage Rates in Rural India (WRRI), monthly database (accessed 2026-11-21)",
    "# notes: FY means over numeric monthly values only ('@'/'-'/empty skipped, no imputation);"
    " n_months = months with a numeric male value; source_flag=partial-year when n_months<12;"
    " occupations kept as published (old/new scheme NOT merged across the Nov-2013 reclassification);"
    " 2022-23 Jul-Dec absent upstream; 2013-14 partial (old-scheme-only months Jul-Oct)",
]


def normalize_fy(year: str) -> str:
    """'2006-2007' → '2006-07' (start year + last two digits of start+1)."""
    start = int(year[:4])
    return f"{start}-{(start + 1) % 100:02d}"


def _numeric(cell: str | None) -> float | None:
    """Wage value as float, or None for '@'/'-'/empty/unparseable cells."""
    if cell is None:
        return None
    text = cell.strip()
    if not text or text in {"@", "-"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse(raw_path: Path, out_path: Path) -> list[dict[str, str]]:
    """Annualize the WRRI raw CSV, write the interim CSV, return the rows."""
    acc: dict[tuple[str, str, str, str], dict[str, list[float]]] = {}
    with raw_path.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            fy = normalize_fy(row["year"])
            key = (fy, row["state"], row["group"], row["occupation"])
            bucket = acc.setdefault(key, {"male": [], "female": []})
            male, female = _numeric(row["male"]), _numeric(row["female"])
            if male is not None:
                bucket["male"].append(male)
            if female is not None:
                bucket["female"].append(female)

    rows: list[dict[str, str]] = []
    for (fy, state, group, occupation), values in sorted(acc.items()):
        male, female = values["male"], values["female"]
        rows.append({
            "fy": fy,
            "state": state,
            "occupation_group": group,
            "occupation": occupation,
            "series": SERIES,
            "inr_day": f"{sum(male) / len(male):.2f}" if male else "",
            "inr_day_female": f"{sum(female) / len(female):.2f}" if female else "",
            "n_months": str(len(male)),
            "source_flag": "partial-year" if len(male) < 12 else "",
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        for line in PROVENANCE:
            fh.write(line + "\n")
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> None:
    rows = parse(RAW_PATH, OUT_PATH)
    partial = sum(1 for row in rows if row["source_flag"] == "partial-year")
    print(f"wrote {OUT_PATH}: {len(rows)} annualized rows ({partial} partial-year)")


if __name__ == "__main__":
    main()
