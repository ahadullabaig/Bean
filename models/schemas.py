from typing import List, Optional
from pydantic import BaseModel, Field

# Layer 1: The Auditor's Domain (Strict Facts)
class EventFacts(BaseModel):
    event_title: Optional[str] = Field(None, description="The official title of the event")
    date: Optional[str] = Field(None, description="The date of the event in YYYY-MM-DD format if possible, or readable string")
    venue: Optional[str] = Field(None, description="The physical location where the event took place")
    speaker_name: Optional[str] = Field(None, description="Name of the primary speaker or guest")
    attendance_count: Optional[int] = Field(None, description="Number of attendees, if mentioned")
    
# Layer 2: The Ghostwriter's Domain (Professional Prose)
class EventNarrative(BaseModel):
    executive_summary: str = Field(..., description="A professional summary of the event")
    key_takeaways: List[str] = Field(default_factory=list, description="Bullet points of high-level outcomes or topics covered")
    
# The Final Container
class FullReport(BaseModel):
    facts: EventFacts
    narrative: EventNarrative
    confidence_score: float = Field(..., description="A 0-1 score indicating confidence in data extraction")
