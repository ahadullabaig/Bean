from core.llm import get_clean_schema
from models.schemas import EventNarrative, EventFacts
from pydantic import BaseModel, Field
from typing import Optional

def test_get_clean_schema_removes_defaults():
    class TestModel(BaseModel):
        name: str = Field(default="Unknown")
    
    clean = get_clean_schema(TestModel)
    assert "default" not in clean["properties"]["name"]

def test_get_clean_schema_handles_optional():
    """Verify that Optional[str] (anyOf) is converted to type: string, nullable: true."""
    class TestModel(BaseModel):
        opt_field: Optional[str] = None
        
    clean = get_clean_schema(TestModel)
    prop = clean["properties"]["opt_field"]
    
    # Check that anyOf is gone
    assert "anyOf" not in prop
    # Check that type is string
    assert prop["type"] == "string"
    # Check that nullable is True
    assert prop.get("nullable") is True

def test_real_models():
    """Verify EventFacts schema is clean."""
    clean = get_clean_schema(EventFacts)
    # event_title is Optional[str]
    assert "anyOf" not in clean["properties"]["event_title"]
    assert clean["properties"]["event_title"]["type"] == "string"
    assert clean["properties"]["event_title"]["nullable"] is True
