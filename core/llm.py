import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def get_gemini_model(model_name: str = "gemini-2.5-flash"):
    """
    Configures and returns a Gemini model instance.
    Raises ValueError if GEMINI_API_KEY is missing.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)

def get_clean_schema(pydantic_model):
    """
    Returns a JSON schema dict from a Pydantic model, 
    stripping 'default' keys which confuse the Gemini SDK.
    """
    schema = pydantic_model.model_json_schema()
    
    def _clean(d):
        if isinstance(d, dict):
            # Remove keys that are not supported by Gemini's Schema proto
            d.pop("default", None)
            d.pop("title", None) 
            
            # Handle Optional[T] -> anyOf: [{type: T}, {type: null}]
            if "anyOf" in d:
                any_of = d.pop("anyOf")
                # Try to find the non-null type
                non_null_type = None
                for sub in any_of:
                    if sub.get("type") != "null":
                        non_null_type = sub
                        break
                
                if non_null_type:
                    # Merge the non-null type properties into d
                    # recursive clean of the sub-schema first
                    _clean(non_null_type)
                    d.update(non_null_type)
                    # Set nullable=True
                    d["nullable"] = True
            
            for k, v in d.items():
                _clean(v)
        elif isinstance(d, list):
            for item in d:
                _clean(item)
        return d
        
    return _clean(schema)
