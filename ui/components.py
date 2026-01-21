import streamlit as st
from models.schemas import EventFacts, Winner

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
            elif field_name == "volunteer_count":
                updated_data[field_name] = st.number_input(
                    label, 
                    value=current_value if current_value is not None else 0,
                    min_value=0
                )
            elif field_name == "mode":
                 updated_data[field_name] = st.selectbox(
                    label,
                    ["Offline", "Online", "Hybrid"],
                    index=["Offline", "Online", "Hybrid"].index(current_value) if current_value in ["Offline", "Online", "Hybrid"] else 0
                )
            elif field_name in ["student_coordinators", "faculty_coordinators", "judges", "key_takeaways"]:
                 # Handle lists as comma separated strings
                 val_str = ", ".join(current_value) if current_value else ""
                 new_val_str = st.text_area(f"{label} (Comma separated)", value=val_str)
                 updated_data[field_name] = [x.strip() for x in new_val_str.split(",") if x.strip()]
            
            elif field_name == "winners":
                st.markdown(f"**{label}**")
                # Simplified winner editing - just text for common cases or expand if needed
                # For v1, let's allow adding via a simple expander or just rely on AI extraction
                # Real implementation: Iterate over winners found
                if not current_value:
                    st.info("No winners extracted. Add via input notes if needed.")
                else:
                    for i, w in enumerate(current_value):
                        st.text(f"Winner {i+1}: {w.place} - {w.team_name} ({w.prize_money})")
                
                # We won't build a full CRUD for winners here yet to keep it simple
                # passing existing value back
                updated_data[field_name] = current_value

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
