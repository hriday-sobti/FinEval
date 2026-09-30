"""View 1: Quality Overview Dashboard.

KPI Row:
- Total Tests
- Pass Rate
- Average Quality Score
- Hallucination Rate
- Instruction Failure Rate
- Critical Failures
- Context Failure Rate

Charts:
1. Prompt Version vs Average Quality Score
2. Failure Type Distribution (F1..F8)
3. Failure Severity Distribution
4. Scenario Category vs Pass Rate
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from app.components.cards import render_header
from src.analysis.prompt_comparison import compare_prompt_benchmarks
from src.database.connection import get_db_session
from src.database.models import BenchmarkRun, Evaluation, FailureEvent, Scenario


def render_quality_overview():
    render_header(title="AI Response Quality Overview", benchmark_label="Operations Benchmark")

    with get_db_session() as session:
        metrics = compare_prompt_benchmarks(session=session)
        runs = session.query(BenchmarkRun).all()

        if not runs or not metrics:
            st.info("No benchmark runs recorded in the database yet. Navigate to 'Benchmark Runner' to execute the smoke or core test.")
            return

        # Overall summary stats across all active runs
        total_tests = sum(m.test_count for m in metrics)
        round(sum(m.pass_rate * m.test_count for m in metrics) / total_tests, 1) if total_tests else 0
        overall_avg_score = round(sum(m.average_score * m.test_count for m in metrics) / total_tests, 1) if total_tests else 0
        latest_v4 = next((m for m in metrics if m.version == "V4"), metrics[-1])

        # KPI Cards (Compact Row)
        cols = st.columns(7)
        with cols[0]:
            st.metric("Total Tests", f"{total_tests:,}", help="Cumulative evaluations across all prompt versions and benchmark runs")
        with cols[1]:
            st.metric("V4 Pass Rate", f"{latest_v4.pass_rate}%", delta=f"{latest_v4.pass_rate - metrics[0].pass_rate:.1f}% vs V1", help="Responses passing all thresholds on V4 (score≥80%, groundedness≥3.0, safety≥3.0, zero critical failures) — evaluated on 200-case full benchmark")
        with cols[2]:
            st.metric("Avg Quality Score", f"{overall_avg_score}%", help="Weighted average across 7 dimensions: Accuracy 20%, Groundedness 20%, Instruction Following 15%, Relevance 15%, Consistency 10%, Safety 10%, Clarity 10%")
        with cols[3]:
            st.metric("Hallucination (F1)", f"{latest_v4.hallucination_rate}%", delta=f"{latest_v4.hallucination_rate - metrics[0].hallucination_rate:.1f}%", delta_color="inverse", help="Rate of responses containing fabricated facts, fees, timelines, or product features not in the knowledge base")
        with cols[4]:
            st.metric("Instruction Fail (F2)", f"{latest_v4.instruction_failure_rate}%", delta=f"{latest_v4.instruction_failure_rate - metrics[0].instruction_failure_rate:.1f}%", delta_color="inverse", help="Rate of responses that ignored explicit behavioral constraints in the system prompt")
        with cols[5]:
            st.metric("Critical Failures", f"{latest_v4.critical_failures}", help="Responses with fabricated account status, prohibited financial advice, or omitted fraud escalation — automatically fail regardless of score")
        with cols[6]:
            st.metric("Context Loss (F4)", f"{latest_v4.context_failure_rate}%", delta=f"{latest_v4.context_failure_rate - metrics[0].context_failure_rate:.1f}%", delta_color="inverse", help="Rate of multi-turn responses that dropped reference identifiers or prior conversation context")

        st.markdown("---")

        # Analytical Charts (2x2 Grid)
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("##### Average Quality Score by Prompt Version")
            df_perf = pd.DataFrame([m.model_dump() for m in metrics])
            fig_perf = px.bar(
                df_perf,
                x="version",
                y="average_score",
                color="version",
                text="average_score",
                color_discrete_sequence=["#94a3b8", "#64748b", "#0284c7", "#16a34a"],
                labels={"average_score": "Score (%)", "version": "Prompt Version"}
            )
            fig_perf.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_perf.update_layout(yaxis=dict(range=[0, 105]), showlegend=False, margin=dict(l=20, r=20, t=30, b=20), height=300)
            st.plotly_chart(fig_perf, width="stretch")
            st.caption("V1–V3 evaluated on 60-case core benchmark. V4 evaluated on 200-case full benchmark. Pass rates are not directly comparable across benchmark sizes.")
            st.caption("Key insight: The largest single-step score jump (+15.29 pts) occurred between V2 and V3, coinciding with the introduction of explicit grounding constraints.")

        with c2:
            st.markdown("##### Failure Type Distribution by Prompt Version")
            failures = session.query(FailureEvent).all()
            if failures:
                df_fail = pd.DataFrame([{
                    "failure_type": f.failure_type,
                    "prompt_version": f.prompt_version,
                    "severity": f.severity
                } for f in failures])
                fig_fail = px.histogram(
                    df_fail,
                    x="failure_type",
                    color="prompt_version",
                    barmode="group",
                    labels={"failure_type": "Failure Code", "count": "Occurrences"},
                    color_discrete_map={"V1": "#ef4444", "V2": "#f59e0b", "V3": "#0ea5e9", "V4": "#22c55e"}
                )
                fig_fail.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=300)
                st.plotly_chart(fig_fail, width="stretch")
                st.caption("F1 (Hallucination) and F6 (Unsupported Certainty) dominated V1. F7 (Formatting) appears in V4 at low severity. Hallucination Trap scenarios (F1) remain unresolved across all versions — 0% pass rate on that category.")
            else:
                st.caption("No failures recorded.")

        c3, c4 = st.columns(2)

        with c3:
            st.markdown("##### Failure Severity Distribution (All Versions)")
            if failures:
                sev_counts = pd.Series([f.severity for f in failures]).value_counts().reset_index()
                sev_counts.columns = ["severity", "count"]
                fig_sev = px.pie(
                    sev_counts,
                    names="severity",
                    values="count",
                    color="severity",
                    color_discrete_map={"critical": "#dc2626", "high": "#ea580c", "medium": "#f59e0b", "low": "#94a3b8"},
                    hole=0.4
                )
                fig_sev.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=300)
                st.plotly_chart(fig_sev, width="stretch")
                st.caption("Critical severity events (27 of 63 total) are treated as automatic failures regardless of weighted score. This prevents a high-clarity response from passing despite containing fabricated account status.")
            else:
                st.caption("No failure severity records.")

        with c4:
            st.markdown("##### Scenario Category Pass Rate by Prompt Version")
            evals = session.query(Evaluation, Scenario.category).join(Scenario, Evaluation.scenario_id == Scenario.scenario_id).all()
            if evals:
                df_cat = pd.DataFrame([{
                    "category": e[1],
                    "prompt_version": e[0].prompt_version,
                    "passed": 1 if e[0].passed else 0
                } for e in evals])
                df_cat_grp = df_cat.groupby(["category", "prompt_version"])["passed"].mean().reset_index()
                df_cat_grp["pass_rate"] = df_cat_grp["passed"] * 100.0

                fig_cat = px.bar(
                    df_cat_grp,
                    x="category",
                    y="pass_rate",
                    color="prompt_version",
                    barmode="group",
                    labels={"category": "Scenario Category", "pass_rate": "Pass Rate (%)"},
                    color_discrete_map={"V1": "#94a3b8", "V2": "#64748b", "V3": "#0ea5e9", "V4": "#16a34a"}
                )
                fig_cat.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=300, yaxis=dict(range=[0, 105]))
                st.plotly_chart(fig_cat, width="stretch")
                st.caption("V4 achieves 100% on Standard and Contradictory categories. Hallucination Trap records 0% pass rate across all versions — the benchmark's most significant remaining gap.")
            else:
                st.caption("No category evaluation records.")

        st.markdown("##### Observed Prompt Performance Summary")
        table_data = []
        for m in metrics:
            table_data.append({
                "Version": m.version,
                "Prompt Name": m.name,
                "Test Count": m.test_count,
                "Pass Rate (%)": f"{m.pass_rate}%",
                "Avg Score (%)": f"{m.average_score}%",
                "Uplift vs V1": f"{m.score_uplift_vs_v1:+.2f}%",
                "F1 Hallucination (%)": f"{m.hallucination_rate}%",
                "F2 Instruction Fail (%)": f"{m.instruction_failure_rate}%",
                "F4 Context Loss (%)": f"{m.context_failure_rate}%",
                "Critical Failures": m.critical_failures,
                "Avg Latency (ms)": f"{m.average_latency_ms:.1f}ms",
            })
        st.dataframe(pd.DataFrame(table_data), width="stretch", hide_index=True)
        st.markdown("---")
        st.markdown("##### Methodology Note")
        st.caption(
            "V1, V2, and V3 were each evaluated on the 60-case core benchmark. "
            "V4 was evaluated on the full 200-case benchmark. "
            "Pass rates and failure counts therefore reflect different evaluation surfaces and should not be treated as a controlled A/B comparison. "
            "The score progression (48.52% → 61.19% → 76.48% → 84.27%) is computed on each version's own benchmark run."
        )
