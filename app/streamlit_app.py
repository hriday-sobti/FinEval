"""FinEval Streamlit Main Console Application.

Main application entrypoint configuring:
- Streamlit page setup, page title, favicon, and wide layout
- Left navigation sidebar matching Section 70 specification:
  - Quality Overview
  - Benchmark Runner
  - Prompt Lab
  - Failure Explorer
  - Transcript Explorer
  - Prompt Debugger
  - Reports & Exports
- Clean analyst theme injection
"""

import streamlit as st

from app.components.styling import apply_analyst_styling
from app.pages.benchmark_runner import render_benchmark_runner
from app.pages.failure_explorer import render_failure_explorer
from app.pages.prompt_debugger import render_prompt_debugger
from app.pages.prompt_lab import render_prompt_lab
from app.pages.quality_overview import render_quality_overview
from app.pages.reports_and_export import render_report_and_export
from app.pages.transcript_explorer import render_transcript_explorer
from src.database.connection import get_db_session, init_db
from src.database.models import Scenario

# Configure wide layout and page metadata
st.set_page_config(
    page_title="FinEval — Financial AI Quality & Prompt Operations Lab",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply Analyst Theme
apply_analyst_styling()

# Ensure database schema and seed data exist on startup if fresh clone
init_db()
with get_db_session() as _session:
    if _session.query(Scenario).count() == 0:
        from scripts.seed_database import seed_database
        seed_database(run_benchmark=True)

# Navigation
st.sidebar.markdown("### **FinEval Console**")
st.sidebar.caption("Financial AI Response Quality Lab")

page_selection = st.sidebar.radio(
    "Navigation Views",
    [
        "Quality Overview",
        "Benchmark Runner",
        "Prompt Lab",
        "Failure Explorer",
        "Transcript Explorer",
        "Prompt Debugger",
        "Reports & Exports",
    ],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.caption("System Status: **Operational**")
st.sidebar.caption("Database: **SQLite / PG Ready**")
st.sidebar.caption("LLM Engine: **Multi-Layer Eval**")

if page_selection == "Quality Overview":
    render_quality_overview()
elif page_selection == "Benchmark Runner":
    render_benchmark_runner()
elif page_selection == "Prompt Lab":
    render_prompt_lab()
elif page_selection == "Failure Explorer":
    render_failure_explorer()
elif page_selection == "Transcript Explorer":
    render_transcript_explorer()
elif page_selection == "Prompt Debugger":
    render_prompt_debugger()
elif page_selection == "Reports & Exports":
    render_report_and_export()
