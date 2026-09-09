# STYLE Golden 500 Buyer Intelligence OS

Streamlit sales-intelligence system for STYLE for Marble & Granite.

## What it does

### 1. Analyze files you upload
Upload CSV or Excel containing up to 500 companies/contacts. The app attempts to recognize fields such as:
- Company
- Website / domain
- Country
- Buyer type
- Email
- Phone / WhatsApp
- Decision maker
- Job title

It then enriches missing decision-maker data through Apollo when enabled, checks public company contact data, evaluates email quality, and ranks the strongest opportunities.

### 2. Search directly by market
Choose:
- Country / countries
- Buyer type
- STYLE materials
- Target number of buyers (50–500)
- Search depth
- Apollo enrichment budget

Serper discovers relevant companies and Apollo is used for decision-maker research and optional email enrichment.

### 3. Ranking dimensions
The app calculates research-based prioritization scores for:
- Company strength
- Import / distributor signal
- STYLE material fit
- Project signal
- Repeat-purchase potential
- Decision-maker access
- Contact quality
- Email quality
- Estimated fast-response likelihood
- Estimated customer probability

These are commercial prioritization estimates, not guarantees of reply, purchase, or revenue.

### 4. Email Intelligence
Emails are ranked using signals such as:
- Syntax
- Business vs free mailbox domain
- Match with company domain
- MX record availability
- Generic vs buying-role/personal mailbox
- Apollo status when available

### 5. Country-specific English outreach
The system creates a separate commercial angle for:
- Saudi Arabia
- United Arab Emirates
- Morocco
- United Kingdom
- United States
- France
- Germany
- Italy
- Spain
- Canada

Each selected buyer can receive:
- Subject
- First email
- Follow-up 1
- Follow-up 2
- LinkedIn message

The five core materials currently configured are:
- Galala Light
- Sunny Light
- Meli Brown
- Meli Grey
- Zafarana Flower

## Streamlit Secrets

Add the following in Streamlit Community Cloud → App Settings → Secrets:

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

The system prioritizes sales opportunities from available signals. A `Customer Probability` score is not a statistical guarantee. For ranking based on actual historical purchasing volume, connect verified shipment/import transaction data.
