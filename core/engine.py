from __future__ import annotations

import concurrent.futures
import re
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin

import pandas as pd
import requests

USER_AGENT = (
    "Mozilla/5.0 (compatible; STYLEBuyerCommandCenter/1.0; "
    "+https://styleformarble.com/)"
)

BLOCKED_DOMAINS = {
    "linkedin.com", "facebook.com", "instagram.com", "youtube.com", "pinterest.com",
    "wikipedia.org", "x.com", "twitter.com", "tiktok.com", "google.com", "bing.com"
}

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
WHATSAPP_LINK_RE = re.compile(
    r"(?:wa\.me/|api\.whatsapp\.com/send\?phone=)(\+?\d+)", re.I
)

BUYER_TITLES = [
    "procurement manager",
    "purchasing manager",
    "sourcing manager",
    "import manager",
    "commercial manager",
    "managing director",
    "general manager",
    "owner",
]

MARKET_PRIOR = {
    "Saudi Arabia": 90,
    "United Arab Emirates": 88,
    "Morocco": 80,
    "United Kingdom": 78,
    "United States": 82,
    "France": 76,
    "Germany": 74,
    "Italy": 78,
    "Spain": 77,
    "Canada": 73,
}

def _domain(url: str) -> str:
    try:
        parsed = urlparse(url if "://" in url else "https://" + url)
        host = parsed.netloc.lower().split("@")[-1].split(":")[0]
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""

def _is_company_url(url: str) -> bool:
    domain = _domain(url)
    if not domain:
        return False
    return not any(domain == d or domain.endswith("." + d) for d in BLOCKED_DOMAINS)

def _safe_get(url: str, timeout: int = 7):
    try:
        return requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
        )
    except Exception:
        return None

def serper_search(api_key: str, query: str, num: int = 10) -> list[dict]:
    r = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "num": max(10, min(int(num), 20))},
        timeout=20,
    )
    r.raise_for_status()
    return (r.json() or {}).get("organic", []) or []

def apollo_people_search(api_key: str, domain: str, per_page: int = 3) -> list[dict]:
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
        r = requests.post(
            "https://api.apollo.io/api/v1/mixed_people/api_search",
            headers={"x-api-key": api_key, "accept": "application/json"},
            params=params,
            timeout=18,
        )
        r.raise_for_status()
        return (r.json() or {}).get("people", []) or []
    except Exception:
        return []

def apollo_enrich_email(api_key: str, person: dict, domain: str) -> dict:
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
        r = requests.post(
            "https://api.apollo.io/api/v1/people/match",
            headers={
                "x-api-key": api_key,
                "accept": "application/json",
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
            },
            params=params,
            timeout=18,
        )
        r.raise_for_status()
        data = r.json() or {}
        p = data.get("person") or {}
        return {
            "email": p.get("email") or "",
            "email_status": p.get("email_status") or "",
            "apollo_match_confidence": p.get("match_confidence") or "",
        }
    except Exception:
        return {}

def _score_text(text: str, terms: list[str], floor: int = 35) -> int:
    t = (text or "").lower()
    hits = sum(1 for term in terms if term.lower() in t)
    return min(100, floor + hits * 11)

def _company_name(title: str, domain: str) -> str:
    value = re.split(r"[\-|–|—|\|]", title or "")[0].strip()
    return value[:140] if value else domain

def infer_materials(text: str, materials: list[str]) -> list[str]:
    t = (text or "").lower()
    hits = [m for m in materials if m.lower() in t]
    return hits or materials

