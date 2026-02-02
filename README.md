<div align="center">

# 🫘 Bean

### AI-Powered Documentation Agent

**Transform messy event notes into polished IEEE reports in seconds.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Google AI](https://img.shields.io/badge/Gemini-2.5_Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev)

</div>

---

## What is Bean?

**Bean** is an agentic AI workflow that automates event documentation for IEEE student branches and technical chapters. It uses a sophisticated **Auditor → Ghostwriter → Critic** pipeline to ensure accurate, hallucination-free reports.

> **Not just summarization** — Bean extracts facts, drafts professional narratives, and self-corrects using chain-of-thought reasoning.

### Why Bean?

| Problem | Bean's Solution |
|---------|-----------------|
| Manual report writing takes hours | Generate reports in seconds |
| Copy-paste errors introduce mistakes | AI extracts facts with 0.0 temperature |
| Reports lack consistency | Template library ensures uniform structure |
| No way to verify AI accuracy | Built-in Critic with confidence scoring |

---

## Key Features

### The Auditor (Fact Extraction)
- **Temperature 0.0** — Deterministic, strict extraction
- Parses dates, names, numbers, and lists into validated Pydantic schemas
- Self-correction loop for malformed LLM responses
- Prompt injection protection with XML delimiters

### The Ghostwriter (Narrative Generation)
- **Temperature 0.3** — Controlled creativity
- Transforms facts into professional IEEE-style prose
- Generates executive summaries and key takeaways
- Strict adherence to source facts (no invention)

### The Critic (Hallucination Checker)
- Compares generated report against original notes
- Returns structured `CriticVerdict` with **confidence score** (0-100%)
- Chain-of-thought reasoning for transparency
- Flags specific unsupported claims

### Event Template Library
- **5 built-in templates**: Workshop, Hackathon, Seminar, Webinar, Competition
- Create custom templates from any report
- Template defaults auto-fill extracted facts
- Usage tracking for popular templates

### Multiple Input Methods
- **Text Notes** — Paste or type your event notes directly
- **Audio Recording** — Record notes and let Gemini transcribe and extract facts

### Export Options
- **DOCX** — Template-based Word document generation
- **PDF** — Native PDF export with professional formatting

### Session History
- View all reports generated in current session
- Load and revisit previous reports from sidebar
- Quick access to confidence scores and metadata

### Production-Ready Reliability
- **Exponential backoff retry** on API failures
- **Double-click protection** prevents duplicate submissions
- **Response caching** for identical inputs
- **Input validation** with character limits
- **Dark mode** enabled by default
- **68 unit tests** across all modules

---

## Architecture

Bean's power comes from its multi-agent pipeline—not a single prompt, but specialized AI roles working in sequence.

![Architecture Diagram](assets/architecture.png)

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **UI** | Streamlit | Reactive agent interface with progress stepper |
| **AI** | Google GenAI SDK | Gemini 2.5 Flash with structured output |
| **Validation** | Pydantic | Schema enforcement and self-correction |
| **Retry** | Tenacity | Exponential backoff for API resilience |
| **Documents** | docxtpl, reportlab | DOCX and PDF generation |
| **Testing** | Pytest | 68 tests with 52% coverage |

---

## Installation

### Prerequisites
- Python 3.10+
- Google Gemini API Key ([Get one here](https://aistudio.google.com/))

### Quick Start

```bash
# Clone the repository
git clone https://github.com/ahadullabaig/bean.git
cd bean

# Install dependencies
pip install -r requirements.txt

# Configure API key (optional - can enter in app)
echo "GEMINI_API_KEY=your_key_here" > .env

# Run the application
streamlit run app.py
```

---

## User Guide

### Step 1: Choose a Template
Select from 5 built-in event types or start from scratch.

### Step 2: Input Your Notes
Choose between two input methods:
- **Text Notes**: Paste your raw, unstructured event notes
- **Audio Recording**: Record your notes directly in the browser

Example input:
> "We conducted a Machine Learning Workshop on 25th January 2024. Dr. Sharma was the speaker. Around 85 students attended..."

### Step 3: Verify Extracted Facts
Review the **Smart Form** pre-filled by the Auditor. Edit any incorrect values including:
- Event details (title, date, venue)
- People (coordinators, judges, speakers)
- Winners (with editable team details for competitions)

### Step 4: Generate and Download
Watch the Ghostwriter draft your narrative, then the Critic verifies for hallucinations. Download your report as:
- **DOCX** — Editable Word document
- **PDF** — Print-ready format

### Step 5: Save as Template (Optional)
Save successful report structures for future use.

---

## Testing

Bean includes a comprehensive test suite covering all core modules.

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=core --cov=ui --cov=models --cov-report=term-missing
```

| Module | Tests | Coverage |
|--------|-------|----------|
| `auditor.py` | 8 | 73% |
| `critic.py` | 7 | 79% |
| `ghostwriter.py` | 8 | 76% |
| `renderer.py` | 14 | 44% |
| `templates.py` | 10 | 97% |
| `handlers.py` | 8 | 69% |
| `llm.py` | 12 | 82% |
| `schemas.py` | - | 100% |
| **Total** | **68** | **52%** |

---

## 📂 Project Structure

```
bean/
├── app.py                 # Main Streamlit application
├── pyproject.toml         # Project metadata and dependencies
├── requirements.txt       # Pip dependencies
├── core/                  # AI Agents
│   ├── auditor.py         # Fact extraction with self-correction
│   ├── ghostwriter.py     # Narrative generation
│   ├── critic.py          # Hallucination detection
│   ├── llm.py             # Gemini client with retry logic
│   ├── renderer.py        # DOCX and PDF generation
│   └── templates.py       # Event template library
├── models/
│   └── schemas.py         # Pydantic schemas (EventFacts, CriticVerdict, etc.)
├── ui/
│   ├── components.py      # Progress stepper, badges, template selector
│   └── handlers.py        # Text and audio input processing
├── templates/             # Custom user templates (JSON)
├── tests/                 # Pytest test suite
│   ├── conftest.py        # Fixtures and mocks
│   ├── test_auditor.py
│   ├── test_critic.py
│   ├── test_ghostwriter.py
│   ├── test_renderer.py
│   ├── test_templates.py
│   ├── test_handlers.py
│   └── test_llm.py
├── assets/                # Static images
└── .streamlit/
    └── config.toml        # Dark mode theme configuration
```

---

<div align="center">

**Built by [Ahad](https://github.com/ahadullabaig) for IEEE RIT-B**

</div>
