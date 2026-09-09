from __future__ import annotations

COUNTRY_ANGLES = {
    "Saudi Arabia": {
        "subject": "Reliable Egyptian marble supply for your Saudi projects",
        "opening": "Saudi buyers usually need fast commercial response, consistent selection and dependable project quantities.",
        "proof": "We can support recurring requirements with export-ready documentation, clear packing details and responsive quotation follow-up.",
        "cta": "If you share the stone, size, thickness and estimated quantity, I can prepare a focused commercial offer for your current buying cycle.",
    },
    "United Arab Emirates": {
        "subject": "Egyptian natural stone supply for UAE distribution & projects",
        "opening": "For UAE stone buyers, speed, finish consistency and dependable project supply are usually more valuable than a generic catalogue.",
        "proof": "STYLE can support distributors, fabricators and project suppliers with blocks, slabs, tiles, custom sizes and multiple finishes.",
        "cta": "Send me your current requirement or your fastest-moving stone category and I will return a focused offer for the UAE market.",
    },
    "Morocco": {
        "subject": "Direct Egyptian marble supply for Morocco",
        "opening": "We are reaching out because your business profile fits the type of Moroccan buyer that can benefit from direct Egyptian stone sourcing.",
        "proof": "Our focus is consistent commercial supply, practical export coordination and material options suitable for distribution and projects.",
        "cta": "If you are reviewing suppliers now, send the preferred material and quantity and I will prepare the most relevant offer first.",
    },
    "United Kingdom": {
        "subject": "Consistent Egyptian stone supply for UK buyers",
        "opening": "UK buyers often need dependable specification, repeatable selection and a supplier that answers commercial questions clearly.",
        "proof": "STYLE supplies Egyptian marble and granite in export formats with multiple finish options and project-oriented support.",
        "cta": "If you send one active specification or material requirement, I can reply with the closest commercial match and next-step quotation.",
    },
    "United States": {
        "subject": "Egyptian marble & granite supply for US stone buyers",
        "opening": "For US importers and distributors, the opportunity is strongest when material fit, consistency and repeat supply are clear from the first conversation.",
        "proof": "STYLE supports export supply of Egyptian marble and granite across blocks, slabs, tiles, custom sizes and multiple finishes.",
        "cta": "Reply with the stone category, format and approximate volume you are buying and I will prepare a targeted export offer.",
    },
    "France": {
        "subject": "Egyptian marble supply opportunity for your French market",
        "opening": "Your company profile matches the type of French stone buyer that may benefit from a focused Egyptian sourcing option rather than a broad generic proposal.",
        "proof": "STYLE offers Egyptian natural stone with commercial formats, finish options and export support for distributors and project buyers.",
        "cta": "If you have an active requirement, send the material, dimensions and quantity and I will return a focused commercial proposal.",
    },
    "Germany": {
        "subject": "Reliable Egyptian natural stone supply for Germany",
        "opening": "German buyers typically value consistency, clear technical communication and a supplier that can support repeat purchasing without unnecessary sales language.",
        "proof": "STYLE focuses on controlled stone selection, practical specification support and export-ready supply across key Egyptian materials.",
        "cta": "Send one current requirement and I will reply with the most relevant material option, format and commercial next step.",
    },
    "Italy": {
        "subject": "Egyptian marble & granite sourcing for Italian stone buyers",
        "opening": "Italy is a highly experienced stone market, so we are approaching you with a focused supply proposition rather than a standard introduction.",
        "proof": "STYLE can support professional stone buyers with Egyptian blocks, slabs, tiles, custom sizing and finish options suitable for fabrication and distribution.",
        "cta": "If you tell me what you are sourcing now, I will send only the most relevant materials and commercial information.",
    },
    "Spain": {
        "subject": "Direct Egyptian stone supply for Spain",
        "opening": "Spanish distributors and project suppliers often need a competitive stone source that combines material fit with responsive commercial follow-up.",
        "proof": "STYLE supplies Egyptian marble and granite in export formats for distribution, fabrication and project requirements.",
        "cta": "Reply with your current stone requirement and I will prepare a focused offer around the material, format and volume you need.",
    },
    "Canada": {
        "subject": "Egyptian natural stone supply for Canadian buyers",
        "opening": "Canadian importers and distributors benefit most from suppliers that can communicate clearly, support repeat orders and match the right material to the buying requirement.",
        "proof": "STYLE offers Egyptian marble and granite in blocks, slabs, tiles and custom formats with multiple finish options.",
        "cta": "Share one current buying requirement and I will return a focused proposal with the closest matching STYLE materials.",
    },
}