def discover_companies(countries: list[str], materials: list[str], serper_api_key: str, max_candidates: int = 120) -> list[dict]:
    material_phrase = " OR ".join(f'"{m}"' for m in materials)
    jobs = []
    for country in countries:
        jobs.extend([
            (country, f'({material_phrase}) natural stone marble granite importer distributor wholesaler {country}'),
            (country, f'Egyptian marble granite stone importer distributor fabricator warehouse projects {country}'),
        ])

    def do_search(job):
        country, query = job
        try:
            return country, serper_search(serper_api_key, query, 10)
        except Exception:
            return country, []

    raw = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for country, results in ex.map(do_search, jobs):
            for item in results:
                url = item.get("link") or ""
                if not _is_company_url(url):
                    continue
                domain = _domain(url)
                snippet = (item.get("snippet") or "").strip()
                title = (item.get("title") or "").strip()
                text = f"{title} {snippet}"
                raw.append({
                    "company": _company_name(title, domain),
                    "country": country,
                    "domain": domain,
                    "website": url,
                    "materials": ", ".join(infer_materials(text, materials)),
                    "search_title": title,
                    "search_snippet": snippet[:650],
                    "importer_signal": _score_text(text,["import","importer","distribution","distributor","wholesale","wholesaler","stockist","warehouse","natural stone"]),
                    "scale_signal": _score_text(text,["group","warehouse","branches","nationwide","projects","commercial","wholesale","distribution"]),
                    "project_signal": _score_text(text,["project","contractor","developer","hotel","hospitality","commercial","construction","architect"]),
                    "market_prior": MARKET_PRIOR.get(country, 70),
                    "evidence_url": url,
                    "last_verified": datetime.now(timezone.utc).date().isoformat(),
                })

    deduped, seen = [], set()
    for row in raw:
        key = row["domain"]
        if not key or key in seen:
            continue
        seen.add(key)
        row["pre_score"] = round(
            0.34 * row["importer_signal"] + 0.20 * row["scale_signal"] + 0.14 * row["project_signal"] +
            0.12 * row["market_prior"] + 0.20 * (90 if any(m.lower() in row["search_snippet"].lower() for m in materials) else 65), 1)
        deduped.append(row)
    return sorted(deduped, key=lambda r: r["pre_score"], reverse=True)[:max_candidates]

def public_contacts(website: str) -> dict:
    result = {"public_email":"", "phone":"", "whatsapp":"", "contact_page":""}
    if not website:
        return result
    parsed = urlparse(website if "://" in website else "https://" + website)
    base = f"{parsed.scheme or 'https'}://{parsed.netloc or parsed.path}".rstrip("/")
    paths = ["", "/contact", "/contact-us", "/contacts", "/about", "/about-us"]
    emails, phones, whatsapps = [], [], []
    for path in paths:
        url = urljoin(base + "/", path.lstrip("/"))
        resp = _safe_get(url)
        if not resp or resp.status_code >= 400 or not resp.text:
            continue
        html = resp.text[:650000]
        lower = html.lower()
        for email in EMAIL_RE.findall(html):
            email = email.lower().strip(".,;:()[]<>")
            if any(bad in email for bad in ["example.com", "sentry.io", "wixpress.com"]):
                continue
            if email not in emails:
                emails.append(email)
        for number in WHATSAPP_LINK_RE.findall(html):
            clean = re.sub(r"\D", "", number)
            if clean:
                whatsapps.append("+" + clean)
        for m in re.finditer("whatsapp", lower):
            window = html[max(0, m.start()-180):m.end()+220]
            for ph in PHONE_RE.findall(window):
                clean = re.sub(r"[^\d+]", "", ph)
                if 8 <= len(re.sub(r"\D", "", clean)) <= 16:
                    whatsapps.append(clean)
        text = re.sub(r"<[^>]+>", " ", html)
        for ph in PHONE_RE.findall(text):
            clean = re.sub(r"[^\d+]", "", ph)
            if 8 <= len(re.sub(r"\D", "", clean)) <= 16 and clean not in phones:
                phones.append(clean)
        if "contact" in resp.url.lower() and not result["contact_page"]:
            result["contact_page"] = resp.url
        if emails and phones and whatsapps:
            break
    result["public_email"] = emails[0] if emails else ""
    result["phone"] = phones[0] if phones else ""
    result["whatsapp"] = whatsapps[0] if whatsapps else ""
    return result

def _best_person(people: list[dict]) -> dict:
    if not people:
        return {}
    title_order = {"procurement":100,"purchasing":98,"sourcing":96,"import":94,"commercial":88,"managing director":86,"general manager":84,"owner":82}
    def rank(p):
        title = (p.get("title") or "").lower(); score = 50
        for term, value in title_order.items():
            if term in title: score = max(score, value)
        if (p.get("seniority") or "").lower() in {"owner","founder","c_suite","vp","head","director"}: score += 5
        return score
    return sorted(people, key=rank, reverse=True)[0]

