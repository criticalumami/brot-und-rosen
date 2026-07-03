# Brot und Rosen

Lebanon real estate price index — scraped daily from Dubizzle (OLX Lebanon).

**Live map →** https://YOUR_USERNAME.github.io/brot-und-rosen/

## What it does

- Scrapes apartment listings across all Lebanon every day at 09:00 Beirut time
- Aggregates mean price per SQM by zone
- Renders an interactive choropleth map with two levels of granularity:
  - **Beirut city** — 13 official ADM3 cadasters (Achrafieh, Ras Beyrouth, etc.)
  - **Rest of Lebanon** — 25 ADM2 districts (El Meten, Tripoli, Zahle, etc.)
- Attribute table with every listing URL, neighborhood, price, and size

## Outputs (auto-committed daily)

| File | Description |
|---|---|
| `index.html` / `real_estate_map.html` | Interactive choropleth + attribute table |
| `listings.csv` | Raw listings with URLs, neighborhood, price, SQM |
| `real_estate_means.csv` | Per-zone averages |

## Data sources

- **Dubizzle / OLX Lebanon** — live scraping (25 pages / ~1,125 listings per run)
- **Facebook Marketplace** — simulated (blocks bots)
- **Boundaries** — OCHA/UNHCR Lebanon Administrative Boundaries (ADM2 + ADM3)

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python gemini-code-1783084154926.py
open real_estate_map.html
```

## Design

Swiss International Style — monochromatic, Space Grotesk typeface,
uppercase labels, 1px borders, grayscale choropleth.
