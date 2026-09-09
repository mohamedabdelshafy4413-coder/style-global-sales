from __future__ import annotations

import re

PRODUCTS = {
    "Galala Light": "a refined Egyptian beige marble with broad commercial and project versatility",
    "Sunny Light": "a warm Egyptian marble suited to high-volume residential and hospitality applications",
    "Meli Brown": "a distinctive brown natural stone option for richer, premium interior palettes",
    "Meli Grey": "a contemporary grey Egyptian stone suited to modern architectural schemes",
    "Zafarana Flower": "a characterful Egyptian marble with strong visual identity for feature-led projects",
}

COUNTRY_ANGLES = {
    "Saudi Arabia": {
        "hook": "large-scale residential, hospitality and mixed-use developments",
        "proof": "consistent project supply, flexible formats and reliable export coordination",
        "cta": "Would a current slab/tile selection and project quotation be useful for one of your active requirements?",
    },
    "United Arab Emirates": {
        "hook": "premium hospitality, luxury residential and fast-moving fit-out projects",
        "proof": "project-ready Egyptian stone, finish flexibility and export support built for demanding timelines",
        "cta": "If you have an active marble package, I can send a focused selection and commercial offer for immediate review.",
    },
    "United States": {
        "hook": "distributors and fabricators looking for differentiated natural-stone programs with dependable supply",
        "proof": "direct Egyptian sourcing, multiple finishes and formats, and a clear path from sample to repeat orders",
        "cta": "Would you like a distributor/fabricator offer with the five strongest STYLE materials and indicative export terms?",
    },
    "Germany": {
        "hook": "buyers who prioritize consistency, specification clarity and reliable long-term supply",
        "proof": "structured inspection, documented product specifications and repeatable processing options",
        "cta": "May I send the technical selection and a supply proposal tailored to your current stone portfolio?",
    },
    "United Kingdom": {
        "hook": "stone distributors, fabricators and project suppliers balancing design quality with commercial reliability",
        "proof": "select Egyptian materials, multiple finishes and practical support for project and stock requirements",
        "cta": "Would it make sense to compare our five core materials against your current sourcing program?",
    },
    "France": {
        "hook": "design-led residential, hospitality and architectural stone requirements",
        "proof": "distinct Egyptian materials, refined finishes and flexible project sizing",
        "cta": "Can I send a concise material board and quotation for the finishes most relevant to your market?",
    },
    "Italy": {
        "hook": "stone professionals seeking distinctive Egyptian materials for fabrication, distribution and design projects",
        "proof": "quarry-origin material choice, processing flexibility and export coordination",
        "cta": "Would you be open to reviewing a five-material Egyptian stone selection for your current sourcing needs?",
    },
    "Spain": {
        "hook": "distributors and project suppliers seeking competitive natural-stone options for residential and hospitality work",
        "proof": "versatile Egyptian marble choices, flexible formats and commercially practical export supply",
        "cta": "Shall I send the most relevant sizes, finishes and commercial proposal for your buyer profile?",
    },
    "Canada": {
        "hook": "distributors and fabricators seeking dependable stone programs with distinctive natural materials",
        "proof": "direct Egyptian sourcing, flexible processing and a repeat-supply approach",
        "cta": "Would you like a shortlist and quotation structured for distribution or fabrication requirements?",
    },
    "Morocco": {
        "hook": "distributors, contractors and project suppliers looking for strong-value natural stone with dependable regional supply",
        "proof": "Egyptian marble options that can serve both stock and project requirements with flexible processing",
        "cta": "Can I send a focused offer for the five materials best suited to your current stock or project needs?",
    },
}


def _first_name(contact_name: str) -> str:
    name = re.sub(r"\s+", " ", (contact_name or "").strip())
    return name.split(" ")[0] if name else ""


def build_email(row: dict, selected_products: list[str] | None = None) -> dict:
    country = row.get("country") or ""
    angle = COUNTRY_ANGLES.get(country, {
        "hook": "natural-stone distribution and project supply",
        "proof": "direct Egyptian sourcing, flexible processing and reliable export support",
        "cta": "Would a focused material selection and commercial proposal be useful for your current sourcing needs?",
    })
    company = row.get("company") or "your company"
    fn = _first_name(row.get("contact_name", ""))
    salutation = f"Dear {fn}," if fn else "Hello,"
    products = selected_products or list(PRODUCTS.keys())
    product_line = ", ".join(products[:5])

    subject = f"{company}: Egyptian stone supply opportunity | STYLE"
    body = f"""{salutation}

I’m reaching out because {company} appears relevant to {angle['hook']}.

STYLE is an Egyptian natural-stone supplier focused on dependable B2B export supply. For your market, I believe the strongest starting selection is:

{product_line}

The commercial value is straightforward: {angle['proof']}. Rather than sending a generic catalogue, we can prepare a focused package around the sizes, finishes and volume that make sense for your business.

{angle['cta']}

If you share the material, finish, size and approximate quantity you are currently sourcing, I’ll reply with a targeted offer.

Best regards,
STYLE Marble & Granite
styleformarble.com
"""

    followup_1 = f"""Hi {fn or 'there'},

Following up on the Egyptian stone selection I sent for {company}. If you have an active requirement, send me the material / finish / size / quantity and I’ll prepare a focused offer rather than a broad catalogue.

Best regards,
STYLE Marble & Granite
"""

    followup_2 = f"""Hi {fn or 'there'},

One last note from my side. We are prioritizing a small number of serious B2B partners in {country or 'your market'} for our core Egyptian materials. If stone sourcing is relevant this quarter, I’d be glad to send the most commercially suitable options and quotation for {company}.

Best regards,
STYLE Marble & Granite
"""

    return {
        "email_subject": subject,
        "email_message": body,
        "followup_1": followup_1,
        "followup_2": followup_2,
    }


def personalize_dataframe(df, selected_products=None):
    out = df.copy()
    payloads = [build_email(r.to_dict(), selected_products) for _, r in out.iterrows()]
    for key in ["email_subject", "email_message", "followup_1", "followup_2"]:
        out[key] = [p[key] for p in payloads]
    return out
