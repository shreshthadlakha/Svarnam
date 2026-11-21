"""Parse the CACP MSP table (S08) into data/interim/msp_annual.csv.

The CACP page https://cacp.da.gov.in/Home/MSP shows the "Minimum Support /
Fair & Remunerative Prices ... (Crop Year)" table (INR/quintal, updated
30.09.2026), but it is rendered client-side: the page HTML is a JS shell
(footnotes only) that does `fetch('/json.json')` and builds the rows from
{seasonname, commodityname, financialyear, reco_price, fixed_price}.
data/raw/msp/msp_table.html is therefore that /json.json response
(HTTP 200, 2026-11-21) — the exact rows the published table is built from.

`financialyear` int N maps to the published crop-year label 'N-(N+1)'
('2025-26'), verified against the published table: Wheat fy=2025 ->
'2025-26' = 2585, Tur (Arhar) fy=2026 -> '2026-27' = 8450.

Value = the FIXED column; when the Fixed cell is empty/'-' the Recommended
value is used with source_flag='recommended-only'; rows with no numeric
cell ('-' or empty) are skipped, so placeholder-only future crop years
(e.g. 2027-28) do not appear in the output.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "msp" / "msp_table.html"
OUT_PATH = ROOT / "data" / "interim" / "msp_annual.csv"

#: Crops kept, named exactly as in the published CACP table.
CROPS: tuple[str, ...] = ("Paddy Common", "Paddy(F)/Grade A", "Tur (Arhar)", "Wheat")

SERIES = "msp_annual"
NOTES = (
    "FIXED column of CACP 'Minimum Support / Fair & Remunerative Prices "
    "(Crop Year)' table in INR/quintal; Recommended fallback flagged "
    "recommended-only; '-' or empty cells skipped; "
    "crop-year as published by CACP; rabi marketing year = crop year + 1 (wheat)"
)


def crop_year_label(financial_year: int) -> str:
    """CACP `financialyear` int -> published crop-year label ('2025-26')."""
    return f"{financial_year}-{(financial_year + 1) % 100:02d}"


def _cell_value(text: object) -> int | None:
    """Numeric price from a table cell; '-' / '' / None -> None."""
    cleaned = str(text).replace(",", "").strip()
    if cleaned in ("", "-"):
        return None
    return int(float(cleaned))


def parse_msp(raw: str) -> list[dict[str, object]]:
    """Parse the saved CACP table artifact into contract rows."""
    records = json.loads(raw)
    if not isinstance(records, list):
        raise ValueError("expected a JSON array of MSP rows")
    rows: dict[tuple[str, str], dict[str, object]] = {}
    for item in records:
        crop = str(item["commodityname"]).strip()
        if crop not in CROPS:
            continue
        label = crop_year_label(int(str(item["financialyear"]).strip()))
        fixed = _cell_value(item["fixed_price"])
        reco = _cell_value(item["reco_price"])
        value, flag = (fixed, "") if fixed is not None else (reco, "recommended-only")
        if value is None:
            continue  # published table shows only '-' placeholders for this year
        row = {"crop": crop, "crop_year": label, "inr_quintal": value, "source_flag": flag}
        key = (crop, label)
        if key in rows and rows[key] != row:
            raise ValueError(f"conflicting duplicate MSP row for {key}: {rows[key]} vs {row}")
        rows[key] = row
    order = {crop: i for i, crop in enumerate(CROPS)}
    return sorted(rows.values(), key=lambda r: (order[str(r["crop"])], str(r["crop_year"])))


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    """Write the interim CSV with the provenance header required by CONTRACT.md."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(f"# series: {SERIES}\n")
        fh.write("# source: S08 CACP MSP (accessed 2026-11-21)\n")
        fh.write(f"# notes: {NOTES}\n")
        writer = csv.DictWriter(fh, fieldnames=["crop", "crop_year", "inr_quintal", "source_flag"])
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    desc = "Parse the CACP MSP table artifact into data/interim/msp_annual.csv"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--raw", type=Path, default=RAW_PATH, help="saved CACP table artifact")
    parser.add_argument("--out", type=Path, default=OUT_PATH, help="interim CSV destination")
    args = parser.parse_args(argv)
    rows = parse_msp(args.raw.read_text(encoding="utf-8"))
    write_csv(rows, args.out)
    print(f"{len(rows)} rows -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
