"""Units — the ONLY place for constants (CODE-STRUCTURE.md §4)."""

TROY_OZ_GRAMS = 31.1034768
QUINTAL_KG = 100.0
GST_RATE = 0.03  # in-force value; calendar drives when it applies


def inr_oz_to_inr_10g(inr_per_oz: float) -> float:
    """₹/troy-oz → ₹/10 g."""
    return inr_per_oz / TROY_OZ_GRAMS * 10.0


def usd_oz_to_inr_10g(usd_per_oz: float, usdinr: float) -> float:
    """$/troy-oz × USD/INR → ₹/10 g (world price in rupees)."""
    return usd_per_oz / TROY_OZ_GRAMS * 10.0 * usdinr


def quintal_to_kg(inr_per_quintal: float) -> float:
    return inr_per_quintal / QUINTAL_KG


def fy_years(fy: str) -> tuple[int, int]:
    """'1985-86' → (1985, 1986); '1999-00' → (1999, 2000)."""
    a, b = fy.split("-")
    y1 = int(a)
    y2 = int(b) if len(b) == 4 else (y1 // 100) * 100 + int(b)
    if y2 <= y1 % 100:
        y2 = (y1 // 100) * 100 + int(b)
    if y2 < y1:
        y2 += 100
    return y1, y2


def fy_label(y1: int, y2: int) -> str:
    return "%d-%02d" % (y1, y2 % 100)


def fy_bounds(fy: str):
    """FY → (first_day, last_day) as datetime.date. Indian FY = 1 Apr – 31 Mar."""
    from datetime import date
    y1, y2 = fy_years(fy)
    return date(y1, 4, 1), date(y2, 3, 31)


def days_between(d1, d2) -> int:
    return (d2 - d1).days + 1
