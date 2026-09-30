# FinEval — Financial AI Response Quality & Prompt Operations Lab

> A specialized internal operations platform for systematically testing, diagnosing, improving, and regression-testing financial LLM assistants.

---

## 1. Practical Problem Addressed
When customer-facing LLMs are deployed in financial services (payments, lending, insurance, wealth), conventional chat evaluations fail to protect operational integrity. Generative models hallucinate transaction outcomes, give unauthorized stock recommendations, fail to freeze compromised accounts during active fraud, and lose context across multi-turn interactions.

**FinEval** implements a closed-loop engineering system:
```text
Synthetic Customer Scenario
           ↓
Prompt Version (V1 → V2 → V3 → V4)
           ↓
LLM Execution (Live or Mock Provider)
           ↓
Multi-Layer Automated Evaluation (Layers 1-4)
           ↓
Failure Detection & Taxonomy Mapping (F1..F8)
           ↓
Root-Cause Diagnosis & Prompt Modification
           ↓
Regression Testing & Benchmark Uplift Audit
```

---

## 2. Key Capabilities
- **200 Benchmark Scenarios:** Balanced across Standard, Ambiguous, Edge Cases, Multi-turn, Contradictory, Hallucination Traps, Adversarial Injection, and Escalation-Sensitive queries.
- **Controlled Knowledge Base:** 50 synthetic operational ground truth facts covering UPI, EMIs, insurance claims, and mutual fund operations.
- **Prompt Versioning & Unified Diff:** Side-by-side visual diffing comparing instructions between V1, V2, V3, and V4.
- **Multi-Layer Defensive Evaluation:**
  - *Layer 1:* Schema & decodability validation.
  - *Layer 2:* Deterministic rule engine (`must_include`, `must_not_include`, format checks).
  - *Layer 3:* Semantic alignment, context grounding, and multi-turn reference retention.
  - *Layer 4:* LLM-as-judge scoring across 7 weighted dimensions with Pydantic JSON validation.
- **Traceable Failure Taxonomy (F1..F8):** Hallucination, Instruction Failure, Inconsistency, Context Loss, Irrelevance, Unsupported Certainty, Formatting Failure, Routing/Escalation Failure.
- **Interactive Prompt Debugger:** Modify prompt instructions in real-time and retest immediately against specific failing scenarios.
- **Failure Fingerprint:** Trace a single scenario's behavior across all prompt iterations to prove whether a prompt change actually solved the root cause.
- **Automated vs Manual Audit Calibration:** 30-case representative calibration set exposing agreement and divergence.
- **SQL Analytics:** 6 production-grade SQL scripts featuring CTEs and window functions.
- **Stable CSV Exports:** Complete exportability for BI dashboards and audit pipelines.

---

## 3. Technology Stack
- **Core:** Python 3.11+, PostgreSQL / SQLite, SQLAlchemy 2.0, Pydantic v2, PyYAML, Pandas.
- **Application Console:** Streamlit with custom analyst design theme.
- **Visualization:** Plotly.
- **Quality & Testing:** Pytest, Ruff.
- **Containerization:** Docker Compose.

---

## 4. Quickstart & Installation

### Local Setup
```bash
# Clone the repository and navigate into FinEval
cd FinEval

# Create and activate virtual environment (optional)
python -m venv venv
# Windows: venv\Scripts\activate | Unix: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
By default, `DATABASE_URL=sqlite:///./data/fineval.db` and `LLM_PROVIDER=mock`, allowing the full application to run without external dependencies or paid API keys.

For Docker PostgreSQL:
```bash
docker compose up -d
# Update DATABASE_URL in .env to:
# postgresql+psycopg://fineval_user:fineval_password@localhost:5432/fineval_db
```

---

## 5. Running FinEval

### 1. Seed Database & Initial Benchmark Runs
```bash
python -m scripts.seed_database
```
Seeds 50 knowledge facts, 200 scenarios, 4 prompt versions, change ledger, and executes baseline core benchmark runs.

### 2. Run Smoke Benchmark
```bash
python -m scripts.run_smoke_test
```

### 3. Launch Streamlit Analyst Console
```bash
python -m streamlit run app/streamlit_app.py
```
Open your browser at `http://localhost:8501`.

### 4. Run Test Suite & Linting
```bash
python -m pytest -v
python -m ruff check .
```

---

## 6. Repository Layout
```text
FinEval/
├── app/                  # Streamlit Analyst Console & Page Views
│   ├── streamlit_app.py  # Main application entry point
│   ├── components/       # Custom cards, badges, and CSS
│   └── pages/            # 7 Dedicated operational console views
├── config/               # Scoring weights, thresholds, and provider configs
├── data/                 # Benchmark scenarios, knowledge base, prompt versions
├── docs/                 # Architecture, evaluation methodology, failure taxonomy
├── prompts/              # System prompt files (V1, V2, V3, V4, Judge)
├── reports/              # Executive audit report (Markdown and PDF)
├── scripts/              # Seed, validation, smoke test, and CLI benchmark tools
├── sql/                  # 6 Production analytical SQL queries
├── src/                  # Application domain, engine, llm, database, and services
└── tests/                # Unit and integration test suite
```

---

## 7. Absolute Integrity Notice
All scenarios, user profiles, transaction reference numbers, accounts, and policies in this repository are **explicitly synthetic and fictional**. They do not represent real-world customer data or proprietary policies of any organization. FinEval is an operational quality evaluation laboratory.
