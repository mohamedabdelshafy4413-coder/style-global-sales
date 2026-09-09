COUNTRY_STRATEGY = {
    "Germany": "Focus on reliability, quality standards, long-term supply partnership and consistency.",
    "Saudi Arabia": "Focus on luxury projects, premium Egyptian stone and fast dependable supply.",
    "UAE": "Focus on hospitality, premium developments and exclusive stone collections.",
    "USA": "Focus on unique Egyptian natural stone value and competitive sourcing.",
    "Italy": "Focus on craftsmanship, material uniqueness and design applications.",
}


def build_email(contact_name, company, country, material):
    opening = COUNTRY_STRATEGY.get(
        country,
        "Focus on premium Egyptian natural stone supply and business partnership."
    )

    return f"""Subject: A Premium Egyptian Stone Supply Opportunity for {company}

Dear {contact_name or 'Sir/Madam'},

I hope this message finds you well.

STYLE specializes in premium Egyptian natural stone solutions including {material}.

{opening}

We would like to explore a long-term supply partnership with {company} and provide competitive materials, reliable production and export support.

I would be pleased to share our latest collection and discuss your upcoming requirements.

Best regards,
STYLE Export Team
"""
