# FinEval System Architecture & Component Lineage

```text
Synthetic Customer Scenario (200 cases)
           ↓
Multi-Turn / User Message Context
           ↓
Active System Prompt (V1 | V2 | V3 | V4)
           ↓
LLM Provider Abstraction (LiveLLMProvider | MockLLMProvider)
           ↓
Raw Model Response + Metadata (Latency, Token Usage)
           ↓
Multi-Layer Evaluation Pipeline:
   ├── Layer 1: Schema & Output Validation (Empty, length, JSON checks)
   ├── Layer 2: Deterministic Rule Engine (Must include, must not include, prohibited claims)
   ├── Layer 3: Semantic Alignment & Consistency (Jaccard token grounding, multi-turn context retention)
   └── Layer 4: LLM-as-Judge Evaluator (Structured 7-dimension scoring + Pydantic validation)
           ↓
Failure Detection & Taxonomy Mapping (F1..F8)
           ↓
Root-Cause Diagnosis & Remediation Guidance
           ↓
PostgreSQL / SQLite Persistence (8 relational tables, foreign keys, analytical indexes)
           ↓
Analytical SQL Layer (6 production queries with CTEs and window functions)
           ↓
Interactive Analyst Console (Streamlit + Plotly visual forensic workbench)
```

## Relational Lineage
The database enforces strict end-to-end auditability across the lifecycle:
`scenarios` $\rightarrow$ `benchmark_runs` $\rightarrow$ `model_responses` $\rightarrow$ `evaluations` $\rightarrow$ `failure_events` $\rightarrow$ `transcripts` $\rightarrow$ `change_ledger`.
