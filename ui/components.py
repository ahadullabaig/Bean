import streamlit as st
from models.schemas import EventFacts

def render_smart_form(facts: EventFacts) -> EventFacts:
    """
    Renders input fields for any missing (None) facts in the EventFacts object.
    Returns the updated EventFacts object.
    """
    st.subheader("🕵️ Auditor's Questions")
    st.info("The Auditor found some facts, but missed others. Please fill in the blanks.")
    
    # We create a dictionary to update, then reconstruct the object
    updated_data = facts.model_dump()
    
    with st.form("smart_form"):
        # Iterate through fields defined in the schema
        for field_name, field_info in EventFacts.model_fields.items():
            current_value = getattr(facts, field_name)
            
            # If value is None, we need to ask for it. 
            # We can also allow editing existing values if needed, 
            # but the requirement emphasizes "missing data".
            # Let's show all, but highlight missing ones?
            # Simpler: Just show inputs for everything, pre-filled.
            
            label = f"{field_name.replace('_', ' ').title()}"
            if field_info.description:
                label += f" ({field_info.description})"
            
            # Type handling could be more robust, but strings/ints cover our schema.
            if field_name == "attendance_count":
                updated_data[field_name] = st.number_input(
                    label, 
                    value=current_value if current_value is not None else 0,
                    min_value=0
                )
            else:
                updated_data[field_name] = st.text_input(
                    label, 
                    value=current_value if current_value else ""
                )
        
        submitted = st.form_submit_button("Confirm Facts")
        
    if submitted:
        # Re-validate and return new object
        # Convert empty strings back to None if strictly needed, 
        # but our schema allows strict strings. 
        # Actually EventFacts fields are Optional[str].
        
        # Clean up: "0" attendance might mean None for some, but let's trust the input.
        return EventFacts(**updated_data)
    
    return None
