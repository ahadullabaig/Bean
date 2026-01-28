"""
Bean: AI Documentation Agent - Main Application

A Streamlit app that transforms messy event notes into professional IEEE reports
using a pipeline of specialized AI agents: Auditor → Ghostwriter → Critic.
"""
import streamlit as st
import os

# Clean imports at top level
from core.critic import check_consistency
from core.ghostwriter import generate_narrative
from core.renderer import render_report
from core.templates import load_templates, get_builtin_templates, apply_template, increment_use_count
from ui.handlers import handle_text_process, handle_audio_process
from ui.components import (
    render_smart_form, 
    render_progress_stepper, 
    render_confidence_badge,
    render_template_selector,
    render_save_template_modal,
    agent_spinner
)
from models.schemas import EventFacts, FullReport


# Page Config
st.set_page_config(
    page_title="Bean: AI Documentation Agent", 
    page_icon="🫘",
    layout="centered"
)


# --- SESSION STATE INITIALIZATION ---
def init_session_state():
    """Initialize all session state variables with defaults."""
    defaults = {
        "stage": "input",  # input -> verify -> report
        "facts": None,
        "raw_text_context": "",
        "final_report": None,
        "critic_verdict": None,
        "processing": False,
        "docx_stream": None,
        "selected_template": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()


# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("assets/ieee_header.png"):
        st.image("assets/ieee_header.png", use_container_width=True)
    st.title("⚙️ Settings")
    api_key = st.text_input("Gemini API Key", type="password")
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
    
    st.divider()
    st.caption("🫘 Bean v1.0")
    st.caption("Powered by Google Gemini")


# --- MAIN UI ---
st.title("🫘 Bean: The Event Reporter")
st.markdown("*Turn your messy notes into professional IEEE reports.*")

# Progress Stepper
render_progress_stepper(st.session_state["stage"])


# --- STAGE 1: INPUT ---
if st.session_state["stage"] == "input":
    st.header("📝 Feed the Bean")
    
    # Template Selection
    all_templates = get_builtin_templates() + load_templates()
    selected_template = render_template_selector(all_templates)
    
    if selected_template:
        st.session_state["selected_template"] = selected_template
    
    st.divider()
    
    input_method = st.radio(
        "Choose your input method:", 
        ["Text Notes", "Audio Recording"],
        horizontal=True
    )
    
    if input_method == "Text Notes":
        # Show different placeholder based on template
        placeholder_text = "Example: We conducted a workshop on Machine Learning on 15th January 2024. Around 45 students attended. Dr. Priya Sharma was the speaker..."
        if selected_template:
            placeholder_text = f"Enter notes for your {selected_template.name}..."
        
        raw_text = st.text_area(
            "Paste your event notes here...", 
            height=200,
            placeholder=placeholder_text
        )
        
        # Double-click protected button
        process_btn = st.button(
            "🚀 Process Notes", 
            disabled=st.session_state.get("processing", False),
            use_container_width=True
        )
        
        if process_btn and not st.session_state.get("processing"):
            if not raw_text.strip():
                st.error("Please enter some text.")
            else:
                st.session_state["processing"] = True
                
                try:
                    st.session_state["raw_text_context"] = raw_text
                    with agent_spinner("Auditor", "Extracting facts from your notes..."):
                        extracted_facts = handle_text_process(raw_text)
                    
                    # Merge template defaults with extracted facts
                    if st.session_state.get("selected_template"):
                        template = st.session_state["selected_template"]
                        # Apply template defaults only for None values
                        if not extracted_facts.organizer:
                            extracted_facts.organizer = template.default_organizer
                        if not extracted_facts.mode:
                            extracted_facts.mode = template.default_mode
                        if not extracted_facts.target_audience:
                            extracted_facts.target_audience = template.default_target_audience
                        if not extracted_facts.agenda:
                            extracted_facts.agenda = template.suggested_agenda
                        
                        # Increment template usage
                        increment_use_count(template.id)
                    
                    st.session_state["facts"] = extracted_facts
                    st.session_state["stage"] = "verify"
                finally:
                    st.session_state["processing"] = False
                    
                st.rerun()

    elif input_method == "Audio Recording":
        audio_val = st.audio_input("Record your notes")
        if audio_val:
            st.info("Audio received.")
            st.warning("🚧 Audio processing is under construction. Please use text for now.")


# --- STAGE 2: VERIFICATION (Smart Form) ---
elif st.session_state["stage"] == "verify":
    st.header("🔍 Verify the Facts")
    
    # Show template in use (if any)
    if st.session_state.get("selected_template"):
        template = st.session_state["selected_template"]
        st.info(f"📋 Using template: **{template.name}**")
    
    # Render the Smart Form
    updated_facts = render_smart_form(st.session_state["facts"])
    
    if updated_facts:
        st.session_state["facts"] = updated_facts
        
        # Trigger Ghostwriter
        with agent_spinner("Ghostwriter", "Drafting the narrative..."):
            narrative = generate_narrative(
                st.session_state["facts"], 
                st.session_state["raw_text_context"]
            )
        
        # Combine into Full Report
        report = FullReport(
            facts=st.session_state["facts"],
            narrative=narrative,
            confidence_score=1.0
        )
        
        # Critic Pass
        with agent_spinner("Critic", "Verifying for hallucinations..."):
            report_text = f"{report.facts}\n\n{report.narrative.executive_summary}\n\n{report.narrative.key_takeaways}"
            verdict = check_consistency(st.session_state["raw_text_context"], report_text)
        
        # Update confidence score from critic
        report.confidence_score = verdict.confidence
        
        st.session_state["final_report"] = report
        st.session_state["critic_verdict"] = verdict
        st.session_state["stage"] = "report"
        st.rerun()


# --- STAGE 3: REPORT PREVIEW ---
elif st.session_state["stage"] == "report":
    st.header("📄 Your Report")
    
    verdict = st.session_state.get("critic_verdict")
    report: FullReport = st.session_state["final_report"]
    
    # Critic Verdict Section
    if verdict:
        col1, col2 = st.columns([1, 3])
        with col1:
            render_confidence_badge(verdict.confidence)
        with col2:
            if verdict.is_safe:
                st.success("✅ Zero Hallucinations detected")
            else:
                st.warning(f"⚠️ {len(verdict.issues)} potential issue(s) found")
        
        if not verdict.is_safe:
            with st.expander("🔎 View Critic's Analysis", expanded=True):
                st.markdown("**Issues Found:**")
                for issue in verdict.issues:
                    st.markdown(f"- {issue}")
                st.divider()
                st.markdown("**Reasoning:**")
                st.write(verdict.reasoning)
    
    st.divider()
    
    # Report Content
    st.subheader(report.facts.event_title or "Untitled Event")
    
    # Metadata row
    meta_cols = st.columns(3)
    with meta_cols[0]:
        st.metric("📅 Date", report.facts.date or "N/A")
    with meta_cols[1]:
        st.metric("📍 Venue", report.facts.venue or "N/A")
    with meta_cols[2]:
        st.metric("👥 Attendance", report.facts.attendance_count or "N/A")
    
    st.divider()
    
    st.subheader("Executive Summary")
    st.write(report.narrative.executive_summary)
    
    st.subheader("Key Takeaways")
    for item in report.narrative.key_takeaways:
        st.markdown(f"✦ {item}")
    
    st.divider()
    
    # Save as Template Option
    render_save_template_modal(report.facts)
    
    st.divider()
    
    # Action Buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Generate DOCX", use_container_width=True):
            with st.spinner("Generating document..."):
                file_stream = render_report(report)
                st.session_state["docx_stream"] = file_stream
    
    with col2:
        if st.button("🔄 Start Over", use_container_width=True):
            for key in ["stage", "facts", "final_report", "critic_verdict", "docx_stream", "selected_template"]:
                if key == "stage":
                    st.session_state[key] = "input"
                else:
                    st.session_state[key] = None
            st.rerun()
    
    # Download button (shown after generation)
    if st.session_state.get("docx_stream"):
        st.download_button(
            label="📥 Download Report",
            data=st.session_state["docx_stream"],
            file_name=f"{report.facts.event_title or 'event'}_report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