def enrich_top_candidates(candidates: list[dict], apollo_api_key: str, email_credit_limit: int = 15) -> list[dict]:
    def web_enrich(row):
        row = dict(row)
        row.update(public_contacts(row.get("website", "")))
        people = apollo_people_search(apollo_api_key, row.get("domain", ""), 3)
        best = _best_person(people)
        row["_apollo_person"] = best
        row["decision_maker"] = " ".join(x for x in [best.get("first_name"), best.get("last_name")] if x).strip()
        row["decision_title"] = best.get("title") or ""
        row["linkedin_url"] = best.get("linkedin_url") or ""
        row["apollo_person_found"] = bool(best)
        return row

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        enriched = list(ex.map(web_enrich, candidates))

    targets = [r for r in sorted(enriched, key=lambda r: r["pre_score"], reverse=True) if not r.get("public_email") and r.get("_apollo_person")]
    targets = targets[:max(0, int(email_credit_limit))]
    def credit_enrich(row):
        row.update(apollo_enrich_email(apollo_api_key, row.get("_apollo_person") or {}, row.get("domain", "")))
        return row
    if targets:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            list(ex.map(credit_enrich, targets))

    results = []
    for row in enriched:
        public_email = row.get("public_email") or ""; apollo_email = row.get("email") or ""
        row["email"] = public_email or apollo_email
        row["email_source"] = "Public website" if public_email else ("Apollo enrichment" if apollo_email else "")
        contact_score = (35 if row.get("email") else 0) + (20 if row.get("phone") else 0) + (20 if row.get("whatsapp") else 0) + (25 if row.get("decision_maker") else 0)
        material_specific = any(m.strip().lower() in (row.get("search_snippet") or "").lower() for m in (row.get("materials") or "").split(",") if m.strip())
        material_fit = 95 if material_specific else 72
        decision_access = 92 if row.get("decision_maker") else 45
        score = 0.27*row["importer_signal"] + 0.14*row["scale_signal"] + 0.12*row["project_signal"] + 0.13*material_fit + 0.10*row["market_prior"] + 0.12*decision_access + 0.12*contact_score
        row["opportunity_score"] = round(min(100, score), 1)
        row["material_fit"] = material_fit; row["contact_score"] = contact_score; row["decision_access"] = decision_access
        if row["opportunity_score"] >= 86: label = "GOLDEN"
        elif row["opportunity_score"] >= 78: label = "A-CLASS"
        elif row["opportunity_score"] >= 68: label = "HIGH POTENTIAL"
        else: label = "RESEARCH"
        reasons = []
        if row["importer_signal"] >= 75: reasons.append("قوي كمستورد/موزع")
        if row["scale_signal"] >= 70: reasons.append("إشارات حجم/مخازن/توزيع")
        if row["project_signal"] >= 70: reasons.append("نشاط مشاريع")
        if row.get("decision_maker"): reasons.append("Decision maker موجود")
        if row.get("email"): reasons.append("Email متاح")
        if row.get("whatsapp"): reasons.append("WhatsApp معلن")
        row["buyer_class"] = label; row["why_ranked"] = " • ".join(reasons) or "يحتاج تحقق أعمق"
        row.pop("_apollo_person", None); results.append(row)
    return sorted(results, key=lambda r: r["opportunity_score"], reverse=True)

def build_top50(countries: list[str], materials: list[str], serper_api_key: str, apollo_api_key: str, email_credit_limit: int = 15) -> pd.DataFrame:
    candidates = discover_companies(countries, materials, serper_api_key, max_candidates=70)
    if not candidates:
        return pd.DataFrame()
    enriched = enrich_top_candidates(candidates[:55], apollo_api_key, email_credit_limit)
    df = pd.DataFrame(enriched).head(50).reset_index(drop=True)
    if not df.empty:
        df.insert(0, "rank", range(1, len(df)+1))
    return df
