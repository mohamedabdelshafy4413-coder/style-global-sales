# TOP GOLDEN 500

**AI B2B Export Sales Intelligence Engine for STYLE Marble & Granite**

Main Streamlit file:

`top_golden_500/app.py`

## Core workflow

Upload client files → normalize data → rank buyer strength → estimate reachability / reply speed / buying intent / customer probability → generate personalized English sales emails → export the strongest contacts.

## Supported input files

- Excel (.xlsx / .xls / .xlsm)
- CSV
- Word (.docx)
- Text-based PDF

## Target markets

Saudi Arabia, United Arab Emirates, Morocco, United Kingdom, United States, France, Germany, Italy, Spain and Canada.

## Core STYLE materials

- Galala Light
- Sunny Light
- Meli Brown
- Meli Grey
- Zafarana Flower

## Buyer filters

- Importer
- Distributor
- Wholesaler
- Stone Fabricator
- Architectural Supplier
- Contractor
- Developer
- Tile & Stone Showroom
- Hotel Supplier

## Ranking dimensions

- Company Strength
- Decision Access
- Email Quality
- STYLE Fit
- Market Fit
- Reachability
- Reply Speed
- Buying Intent
- Customer Probability

## Personalized outreach

The app creates for each ranked contact:

- First-touch subject line
- Personalized English sales email
- Follow-up 1
- Follow-up 2
- Country-specific commercial angle

## Optional Apollo enrichment

If `APOLLO_API_KEY` is available in Streamlit Secrets, the app can try to find a relevant decision-maker for high-priority records missing a contact name or job title.

## Streamlit Secrets

```toml
APOLLO_API_KEY = "YOUR_APOLLO_KEY"
SERPER_API_KEY = "YOUR_SERPER_KEY"
```

Never commit live keys to GitHub.

## Deploy

Repository:

`mohamedabdelshafy4413-coder/style-global-sales`

Branch:

`main`

Main file path:

`top_golden_500/app.py`

Suggested app URL:

`top-golden-500`

## Important scoring note

The probability, reply-speed and buying-intent values are prioritization scores based on the information available in the uploaded file. They are not guarantees of replies, purchases, revenue or profit. Verified shipment/import data is required for a historical purchase-volume ranking.
