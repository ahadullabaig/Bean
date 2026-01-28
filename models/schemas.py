from typing import List, Optional
from pydantic import BaseModel, Field

# Layer 1: The Auditor's Domain (Strict Facts)
# Layer 1: The Auditor's Domain (Strict Facts)
class Winner(BaseModel):
    place: Optional[str] = Field(None, description="Placement (e.g., 'First Place', 'Second Place')")
    prize_money: Optional[str] = Field(None, description="Prize amount if mentioned")
    team_name: Optional[str] = Field(None, description="Name of the winning team")
    members: List[str] = Field(default_factory=list, description="List of team member names")

class EventFacts(BaseModel):
    event_title: Optional[str] = Field(None, description="The official title of the event")
    date: Optional[str] = Field(None, description="The date of the event in YYYY-MM-DD format if possible")
    venue: Optional[str] = Field(None, description="The physical location where the event took place")
    speaker_name: Optional[str] = Field(None, description="Name of the primary speaker or guest")
    attendance_count: Optional[int] = Field(None, description="Number of attendees")
    
    # New Fields for Generalization Template
    organizer: str = Field("IEEE RIT Student Branch", description="Organizing body")
    student_coordinators: List[str] = Field(default_factory=list, description="List of student coordinator names")
    faculty_coordinators: List[str] = Field(default_factory=list, description="List of faculty coordinator names")
    judges: List[str] = Field(default_factory=list, description="List of judges")
    volunteer_count: Optional[int] = Field(None, description="Number of volunteers")
    target_audience: Optional[str] = Field(None, description="Target audience (e.g. '2nd Year CSE')")
    mode: Optional[str] = Field(None, description="Mode of conduction: 'Online', 'Offline', or 'Hybrid'")
    agenda: Optional[str] = Field(None, description="Short agenda or flow of the event")
    media_link: Optional[str] = Field(None, description="Link to photos or registration")
    winners: List[Winner] = Field(default_factory=list, description="List of winners")
    
# Layer 2: The Ghostwriter's Domain (Professional Prose)
class EventNarrative(BaseModel):
    executive_summary: str = Field(..., description="A professional summary of the event")
    key_takeaways: List[str] = Field(default_factory=list, description="Bullet points of high-level outcomes or topics covered")

# Layer 3: The Critic's Domain (Hallucination Check)
class CriticVerdict(BaseModel):
    """Structured output from the Critic's consistency check."""
    is_safe: bool = Field(..., description="True if no hallucinations found in the report")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1) in this verdict")
    issues: List[str] = Field(default_factory=list, description="List of specific hallucinated facts found")
    reasoning: str = Field(..., description="Brief explanation of how the verdict was reached")
    
# The Final Container
class FullReport(BaseModel):
    facts: EventFacts
    narrative: EventNarrative
    confidence_score: float = Field(..., description="A 0-1 score indicating confidence in data extraction")

