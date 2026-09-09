from __future__ import annotations

import re
import pandas as pd

TARGET_COUNTRIES = [
    "Saudi Arabia", "United Arab Emirates", "Morocco", "United Kingdom",
    "United States", "France", "Germany", "Italy", "Spain", "Canada"
]

COUNTRY_ALIASES = {
    "saudi": "Saudi Arabia", "ksa": "Saudi Arabia", "السعودية": "Saudi Arabia",
    "uae": "United Arab Emirates", "emirates": "United Arab Emirates", "الإمارات": "United Arab Emirates",
    "morocco": "Morocco", "المغرب": "Morocco",
    "uk": "United Kingdom", "united kingdom": "United Kingdom", "britain": "United Kingdom",
    "usa": "United States", "us": "United States", "united states": "United States", "america": "United States",
    "france": "France", "germany": "Germany", "italy": "Italy", "spain": "Spain", "canada": "Canada",
}

COUNTRY_PRIOR = {
    "Saudi Arabia": 92, "United Arab Emirates": 90, "United States": 86,
    "Italy": 84, "Germany": 82, "United Kingdom": 82, "France": 80,
    "Spain": 79, "Canada": 78, "Morocco": 77,
}

TYPE_PRIOR = {
    "Importer": 98, "Distributor": 94, "Wholesaler": 92,
    "Stone Fabricator": 86, "Architectural Supplier": 84,
    "Contractor": 82, "Developer": 80, "Tile & Stone Showroom": 76,
    "Hotel Supplier": 74, "Other": 58,
}

ROLE_PRIOR = {
    "owner": 96, "ceo": 96, "founder": 94, "managing director": 94,
    "procurement director": 98, "procurement manager": 96,
    "purchasing manager": 96, "sourcing manager": 94,
    "import manager": 94, "commercial director": 92,
    "commercial manager": 88, "general manager": 88,
    "project director": 84, "project manager": 78, "sales": 60,
}

MATERIAL_TERMS = [
    "marble", "granite", "natural stone", "stone", "slab", "slabs",
    "tile", "tiles", "quarry", "fabricator", "fabrication",
]

BUYER_TYPE_TERMS = {
    "Importer": ["importer", "import ", "imports", "importation"],
    "Distributor": ["distributor", "distribution", "stockist", "warehouse"],
    "Wholesaler": ["wholesale", "wholesaler"],
    "Stone Fabricator": ["fabricator", "fabrication", "cut to size"],
    "Architectural Supplier": ["architectural supplier", "architectural materials", "specifier"],
    "Contractor": ["contractor", "construction", "contracting"],
    "Developer": ["developer", "development", "real estate"],
    "Tile & Stone Showroom": ["showroom", "tile & stone", "tiles and stone"],
    "Hotel Supplier": ["hotel supplier", "hospitality", "hotel projects"],
}

FREE_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com",
    "aol.com", "proton.me", "protonmail.com"
}


def _blob(row: dict) -> str:
    return " ".join(str(row.get(k, "") or "") for k in [
        "company", "country", "customer_type", "contact_name", "job_title",
        "email", "website", "notes"
    ]).lower()


def normalize_country(value: str, blob: str = "") -> str:
    text = f"{value or ''} {blob or ''}".lower()
    for alias, canonical in COUNTRY_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", text):
            return canonical
    return value.strip() if value else ""


def infer_customer_type(value: str, blob: str) -> str:
    if value:
        lower = value.lower()
        for typ in TYPE_PRIOR:
            if typ.lower() in lower:
                return typ
    best_type, best_hits = "Other", 0
    for typ, terms in BUYER_TYPE_TERMS.items():
        hits = sum(1 for term in terms if term in blob)
        if hits > best_hits:
            best_type, best_hits = typ, hits
    return best_type


def role_score(title: str) -> int:
    text = (title or "").lower()
    score = 45
    for term, value in ROLE_PRIOR.items():
        if term in text:
            score = max(score, value)
    return score


