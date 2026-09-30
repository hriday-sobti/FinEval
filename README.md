# FinEval — Financial AI Response Quality & Prompt Operations Lab

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite_%26_PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](src/database/)
[![Tests](https://img.shields.io/badge/Tests-229_Passing-2EA44F?style=for-the-badge&logo=pytest&logoColor=white)](tests/)
[![Power BI](https://img.shields.io/badge/Power_BI-Ready-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](data/powerbi/)
[![Excel Model](https://img.shields.io/badge/Excel-Scenario_Model-107C41?style=for-the-badge&logo=microsoftexcel&logoColor=white)](data/fineval_scenario_model.xlsx)
[![Author](https://img.shields.io/badge/Author-Hriday_Singh_Sobti-0F172A?style=for-the-badge&logo=github&logoColor=white)](https://github.com/hriday-sobti)

## Project Report

[View the full evaluation report (PDF)](reports/FinEval_Evaluation_Report.pdf)

---

## Deliverables

* **Interactive Dashboard:** Run locally via `python -m streamlit run app/streamlit_app.py`
* **Full Evaluation Report (PDF):** [`reports/FinEval_Evaluation_Report.pdf`](reports/FinEval_Evaluation_Report.pdf)
* **Full Evaluation Report (Markdown):** [`reports/FinEval_Evaluation_Report.md`](reports/FinEval_Evaluation_Report.md)
* **Excel Scenario & Sensitivity Model:** [`data/fineval_scenario_model.xlsx`](data/fineval_scenario_model.xlsx)
* **Power BI Star-Schema Data Model:** [`data/powerbi/`](data/powerbi/)
* **Master Automated Test Suite (229 tests):** [`tests/test_fineval_master.py`](tests/test_fineval_master.py)

---

## The Problem

Financial AI assistants fail in specific, consequential ways. A customer reporting active fraud gets told to "wait 5–7 business days." A model confirms activation of a fabricated product — "SuperFast Instant Reversal 30-Second Guarantee" — that does not exist. When a customer references a prior message ("like I said earlier…"), the model asks for the payment ID again, losing context it was given one turn ago. A coupon code invented on social media gets applied without question. These are not edge cases in a lab — they are operational failures with compliance and trust consequences. Without systematic evaluation, they go undetected in production.

---

## What This System Does

1. **Benchmark Scenario Bank (200 Scenarios):** Covers eight scenario categories — Standard, Ambiguous, Edge Case, Multi-turn, Contradictory, Hallucination Trap, Adversarial, and Policy/Escalation — across four operational domains: Payments, Lending, Insurance, and Investments.
2. **Ground Truth Knowledge Base (50 Facts):** Synthetic operational reference rules defining settlement windows, fee structures, cancellation deadlines, and regulatory limits — used to score groundedness against something concrete.
3. **Prompt Versioning & Diffing:** Tracks iterative changes across four benchmark prompt versions (V1 Minimal, V2 Structured, V3 Grounded, V4 Operations-Safe) with line-level unified diffs and an immutable change ledger.
4. **Multi-Layer Defensive Evaluation:**
   - **Layer 1 (Schema & Output):** Validates response presence, minimum word count, decodability, and catches raw JSON leaks.
   - **Layer 2 (Deterministic Rules):** Verifies required terminology, catches prohibited phrases, and checks structural layout — no LLM involved.
   - **Layer 3 (Semantic & Consistency):** Token-level Jaccard grounding against reference context; cross-turn entity retention tracking to catch context loss.
   - **Layer 4 (LLM-as-Judge):** Rubric scoring across 7 dimensions (Accuracy 20%, Groundedness 20%, Instruction Following 15%, Relevance 15%, Consistency 10%, Safety 10%, Clarity 10%) returning Pydantic-validated JSON.
5. **Standardized Failure Taxonomy (F1–F8):** Categorizes failures as Hallucination (F1), Instruction Failure (F2), Logical Inconsistency (F3), Context Loss (F4), Irrelevance (F5), Unsupported Certainty (F6), Formatting Failure (F7), and Routing/Escalation Failure (F8).
6. **Prompt Debugger & Live Retest Sandbox:** Inspect individual scenario failures, read root-cause evidence, edit the prompt directly, and retest — all in one view.
7. **Failure Fingerprinting:** Traces how a specific scenario performs across V1 → V4 to verify whether a prompt change actually resolved the underlying failure or just masked it.
8. **Relational Database Lineage:** Full SQLAlchemy schema tracking runs, prompts, responses, evaluations, failure events, transcripts, and change ledgers in SQLite (or PostgreSQL via Docker Compose).
9. **SQL Analytics Engine:** 6 analytical queries using CTEs and window functions to compute prompt uplift, category risk, and multi-turn context retention rates.
10. **Automated vs Manual Audit Calibration:** 30 representative calibration cases measuring concordance between automated scoring and manual review.

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

## Key Findings

> **Methodology note:** V1, V2, and V3 each ran 60 cases (core benchmark). V4 ran 200 cases (full benchmark). Pass rates are not directly comparable across benchmark sizes — a lower bar at 60 cases is not the same test as 200 cases with broader scenario coverage.

| Metric | V1 Baseline | V4 Operations-Safe | Note |
|---|---|---|---|
| Benchmark size | 60 cases | 200 cases | Different benchmarks — see note above |
| Pass rate | 0.0% | 86.5% | V1 failed every case at threshold |
| Average score | 48.52% | 84.27% | +35.75 percentage points |
| Critical failures | 4 | 15 of 200 (7.5%) | V1 ran 60 cases; raw count not comparable |
| Hallucination rate | 5.0% | 8.5% | V4 includes 26 deliberate hallucination-trap cases |
| Context loss rate | 6.67% | 0.5% | Multi-turn retention largely resolved |

Hallucination Trap is the one unresolved category gap in V4: 0 of 26 cases pass at threshold, even though responses correctly refuse fabricated products. The failure driver is low-severity formatting issues (F7) rather than actual hallucination — the evaluation threshold is strict.

---

## What Changed

| Area | Baseline Approach | Contribution | Evidence |
|---|---|---|---|
| Evaluation | Single scoring pass, no failure taxonomy | Four-layer evaluation engine (schema → rules → semantic → LLM-judge) with F1–F8 failure classification | 63 total failure events classified across 4 runs; severity distribution tracked per prompt version |
| Prompt Design | Minimal instruction, no grounding anchor | Iterative four-version prompt engineering — structured output (V2), knowledge grounding (V3), operations-safe guardrails (V4) | Avg score: 48.52% → 84.27%; pass rate: 0% → 86.5% on respective benchmarks |
| Failure Analysis | Failures were unobserved | Root-cause diagnostic view per scenario with failure type, severity, and contributing layer | SC-146: V1 fabricated and confirmed a non-existent product; V4 refuses correctly |
| Regression Testing | No regression visibility | Automated before/after comparison across prompt versions | V2→V3: 5 resolved, 0 regressions; V3→V4 (60-case): 48 resolved, 0 regressions |
| Transcript Analysis | No cross-turn visibility | Per-scenario conversation viewer with entity retention tracking across turns | SC-101: V1 lost payment reference within one turn; V4 retains it and gives pending status |
| Reporting | No structured output | Calibration audit (30 cases), SQL analytics with CTEs, Excel model, Power BI star-schema, PDF/Markdown report | Full audit trail from raw scenario to scored result stored in relational schema |

---

## Synthetic Data Notice

All customer queries, account numbers, reference tokens (`REF-`, `LN-`, `CLM-`), and institutional policies in this repository are synthetic and fictional. They are constructed solely to evaluate LLM response quality, failure modes, and prompt instructions under controlled operational conditions.
