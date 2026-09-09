from __future__ import annotations

from urllib.parse import urlparse
import requests

BUYER_TITLES = [
    "procurement director", "procurement manager", "purchasing manager",
    "sourcing manager", "import manager", "commercial director",
    "managing director", "owner", "ceo"
]


def domain_from_website_or_email(website: str, email: str) -> str:
    if website:
        value = website if "://" in website else "https://" + website
        host = urlparse(value).netloc.lower().split(":")[0]
        return host[4:] if host.startswith("www.") else host
    if email and "@" in email:
        return email.split("@")[-1].lower().strip()
    return ""


def apollo_people_search(api_key: str, domain: str, per_page: int = 5) -> list[dict]:
    if not api_key or not domain:
        return []
    params = [
        ("q_organization_domains_list[]", domain),
        ("include_similar_titles", "true"),
        ("per_page", str(max(1, min(per_page, 10)))),
        ("page", "1"),
    ]
    for title in BUYER_TITLES:
        params.append(("person_titles[]", title))
    try:
        response = requests.post(
            "https://api.apollo.io/api/v1/mixed_people/api_search",
            headers={"x-api-key": api_key, "accept": "application/json"},
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        return (response.json() or {}).get("people", []) or []
    except Exception:
        return []


def best_apollo_person(people: list[dict]) -> dict:
    weights = {
        "procurement": 100, "purchasing": 98, "sourcing": 96,
        "import": 94, "commercial": 90, "managing director": 90,
        "owner": 88, "ceo": 88,
    }

    def score(person):
        title = (person.get("title") or "").lower()
        value = 50
        for term, weight in weights.items():
            if term in title:
                value = max(value, weight)
        return value

    return sorted(people, key=score, reverse=True)[0] if people else {}


def enrich_row_with_apollo(row: dict, api_key: str) -> dict:
    domain = domain_from_website_or_email(row.get("website", ""), row.get("email", ""))
    person = best_apollo_person(apollo_people_search(api_key, domain, 5))
    if not person:
        return dict(row)

    enriched = dict(row)
    if not enriched.get("contact_name"):
        enriched["contact_name"] = " ".join(
            value for value in [person.get("first_name"), person.get("last_name")] if value
        ).strip()
    if not enriched.get("job_title"):
        enriched["job_title"] = person.get("title") or ""
    enriched["linkedin_url"] = person.get("linkedin_url") or ""
    enriched["apollo_person_found"] = True
    return enriched
