from pydantic import BaseModel, Field
from typing import List, Optional

class Bedrijfsprofiel(BaseModel):
    naam: Optional[str] = ""
    sector: Optional[str] = ""
    tech_stack: List[str] = Field(default_factory=list)
    machine_park: List[str] = Field(default_factory=list)
    contactgegevens: Optional[str] = ""
    business_trigger: Optional[str] = ""
    keywords: List[str] = Field(default_factory=list)
    locatie: Optional[str] = ""