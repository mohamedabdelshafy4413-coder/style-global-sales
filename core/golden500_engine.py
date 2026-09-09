from __future__ import annotations

import concurrent.futures
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests

from .email_intelligence import choose_best_email, domain_from_url, email_quality
from .scoring_engine import (
    buyer_score,
    classify_buyer,
    estimated_customer_probability,
    explain_score,
    probability_band,
    title_strength,
)


SERPER_URL = "https://google.serper.dev/search"
APOLLO_PEOPLE_SEARCH_URL = "https://api.apollo.io/api/v1/mixed_people/api_search"
APOLLO_PEOPLE_MATCH_URL = "https://api.apollo.io/api/v1/people/match"
USER_AGENT = "Mozilla/5.0 (compatible; STYLEGolden500/1.0; +https://styleformarble.com/)"

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
WHATSAPP_RE = re.compile(r"(?:wa\.me/|api\.whatsapp\.com/send\?phone=)(\+?\d+)", re.I)

BLOCKED_DOMAINS = {
    "facebook.com", "linkedin.com", "instagram.com", "youtube.com", "wikipedia.org",
    "pinterest.com", "x.com", "twitter.com", "tiktok.com", "google.com", "bing.com",
    "yellowpages.com", "yelp.com", "tripadvisor.com",
}

CLIENT_TYPE_TERMS = {
    "Importer": ["importer", "imports", "importing", "international sourcing"],
    "Distributor": ["distributor", "distribution", "regional distributor", "exclusive distributor"],
    "Wholesaler": ["wholesaler", "wholesale", "stockist", "stone stock"],
    "Fabricator": ["fabricator", "fabrication", "cut to size", "stone workshop"],
    "Contractor": ["contractor", "construction company", "general contractor", "fit out"],
    "Developer": ["developer", "real estate development", "property developer"],
    "Architectural Supplier": ["architectural supplier", "architectural materials", "specification"],
    "Hotel / Hospitality Supplier": ["hospitality", "hotel supplier", "hotel projects"],
    "Stone Showroom": ["showroom", "tile showroom", "stone showroom"],
    "Project Procurement": ["procurement", "project procurement", "project supply"],
}

BUYING_TERMS = [
    "import", "importer", "distribution", "distributor", "wholesale", "stockist", "warehouse",
    "natural stone", "marble", "granite", "slabs", "tiles", "projects", "procurement",
]
SCALE_TERMS = [
    "group", "warehouse", "warehouses", "branches", "showrooms", "nationwide", "regional",
    "projects", "commercial", "wholesale", "distribution", "factory", "fabrication",
]
PROJECT_TERMS = [
    "project", "projects", "contractor", "developer", "hotel", "hospitality", "commercial",
    "construction", "architect", "residential", "fit-out", "fit out",
]
REPEAT_TERMS = [
    "stock", "stockist", "warehouse", "distribution", "wholesale", "inventory", "slabs", "tiles",
]

DECISION_TITLES = [
    "owner", "founder", "chief executive officer", "CEO", "managing director",
    "procurement director", "head of procurement", "purchasing director", "head of purchasing",
    "sourcing director", "import director", "procurement manager", "purchasing manager",
    "sourcing manager", "import manager", "commercial director", "commercial manager",
    "project director", "general manager",
]


def _domain(url: str) -> str:
    return domain_from_url(url)


def _valid_company_url(url: str) -> bool:
    domain = _domain(url)
    if not domain:
        return False
    return not any(domain == d or domain.endswith("." + d) for d in BLOCKED_DOMAINS)


def _keyword_score(text: str, terms: list[str], floor: int = 30, points: int = 10) -> int:
    text = (text or "").lower()
    hits = sum(1 for term in terms if term.lower() in text)
    return min(100, floor + hits * points)


def _safe_get(url: str, timeout: int = 7):
    try:
        return requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            allow_redirects=True,
        )
    except Exception:
        return None


def serper_search(api_key: str, query: str, num: int = 20) -> list[dict]:
    response = requests.post(
        SERPER_URL,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "num": max(10, min(int(num), 20))},
        timeout=25,
    )
    response.raise_for_status()
    return (response.json() or {}).get("organic", []) or []


