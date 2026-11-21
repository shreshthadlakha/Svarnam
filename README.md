# Svarnam

What is ₹1.18 lakh / 10g of gold made of? Metal, dollar, tax, fear — decomposed,
FY1985-86 → today.

- Live tool: https://svarnam.vercel.app (deploy via Vercel — LAUNCH-KIT §4)
- [Data sources](site/sources.md) · [Download CSV](site/dataset.json) · [Methodology](docs/TECH-DESIGN.md)
- **Model, not advice** (see [DISCLAIMER.md](DISCLAIMER.md)) · no forecasts, no targets — by design
- Built from public data only: RBI Handbook, LBMA (via Wayback), WGC Goldhub, Labour Bureau, CACP, FRED
- Status: **v1 build complete** — pipeline + page + monthly auto-refresh (Vercel redeploys on every refresh commit); awaiting repo push · regime breaks annotated · provisional labels everywhere

## Layout

| Folder | What lives here |
|---|---|
| `docs/` | All documents: PRD, TECH-DESIGN, CODE-STRUCTURE, PLAN, LAUNCH-KIT, the master KT bundle, decision-trail transcript |
| `pipeline/` | The local build system (Python; never deployed): parsers → derive → validate → build |
| `site/` | The only deployed directory (GitHub Pages): renders exclusively from `dataset.json` |
| `data/` | Raw downloads (gitignored, checksummed), hand-curated policy CSVs (in git), build report |
| `research/` | The six verification-track evidence files (workspace-only) |

Build: `make build` · Test: `make test` · Serve locally: `make serve`
