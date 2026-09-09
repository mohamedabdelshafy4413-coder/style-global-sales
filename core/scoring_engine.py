from __future__ import annotations

from dataclasses import dataclass


BUYER_WEIGHTS = {
    "import_signal": 0.24,
    "company_strength": 0.18,
    "style_fit": 0.16,
    "project_signal": 0.10,
    "repeat_potential": 0.10,
    "decision_access": 0.10,
    "contact_quality": 0.08,
    "source_confidence": 0.04,
}

TITLE_PRIORITY = {
    "owner": 100,
    "founder": 99,
    "chief executive": 98,
    "ceo": 98,
    "managing director": 97,
    "procurement director": 97,
    "head of procurement": 96,
    "purchasing director": 95,
    "head of purchasing": 94,
    "sourcing director": 94,
    "import director": 94,
    "procurement manager": 92,
    "purchasing manager": 91,
    "sourcing manager": 90,
    "import manager": 90,
    "commercial director": 86,
    "commercial manager": 82,
    "project director": 80,
    "general manager": 79,
}


def clamp(value: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, float(value)))


def title_strength(title: str) -> int:
    text = (title or "").strip().lower()
    if not text:
        return 35
    best = 45
    for phrase, score in TITLE_PRIORITY.items():
        if phrase in text:
            best = max(best, score)
    return best


def classify_buyer(score: float) -> str:
    score = float(score)
    if score >= 88:
        return "GOLDEN"
    if score >= 80:
        return "A-CLASS"
    if score >= 70:
        return "HIGH POTENTIAL"
    if score >= 60:
        return "POTENTIAL"
    return "RESEARCH"


def probability_band(score: float) -> str:
    score = float(score)
    if score >= 90:
        return "VERY HIGH"
    if score >= 80:
        return "HIGH"
    if score >= 70:
        return "GOOD"
    if score >= 60:
        return "MEDIUM"
    return "LOW / RESEARCH"


def buyer_score(row: dict) -> float:
    components = {
        "import_signal": row.get("import_signal", 50),
        "company_strength": row.get("company_strength", 50),
        "style_fit": row.get("style_fit", 50),
        "project_signal": row.get("project_signal", 50),
        "repeat_potential": row.get("repeat_potential", 50),
        "decision_access": row.get("decision_access", 45),
        "contact_quality": row.get("contact_quality", 35),
        "source_confidence": row.get("source_confidence", 50),
    }
    score = sum(clamp(components[k]) * w for k, w in BUYER_WEIGHTS.items())
    return round(clamp(score), 1)


def estimated_customer_probability(row: dict) -> float:
    """
    Commercial prioritization estimate, not a statistical guarantee.
    Intentionally capped at 96 to avoid presenting research signals as certainty.
    """
    base = buyer_score(row)
    dm = title_strength(row.get("decision_title", ""))
    email_q = clamp(row.get("email_quality_score", 0))
    recent_signal = clamp(row.get("buying_signal", 50))
    probability = (
        0.62 * base
        + 0.13 * dm
        + 0.15 * email_q
        + 0.10 * recent_signal
    )
    return round(min(96.0, clamp(probability)), 1)


def explain_score(row: dict) -> str:
    reasons: list[str] = []
    if row.get("import_signal", 0) >= 75:
        reasons.append("strong importer/distributor evidence")
    if row.get("company_strength", 0) >= 75:
        reasons.append("strong company scale")
    if row.get("style_fit", 0) >= 80:
        reasons.append("high STYLE material fit")
    if row.get("project_signal", 0) >= 72:
        reasons.append("active project signal")
    if row.get("decision_maker"):
        reasons.append("decision maker identified")
    if row.get("email_quality_score", 0) >= 80:
        reasons.append("strong email quality")
    if row.get("whatsapp"):
        reasons.append("public WhatsApp available")
    return "; ".join(reasons) if reasons else "requires deeper verification"
