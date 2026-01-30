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
from core.llm import reset_client, RateLimitError, AuthenticationError
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
        "api_key": None,  # User's API key (session-scoped, secure)
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()


# --- API KEY GATE ---
# Always require user to enter API key per session (stored in session state, not os.environ)
if not st.session_state.get("api_key"):
    # Centered welcome screen
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists("assets/ieee_header.png"):
            st.image("assets/ieee_header.png", use_container_width=True)
        
        st.title("🫘 Bean")
        st.markdown("*Turn your messy notes into professional IEEE reports.*")
        
        st.divider()
        
        st.markdown("### 🔑 Enter Your API Key")
        st.caption("Get your free API key from [Google AI Studio](https://aistudio.google.com/apikey)")
        
        api_key_input = st.text_input(
            "Gemini API Key", 
            type="password",
            placeholder="Paste your API key here...",
            label_visibility="collapsed"
        )
        
        if st.button("🚀 Get Started", use_container_width=True, type="primary"):
            if api_key_input.strip():
                # Store in session state ONLY (not os.environ - that's shared!)
                st.session_state["api_key"] = api_key_input.strip()
                st.rerun()
            else:
                st.error("Please enter a valid API key.")
        
        st.divider()
        st.caption("🔒 Your API key is stored only for this session and never saved.")
    
    st.stop()  # Don't render the rest of the app


# --- SIDEBAR (shown after API key is set) ---
with st.sidebar:
    if os.path.exists("assets/ieee_header.png"):
        st.image("assets/ieee_header.png", use_container_width=True)
    st.title("⚙️ Settings")
    
    # Show current API key status with option to change
    st.success("✓ API Key Set")
    if st.button("🔄 Change API Key", use_container_width=True):
        # Clear from session state (the only place it's stored)
        old_key = st.session_state.get("api_key")
        st.session_state["api_key"] = None
        reset_client(old_key)  # Clear cached client for this key
        st.rerun()
    
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
            elif not st.session_state.get("api_key"):
                st.error("⚠️ Please enter your Gemini API Key first.")
            else:
                st.session_state["processing"] = True
                
                try:
                    st.session_state["raw_text_context"] = raw_text
                    with agent_spinner("Auditor", "Extracting facts from your notes..."):
                        extracted_facts = handle_text_process(raw_text, st.session_state["api_key"])
                    
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
                    st.rerun()
                except RateLimitError as e:
                    st.error(f"⏳ {e.message}")
                    st.info("💡 **Tip:** The free tier allows ~15-20 requests/minute. Wait a moment and try again.")
                except AuthenticationError as e:
                    st.error(f"🔑 {e.message}")
                    st.warning("Your API key appears to be invalid. Please check that you've copied the full key from [Google AI Studio](https://aistudio.google.com/apikey).")
                    if st.button("🔄 Enter a New API Key"):
                        old_key = st.session_state.get("api_key")
                        st.session_state["api_key"] = None
                        st.session_state["stage"] = "input"  # Go back to API gate
                        reset_client(old_key)  # Clear cached invalid client
                        st.rerun()
                except ValueError as e:
                    st.error(f"❌ Processing failed: {e}")
                finally:
                    st.session_state["processing"] = False

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
        
        try:
            # Trigger Ghostwriter
            with agent_spinner("Ghostwriter", "Drafting the narrative..."):
                narrative = generate_narrative(
                    st.session_state["facts"], 
                    st.session_state["raw_text_context"],
                    api_key=st.session_state["api_key"]
                )
            
            # Combine into Full Report
            report = FullReport(
                facts=st.session_state["facts"],
                narrative=narrative,
                confidence_score=1.0
            )
            
            # Critic Pass - only check AI-generated narrative, not user-verified facts
            # The narrative is what the AI created; facts are already human-verified
            with agent_spinner("Critic", "Verifying for hallucinations..."):
                # Only check executive summary and key takeaways (AI-generated)
                narrative_text = f"""Executive Summary:
{report.narrative.executive_summary}

Key Takeaways:
{chr(10).join(f'- {t}' for t in report.narrative.key_takeaways)}"""
                
                # Combine original notes + user-verified facts as the source of truth
                verified_facts = st.session_state["facts"]
                source_text = f"""{st.session_state["raw_text_context"]}

--- USER-VERIFIED FACTS ---
Event: {verified_facts.event_title or 'N/A'}
Date: {verified_facts.date or 'N/A'}
Venue: {verified_facts.venue or 'N/A'}
Speaker: {verified_facts.speaker_name or 'N/A'}
Organizer: {verified_facts.organizer or 'N/A'}
Attendance: {verified_facts.attendance_count or 'N/A'}
Mode: {verified_facts.mode or 'N/A'}
Target Audience: {verified_facts.target_audience or 'N/A'}
Volunteer Count: {verified_facts.volunteer_count or 'N/A'}
Student Coordinators: {', '.join(verified_facts.student_coordinators) if verified_facts.student_coordinators else 'N/A'}
Faculty Coordinators: {', '.join(verified_facts.faculty_coordinators) if verified_facts.faculty_coordinators else 'N/A'}
Agenda: {verified_facts.agenda or 'N/A'}"""
                
                verdict = check_consistency(source_text, narrative_text, api_key=st.session_state["api_key"])
            
            # Update confidence score from critic
            report.confidence_score = verdict.confidence
            
            st.session_state["final_report"] = report
            st.session_state["critic_verdict"] = verdict
            st.session_state["stage"] = "report"
            st.rerun()
        except RateLimitError as e:
            st.error(f"⏳ {e.message}")
            st.info("💡 **Tip:** The free tier allows ~15-20 requests/minute. Wait a moment and try again.")
        except AuthenticationError as e:
            st.error(f"🔑 {e.message}")
            st.warning("Your API key appears to be invalid. Please check that you've copied the full key from [Google AI Studio](https://aistudio.google.com/apikey).")
            if st.button("🔄 Enter a New API Key"):
                old_key = st.session_state.get("api_key")
                st.session_state["api_key"] = None
                st.session_state["stage"] = "input"  # Go back to API gate
                reset_client(old_key)  # Clear cached invalid client
                st.rerun()
        except ValueError as e:
            st.error(f"❌ Report generation failed: {e}")


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
