from __future__ import annotations

import re
from functools import lru_cache
from urllib.parse import urlparse

try:
    import dns.resolver
except Exception:  # optional until installed
    dns = None


EMAIL_RE = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.I)
GENERIC_LOCAL_PARTS = {
    "info", "contact", "hello", "office", "admin", "support", "sales", "mail",
    "enquiries", "enquiry", "marketing", "customerservice", "service"
}
STRONG_ROLE_LOCAL_PARTS = {
    "procurement", "purchasing", "sourcing", "imports", "import", "buying", "commercial"
}
FREE_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "aol.com",
    "live.com", "msn.com", "proton.me", "protonmail.com"
}


def normalize_email(email: str) -> str:
    return (email or "").strip().lower().strip(".,;:()[]<>")


def domain_from_url(url: str) -> str:
    if not url:
        return ""
    try:
        parsed = urlparse(url if "://" in url else "https://" + url)
        host = parsed.netloc.lower().split(":")[0]
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


@lru_cache(maxsize=2048)
def has_mx(domain: str) -> bool:
    domain = (domain or "").strip().lower()
    if not domain:
        return False
    try:
        if dns is None:
            return False
        answers = dns.resolver.resolve(domain, "MX", lifetime=4)
        return bool(list(answers))
    except Exception:
        return False


def email_quality(email: str, company_domain: str = "", apollo_status: str = "") -> dict:
    email = normalize_email(email)
    if not email or not EMAIL_RE.match(email):
        return {
            "email_quality_score": 0,
            "email_quality": "INVALID / MISSING",
            "email_domain_match": False,
            "email_mx": False,
            "email_reason": "missing or invalid syntax",
        }

    local, domain = email.split("@", 1)
    company_domain = (company_domain or "").lower().strip()
    score = 40
    reasons = ["valid syntax"]

    if domain not in FREE_DOMAINS:
        score += 12
        reasons.append("business domain")
    else:
        score -= 18
        reasons.append("free mailbox domain")

    domain_match = bool(company_domain and (domain == company_domain or domain.endswith("." + company_domain)))
    if domain_match:
        score += 20
        reasons.append("matches company domain")
    elif company_domain:
        score -= 10
        reasons.append("does not match company domain")

    mx = has_mx(domain)
    if mx:
        score += 12
        reasons.append("MX record found")
    else:
        score -= 12
        reasons.append("MX not confirmed")

    if local in STRONG_ROLE_LOCAL_PARTS:
        score += 9
        reasons.append("strong buying-role mailbox")
    elif local in GENERIC_LOCAL_PARTS:
        score -= 5
        reasons.append("generic mailbox")
    elif "." in local or len(local) >= 6:
        score += 6
        reasons.append("likely personal business mailbox")

    status = (apollo_status or "").lower().strip()
    if status in {"verified", "valid"}:
        score += 15
        reasons.append("Apollo verified/valid")
    elif status in {"guessed", "unverified", "unknown"}:
        score -= 3
        reasons.append(f"Apollo status: {status}")
    elif status in {"invalid", "bounced"}:
        score = min(score, 20)
        reasons.append(f"Apollo status: {status}")

    score = max(0, min(100, int(round(score))))
    if score >= 90:
        label = "GOLDEN EMAIL"
    elif score >= 80:
        label = "STRONG"
    elif score >= 65:
        label = "USABLE"
    elif score >= 45:
        label = "VERIFY FIRST"
    else:
        label = "WEAK"

    return {
        "email_quality_score": score,
        "email_quality": label,
        "email_domain_match": domain_match,
        "email_mx": mx,
        "email_reason": "; ".join(reasons),
    }


def choose_best_email(candidates: list[dict], company_domain: str = "") -> dict:
    ranked = []
    for candidate in candidates:
        email = normalize_email(candidate.get("email", ""))
        if not email:
            continue
        quality = email_quality(email, company_domain, candidate.get("email_status", ""))
        ranked.append({**candidate, **quality, "email": email})
    if not ranked:
        return {}
    ranked.sort(key=lambda r: (r.get("email_quality_score", 0), r.get("role_strength", 0)), reverse=True)
    return ranked[0]
