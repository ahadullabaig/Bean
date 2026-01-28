"""
UI Components - Reusable Streamlit widgets for Bean.

Includes:
- Progress stepper for stage visualization
- Confidence badge with color coding
- Agent-styled spinners
- Smart form for fact verification
"""
import streamlit as st
from models.schemas import EventFacts, Winner


# --- PROGRESS STEPPER ---

def render_progress_stepper(current_stage: str):
    """
    Renders a visual progress stepper showing the current stage in the pipeline.
    
    Stages: input → verify → report
    """
    stages = [
        ("input", "📝 Input", "Feed your notes"),
        ("verify", "🔍 Verify", "Check the facts"),
        ("report", "📄 Report", "Get your document"),
    ]
    
    cols = st.columns(len(stages))
    
    for i, (col, (stage_id, stage_name, stage_desc)) in enumerate(zip(cols, stages)):
        with col:
            stage_index = [s[0] for s in stages].index(stage_id)
            current_index = [s[0] for s in stages].index(current_stage)
            
            if stage_index < current_index:
                # Completed
                icon = "✅"
                color = "#28a745"
            elif stage_id == current_stage:
                # Current
                icon = "🔵"
                color = "#007bff"
            else:
                # Upcoming
                icon = "⚪"
                color = "#6c757d"
            
            st.markdown(f"""
            <div style='text-align: center; padding: 8px;'>
                <div style='font-size: 1.5rem;'>{icon}</div>
                <div style='font-weight: bold; color: {color};'>{stage_name}</div>
                <div style='font-size: 0.75rem; color: #888;'>{stage_desc}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()


# --- CONFIDENCE BADGE ---

def render_confidence_badge(confidence: float, show_label: bool = True):
    """
    Renders a color-coded confidence badge.
    
    Colors:
    - Green: > 80% confidence
    - Orange: 50-80% confidence  
    - Red: < 50% confidence
    """
    if confidence > 0.8:
        color = "#28a745"  # Green
        bg_color = "#d4edda"
    elif confidence > 0.5:
        color = "#fd7e14"  # Orange
        bg_color = "#fff3cd"
    else:
        color = "#dc3545"  # Red
        bg_color = "#f8d7da"
    
    label = "Confidence: " if show_label else ""
    
    st.markdown(f"""
    <div style='margin-bottom: 1rem;'>
        <span style='
            background: {bg_color}; 
            color: {color}; 
            padding: 6px 14px; 
            border-radius: 20px; 
            font-weight: bold;
            border: 2px solid {color};
            display: inline-block;
        '>
            {label}{confidence:.0%}
        </span>
    </div>
    """, unsafe_allow_html=True)


# --- AGENT SPINNERS ---

def agent_spinner(agent_name: str, message: str):
    """
    Returns a context manager for agent-styled spinner.
    
    Usage:
        with agent_spinner("Auditor", "Reading your notes..."):
            do_work()
    """
    agent_icons = {
        "auditor": "🕵️",
        "ghostwriter": "✍️", 
        "critic": "🔎",
    }
    
    icon = agent_icons.get(agent_name.lower(), "⚙️")
    return st.spinner(f"{icon} {agent_name}: {message}")


# --- SMART FORM ---

def render_smart_form(facts: EventFacts) -> EventFacts:
    """
    Renders input fields for verifying and editing extracted event facts.
    Returns the updated EventFacts object upon form submission.
    """
    st.subheader("🕵️ Auditor's Extraction")
    st.info("Review the extracted facts below. Edit any incorrect values before proceeding.")
    
    # We create a dictionary to update, then reconstruct the object
    updated_data = facts.model_dump()
    
    with st.form("smart_form"):
        # Group fields into sections for better UX
        st.markdown("### 📋 Basic Information")
        col1, col2 = st.columns(2)
        
        with col1:
            updated_data["event_title"] = st.text_input(
                "Event Title",
                value=facts.event_title or ""
            )
            updated_data["date"] = st.text_input(
                "Date (YYYY-MM-DD)",
                value=facts.date or ""
            )
            updated_data["venue"] = st.text_input(
                "Venue",
                value=facts.venue or ""
            )
        
        with col2:
            updated_data["speaker_name"] = st.text_input(
                "Speaker/Guest Name",
                value=facts.speaker_name or ""
            )
            updated_data["attendance_count"] = st.number_input(
                "Attendance Count",
                value=facts.attendance_count if facts.attendance_count is not None else 0,
                min_value=0
            )
            updated_data["mode"] = st.selectbox(
                "Mode",
                ["Offline", "Online", "Hybrid"],
                index=["Offline", "Online", "Hybrid"].index(facts.mode) if facts.mode in ["Offline", "Online", "Hybrid"] else 0
            )
        
        st.markdown("### 👥 People")
        col1, col2 = st.columns(2)
        
        with col1:
            updated_data["organizer"] = st.text_input(
                "Organizer",
                value=facts.organizer or "IEEE RIT Student Branch"
            )
            
            coord_str = ", ".join(facts.student_coordinators) if facts.student_coordinators else ""
            new_coord = st.text_area("Student Coordinators (comma-separated)", value=coord_str, height=68)
            updated_data["student_coordinators"] = [x.strip() for x in new_coord.split(",") if x.strip()]
        
        with col2:
            updated_data["volunteer_count"] = st.number_input(
                "Volunteer Count",
                value=facts.volunteer_count if facts.volunteer_count is not None else 0,
                min_value=0
            )
            
            faculty_str = ", ".join(facts.faculty_coordinators) if facts.faculty_coordinators else ""
            new_faculty = st.text_area("Faculty Coordinators (comma-separated)", value=faculty_str, height=68)
            updated_data["faculty_coordinators"] = [x.strip() for x in new_faculty.split(",") if x.strip()]
        
        st.markdown("### 📝 Additional Details")
        
        updated_data["target_audience"] = st.text_input(
            "Target Audience",
            value=facts.target_audience or ""
        )
        updated_data["agenda"] = st.text_area(
            "Agenda/Flow",
            value=facts.agenda or "",
            height=80
        )
        updated_data["media_link"] = st.text_input(
            "Media/Registration Link",
            value=facts.media_link or ""
        )
        
        # Judges
        judges_str = ", ".join(facts.judges) if facts.judges else ""
        new_judges = st.text_input("Judges (comma-separated)", value=judges_str)
        updated_data["judges"] = [x.strip() for x in new_judges.split(",") if x.strip()]
        
        # Winners section
        st.markdown("### 🏆 Winners")
        if facts.winners:
            for i, winner in enumerate(facts.winners):
                st.text(f"{winner.place}: {winner.team_name} - {winner.prize_money or 'No prize specified'}")
        else:
            st.caption("No winners extracted. Add details in the notes if needed.")
        
        # Keep winners as-is (complex editing deferred)
        updated_data["winners"] = facts.winners
        
        st.divider()
        submitted = st.form_submit_button("✅ Confirm Facts & Generate Report", use_container_width=True)
    
    if submitted:
        return EventFacts(**updated_data)
    
    return None
