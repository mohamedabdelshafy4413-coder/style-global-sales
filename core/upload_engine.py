from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from .email_intelligence import domain_from_url, email_quality
from .golden500_engine import apollo_enrich_person, apollo_people_search, best_decision_maker, public_contacts
from .scoring_engine import buyer_score, classify_buyer, estimated_customer_probability, explain_score, probability_band, title_strength


def _find_col(df: pd.DataFrame, aliases: list[str]):
    normalized = {str(c).strip().lower(): c for c in df.columns}
    for alias in aliases:
        if alias.lower() in normalized:
            return normalized[alias.lower()]
    return None


def analyze_uploaded_file(
    frame: pd.DataFrame,
    apollo_api_key: str,
    max_rows: int = 500,
    use_apollo: bool = True,
) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()

    df = frame.head(max_rows).copy()

    company_col = _find_col(df, ["company", "company name", "business", "account", "name"])
    website_col = _find_col(df, ["website", "web", "url", "company website", "domain"])
    country_col = _find_col(df, ["country", "market", "location"])
    type_col = _find_col(df, ["buyer type", "buyer_type", "customer type", "type", "segment"])
    email_col = _find_col(df, ["email", "email address", "business email", "work email"])
    phone_col = _find_col(df, ["phone", "mobile", "telephone", "tel"])
    whatsapp_col = _find_col(df, ["whatsapp", "whats app", "wa"])
    contact_col = _find_col(df, ["contact", "contact name", "decision maker", "decision_maker", "person"])
    title_col = _find_col(df, ["title", "position", "job title", "role"])

    results = []
    for _, src in df.iterrows():
        website = str(src.get(website_col, "") or "").strip() if website_col else ""
        domain = domain_from_url(website)
        company = str(src.get(company_col, "") or "").strip() if company_col else domain
        country = str(src.get(country_col, "") or "").strip() if country_col else ""
        buyer_type = str(src.get(type_col, "") or "Uploaded Lead").strip() if type_col else "Uploaded Lead"
        email = str(src.get(email_col, "") or "").strip() if email_col else ""
        phone = str(src.get(phone_col, "") or "").strip() if phone_col else ""
        whatsapp = str(src.get(whatsapp_col, "") or "").strip() if whatsapp_col else ""
        decision_maker = str(src.get(contact_col, "") or "").strip() if contact_col else ""
        decision_title = str(src.get(title_col, "") or "").strip() if title_col else ""

        public = public_contacts(website) if website else {"public_emails": [], "phone": "", "whatsapp": "", "contact_page": ""}
        if not email and public.get("public_emails"):
            email = public["public_emails"][0]
        if not phone:
            phone = public.get("phone", "")
        if not whatsapp:
            whatsapp = public.get("whatsapp", "")

        apollo_status = ""
        linkedin_url = ""
        if use_apollo and apollo_api_key and domain:
            people = apollo_people_search(apollo_api_key, domain, per_page=5)
            best = best_decision_maker(people)
            if best:
                if not decision_maker:
                    decision_maker = " ".join(x for x in [best.get("first_name"), best.get("last_name")] if x).strip()
                if not decision_title:
                    decision_title = best.get("title") or ""
                linkedin_url = best.get("linkedin_url") or ""
                if not email:
                    enriched = apollo_enrich_person(apollo_api_key, best, domain)
                    email = enriched.get("email", "") or email
                    apollo_status = enriched.get("email_status", "") or ""
                    linkedin_url = enriched.get("linkedin_url", "") or linkedin_url

        email_meta = email_quality(email, domain, apollo_status)
        role_score = title_strength(decision_title)
        contact_points = sum(bool(x) for x in [email, phone, whatsapp, decision_maker])
        contact_quality = {0: 15, 1: 40, 2: 62, 3: 82, 4: 96}[contact_points]

        row = {
            "company": company or domain or "Unknown Company",
            "country": country,
            "buyer_type": buyer_type,
            "website": website,
            "domain": domain,
            "decision_maker": decision_maker,
            "decision_title": decision_title,
            "email": email,
            "email_source": "Uploaded / public / Apollo",
            "phone": phone,
            "whatsapp": whatsapp,
            "linkedin_url": linkedin_url,
            "import_signal": 60,
            "company_strength": 60,
            "style_fit": 65,
            "project_signal": 55,
            "repeat_potential": 60,
            "decision_access": role_score if decision_maker else 35,
            "contact_quality": contact_quality,
            "source_confidence": 78 if website or email else 55,
            "buying_signal": 58,
            "last_verified": datetime.now(timezone.utc).date().isoformat(),
            **email_meta,
        }
        row["buyer_score"] = buyer_score(row)
        row["customer_probability"] = estimated_customer_probability(row)
        row["probability_band"] = probability_band(row["customer_probability"])
        row["buyer_class"] = classify_buyer(row["buyer_score"])
        row["why_ranked"] = explain_score(row)
        results.append(row)

    out = pd.DataFrame(results)
    if out.empty:
        return out
    out = out.sort_values(
        ["customer_probability", "buyer_score", "email_quality_score", "decision_access"],
        ascending=False,
    ).reset_index(drop=True)
    out.insert(0, "rank", range(1, len(out) + 1))
    return out
