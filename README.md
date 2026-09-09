# STYLE Buyer Command Center

Streamlit app for ranking the strongest potential natural-stone importers/distributors across 10 markets.

## Main capabilities
- Serper web discovery
- Public website email / phone / WhatsApp extraction
- Apollo People Search for procurement / purchasing / sourcing / import decision makers
- Optional Apollo email enrichment with a user-controlled credit limit
- Buyer opportunity scoring
- Top 50 ranking
- CSV / Excel export

## Streamlit Secrets

Add these in Streamlit Community Cloud → App Settings → Secrets:

```toml
SERPER_API_KEY = "YOUR_SERPER_KEY"
APOLLO_API_KEY = "YOUR_APOLLO_KEY"
```

Never commit real API keys to GitHub.

## Deploy
- Repository: `mohamedabdelshafy4413-coder/style-global-sales`
- Branch: `main`
- Main file path: `app.py`

## Important
This app ranks research/sales opportunity. It does not prove actual historical import volume unless a shipment/import database is connected.
