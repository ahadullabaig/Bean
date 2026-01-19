Master Plan — Bean: AI Documentation Agent for IEEE

Executive summary

Bean is an AI-assisted documentation agent that converts short, often vague event notes into production-quality event reports (DOCX) for the IEEE student club. The goal: reduce humans' documentation time from days to minutes while keeping accuracy, traceability, and low hallucination risk.

This master plan outlines the product goals, system architecture, data schema, extraction pipeline, anti-hallucination strategy, testing & monitoring, deployment, security, cost controls, and an implementation roadmap to produce a robust, production-ready system.

Goals & success criteria

Primary goals

Produce readable, accurate event documentation (executive summary, logistics, attendance, speakers, highlights, images) from short raw notes.

Maintain traceability: every extracted fact must be linkable to the original input text (provenance).

Minimize hallucinations: prefer null/UNKNOWN over inventing facts.

High-level architecture

Frontend: Streamlit for early MVP.

API / Backend: FastAPI (Python) to handle preprocessing, model orchestration, job management, and DOCX generation.

Model Providers: Primary = Gemini (structured output), Verifier = alternate provider/model.

Monitoring & Telemetry: Prometheus + Grafana or hosted logging (Sentry, Datadog) to track latency, costs, and disagreement rates.

### **Phase 1: The Foundation (Data Modeling & Static Context)**

Before writing logic, we must define the "Truth." We separate *hard facts* (which must be exact) from *narrative* (which must be professional).

#### **Step 1.1: The "Context Vault" (Static Knowledge)**

**What:** Create a JSON file (`constants.json`) containing immutable details about your IEEE branch.
**How:**

```json
// utils/constants.json
{
  "organization_name": "IEEE RIT Student Branch",
  "branch_counselor": "Dr. [Name]",
  "standard_venues": ["Apex Block Auditorium", "LHC Seminar Hall 1"],
  "logos": {"header": "assets/ieee_header.png"}
}

```

**Why:**

* **Efficiency:** Stops the agent from asking redundant questions like "Who is the counselor?" or "What college is this?"
* **Accuracy:** Ensures names and designations are always spelled correctly.

#### **Step 1.2: Dual-Schema Architecture**

**What:** Split your Pydantic models into two distinct layers: `FactLayer` and `NarrativeLayer`.
**How:**

```python
# models/schemas.py

# Layer 1: The Auditor's Domain (Strict Facts)
class EventFacts(BaseModel):
    event_title: Optional[str]
    date: Optional[str]
    speaker_name: Optional[str]
    # "Unknown" is better than a guess
    attendance_count: Optional[int] 
    
# Layer 2: The Ghostwriter's Domain (Professional Prose)
class EventNarrative(BaseModel):
    executive_summary: str  # Generated based on facts
    key_takeaways: List[str]
    
# The Final Container
class FullReport(BaseModel):
    facts: EventFacts
    narrative: EventNarrative
    confidence_score: float

```

**Why:** Prevents the LLM from mixing up "guessing a missing date" (bad) with "creatively phrasing a summary" (good).

---

### **Phase 2: The Intelligence Engine (Backend Logic)**

This is the core differentiator. Instead of one big prompt, we use a pipeline.

#### **Step 2.1: Brain 1 - "The Auditor" (Fact Extraction)**

**What:** A strict, low-temperature LLM call that extracts *only* explicit data points.
**How:**

* **Input:** Raw user notes + Audio transcript.
* **Temperature:** `0.0` (Maximum Determinism).
* **System Prompt:** "You are a data entry clerk. Extract fields strictly from the text. If a piece of information (like venue or date) is not explicitly stated, return `null`. Do not infer."

#### **Step 2.2: Brain 2 - "The Ghostwriter" (Narrative Synthesis)**

**What:** A creative, medium-temperature LLM call that writes the professional prose.
**How:**

* **Input:** The *Clean Facts* from Step 2.1 + Original Notes (for tone context).
* **Temperature:** `0.3` (Controlled Creativity).
* **Pseudocode:**
```python
def generate_narrative(facts, raw_notes):
    prompt = f"""
    Write an Executive Summary for an IEEE report based strictly on these facts: {facts}.
    Use the tone from these notes: {raw_notes}.
    RULES:
    1. Use professional, academic English.
    2. Do NOT add new facts (like numbers or names) that are not in the 'facts' dictionary.
    3. Transform "good event" -> "The event successfully engaged the student community..."
    """
    return call_gemini(prompt, model=EventNarrative)

```



**Why:** This ensures the "story" matches the "data." The Ghostwriter cannot invent a speaker because it is constrained to write about the speaker found by the Auditor.

---

### **Phase 3: The Interaction Layer (Frontend UI)**

The UI must handle the "Human-in-the-Loop" seamlessly.

#### **Step 3.1: Audio-First Input**

**What:** Add a microphone button as the primary input method.
**How:** Use `st.audio_input` (Streamlit). Send the audio file directly to Gemini 2.5 Flash (it handles audio natively, which is cheaper/faster than Whisper).
**Why:** Users are lazy. "We met at the lab and built a drone" (typed) vs. "So we met at the lab around 4 PM, Dr. Smith was there, and we built a quadcopter using Arduino..." (spoken). You get 5x more detail from audio.

#### **Step 3.2: The "Smart Form" (Validation)**

**What:** Dynamic rendering of input fields based on missing data.
**How:**

* **Logic:** After the Auditor runs, check which required fields are `null`.
* **UI:** Instead of a chat message ("What was the date?"), render a native Streamlit form.
```python
# pseudocode
if not report.facts.date:
    report.facts.date = st.date_input("I missed the date. When was it?")
if not report.facts.venue:
    report.facts.venue = st.selectbox("Where was it?", constants["standard_venues"])

```



**Why:** Clicking a calendar is faster than typing "October 12th, 2024" in a chat. It reduces friction.

---

### **Phase 4: The Output Factory (Document Generation)**

We need to ensure the final file doesn't break.

#### **Step 4.1: The ViewModel Sanitizer**

**What:** A middleware layer that cleans data before it touches the Word template.
**How:**

* **Never** pass the raw Pydantic model to `docxtpl`.
* Create a function `prepare_for_rendering(report)`:
* Converts `None` to "N/A".
* Formats dates (`2023-10-12` -> `October 12, 2023`).
* Ensures lists are not empty (adds a placeholder bullet if list is empty).
**Why:** Jinja2 templates inside Word docs are fragile. If they encounter a `null` value where they expect a string, the generated .docx will be corrupted and won't open.



#### **Step 4.2: Template Management**

**What:** Use `docxtpl` with Jinja2 tags.
**How:**

* Create `master_template.docx` with tags like `{{ executive_summary }}`.
* Use conditional blocks for optional sections:
```jinja2
{% if winners %}
## Competition Results
{% for w in winners %}- {{ w.team }}: {{ w.position }}{% endfor %}
{% endif %}

```



---

### **Phase 5: The Safety Net (The "Critic")**

This is your "Zero Hallucination" guarantee.

#### **Step 5.1: The Consistency Check**

**What:** A final, invisible AI pass before the user sees the result.
**How:**

* **Prompt:** "Compare the Input Text vs. The Generated Report. List any entity (name, number, date) present in the Report that is NOT in the Input. If found, return Alert."
* **UI Action:** If the Critic flags something, highlight it in **Red** in the preview with a tooltip: *"Verified source not found. Please check."*
**Why:** Trust. If the AI hallucinates once and you don't catch it, users will stop trusting it. This automated double-check catches 99% of errors.
