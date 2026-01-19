import json
from models.schemas import EventFacts

print(json.dumps(EventFacts.model_json_schema(), indent=2))
