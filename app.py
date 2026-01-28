"""
Bean: AI Documentation Agent - Main Application

A Streamlit app that transforms messy event notes into professional IEEE reports
using a pipeline of specialized AI agents: Auditor → Ghostwriter → Critic.
"""
import streamlit as st
import hashlib
import os

# Clean imports at top level
from core.critic import check_consistency
from core.ghostwriter import generate_narrative
from core.renderer import render_report
from ui.handlers import handle_text_process, handle_audio_process
from ui.components import render_smart_form
from models.schemas import EventFacts, FullReport


# Page Config
st.set_page_config(page_title="Bean: AI Documentation Agent", page_icon="🫘")


# --- SESSION STATE INITIALIZATION ---
def init_session_state():
    """Initialize all session state variables with defaults."""
    defaults = {
        "stage": "input",  # input -> verify -> report
        "facts": None,
        "raw_text_context": "",
        "final_report": None,
        "critic_verdict": None,
        "processing": False,  # Double-click protection flag
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()


# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("assets/ieee_header.png"):
        st.image("assets/ieee_header.png", use_column_width=True)
    st.title("Settings")
    api_key = st.text_input("Gemini API Key", type="password")
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key


# --- MAIN UI ---
st.title("🫘 Bean: The Event Reporter")
st.markdown("Turn your messy notes into professional IEEE reports.")


# --- STAGE 1: INPUT ---
if st.session_state["stage"] == "input":
    st.header("Step 1: Feed the Bean")
    
    input_method = st.radio("Input Method", ["Text Notes", "Audio Recording"])
    
    if input_method == "Text Notes":
        raw_text = st.text_area("Paste your event notes here...", height=200)
        
        # Double-click protected button
        process_btn = st.button(
            "Process Notes", 
            disabled=st.session_state.get("processing", False)
        )
        
        if process_btn and not st.session_state.get("processing"):
            if not raw_text.strip():
                st.error("Please enter some text.")
            else:
                # Set processing flag to prevent double-clicks
                st.session_state["processing"] = True
                
                try:
                    st.session_state["raw_text_context"] = raw_text
                    st.session_state["facts"] = handle_text_process(raw_text)
                    st.session_state["stage"] = "verify"
                finally:
                    st.session_state["processing"] = False
                    
                st.rerun()

    elif input_method == "Audio Recording":
        audio_val = st.audio_input("Record your notes")
        if audio_val:
            st.info("Audio received. Processing...")
            st.warning("Audio processing is under construction. Please use text.")


# --- STAGE 2: VERIFICATION (Smart Form) ---
elif st.session_state["stage"] == "verify":
    st.header("Step 2: The Auditor's Check")
    
    # Render the Smart Form
    updated_facts = render_smart_form(st.session_state["facts"])
    
    if updated_facts:
        st.session_state["facts"] = updated_facts
        
        # Trigger Ghostwriter
        with st.spinner("The Ghostwriter is drafting the narrative..."):
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
            
            # --- CRITIC PASS ---
            with st.spinner("The Critic is verifying the report..."):
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
    st.header("Step 3: Your Report")
    
    # Display Critic verdict with confidence
    verdict = st.session_state.get("critic_verdict")
    if verdict:
        # Confidence badge with color coding
        conf_color = "green" if verdict.confidence > 0.8 else "orange" if verdict.confidence > 0.5 else "red"
        st.markdown(f"""
        <div style='margin-bottom: 1rem;'>
            <span style='background:{conf_color}; color:white; padding:4px 12px; border-radius:4px; font-weight:bold;'>
                Confidence: {verdict.confidence:.0%}
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        if not verdict.is_safe:
            st.error("⚠️ The Critic found potential inconsistencies:")
            for issue in verdict.issues:
                st.write(f"- {issue}")
            with st.expander("Critic's Reasoning"):
                st.write(verdict.reasoning)
        else:
            st.success("✅ The Critic approved this report (Zero Hallucinations detected).")
    
    report: FullReport = st.session_state["final_report"]
    
    st.subheader(report.facts.event_title or "Untitled Event")
    st.markdown(f"**Date:** {report.facts.date} | **Venue:** {report.facts.venue}")
    st.markdown(f"**Attendance:** {report.facts.attendance_count}")
    
    st.divider()
    
    st.subheader("Executive Summary")
    st.write(report.narrative.executive_summary)
    
    st.subheader("Key Takeaways")
    for item in report.narrative.key_takeaways:
        st.markdown(f"- {item}")
    
    st.divider()
    
    # Generate and Download - two-step to avoid nested buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Generate .docx"):
            file_stream = render_report(report)
            st.session_state["docx_stream"] = file_stream
    
    # Show download button if stream is ready
    if st.session_state.get("docx_stream"):
        with col1:
            st.download_button(
                label="📥 Download DOCX",
                data=st.session_state["docx_stream"],
                file_name=f"{report.facts.event_title or 'event'}_report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    
    with col2:
        if st.button("🔄 Start Over"):
            # Clear all session state
            for key in ["stage", "facts", "final_report", "critic_verdict", "docx_stream"]:
                if key == "stage":
                    st.session_state[key] = "input"
                else:
                    st.session_state[key] = None
            st.rerun()