def email_quality(email: str, company: str, website: str) -> tuple[int, str]:
    value = (email or "").lower().strip()
    if "@" not in value:
        return 10, "Missing"
    local, domain = value.split("@", 1)
    score, status = 70, "Usable"
    if domain in FREE_DOMAINS:
        score -= 22
        status = "Free-domain"
    if local in {"info", "sales", "office", "contact", "hello", "admin", "support", "enquiries", "inquiry", "marketing"}:
        score -= 12
        status = "Generic inbox"
    elif "." in local or len(local) >= 6:
        score += 8
        status = "Likely personal"
    web_domain = re.sub(r"^https?://(www\.)?", "", website or "", flags=re.I).split("/")[0].lower()
    if web_domain and (domain == web_domain or domain.endswith("." + web_domain)):
        score += 12
        status = "Company-domain"
    if company and any(token in domain for token in re.findall(r"[a-z0-9]+", company.lower()) if len(token) >= 5):
        score += 5
    return max(0, min(100, score)), status


def score_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, series in df.iterrows():
        row = series.to_dict()
        blob = _blob(row)
        country = normalize_country(row.get("country", ""), blob)
        customer_type = infer_customer_type(row.get("customer_type", ""), blob)
        role = role_score(row.get("job_title", ""))
        email_score, email_status = email_quality(
            row.get("email", ""), row.get("company", ""), row.get("website", "")
        )

        stone_hits = sum(1 for term in MATERIAL_TERMS if term in blob)
        style_fit = min(100, 52 + stone_hits * 8)
        company_strength = TYPE_PRIOR.get(customer_type, 58)
        if any(term in blob for term in ["group", "warehouse", "branches", "projects", "commercial", "nationwide", "international"]):
            company_strength = min(100, company_strength + 6)
        if any(term in blob for term in ["import", "distributor", "wholesale", "stockist"]):
            company_strength = min(100, company_strength + 6)

        market_fit = COUNTRY_PRIOR.get(country, 60)
        contact_quality = round(0.62 * email_score + 0.38 * role)
        reachability = round(
            0.56 * email_score
            + 0.18 * (88 if row.get("phone") else 40)
            + 0.26 * role
        )
        reply_speed = round(
            0.30 * role
            + 0.25 * email_score
            + 0.25 * TYPE_PRIOR.get(customer_type, 58)
            + 0.20 * market_fit
        )
        buying_intent = round(
            0.34 * TYPE_PRIOR.get(customer_type, 58)
            + 0.26 * style_fit
            + 0.22 * company_strength
            + 0.18 * market_fit
        )
        customer_probability = round(
            0.24 * buying_intent
            + 0.19 * reachability
            + 0.16 * reply_speed
            + 0.16 * style_fit
            + 0.14 * company_strength
            + 0.11 * market_fit
        )

        if customer_probability >= 88:
            buyer_class = "GOLDEN"
        elif customer_probability >= 78:
            buyer_class = "A-CLASS"
        elif customer_probability >= 66:
            buyer_class = "HIGH POTENTIAL"
        else:
            buyer_class = "NURTURE"

        row.update({
            "country": country,
            "customer_type": customer_type,
            "email_quality": email_score,
            "email_status": email_status,
            "company_strength": company_strength,
            "decision_access": role,
            "contact_quality": contact_quality,
            "style_fit": style_fit,
            "market_fit": market_fit,
            "reachability": reachability,
            "reply_speed": reply_speed,
            "buying_intent": buying_intent,
            "customer_probability": customer_probability,
            "buyer_class": buyer_class,
        })
        rows.append(row)

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out.sort_values(
        ["customer_probability", "buying_intent", "reply_speed", "reachability"],
        ascending=False,
    ).reset_index(drop=True)
    out.insert(0, "rank", range(1, len(out) + 1))
    return out