def _company_name(title: str, domain: str) -> str:
    value = re.split(r"[\-|–|—|\|]", title or "")[0].strip()
    return (value or domain)[:160]


def infer_client_type(text: str, requested_types: list[str]) -> str:
    text = (text or "").lower()
    best_type, best_hits = "Other / Research", 0
    for buyer_type in requested_types:
        terms = CLIENT_TYPE_TERMS.get(buyer_type, [buyer_type.lower()])
        hits = sum(1 for t in terms if t.lower() in text)
        if hits > best_hits:
            best_type, best_hits = buyer_type, hits
    return best_type if best_hits else (requested_types[0] if len(requested_types) == 1 else "Other / Research")


def infer_material_fit(text: str, materials: list[str]) -> tuple[str, int]:
    text_l = (text or "").lower()
    exact = [m for m in materials if m.lower() in text_l]
    if exact:
        return ", ".join(exact), min(100, 88 + 3 * len(exact))
    generic_hits = sum(1 for t in ["egyptian marble", "marble", "granite", "natural stone", "slabs", "tiles"] if t in text_l)
    score = min(88, 55 + generic_hits * 6)
    return ", ".join(materials), score


def build_queries(country: str, buyer_type: str, materials: list[str], depth: int = 2) -> list[str]:
    material_or = " OR ".join(f'"{m}"' for m in materials)
    type_terms = " ".join(CLIENT_TYPE_TERMS.get(buyer_type, [buyer_type]))
    variants = [
        f'({material_or}) marble granite natural stone {type_terms} {country}',
        f'Egyptian marble granite slabs tiles {type_terms} {country}',
        f'natural stone warehouse projects procurement {type_terms} {country}',
    ]
    return variants[: max(1, min(int(depth), 3))]


