# FinEval — Financial AI Response Quality & Prompt Operations Lab

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite_%26_PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](src/database/)
[![Tests](https://img.shields.io/badge/Tests-229_Passing-2EA44F?style=for-the-badge&logo=pytest&logoColor=white)](tests/)
[![Power BI](https://img.shields.io/badge/Power_BI-Ready-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](data/powerbi/)
[![Excel Model](https://img.shields.io/badge/Excel-Scenario_Model-107C41?style=for-the-badge&logo=microsoftexcel&logoColor=white)](data/fineval_scenario_model.xlsx)
[![Author](https://img.shields.io/badge/Author-Hriday_Singh_Sobti-0F172A?style=for-the-badge&logo=github&logoColor=white)](https://github.com/hriday-sobti)

## Deliverables

* **Interactive Streamlit Decision Workbench**: Launch locally via `python -m streamlit run app/streamlit_app.py`
* **Executive Evaluation Report (PDF)**: [`reports/FinEval_Evaluation_Report.pdf`](reports/FinEval_Evaluation_Report.pdf)
* **Executive Evaluation Report (Markdown)**: [`reports/FinEval_Evaluation_Report.md`](reports/FinEval_Evaluation_Report.md)
* **Excel Scenario & Sensitivity Model**: [`data/fineval_scenario_model.xlsx`](data/fineval_scenario_model.xlsx)
* **Power BI Dimensional Star-Schema Data Model**: [`data/powerbi/`](data/powerbi/)
* **Automated Master Test Suite (229 Tests)**: [`tests/test_fineval_master.py`](tests/test_fineval_master.py)

---

## Overview

FinEval is an evaluation and prompt debugging workbench built to test, evaluate, diagnose, and iterate on LLMs handling financial customer interactions.

In financial services (payments, consumer lending, retail insurance, and investments), deploying conversational assistants without continuous evaluation leads to operational failures: models fabricate transaction statuses, offer informal loan forgiveness, fail to instruct account freezes during active fraud, and drop reference identifiers across turns.

FinEval enforces a closed-loop engineering workflow:
```text
Synthetic Customer Scenario
           ↓
Prompt Version (V1 → V2 → V3 → V4)
           ↓
Model Generation (Live LLM or Deterministic Mock)
           ↓
Multi-Layer Automated Evaluation (Layers 1 to 4)
           ↓
Failure Detection & Taxonomy Mapping (F1..F8)
           ↓
Root-Cause Diagnosis & Prompt Modification
           ↓
Regression Testing & Benchmark Uplift Audit
```

---

## What the System Does

1. **Benchmark Scenario Bank (200 Scenarios):** Real-world test cases covering Standard inquiries, Ambiguous inputs, Boundary edge cases, Multi-turn dialogues, Contradictory statements, Hallucination traps, Adversarial injection, and Escalation-sensitive events across 4 operational domains (Payments, Lending, Insurance, Investments).
2. **Ground Truth Knowledge Base (50 Facts):** Synthetic operational reference rules defining settlement turnaround windows, fee structures, cancellation windows, and regulatory boundaries.
3. **Prompt Versioning & Diffing:** Tracks iterative changes across 4 benchmark prompt versions (V1 Minimal, V2 Structured, V3 Grounded, V4 Operations-Safe) with unified line diffing and an audit change ledger.
4. **Multi-Layer Defensive Evaluation:**
   - **Layer 1 (Schema & Output):** Validates response presence, minimum word counts, decodability, and catches raw JSON leaks.
   - **Layer 2 (Deterministic Rules):** Verifies required terminology, catches prohibited phrases, and verifies structured layout without invoking an LLM.
   - **Layer 3 (Semantic & Consistency):** Token-level Jaccard grounding against reference context and cross-turn entity retention tracking.
   - **Layer 4 (LLM-as-Judge):** Rubric scoring across 7 dimensions (Accuracy 20%, Groundedness 20%, Instruction Following 15%, Relevance 15%, Consistency 10%, Safety 10%, Clarity 10%) returning Pydantic-validated JSON.
5. **Standardized Failure Taxonomy (F1..F8):** Categorizes failures into Hallucination (F1), Instruction Failure (F2), Logical Inconsistency (F3), Context Loss (F4), Irrelevance (F5), Unsupported Certainty (F6), Formatting Failure (F7), and Routing/Escalation Failure (F8).
6. **Prompt Debugger & Live Retest Sandbox:** Inspects individual scenario failures, displays root cause evidence, allows real-time prompt edits, and retests immediately.
7. **Failure Fingerprinting:** Traces how an individual scenario performs across V1, V2, V3, and V4 to verify whether an iterative prompt modification actually fixed the underlying issue.
8. **Relational Database Lineage:** Full SQLAlchemy schema tracking runs, prompts, responses, evaluations, failure events, transcripts, and change ledgers in SQLite (or PostgreSQL via Docker Compose).
9. **SQL Analytics Engine:** 6 SQL queries using CTEs and window functions to compute prompt uplift, category risk, and multi-turn context retention.
10. **Automated vs Manual Audit Calibration:** 30 representative calibration cases evaluating concordance between automated scoring and manual review.

---

## Technical Stack

- **Backend & Evaluation:** Python 3.10+, SQLAlchemy 2.0, Pydantic v2, Pandas, PyYAML, HTTPX
- **Database:** SQLite (default for local zero-config runs), PostgreSQL (via Docker Compose)
- **Data Modeling & BI:** Microsoft Excel (`fineval_scenario_model.xlsx`), Power BI Star-Schema (`data/powerbi/`)
- **UI & Analytics:** Streamlit, Plotly
- **Testing & Quality:** Pytest (229 passing tests), Ruff

---

## Quickstart

### 1. Installation
```bash
git clone https://github.com/hriday-sobti/FinEval.git
cd FinEval

pip install -r requirements.txt
```

### 2. Environment Configuration
Copy the template configuration file:
```bash
cp .env.example .env
```
Default settings run with `DATABASE_URL=sqlite:///./data/fineval.db` and `LLM_PROVIDER=mock`, enabling the full application to run locally without external API keys or cloud dependencies.

To use Docker PostgreSQL:
```bash
docker compose up -d
# Set DATABASE_URL in .env to:
# postgresql+psycopg://fineval_user:fineval_password@localhost:5432/fineval_db
```

### 3. Launching the Console
```bash
python -m streamlit run app/streamlit_app.py
```
Open your browser at `http://localhost:8501`. On first run, the app automatically checks the database and seeds the 200 scenarios, knowledge base, prompt versions, and baseline runs.

### 4. Running Benchmarks via CLI
```bash
# Run deterministic smoke test (6 core cases)
python -m scripts.run_smoke_test

# Run core benchmark (60 balanced cases) on Prompt V4
python -m scripts.run_benchmark --level core --prompt V4

# Run full benchmark (all 200 cases)
python -m scripts.run_benchmark --level full --prompt V4
```

### 5. Running Tests & Linting
```bash
# Run master test suite (229 passing tests)
python -m pytest -v

# Run linter
python -m ruff check .

# Validate dataset schema and category distributions
python -m scripts.validate_dataset
```

---

## Repository Structure

```text
FinEval/
├── app/                  # Streamlit analyst console
│   ├── streamlit_app.py  # Application entrypoint
│   ├── components/       # Custom styling, badges, and layout cards
│   └── pages/            # 7 console views
│       ├── quality_overview.py    # KPI metrics and Plotly analytical charts
│       ├── benchmark_runner.py    # Bulk execution and CSV upload validator
│       ├── prompt_lab.py          # Unified prompt diff and change ledger
│       ├── failure_explorer.py    # Root-cause diagnostic card ("Why Did It Fail?")
│       ├── transcript_explorer.py # Chronological conversation viewer
│       ├── prompt_debugger.py     # Prompt editor sandbox & failure fingerprint
│       └── reports_and_export.py  # Manual audit calibration and CSV downloads
├── config/               # Scoring weights, thresholds, and model parameters
├── data/                 # Benchmark scenarios, knowledge base, prompt versions
│   ├── fineval_scenario_model.xlsx  # Excel scenario & sensitivity model
│   └── powerbi/          # Star-schema dimensional tables for Power BI
├── docs/                 # Architecture, evaluation methodology, failure taxonomy
├── prompts/              # System prompt versions (V1, V2, V3, V4, Judge)
├── reports/              # Audit reports in Markdown and PDF
├── scripts/              # Seed, validation, smoke test, and benchmark CLI scripts
├── sql/                  # 6 SQL analytics scripts using CTEs and window functions
├── src/                  # Application source code
│   ├── analysis/         # Prompt comparison, diff engine, regression detector
│   ├── database/         # SQLAlchemy models, connection, and session management
│   ├── domain/           # Scenario and failure taxonomy schemas
│   ├── evaluation/       # Layers 1 to 4 evaluation engine and scoring rules
│   ├── ingestion/        # Knowledge base and scenario generators
│   ├── llm/              # Provider abstraction (Mock and Live implementations)
│   ├── services/         # Bulk benchmark runner and execution pipeline
│   └── utils/            # Centralized settings and structured logging
└── tests/                # Master test suite (229 automated tests)
```

---

## Synthetic Data Notice

All customer queries, account numbers, reference tokens (`REF-`, `LN-`, `CLM-`), and institutional policies in this repository are synthetic and fictional. They are constructed solely to evaluate LLM response quality, failure modes, and prompt instructions under controlled operational conditions.

