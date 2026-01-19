# 🫘 Bean: The AI Event Reporter

**Turn messy notes into professional IEEE event reports in seconds.**

Bean is an AI-powered documentation agent designed for the IEEE Student Branch. It takes rough, unstructured input (text or audio notes) and "ghostwrites" a structured, production-ready `.docx` report. It prioritizes **accuracy** over creativity for facts, but **professionalism** for narrative.

## ✨ Key Features

-   **🕵️ The Auditor (Fact Extraction)**: Uses a strict, low-temperature LLM (Gemini 2.0 Flash) to act as a data entry clerk. It extracts strict facts (Date, Venue, Attendance) and refuses to guess missing info.
-   **👻 The Ghostwriter (Narrative Synthesis)**: A creative AI layer that turns bullet points into professional executive summaries and key takeaways, adhering to academic tone.
-   **📝 Smart Forms**: If the Auditor misses a fact (e.g., you forgot to mention the date), Bean dynamically generates a UI form asking *only* for what's missing.
-   **⚖️ The Critic (Hallucination Check)**: A final safety net that compares the generated report against your original notes. If the AI "invented" a fact (like a fake specific number), the Critic flags it instantly.
-   **📄 Production DOCX**: Generates a perfectly formatted Word document (`master_template.docx`) ready for submission.

## 🏗️ Architecture

Bean uses a **Dual-Schema Architecture** to separate truth from style:

1.  **Fact Layer (`EventFacts`)**: Strict Pydantic model. If it's not in the text, it's `null`.
2.  **Narrative Layer (`EventNarrative`)**: Professional prose derived *only* from the Facts.

**The Pipeline:**
`Input` -> `Auditor` -> `Smart Form (Human Loop)` -> `Ghostwriter` -> `Critic` -> `DOCX Renderer`

## 🚀 Getting Started

### Prerequisites

-   Python 3.10+
-   A Google Gemini API Key

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-repo/bean.git
    cd bean
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Environment**:
    Create a `.env` file in the root directory:
    ```env
    GEMINI_API_KEY=AIzaSy...your_api_key...
    ```

4.  **Create the Template**:
    Run the script to generate the base Word template:
    ```bash
    python3 scripts/create_template.py
    ```

### Usage

Run the Streamlit application:

```bash
streamlit run app.py
```

1.  **Feed the Bean**: Paste your rough notes or use the audio input.
2.  **Verify**: The Auditor will show you what it found. Fill in any blanks.
3.  **Download**: Get your `.docx` report.

## 📂 Project Structure

```
bean/
├── app.py                 # Main Streamlit Application
├── core/                  # Intelligence Engine
│   ├── auditor.py         # Fact Extraction Logic
│   ├── ghostwriter.py     # Narrative Generation Logic
│   ├── critic.py          # Hallucination Checker
│   ├── llm.py             # Gemini Wrapper & Schema Cleaner
│   └── renderer.py        # DOCX Generation Logic
├── models/
│   └── schemas.py         # Pydantic Data Models
├── ui/
│   ├── components.py      # UI Widgets (Smart Form)
│   └── handlers.py        # Input Processors
└── utils/
    └── constants.json     # Static Knowledge (Venues, Names)
```

## 🔧 Troubleshooting

**Error: `ValueError: Unknown field for Schema: default`**
This is a known issue with the `google-generativeai` SDK handling Pydantic `default` values. We have patched this in `core/llm.py` with a custom `get_clean_schema` function. If you encounter this, ensure you are using the latest code from this repo.

## 🤝 Contributing

1.  Fork the repo.
2.  Create a feature branch.
3.  Submit a Pull Request.

---
*Built with ❤️ for the IEEE Student Branch.*
