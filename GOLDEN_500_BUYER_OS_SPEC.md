# STYLE Golden 500 Buyer Intelligence OS

## Objective
Build a B2B export intelligence system for STYLE that discovers, ranks, and prioritizes the highest-probability marble and granite buyers.

## Core workflow
Country -> Customer Type -> Company Strength -> Decision Maker -> Verified Contact -> Purchase Probability -> Outreach Campaign

## Filters

### Countries
- Saudi Arabia
- UAE
- USA
- UK
- Germany
- France
- Italy
- Spain
- Canada
- Morocco

### Customer Types
- Importer
- Marble Distributor
- Granite Distributor
- Stone Fabricator
- Showroom
- Contractor
- Developer Supplier
- Architectural Supplier

## Buyer scoring model

Purchase Intent 40%
- Natural stone import signals
- Marble/granite relevance
- Distribution activity
- Project activity

Company Power 25%
- Size indicators
- Branches
- Market presence
- Projects

Contact Quality 20%
- Decision maker found
- Role strength
- Domain email quality

STYLE Fit 15%
- Material match
- Market match

## Output

Every ranked buyer should contain:

- Company
- Country
- Customer type
- Website
- Decision maker
- Job title
- Email
- Phone
- WhatsApp (only if publicly verified)
- Buyer score
- Customer probability
- Reason for ranking
- Recommended first action

## Golden Classification

90-100: Golden Target

75-90: A Class

60-75: Potential

Below 60: Nurture

## Data sources architecture

- Serper: discovery and web intelligence
- Apollo: B2B contacts and decision makers
- Email verification layer: deliverability quality
- Future shipment/import databases: real purchase history

## Product principle

The system ranks sales opportunities. It must never invent contacts or claim unverified purchasing history.
