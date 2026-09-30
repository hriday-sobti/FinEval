# FinEval Implementation Notes & Engineering Decisions

## 1. Engineering Principles
- **No Marketing Fluff:** The application is built as an internal quality-control console for operations analysts, not a consumer chatbot.
- **Traceable End-to-End Lineage:** Every single evaluation score, failure event, and transcript turn maps back to a specific benchmark run, prompt version, and scenario ID.
- **Relational Integrity:** Uses SQLAlchemy with clean foreign keys, indexes on high-cardinality fields (`prompt_version`, `scenario_id`, `failure_type`, `severity`), and dialect-aware JSON storage (`JSONB` on PostgreSQL, `Text` on SQLite).
- **Deterministic Mock Mode:** Enables complete local test suite execution, benchmark runs, and Streamlit exploration without requiring live LLM API keys.
- **Live Provider Safety:** Protects credentials; API keys are never printed, stored in tables, or logged. Implements exponential backoff on HTTP 429/5xx transient errors.
- **SQL Analytics:** Six native SQL queries demonstrate CTEs, window functions, and multi-turn aggregate analysis directly in the database.
