# Sources

Every series on this page resolves to one of these ids. Access dates are the dates files were fetched and verified.

## S01 — RBI Handbook of Statistics on the Indian Economy 2025-26, Table 35 — Average Price of Gold and Silver in Domestic and Foreign Markets
- URL: https://rbi.org.in/Scripts/AnnualPublications.aspx?head=Handbook%20of%20Statistics%20on%20Indian%20Economy
- Local file: `data/rbi/t35_gold_annual.xlsx`
- Coverage: FY1985-86..FY2025-26 (annual)
- Accessed: 2026-11-20
- License: public-sector publication, reuse with attribution; cite edition + table number

## S02 — RBI Handbook 2025-26, Table 164 — Monthly Average Price of Gold and Silver
- URL: https://rbi.org.in/Scripts/AnnualPublications.aspx?head=Handbook%20of%20Statistics%20on%20Indian%20Economy
- Local file: `data/rbi/t164_gold_monthly.xlsx`
- Coverage: 2022-04..2026-04 (monthly; history rotates out each edition)
- Accessed: 2026-11-20
- License: public-sector publication, reuse with attribution

## S03 — WGC Goldhub — Gold price averages in a range of currencies since 1978 (monthly USD from 1978-01; INR column = Indian domestic price from 2005-10, byte-verified 2026-11-21 vs RBI T35 within ±0.06%)
- URL: https://www.gold.org/goldhub/data/gold-prices
- Local file: `data/rbi/goldhub_averages_since_1978.xlsx`
- Coverage: USD monthly 1978-01..2026-10; INR (domestic) monthly 2005-10..2026-10
- Accessed: 2026-11-21 (downloaded by owner; login-gated)
- License: World Gold Council Goldhub terms; used with attribution; raw file not redistributed

## S04 — RBI Handbook 2025-26, Table 133 — Exchange Rate of the Indian Rupee (FY annual average and end-year)
- URL: https://rbi.org.in/Scripts/AnnualPublications.aspx?head=Handbook%20of%20Statistics%20on%20Indian%20Economy
- Local file: `data/rbi/t133_fx_fy.xlsx`
- Coverage: FY1986-87..FY2025-26
- Accessed: 2026-11-20
- License: public-sector publication; official-rate era documented in-table (official till 1991-92; FEDAI from 1992-93; RBI ref from 2012-05; FBIL from 2018-07)

## S05 — FRED DEXINUS — Indian Rupees to U.S. Dollar Spot Exchange Rate (Fed H.10, NY noon buying rate)
- URL: https://fred.stlouisfed.org/series/DEXINUS
- Local file: `data/rbi/dexinus_daily.csv`
- Coverage: 1973-01-02..2026-11-13 (daily)
- Accessed: 2026-11-21 (owner manual download; automated routes time out)
- License: free use with attribution to FRED; market rate, not RBI official

## S06 — Labour Bureau — Wage Rates in Rural India (WRRI), monthly database
- URL: https://www.labourbureau.gov.in/rural-wages
- Local file: `data/wages/wrri_raw.csv (extracted 2026-11-21 via data/wages/_wrri_extract.py)`
- Coverage: 2006-07..2023-24 monthly, 20 states + All-India (2022-23 Jul-Dec not yet published; 2013-14 partial)
- Accessed: 2026-11-21
- License: Government of India publication; attribution

## S07 — DES, Dept of Agriculture & Farmers Welfare — Agricultural Wages in India (AWI) 2023-24 volume
- URL: https://desagri.gov.in/wp-content/uploads/2025/07/AWI-2023-24-for-printing-uploading-1.pdf
- Local file: `data/wages/AWI-2023-24.pdf`
- Coverage: 2023-24 volume (district-level series collected since 1950-51; 2-3 yr lag)
- Accessed: 2026-11-21
- License: Government of India publication; attribution