DEFAULT_ANGLE = {
    "subject": "Reliable Egyptian marble & granite supply",
    "opening": "Your company profile appears relevant to the type of professional stone buyer we want to support with direct Egyptian supply.",
    "proof": "STYLE supplies Egyptian marble and granite in blocks, slabs, tiles, custom sizes and multiple finishes for international buyers.",
    "cta": "If you share one active requirement, I will prepare a focused commercial proposal rather than a generic catalogue email.",
}

BUYER_TYPE_ANGLES = {
    "Importer": "direct import supply, repeat purchasing and dependable commercial response",
    "Distributor": "repeat stock supply, commercially relevant formats and consistent material selection",
    "Wholesaler": "repeat stock availability, scalable supply and practical commercial pricing",
    "Fabricator": "slab quality, usable dimensions, finish options and fabrication-friendly consistency",
    "Contractor": "project quantities, specification matching, custom sizing and delivery coordination",
    "Developer": "project-scale supply, specification consistency and dependable commercial follow-through",
    "Architectural Supplier": "specification support, material presentation and project-ready formats",
    "Hotel / Hospitality Supplier": "hospitality project consistency, finish options and coordinated project supply",
    "Stone Showroom": "saleable material selection, display-friendly finishes and repeat stock supply",
    "Project Procurement": "RFQ speed, specification matching and project-oriented supply coordination",
}

MATERIALS_LINE = (
    "Our core Egyptian materials include Galala Light, Sunny Light, Meli Brown, "
    "Meli Grey and Zafarana Flower, with blocks, slabs, tiles, custom sizes and multiple finishes available depending on the requirement."
)


def _first_name(name: str) -> str:
    value = (name or "").strip()
    return value.split()[0] if value else "there"


def generate_email(row: dict, company_name: str = "STYLE for Marble & Granite") -> dict:
    country = row.get("country") or ""
    company = row.get("company") or "your company"
    buyer_type = row.get("buyer_type") or "Buyer"
    contact = row.get("decision_maker") or ""
    first = _first_name(contact)
    score = row.get("customer_probability", "")
    angle = COUNTRY_ANGLES.get(country, DEFAULT_ANGLE)
    buyer_angle = BUYER_TYPE_ANGLES.get(buyer_type, "reliable Egyptian natural-stone supply")

    subject = angle["subject"]
    if company and company != "your company":
        subject = f"{subject} — {company}"

    body = f"""Dear {first},

{angle['opening']}

I am contacting you from {company_name}. Based on your company profile, I believe there may be a strong fit around {buyer_angle}.

{MATERIALS_LINE}

{angle['proof']}

Instead of sending a large generic catalogue, we prefer to start with the requirement that matters commercially to you now.

{angle['cta']}

Best regards,
STYLE for Marble & Granite
Egypt
https://styleformarble.com/
"""

    follow_up_1 = f"""Subject: Re: {subject}

Dear {first},

Following up briefly in case Egyptian marble or granite is currently relevant to your buying plan.

If you send only 4 points — material, format, thickness and approximate quantity — we can respond with a focused commercial direction instead of a broad sales presentation.

Best regards,
STYLE for Marble & Granite
"""

    follow_up_2 = f"""Subject: One quick question for {company}

Dear {first},

Before I close the loop, which is more relevant for you at the moment: regular stock supply, a project/RFQ, or a new Egyptian stone source?

A one-line reply is enough. I will send only the materials and commercial details that match that need.

Best regards,
STYLE for Marble & Granite
"""

    linkedin = (
        f"Hi {first}, I’m with STYLE for Marble & Granite in Egypt. "
        f"Your work at {company} looks relevant to our supply of Galala Light, Sunny Light, "
        f"Meli Brown, Meli Grey and Zafarana Flower. If you handle {buyer_angle}, "
        "I’d be glad to send a focused offer based on your current requirement."
    )

    return {
        "subject": subject,
        "email_body": body,
        "follow_up_1": follow_up_1,
        "follow_up_2": follow_up_2,
        "linkedin_message": linkedin,
        "commercial_angle": buyer_angle,
        "internal_probability": score,
    }
