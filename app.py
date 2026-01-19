import streamlit as st
import json
import os
from ui.handlers import handle_text_process, handle_audio_process
from ui.components import render_smart_form
from core.ghostwriter import generate_narrative
from models.schemas import EventFacts, FullReport

# Page Config
st.set_page_config(page_title="Bean: AI Documentation Agent", page_icon="🫘")

# Session State Initialization
if "stage" not in st.session_state:
    st.session_state["stage"] = "input" # input -> verify -> report
if "facts" not in st.session_state:
    st.session_state["facts"] = None
if "raw_text_context" not in st.session_state:
    st.session_state["raw_text_context"] = ""
if "final_report" not in st.session_state:
    st.session_state["final_report"] = None

# Sidebar
with st.sidebar:
    st.image("assets/ieee_header.png", use_column_width=True) if os.path.exists("assets/ieee_header.png") else None
    st.title("Settings")
    api_key = st.text_input("Gemini API Key", type="password")
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key

st.title("🫘 Bean: The Event Reporter")
st.markdown("Turn your messy notes into professional IEEE reports.")

# --- STAGE 1: INPUT ---
if st.session_state["stage"] == "input":
    st.header("Step 1: Feed the Bean")
    
    input_method = st.radio("Input Method", ["Text Notes", "Audio Recording"])
    
    if input_method == "Text Notes":
        raw_text = st.text_area("Paste your event notes here...", height=200)
        if st.button("Process Notes"):
            if not raw_text.strip():
                st.error("Please enter some text.")
            else:
                st.session_state["raw_text_context"] = raw_text
                st.session_state["facts"] = handle_text_process(raw_text)
                st.session_state["stage"] = "verify"
                st.rerun()

    elif input_method == "Audio Recording":
        audio_val = st.audio_input("Record your notes")
        if audio_val:
            st.info("Audio received. Processing...")
            # Placeholder for audio logic
            # facts = handle_audio_process(audio_val)
            # if facts:
            #     st.session_state["facts"] = facts
            #     st.session_state["stage"] = "verify"
            #     st.rerun()
            st.warning("Audio processing is under construction. Please use text.")

# --- STAGE 2: VERIFICATION (Smart Form) ---
elif st.session_state["stage"] == "verify":
    st.header("Step 2: The Auditor's Check")
    
    # Render the Smart Form
    # The component returns the updated facts object upon submission
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
            from core.critic import check_consistency
            # Reconstruct text for critic
            report_text = f"{report.facts}\n\n{report.narrative.executive_summary}\n\n{report.narrative.key_takeaways}"
            warnings = check_consistency(st.session_state["raw_text_context"], report_text)
            
            st.session_state["final_report"] = report
            st.session_state["warnings"] = warnings
            st.session_state["stage"] = "report"
            st.rerun()

# --- STAGE 3: REPORT PREVIEW ---
elif st.session_state["stage"] == "report":
    st.header("Step 3: Your Report")
    
    warnings = st.session_state.get("warnings", [])
    if warnings:
        st.error("⚠️ The Critic found potential inconsistencies:")
        for w in warnings:
            st.write(f"- {w}")
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
    
    # Generate and Download
    if st.button("Generate .docx"):
        from core.renderer import render_report
        file_stream = render_report(report)
        st.download_button(
            label="Download DOCX",
            data=file_stream,
            file_name=f"{report.facts.event_title or 'event'}_report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    
    if st.button("Start Over"):
        st.session_state["stage"] = "input"
        st.session_state["facts"] = None
        st.session_state["final_report"] = None
        st.rerun()
