"""
UI Components - Reusable Streamlit widgets for Bean.

Includes:
- Progress stepper for stage visualization
- Confidence badge with color coding
- Agent-styled spinners
- Template selector for event templates
- Smart form for fact verification
"""
import streamlit as st
from typing import Optional, List
from models.schemas import EventFacts, Winner, EventTemplate


# --- TEMPLATE SELECTOR ---

def render_template_selector(templates: List[EventTemplate]) -> Optional[EventTemplate]:
    """
    Renders a template selection interface.
    
    Args:
        templates: List of available templates
        
    Returns:
        Selected EventTemplate, or None if using blank template
    """
    st.subheader("📋 Choose a Template")
    st.caption("Start with a template or create from scratch.")
    
    # Group templates by category
    categories = {}
    for template in templates:
        if template.category not in categories:
            categories[template.category] = []
        categories[template.category].append(template)
    
    # Create template options with "None" option
    options = ["🆕 Start from Scratch"]
    template_map = {}
    
    for category, cat_templates in sorted(categories.items()):
        for template in cat_templates:
            option_key = f"{template.name}"
            options.append(option_key)
            template_map[option_key] = template
    
    # Template selector
    selected_option = st.selectbox(
        "Event Type",
        options,
        help="Select a template to pre-fill common fields"
    )
    
    # Show template preview if selected
    if selected_option != "🆕 Start from Scratch":
        selected_template = template_map.get(selected_option)
        if selected_template:
            with st.expander("📌 Template Details", expanded=False):
                st.markdown(f"**{selected_template.name}**")
                if selected_template.description:
                    st.caption(selected_template.description)
                st.markdown(f"- **Mode:** {selected_template.default_mode or 'Not specified'}")
                st.markdown(f"- **Audience:** {selected_template.default_target_audience or 'Not specified'}")
                if selected_template.suggested_agenda:
                    st.markdown(f"- **Agenda:** {selected_template.suggested_agenda}")
            return selected_template
    
    return None


def render_save_template_modal(facts: EventFacts) -> Optional[EventTemplate]:
    """
    Renders a modal/expander for saving current facts as a template.
    
    Args:
        facts: The EventFacts to base the template on
        
    Returns:
        New EventTemplate if saved, None otherwise
    """
    with st.expander("💾 Save as Template", expanded=False):
        st.caption("Save this event structure for future use")
        
        col1, col2 = st.columns(2)
        with col1:
            template_name = st.text_input(
                "Template Name",
                placeholder="e.g., Annual Hackathon"
            )
        with col2:
            template_id = st.text_input(
                "Template ID (slug)",
                placeholder="e.g., annual-hackathon",
                help="Lowercase, no spaces"
            )
        
        template_desc = st.text_input(
            "Description",
            placeholder="Brief description of this event type"
        )
        
        category = st.selectbox(
            "Category",
            ["Technical", "Competition", "Knowledge", "Social", "Custom"]
        )
        
        if st.button("💾 Save Template", key="save_template_btn"):
            if template_name and template_id:
                # Create template
                from core.templates import create_template_from_facts, save_template
                
                new_template = create_template_from_facts(
                    facts=facts,
                    name=template_name,
                    template_id=template_id.lower().replace(" ", "-"),
                    description=template_desc,
                    category=category
                )
                
                if save_template(new_template):
                    st.success(f"✅ Template '{template_name}' saved!")
                    return new_template
                else:
                    st.error("Failed to save template")
            else:
                st.warning("Please enter both name and ID")
    
    return None


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
    
    with st.form("smart_form", enter_to_submit=False):
        # Group fields into sections for better UX
        st.markdown("### 📋 Basic Information")
        col1, col2 = st.columns(2)
        
        with col1:
            updated_data["event_title"] = st.text_input(
                "Event Title",
                value=facts.event_title or ""
            )
            
            # Date picker with graceful parsing of existing dates
            existing_date = None
            if facts.date:
                from datetime import datetime
                for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                    try:
                        existing_date = datetime.strptime(facts.date, fmt).date()
                        break
                    except ValueError:
                        continue
            
            date_value = st.date_input(
                "Event Date",
                value=existing_date,
                format="YYYY-MM-DD"
            )
            # Store as ISO format string for consistency
            updated_data["date"] = date_value.isoformat() if date_value else None
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
        
        # Winners section - Now editable!
        st.markdown("### 🏆 Winners")
        st.caption("Edit winner details or add new winners below.")
        
        # Build list of winners (editable)
        edited_winners = []
        
        # Show existing winners in expanders
        if facts.winners:
            for i, winner in enumerate(facts.winners):
                with st.expander(f"🥇 {winner.place or f'Winner {i+1}'}: {winner.team_name or 'Unnamed Team'}", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        place = st.selectbox(
                            "Placement",
                            ["First Place", "Second Place", "Third Place", "Runner Up", "Special Mention"],
                            index=["First Place", "Second Place", "Third Place", "Runner Up", "Special Mention"].index(winner.place) if winner.place in ["First Place", "Second Place", "Third Place", "Runner Up", "Special Mention"] else 0,
                            key=f"winner_place_{i}"
                        )
                        team_name = st.text_input("Team Name", value=winner.team_name or "", key=f"winner_team_{i}")
                    with col2:
                        prize = st.text_input("Prize", value=winner.prize_money or "", key=f"winner_prize_{i}")
                        members_str = ", ".join(winner.members) if winner.members else ""
                        new_members = st.text_input("Members (comma-separated)", value=members_str, key=f"winner_members_{i}")
                    
                    edited_winners.append(Winner(
                        place=place,
                        team_name=team_name if team_name else None,
                        prize_money=prize if prize else None,
                        members=[x.strip() for x in new_members.split(",") if x.strip()]
                    ))
        else:
            st.info("No winners extracted. Use the button below to add winners if this is a competition.")
        
        # Add new winner button (outside the form, we store in session state)
        if "new_winners_count" not in st.session_state:
            st.session_state["new_winners_count"] = 0
        
        # Show fields for new winners
        for j in range(st.session_state["new_winners_count"]):
            with st.expander(f"➕ New Winner {j+1}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    new_place = st.selectbox(
                        "Placement",
                        ["First Place", "Second Place", "Third Place", "Runner Up", "Special Mention"],
                        key=f"new_winner_place_{j}"
                    )
                    new_team = st.text_input("Team Name", key=f"new_winner_team_{j}")
                with col2:
                    new_prize = st.text_input("Prize", key=f"new_winner_prize_{j}")
                    new_members_str = st.text_input("Members (comma-separated)", key=f"new_winner_members_{j}")
                
                if new_team:  # Only add if team name provided
                    edited_winners.append(Winner(
                        place=new_place,
                        team_name=new_team,
                        prize_money=new_prize if new_prize else None,
                        members=[x.strip() for x in new_members_str.split(",") if x.strip()]
                    ))
        
        updated_data["winners"] = edited_winners
        
        st.divider()
        submitted = st.form_submit_button("✅ Confirm Facts & Generate Report", use_container_width=True)
    
    if submitted:
        return EventFacts(**updated_data)
    
    return None
