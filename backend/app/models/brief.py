from typing import Literal

from pydantic import BaseModel


class NegotiationPoint(BaseModel):
    clause_id: str
    section: str
    risk_level: Literal['High', 'Medium']
    clause_title: str
    negotiation_summary: str


class NegotiationBrief(BaseModel):
    overview: str
    primary_focus: list[str]
    overall_recommendation: str
    overall_negotiation_strategy: str
    top_redlines: list[str]
    deal_breakers: list[str]
    negotiation_points: list[NegotiationPoint]