## S08 — CACP — Minimum Support / F&RP prices (crop-year table) + Price Policy report archive
- URL: https://cacp.da.gov.in/Home/MSP
- Local file: `data/msp/ (archive PDFs 1982-83..2010-11 + born-digital reports; URL manifest _urls.csv)`
- Coverage: clean table 2010-11..2027-28; archive compendiums 1982-83..2010-11 (1985-86 absent; rabi MY 2011-12 healable via archive)
- Accessed: 2026-11-21
- License: Government of India publication; attribution; pre-2004 PDFs are JBIG2 scans (OCR required)

## S09 — LBMA Gold Price PM (USD) — daily; live endpoint Cloudflare-blocked, Wayback capture used
- URL: https://prices.lbma.org.uk/json/gold_pm.json (via web.archive.org/web/20260928143415id_)
- Local file: `data/rbi/gold_pm_wb.json (history) + gold_pm_live.json (capture to 2026-09-25)`
- Coverage: 1968-04-01..2026-09-25 (daily)
- Accessed: 2026-11-21
- License: deep history carries ICE Benchmark Administration terms — project displays derived model outputs, not the raw licensed feed

## S10 — Gold (Control) Act repeal + customs notification history (referencer.in compilation)
- URL: https://www.referencer.in/Baggage_Rules/Articles_View.aspx?ArticleID=51536
- Local file: `data/policy/duty_calendar.csv (rows sourced per dive_05 §13)`
- Coverage: 1990-06-06→ notification-by-notification
- Accessed: 2026-11-20
- License: specialist compilation of CBIC notifications; primary notifications cited therein

## S11 — GST 3% on gold value from 2017-07-01 (3% IGST at import on duty-paid value; 5% making charges)
- URL: https://www.legal500.com/intelligence/india/tax/gst-on-gold-18-22-24-carat-jewellery-rates-&-ornaments
- Local file: `data/policy/duty_calendar.csv (gst_rate column)`
- Coverage: 2017-07-01→
- Accessed: 2026-11-20
- License: rate sourced from WGC/legal summaries of CBIC notifications

## S12 — May 2026 duty re-hike to 15% (BCD 10% + AIDC 5%), effective 2026-05-13
- URL: https://www.reuters.com/world/india/india-raises-import-tariffs-gold-silver-government-order-says-2026-05-12
- Local file: `data/policy/duty_calendar.csv (2026-05-13 row)`
- Coverage: 2026-05-13→
- Accessed: 2026-11-20
- License: Reuters reporting of the government order; notification detail via a2ztaxcorp (S-note)

## S13 — Reuters 'Asia Gold' premium/discount episodes (dealer quotes vs official landed prices)
- URL: https://www.reuters.com/world/china/asia-gold-india-gold-discounts-hit-seven-week-high-demand-weakens-china-buying-2026-07-24
- Local file: `data/policy/episodes.csv`
- Coverage: documented premium/discount episodes 2013-12→2026-07 (Reuters 'Asia Gold' dated list; magnitudes quoted, not a feed)
- Accessed: 2026-11-20
- License: press reporting; episode magnitudes quoted with dates, not reproduced as a feed

## S14 — WGC duty analyses (Feb 2021 cut to 10.75% effective; Jul 2024 cut to 6%)
- URL: https://www.gold.org/goldhub/gold-focus/2024/07/indian-gold-import-duties-reduced-lowest-level-over-decade
- Local file: `data/policy/duty_calendar.csv (2021/2022/2024 rows)`
- Coverage: 2019→2024 duty structure
- Accessed: 2026-11-20
- License: WGC analysis quoting MoF/CBIC; attribution

## S15 — Sovereign Gold Bonds arc (launch 2015-11-05 ₹2,684/g; last tranche 2024-02-21; discontinued confirmed 2025-02-01)
- URL: https://www.moneycontrol.com/news/business/sovereign-gold-bond-scheme-likely-to-be-discontinued-in-2025-26-report-12885706.html
- Local file: `site copy (SGB context card, PRD FR12)`
- Coverage: 2015-11-05→2025-02-01
- Accessed: 2026-11-20
- License: PIB/RBI notifications as reported by Moneycontrol/Wikipedia