def discover_companies(
    countries: list[str],
    buyer_types: list[str],
    materials: list[str],
    serper_api_key: str,
    target: int = 500,
    search_depth: int = 2,
) -> list[dict]:
    jobs: list[tuple[str, str, str]] = []
    for country in countries:
        for buyer_type in buyer_types:
            for query in build_queries(country, buyer_type, materials, search_depth):
                jobs.append((country, buyer_type, query))

    def run_job(job: tuple[str, str, str]):
        country, buyer_type, query = job
        try:
            return country, buyer_type, serper_search(serper_api_key, query, 20)
        except Exception:
            return country, buyer_type, []

    raw: list[dict] = []
    workers = min(10, max(3, len(jobs)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        for country, requested_type, results in executor.map(run_job, jobs):
            for item in results:
                url = item.get("link") or ""
                if not _valid_company_url(url):
                    continue
                domain = _domain(url)
                title = (item.get("title") or "").strip()
                snippet = (item.get("snippet") or "").strip()
                text = f"{title} {snippet}"
                materials_match, style_fit = infer_material_fit(text, materials)
                company_strength = _keyword_score(text, SCALE_TERMS, 38, 9)
                import_signal = _keyword_score(text, BUYING_TERMS, 35, 9)
                project_signal = _keyword_score(text, PROJECT_TERMS, 30, 10)
                repeat_potential = _keyword_score(text, REPEAT_TERMS, 35, 10)
                source_confidence = 68 if snippet else 50
                row = {
                    "company": _company_name(title, domain),
                    "country": country,
                    "buyer_type": infer_client_type(text, [requested_type]),
                    "domain": domain,
                    "website": url,
                    "materials": materials_match,
                    "import_signal": import_signal,
                    "company_strength": company_strength,
                    "style_fit": style_fit,
                    "project_signal": project_signal,
                    "repeat_potential": repeat_potential,
                    "decision_access": 35,
                    "contact_quality": 20,
                    "source_confidence": source_confidence,
                    "buying_signal": round((import_signal + project_signal + repeat_potential) / 3, 1),
                    "search_snippet": snippet[:700],
                    "evidence_url": url,
                    "last_verified": datetime.now(timezone.utc).date().isoformat(),
                }
                row["pre_score"] = buyer_score(row)
                raw.append(row)

    deduped: list[dict] = []
    seen: set[str] = set()
    for row in sorted(raw, key=lambda r: r.get("pre_score", 0), reverse=True):
        key = row.get("domain") or f"{row.get('company')}|{row.get('country')}"
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    candidate_cap = max(int(target * 1.35), min(650, target + 100))
    return deduped[:candidate_cap]


def public_contacts(website: str) -> dict:
    result = {
        "public_emails": [],
        "phone": "",
        "whatsapp": "",
        "contact_page": "",
    }
    if not website:
        return result

    parsed = urlparse(website if "://" in website else "https://" + website)
    base = f"{parsed.scheme or 'https'}://{parsed.netloc or parsed.path}".rstrip("/")
    paths = ["", "/contact", "/contact-us", "/contacts", "/about", "/about-us", "/team"]
    emails: list[str] = []
    phones: list[str] = []
    whatsapps: list[str] = []

    for path in paths:
        page_url = urljoin(base + "/", path.lstrip("/"))
        response = _safe_get(page_url)
        if not response or response.status_code >= 400 or not response.text:
            continue
        html = response.text[:700000]
        lower = html.lower()

        for email in EMAIL_RE.findall(html):
            email = email.lower().strip(".,;:()[]<>")
            if any(bad in email for bad in ["example.com", "sentry.io", "wixpress.com", "cloudflare.com"]):
                continue
            if email not in emails:
                emails.append(email)

        for value in WHATSAPP_RE.findall(html):
            digits = re.sub(r"\D", "", value)
            if digits:
                normalized = "+" + digits
                if normalized not in whatsapps:
                    whatsapps.append(normalized)

        for match in re.finditer("whatsapp", lower):
            window = html[max(0, match.start() - 180): match.end() + 240]
            for phone in PHONE_RE.findall(window):
                clean = re.sub(r"[^\d+]", "", phone)
                if 8 <= len(re.sub(r"\D", "", clean)) <= 16 and clean not in whatsapps:
                    whatsapps.append(clean)

        text = re.sub(r"<[^>]+>", " ", html)
        for phone in PHONE_RE.findall(text):
            clean = re.sub(r"[^\d+]", "", phone)
            if 8 <= len(re.sub(r"\D", "", clean)) <= 16 and clean not in phones:
                phones.append(clean)

        if "contact" in response.url.lower() and not result["contact_page"]:
            result["contact_page"] = response.url
        if len(emails) >= 3 and phones and whatsapps:
            break

    result["public_emails"] = emails[:8]
    result["phone"] = phones[0] if phones else ""
    result["whatsapp"] = whatsapps[0] if whatsapps else ""
    return result


def apollo_people_search(api_key: str, domain: str, per_page: int = 5) -> list[dict]:
    if not api_key or not domain:
        return []
    params: list[tuple[str, str]] = [
        ("q_organization_domains_list[]", domain),
        ("include_similar_titles", "true"),
        ("per_page", str(max(1, min(int(per_page), 10)))),
        ("page", "1"),
    ]
    for title in DECISION_TITLES:
        params.append(("person_titles[]", title))
    for seniority in ["owner", "founder", "c_suite", "head", "director", "manager"]:
        params.append(("person_seniorities[]", seniority))
    try:
        response = requests.post(
            APOLLO_PEOPLE_SEARCH_URL,
            headers={
                "x-api-key": api_key,
                "accept": "application/json",
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
            },
            params=params,
            timeout=20,
        )
        response.raise_for_status()
        return (response.json() or {}).get("people", []) or []
    except Exception:
        return []


def best_decision_maker(people: list[dict]) -> dict:
    if not people:
        return {}
    def rank(person: dict):
        role = title_strength(person.get("title", ""))
        seniority = (person.get("seniority") or "").lower()
        seniority_bonus = 8 if seniority in {"owner", "founder", "c_suite", "head", "director"} else 3
        return role + seniority_bonus
    return sorted(people, key=rank, reverse=True)[0]


def apollo_enrich_person(api_key: str, person: dict, domain: str) -> dict:
    if not api_key or not person or not domain:
        return {}
    params = {
        "first_name": person.get("first_name") or "",
        "last_name": person.get("last_name") or "",
        "domain": domain,
        "reveal_personal_emails": "false",
        "reveal_phone_number": "false",
    }
    try:
        response = requests.post(
            APOLLO_PEOPLE_MATCH_URL,
            headers={
                "x-api-key": api_key,
                "accept": "application/json",
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
            },
            params=params,
            timeout=20,
        )
        response.raise_for_status()
        person_data = (response.json() or {}).get("person") or {}
        return {
            "email": person_data.get("email") or "",
            "email_status": person_data.get("email_status") or "",
            "linkedin_url": person_data.get("linkedin_url") or person.get("linkedin_url") or "",
            "apollo_match_confidence": person_data.get("match_confidence") or "",
        }
    except Exception:
        return {}


def enrich_companies(
    candidates: list[dict],
    apollo_api_key: str,
    target: int = 500,
    email_enrichment_budget: int = 500,
) -> list[dict]:
    candidates = candidates[: max(target, min(len(candidates), target + 100))]

    def first_pass(row: dict) -> dict:
        row = dict(row)
        contacts = public_contacts(row.get("website", ""))
        row.update(contacts)
        people = apollo_people_search(apollo_api_key, row.get("domain", ""), 5)
        best = best_decision_maker(people)
        row["_apollo_person"] = best
        row["decision_maker"] = " ".join(
            x for x in [best.get("first_name"), best.get("last_name")] if x
        ).strip()
        row["decision_title"] = best.get("title") or ""
        row["linkedin_url"] = best.get("linkedin_url") or ""
        role_score = title_strength(row["decision_title"])
        row["decision_access"] = role_score if best else 35

        public_candidates = [
            {"email": email, "source": "Public website", "role_strength": 45, "email_status": ""}
            for email in row.get("public_emails", [])
        ]
        best_public = choose_best_email(public_candidates, row.get("domain", ""))
        if best_public:
            row["email"] = best_public.get("email", "")
            row["email_source"] = "Public website"
            row["email_status"] = ""
            row.update({k: v for k, v in best_public.items() if k.startswith("email_")})
        else:
            row["email"] = ""
            row["email_source"] = ""
            row["email_status"] = ""
            row.update(email_quality("", row.get("domain", "")))

        contact_points = sum(bool(row.get(k)) for k in ["email", "phone", "whatsapp", "decision_maker"])
        row["contact_quality"] = {0: 20, 1: 45, 2: 65, 3: 82, 4: 95}[contact_points]
        row["source_confidence"] = min(96, row.get("source_confidence", 50) + (10 if contacts.get("public_emails") else 0) + (8 if best else 0))
        row["pre_enrich_score"] = buyer_score(row)
        return row

    workers = min(10, max(3, len(candidates)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        rows = list(executor.map(first_pass, candidates))

    # Apollo email enrichment is credit-consuming, so apply it to the highest-priority rows first.
    budget = max(0, min(int(email_enrichment_budget), len(rows)))
    enrich_targets = [
        row for row in sorted(rows, key=lambda r: r.get("pre_enrich_score", 0), reverse=True)
        if row.get("_apollo_person")
    ][:budget]

    def enrich_one(row: dict) -> dict:
        apollo = apollo_enrich_person(apollo_api_key, row.get("_apollo_person") or {}, row.get("domain", ""))
        apollo_email = apollo.get("email", "")
        if apollo_email:
            candidate = {
                "email": apollo_email,
                "source": "Apollo enrichment",
                "role_strength": title_strength(row.get("decision_title", "")),
                "email_status": apollo.get("email_status", ""),
            }
            current = {
                "email": row.get("email", ""),
                "source": row.get("email_source", ""),
                "role_strength": 45,
                "email_status": row.get("email_status", ""),
            }
            best = choose_best_email([current, candidate], row.get("domain", ""))
            if best:
                row["email"] = best.get("email", "")
                row["email_source"] = best.get("source", "")
                row["email_status"] = best.get("email_status", "")
                row.update({k: v for k, v in best.items() if k.startswith("email_")})
        row["linkedin_url"] = apollo.get("linkedin_url") or row.get("linkedin_url", "")
        row["apollo_match_confidence"] = apollo.get("apollo_match_confidence", "")
        return row

    if enrich_targets:
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            list(executor.map(enrich_one, enrich_targets))

    final: list[dict] = []
    for row in rows:
        if row.get("email") and "email_quality_score" not in row:
            row.update(email_quality(row.get("email", ""), row.get("domain", ""), row.get("email_status", "")))
        contact_points = sum(bool(row.get(k)) for k in ["email", "phone", "whatsapp", "decision_maker"])
        row["contact_quality"] = {0: 20, 1: 45, 2: 65, 3: 82, 4: 95}[contact_points]
        row["buyer_score"] = buyer_score(row)
        row["customer_probability"] = estimated_customer_probability(row)
        row["probability_band"] = probability_band(row["customer_probability"])
        row["buyer_class"] = classify_buyer(row["buyer_score"])
        row["why_ranked"] = explain_score(row)
        row.pop("_apollo_person", None)
        row.pop("public_emails", None)
        final.append(row)

    final.sort(
        key=lambda r: (
            r.get("customer_probability", 0),
            r.get("buyer_score", 0),
            r.get("email_quality_score", 0),
        ),
        reverse=True,
    )
    return final[:target]


def build_golden500(
    countries: list[str],
    buyer_types: list[str],
    materials: list[str],
    serper_api_key: str,
    apollo_api_key: str,
    target: int = 500,
    search_depth: int = 2,
    email_enrichment_budget: int = 500,
) -> pd.DataFrame:
    candidates = discover_companies(
        countries=countries,
        buyer_types=buyer_types,
        materials=materials,
        serper_api_key=serper_api_key,
        target=target,
        search_depth=search_depth,
    )
    if not candidates:
        return pd.DataFrame()
    rows = enrich_companies(
        candidates=candidates,
        apollo_api_key=apollo_api_key,
        target=target,
        email_enrichment_budget=email_enrichment_budget,
    )
    df = pd.DataFrame(rows)
    if not df.empty:
        df.insert(0, "rank", range(1, len(df) + 1))
    return df


def enrich_uploaded_companies(
    frame: pd.DataFrame,
    apollo_api_key: str,
    target: int = 500,
    email_enrichment_budget: int = 500,
) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()

    df = frame.copy()
    normalized = {str(c).strip().lower(): c for c in df.columns}
    website_col = next((normalized[k] for k in ["website", "web", "url", "company website"] if k in normalized), None)
    company_col = next((normalized[k] for k in ["company", "company name", "name", "account"] if k in normalized), None)
    country_col = next((normalized[k] for k in ["country", "market", "location"] if k in normalized), None)
    type_col = next((normalized[k] for k in ["buyer_type", "buyer type", "type", "customer type"] if k in normalized), None)

    rows: list[dict] = []
    for _, source in df.head(max(target, 500)).iterrows():
        website = str(source.get(website_col, "") or "").strip() if website_col else ""
        domain = _domain(website)
        company = str(source.get(company_col, "") or "").strip() if company_col else domain
        country = str(source.get(country_col, "") or "").strip() if country_col else ""
        buyer_type = str(source.get(type_col, "") or "").strip() if type_col else "Uploaded Lead"
        row = {
            "company": company or domain,
            "country": country,
            "buyer_type": buyer_type or "Uploaded Lead",
            "domain": domain,
            "website": website,
            "materials": "",
            "import_signal": 60,
            "company_strength": 55,
            "style_fit": 60,
            "project_signal": 50,
            "repeat_potential": 55,
            "decision_access": 35,
            "contact_quality": 20,
            "source_confidence": 60,
            "buying_signal": 55,
            "search_snippet": "Uploaded company record",
            "evidence_url": website,
            "last_verified": datetime.now(timezone.utc).date().isoformat(),
            "pre_score": 55,
        }
        rows.append(row)

    enriched = enrich_companies(
        rows,
        apollo_api_key=apollo_api_key,
        target=min(target, len(rows)),
        email_enrichment_budget=email_enrichment_budget,
    )
    out = pd.DataFrame(enriched)
    if not out.empty:
        out.insert(0, "rank", range(1, len(out) + 1))
    return out
