from pydantic import BaseModel, Field
from typing import List

class Bedrijfsprofiel(BaseModel):
    # We dwingen hier af dat velden niet leeg mogen zijn voor die 99% score
    naam: str = Field(..., min_length=1)
    sector: str = Field(..., min_length=1)
    tech_stack: List[str]
    machine_park: List[str]
    contactgegevens: str
    business_trigger: str
    keywords: List[str]
    locatie: str