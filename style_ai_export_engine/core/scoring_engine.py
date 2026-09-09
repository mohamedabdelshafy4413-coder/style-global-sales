from dataclasses import dataclass


@dataclass
class BuyerScore:
    company_power: float
    material_fit: float
    contact_quality: float
    buying_intent: float
    market_fit: float

    def total(self) -> float:
        return round(
            self.company_power * 0.25
            + self.material_fit * 0.20
            + self.contact_quality * 0.20
            + self.buying_intent * 0.25
            + self.market_fit * 0.10,
            2,
        )


def classify(score: float) -> str:
    if score >= 90:
        return "GOLDEN TARGET"
    if score >= 80:
        return "A-CLASS"
    if score >= 65:
        return "HIGH POTENTIAL"
    return "NURTURE"
