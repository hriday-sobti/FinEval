"""View 2: Benchmark Runner Console and CSV Importer.

Supports:
1. Benchmark configuration:
   - Dataset Selection (Standard synthetic repository vs Uploaded CSV)
   - Benchmark Mode (Smoke: 6, Core: 60, Full: 200)
   - Prompt Version Selection (V1, V2, V3, V4)
   - Provider Mode (Mock vs Live)
   - Model Name (gpt-4o-mini, gpt-4o, claude-3-5-sonnet, etc.)
2. CSV Upload Validation:
   - Validates schema, columns, duplicate IDs, invalid categories, and null values
   - Prevents unvalidated files from executing
3. Execution Progress Bar and Live Logging:
   - Visual progress bar and status indicator
   - Immediate feedback upon run completion
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from app.components.cards import render_header
from scripts.validate_dataset import validate_scenario_csv
from src.database.connection import get_db_session
from src.database.models import BenchmarkRun, Scenario
from src.domain.scenario import ScenarioSchema
from src.services.benchmark_runner import BenchmarkRunner, select_benchmark_scenarios


def render_benchmark_runner():
    render_header(title="Benchmark Execution Console", benchmark_label="Operations Runner")

    tab1, tab2 = st.tabs(["Execute Benchmark", "Upload Custom Benchmark CSV"])

    with tab1:
        st.markdown("##### Benchmark Execution Configuration")
        st.caption(
            "Mock mode uses deterministic scenario fixtures — no API key required. "
            "Live mode calls a configured LLM provider and consumes tokens. "
            "All runs are persisted to the relational database with full evaluation lineage."
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            eval_mode = st.selectbox(
                "Benchmark Level",
                ["Smoke (6 cases - Fast check)", "Core (60 cases - Balanced)", "Full (200 cases - Complete)"],
                index=1
            )
            mode_code = "smoke" if "Smoke" in eval_mode else ("core" if "Core" in eval_mode else "full")

        with c2:
            prompt_ver = st.selectbox("Prompt Version", ["V1", "V2", "V3", "V4"], index=3)

        with c3:
            provider = st.selectbox("Provider Mode", ["Mock (Deterministic, No API Key)", "Live (Requires API Key)"], index=0)
            prov_code = "mock" if "Mock" in provider else "live"

        c4, c5 = st.columns(2)
        with c4:
            model_name = st.text_input("Model Identifier", value="gpt-4o-mini")
        with c5:
            st.selectbox("Dataset Source", ["Synthetic Standard Repository (200 cases)", "Custom Uploaded File"], index=0)

        # Cost Control notice matching Section 59
        st.caption("Benchmark execution requires explicit confirmation to prevent unintentional live token consumption.")

        if st.button("Start Benchmark Execution", type="primary"):
            # Load scenarios
            scenarios: list[ScenarioSchema] = []
            with get_db_session() as s:
                db_scs = s.query(Scenario).all()
                for db_s in db_scs:
                    scenarios.append(ScenarioSchema(
                        scenario_id=db_s.scenario_id,
                        domain=db_s.domain,
                        category=db_s.category,
                        subcategory=db_s.subcategory,
                        difficulty=db_s.difficulty,
                        language_style=db_s.language_style,
                        conversation_type=db_s.conversation_type,
                        turns=db_s.turns,
                        user_input=db_s.user_input,
                        context=db_s.context,
                        expected_action=db_s.expected_action,
                        expected_facts=db_s.expected_facts,
                        allowed_claims=db_s.allowed_claims,
                        prohibited_claims=db_s.prohibited_claims,
                        must_include=db_s.must_include,
                        must_not_include=db_s.must_not_include,
                        severity_if_failed=db_s.severity_if_failed,
                        tags=db_s.tags,
                        gold_rationale=db_s.gold_rationale,
                    ))

            if not scenarios:
                st.error("No scenarios found in database. Please run seed script first.")
                return

            filtered_scenarios = select_benchmark_scenarios(scenarios, mode=mode_code)
            st.info(f"Loaded {len(filtered_scenarios)} scenarios for {mode_code.upper()} run on prompt {prompt_ver}.")

            progress_bar = st.progress(0.0)
            status_text = st.empty()

            runner = BenchmarkRunner(
                prompt_version=prompt_ver,
                model_name=model_name,
                provider_type=prov_code,
                evaluation_mode=mode_code,
                judge_provider_type="mock" if prov_code == "mock" else "live",
            )

            def update_progress(curr, total, msg):
                pct = curr / total
                progress_bar.progress(pct)
                status_text.text(f"[{curr}/{total}] {msg}")

            with st.spinner("Executing benchmark scenarios and multi-layer evaluations..."):
                run_id = runner.run(filtered_scenarios, progress_callback=update_progress)

            progress_bar.progress(1.0)
            status_text.text(f"Benchmark completed successfully! Run ID: {run_id}")
            st.success(f"Benchmark run {run_id} finished and persisted to relational database.")

        st.markdown("---")
        st.markdown("##### Recent Benchmark Runs")
        st.caption("Each run stores full evaluation lineage: prompt version, scores, failures, and transcripts. Use the Failure Explorer to drill into any run.")
        with get_db_session() as s:
            runs = s.query(BenchmarkRun).order_by(BenchmarkRun.timestamp.desc()).limit(10).all()
            if runs:
                df_runs = pd.DataFrame([{
                    "Run ID": r.benchmark_run_id,
                    "Timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M"),
                    "Prompt Version": r.prompt_version,
                    "Model": r.model_name,
                    "Mode": r.evaluation_mode,
                    "Total Cases": r.total_scenarios,
                    "Passed": r.passed_scenarios,
                    "Pass Rate (%)": f"{round((r.passed_scenarios / r.total_scenarios * 100), 1) if r.total_scenarios else 0}%",
                    "Avg Quality Score": f"{r.average_score}%",
                    "Duration": f"{r.duration_seconds:.1f}s",
                } for r in runs])
                st.dataframe(df_runs, width="stretch", hide_index=True)
            else:
                st.caption("No benchmark runs recorded yet.")

    with tab2:
        st.markdown("##### Upload Benchmark Dataset CSV")
        st.caption("Strict schema validation will check for required fields, JSON columns, duplicate IDs, and invalid categories before enabling execution.")

        uploaded_file = st.file_uploader("Select Scenario CSV File", type=["csv"])
        if uploaded_file is not None:
            # Temporary save for validator
            temp_path = Path("data/temp_uploaded_scenarios.csv")
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            is_valid, errors, counts = validate_scenario_csv(temp_path)

            c_val1, c_val2 = st.columns(2)
            with c_val1:
                st.markdown(f"**Validation Status:** {'VALID' if is_valid else 'INVALID'}")
                st.markdown(f"**Rows Detected:** {sum(counts.values())}")
            with c_val2:
                st.markdown(f"**Errors Detected:** {len(errors)}")

            if is_valid:
                st.success("CSV file passed all schema, category, and distribution checks. Ready for benchmarking.")
                df_preview = pd.read_csv(temp_path)
                st.dataframe(df_preview.head(5), width="stretch")
            else:
                st.error("Validation failed. Please correct the following errors before attempting benchmark execution:")
                for err in errors[:8]:
                    st.write(f"- {err}")
