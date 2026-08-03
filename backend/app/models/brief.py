from pydantic import BaseModel

class NegotiationPoint(BaseModel):
    clause_id: str
    section: str
    risk_level: str
    negotiation_summary: str

class NegotiationBrief(BaseModel):
    overview: str
    negotiation_points: list[NegotiationPoint]