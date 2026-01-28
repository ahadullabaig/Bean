<div align="center">

# 🫘 Bean

### AI-Powered Documentation Agent

**Transform messy event notes into polished IEEE reports in seconds.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Google AI](https://img.shields.io/badge/Gemini-2.5_Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev)

</div>

---

## ✨ What is Bean?

**Bean** is an agentic AI workflow that automates event documentation for IEEE student branches and technical chapters. It uses a sophisticated **Auditor → Ghostwriter → Critic** pipeline to ensure accurate, hallucination-free reports.

> 💡 **Not just summarization** — Bean extracts facts, drafts professional narratives, and self-corrects using chain-of-thought reasoning.

### Why Bean?

| Problem | Bean's Solution |
|---------|-----------------|
| Manual report writing takes hours | Generate reports in seconds |
| Copy-paste errors introduce mistakes | AI extracts facts with 0.0 temperature |
| Reports lack consistency | Template library ensures uniform structure |
| No way to verify AI accuracy | Built-in Critic with confidence scoring |

---

## 🚀 Key Features

### 🕵️ The Auditor (Fact Extraction)
- **Temperature 0.0** — Deterministic, strict extraction
- Parses dates, names, numbers, and lists into validated Pydantic schemas
- Self-correction loop for malformed LLM responses
- Prompt injection protection with XML delimiters

### ✍️ The Ghostwriter (Narrative Generation)
- **Temperature 0.3** — Controlled creativity
- Transforms facts into professional IEEE-style prose
- Generates executive summaries and key takeaways
- Strict adherence to source facts (no invention)

### 🔎 The Critic (Hallucination Checker)
- Compares generated report against original notes
- Returns structured `CriticVerdict` with **confidence score** (0-100%)
- Chain-of-thought reasoning for transparency
- Flags specific unsupported claims

### 📋 Event Template Library
- **5 built-in templates**: Workshop, Hackathon, Seminar, Webinar, Competition
- Create custom templates from any report
- Template defaults auto-fill extracted facts
- Usage tracking for popular templates

### 🛡️ Production-Ready Reliability
- **Exponential backoff retry** on API failures
- **Double-click protection** prevents duplicate submissions
- **Response caching** for identical inputs
- **92% test coverage** with 37 unit tests

---

## 🏗️ Architecture

Bean's power comes from its multi-agent pipeline—not a single prompt, but specialized AI roles working in sequence.

![Architecture Diagram](assets/architecture.png)

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **UI** | Streamlit | Reactive agent interface with progress stepper |
| **AI** | Google GenAI SDK | Gemini 2.5 Flash with structured output |
| **Validation** | Pydantic | Schema enforcement & self-correction |
| **Retry** | Tenacity | Exponential backoff for API resilience |
| **Documents** | docxtpl | Template-based DOCX generation |
| **Testing** | Pytest | 37 tests with 92% coverage |

---

## 📦 Installation

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

# Configure API key
echo "GEMINI_API_KEY=your_key_here" > .env

# Run the application
streamlit run app.py
```

---

## 📖 User Guide

### Step 1: Choose a Template
Select from 5 built-in event types or start from scratch.

### Step 2: Input Your Notes
Paste your raw, unstructured event notes. Example:
> "We conducted a Machine Learning Workshop on 25th January 2024. Dr. Sharma was the speaker. Around 85 students attended..."

### Step 3: Verify Extracted Facts
Review the **Smart Form** pre-filled by the Auditor. Edit any incorrect values using the intuitive grouped layout.

### Step 4: Generate & Download
Watch the Ghostwriter draft your narrative, then the Critic verifies for hallucinations. Download your polished `.docx` report.

### Step 5: Save as Template (Optional)
Save successful report structures for future use.

---

## 🧪 Testing

Bean includes a comprehensive test suite covering all core modules.

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=core --cov-report=term-missing
```

| Module | Tests | Coverage |
|--------|-------|----------|
| `auditor.py` | 8 | 95% |
| `critic.py` | 7 | 96% |
| `ghostwriter.py` | 8 | 96% |
| `renderer.py` | 14 | 100% |
| **Total** | **37** | **92%** |

---

## 📂 Project Structure

```
bean/
├── app.py                 # Main Streamlit application
├── core/                  # AI Agents
│   ├── auditor.py         # Fact extraction with self-correction
│   ├── ghostwriter.py     # Narrative generation
│   ├── critic.py          # Hallucination detection
│   ├── llm.py             # Gemini client with retry logic
│   ├── renderer.py        # DOCX document generation
│   └── templates.py       # Event template library
├── models/
│   └── schemas.py         # Pydantic schemas (EventFacts, CriticVerdict, etc.)
├── ui/
│   ├── components.py      # Progress stepper, badges, template selector
│   └── handlers.py        # Input processing with caching
├── templates/             # Custom user templates (JSON)
├── tests/                 # Pytest test suite
│   ├── conftest.py        # Fixtures and mocks
│   ├── test_auditor.py
│   ├── test_critic.py
│   ├── test_ghostwriter.py
│   └── test_renderer.py
└── assets/                # Static images
```

---

<div align="center">

**Built by [Ahad](https://github.com/ahadullabaig) for IEEE RIT-B**

</div>
