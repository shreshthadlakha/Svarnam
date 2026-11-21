"""Source registry — every source id, name, URL, coverage, access date, license note.

RBI entries record edition + table number together (table numbers drift between
editions: gold was T38 in the 2024-25 edition, T35 in 2025-26).
"""

SOURCES = {
    "S01": {
        "name": "RBI Handbook of Statistics on the Indian Economy 2025-26, Table 35 — Average Price of Gold and Silver in Domestic and Foreign Markets",
        "url": "https://rbi.org.in/Scripts/AnnualPublications.aspx?head=Handbook%20of%20Statistics%20on%20Indian%20Economy",
        "file": "data/rbi/t35_gold_annual.xlsx",
        "coverage": "FY1985-86..FY2025-26 (annual)",
        "accessed": "2026-11-20",
        "license_note": "public-sector publication, reuse with attribution; cite edition + table number",
    },
    "S02": {
        "name": "RBI Handbook 2025-26, Table 164 — Monthly Average Price of Gold and Silver",
        "url": "https://rbi.org.in/Scripts/AnnualPublications.aspx?head=Handbook%20of%20Statistics%20on%20Indian%20Economy",
        "file": "data/rbi/t164_gold_monthly.xlsx",
        "coverage": "2022-04..2026-04 (monthly; history rotates out each edition)",
        "accessed": "2026-11-20",
        "license_note": "public-sector publication, reuse with attribution",
    },
    "S03": {
        "name": "WGC Goldhub — Gold price averages in a range of currencies since 1978 (monthly USD from 1978-01; INR column = Indian domestic price from 2005-10, byte-verified 2026-11-21 vs RBI T35 within ±0.06%)",
        "url": "https://www.gold.org/goldhub/data/gold-prices",
        "file": "data/rbi/goldhub_averages_since_1978.xlsx",
        "coverage": "USD monthly 1978-01..2026-10; INR (domestic) monthly 2005-10..2026-10",
        "accessed": "2026-11-21 (downloaded by owner; login-gated)",
        "license_note": "World Gold Council Goldhub terms; used with attribution; raw file not redistributed",
    },
    "S04": {
        "name": "RBI Handbook 2025-26, Table 133 — Exchange Rate of the Indian Rupee (FY annual average and end-year)",
        "url": "https://rbi.org.in/Scripts/AnnualPublications.aspx?head=Handbook%20of%20Statistics%20on%20Indian%20Economy",
        "file": "data/rbi/t133_fx_fy.xlsx",
        "coverage": "FY1986-87..FY2025-26",
        "accessed": "2026-11-20",
        "license_note": "public-sector publication; official-rate era documented in-table (official till 1991-92; FEDAI from 1992-93; RBI ref from 2012-05; FBIL from 2018-07)",
    },
    "S05": {
        "name": "FRED DEXINUS — Indian Rupees to U.S. Dollar Spot Exchange Rate (Fed H.10, NY noon buying rate)",
        "url": "https://fred.stlouisfed.org/series/DEXINUS",
        "file": "data/rbi/dexinus_daily.csv",
        "coverage": "1973-01-02..2026-11-13 (daily)",
        "accessed": "2026-11-21 (owner manual download; automated routes time out)",
        "license_note": "free use with attribution to FRED; market rate, not RBI official",
    },
    "S06": {
        "name": "Labour Bureau — Wage Rates in Rural India (WRRI), monthly database",
        "url": "https://www.labourbureau.gov.in/rural-wages",
        "file": "data/wages/wrri_raw.csv (extracted 2026-11-21 via data/wages/_wrri_extract.py)",
        "coverage": "2006-07..2023-24 monthly, 20 states + All-India (2022-23 Jul-Dec not yet published; 2013-14 partial)",
        "accessed": "2026-11-21",
        "license_note": "Government of India publication; attribution",
    },
    "S07": {
        "name": "DES, Dept of Agriculture & Farmers Welfare — Agricultural Wages in India (AWI) 2023-24 volume",
        "url": "https://desagri.gov.in/wp-content/uploads/2025/07/AWI-2023-24-for-printing-uploading-1.pdf",
        "file": "data/wages/AWI-2023-24.pdf",
        "coverage": "2023-24 volume (district-level series collected since 1950-51; 2-3 yr lag)",
        "accessed": "2026-11-21",
        "license_note": "Government of India publication; attribution",
    },
    "S08": {
        "name": "CACP — Minimum Support / F&RP prices (crop-year table) + Price Policy report archive",
        "url": "https://cacp.da.gov.in/Home/MSP",
        "file": "data/msp/ (archive PDFs 1982-83..2010-11 + born-digital reports; URL manifest _urls.csv)",
        "coverage": "clean table 2010-11..2027-28; archive compendiums 1982-83..2010-11 (1985-86 absent; rabi MY 2011-12 healable via archive)",
        "accessed": "2026-11-21",
        "license_note": "Government of India publication; attribution; pre-2004 PDFs are JBIG2 scans (OCR required)",
    },
    "S09": {
        "name": "LBMA Gold Price PM (USD) — daily; live endpoint Cloudflare-blocked, Wayback capture used",
        "url": "https://prices.lbma.org.uk/json/gold_pm.json (via web.archive.org/web/20260928143415id_)",
        "file": "data/rbi/gold_pm_wb.json (history) + gold_pm_live.json (capture to 2026-09-25)",
        "coverage": "1968-04-01..2026-09-25 (daily)",
        "accessed": "2026-11-21",
        "license_note": "deep history carries ICE Benchmark Administration terms — project displays derived model outputs, not the raw licensed feed",
    },
    "S10": {
        "name": "Gold (Control) Act repeal + customs notification history (referencer.in compilation)",
        "url": "https://www.referencer.in/Baggage_Rules/Articles_View.aspx?ArticleID=51536",
        "file": "data/policy/duty_calendar.csv (rows sourced per dive_05 §13)",
        "coverage": "1990-06-06→ notification-by-notification",
        "accessed": "2026-11-20",
        "license_note": "specialist compilation of CBIC notifications; primary notifications cited therein",
    },
    "S11": {
        "name": "GST 3% on gold value from 2017-07-01 (3% IGST at import on duty-paid value; 5% making charges)",
        "url": "https://www.legal500.com/intelligence/india/tax/gst-on-gold-18-22-24-carat-jewellery-rates-&-ornaments",
        "file": "data/policy/duty_calendar.csv (gst_rate column)",
        "coverage": "2017-07-01→",
        "accessed": "2026-11-20",
        "license_note": "rate sourced from WGC/legal summaries of CBIC notifications",
    },
    "S12": {
        "name": "May 2026 duty re-hike to 15% (BCD 10% + AIDC 5%), effective 2026-05-13",
        "url": "https://www.reuters.com/world/india/india-raises-import-tariffs-gold-silver-government-order-says-2026-05-12",
        "file": "data/policy/duty_calendar.csv (2026-05-13 row)",
        "coverage": "2026-05-13→",
        "accessed": "2026-11-20",
        "license_note": "Reuters reporting of the government order; notification detail via a2ztaxcorp (S-note)",
    },
    "S13": {
        "name": "Reuters 'Asia Gold' premium/discount episodes (dealer quotes vs official landed prices)",
        "url": "https://www.reuters.com/world/china/asia-gold-india-gold-discounts-hit-seven-week-high-demand-weakens-china-buying-2026-07-24",
        "file": "data/policy/episodes.csv",
        "coverage": "documented episodes 2013-12→2026-07 (dated list in dive_05 §9)",
        "accessed": "2026-11-20",
        "license_note": "press reporting; episode magnitudes quoted with dates, not reproduced as a feed",
    },
    "S14": {
        "name": "WGC duty analyses (Feb 2021 cut to 10.75% effective; Jul 2024 cut to 6%)",
        "url": "https://www.gold.org/goldhub/gold-focus/2024/07/indian-gold-import-duties-reduced-lowest-level-over-decade",
        "file": "data/policy/duty_calendar.csv (2021/2022/2024 rows)",
        "coverage": "2019→2024 duty structure",
        "accessed": "2026-11-20",
        "license_note": "WGC analysis quoting MoF/CBIC; attribution",
    },
    "S15": {
        "name": "Sovereign Gold Bonds arc (launch 2015-11-05 ₹2,684/g; last tranche 2024-02-21; discontinued confirmed 2025-02-01)",
        "url": "https://www.moneycontrol.com/news/business/sovereign-gold-bond-scheme-likely-to-be-discontinued-in-2025-26-report-12885706.html",
        "file": "site copy (SGB context card, PRD FR12)",
        "coverage": "2015-11-05→2025-02-01",
        "accessed": "2026-11-20",
        "license_note": "PIB/RBI notifications as reported by Moneycontrol/Wikipedia",
    },
}


def get(sid: str) -> dict:
    return SOURCES[sid]


def render_sources_md() -> str:
    lines = ["# Sources", "", "Every series on this page resolves to one of these ids. "
             "Access dates are the dates files were fetched and verified.", ""]
    for sid in sorted(SOURCES):
        s = SOURCES[sid]
        lines.append("## %s — %s" % (sid, s["name"]))
        lines.append("- URL: %s" % s["url"])
        lines.append("- Local file: `%s`" % s["file"])
        lines.append("- Coverage: %s" % s["coverage"])
        lines.append("- Accessed: %s" % s["accessed"])
        lines.append("- License: %s" % s["license_note"])
        lines.append("")
    return "\n".join(lines)
