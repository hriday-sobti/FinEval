"""View 4: Failure Explorer and 'Why Did This Response Fail?' Diagnostic Tool.

Features:
1. Filterable Failure Grid
   - Filter by Prompt Version, Failure Type (F1..F8), Severity (Critical, High, Medium, Low), and Domain
2. 'Why Did This Response Fail?' Root Cause Card (Section 68)
   - Failure Code & Name
   - Concrete Evidence
   - Root-Cause Diagnosis
   - Recommended Prompt Fix
   - Regression Check Guidance
"""

import pandas as pd
import streamlit as st

from app.components.cards import render_header
from src.database.connection import get_db_session
from src.database.models import FailureEvent, ModelResponse, Scenario
from src.domain.failure_taxonomy import FAILURE_TAXONOMY


def render_failure_explorer():
    render_header(title="Failure Explorer & Root Cause Diagnostics", benchmark_label="Failure Forensics")

    with get_db_session() as session:
        failures = (
            session.query(FailureEvent, Scenario.domain, Scenario.category, Scenario.user_input, ModelResponse.raw_response)
            .join(Scenario, FailureEvent.scenario_id == Scenario.scenario_id)
            .join(ModelResponse, FailureEvent.scenario_id == ModelResponse.scenario_id and FailureEvent.benchmark_run_id == ModelResponse.benchmark_run_id)
            .order_by(FailureEvent.created_at.desc())
            .all()
        )

        if not failures:
            st.info("No failure events found in the database. Run a benchmark from the Benchmark Runner console.")
            return

        # Filters
        st.markdown("##### Failure Event Filters")
        st.caption(
            "Filter by prompt version, failure type (F1–F8), severity, and domain. "
            "Critical failures automatically fail evaluation regardless of weighted score. "
            "Use the root-cause diagnostic below to understand why a specific response failed."
        )
        f_cols = st.columns(4)

        all_versions = sorted(list(set(f[0].prompt_version for f in failures)))
        all_types = sorted(list(set(f[0].failure_type for f in failures)))
        all_sevs = ["critical", "high", "medium", "low"]
        all_domains = sorted(list(set(f[1] for f in failures)))

        with f_cols[0]:
            sel_ver = st.multiselect("Prompt Version", all_versions, default=all_versions)
        with f_cols[1]:
            sel_type = st.multiselect("Failure Type (F1..F8)", all_types, default=all_types)
        with f_cols[2]:
            sel_sev = st.multiselect("Severity", all_sevs, default=all_sevs)
        with f_cols[3]:
            sel_domain = st.multiselect("Domain", all_domains, default=all_domains)

        # Apply filtering
        filtered = [
            f for f in failures
            if f[0].prompt_version in sel_ver
            and f[0].failure_type in sel_type
            and f[0].severity in sel_sev
            and f[1] in sel_domain
        ]

        st.caption(f"Showing {len(filtered)} of {len(failures)} failure events.")

        # Data Table
        df_rows = []
        for f in filtered:
            ev, dom, cat, u_in, resp = f
            df_rows.append({
                "Failure ID": ev.failure_id,
                "Scenario ID": ev.scenario_id,
                "Prompt Version": ev.prompt_version,
                "Failure Type": f"{ev.failure_type} ({FAILURE_TAXONOMY.get(ev.failure_type, None).name if ev.failure_type in FAILURE_TAXONOMY else 'Failure'})",
                "Severity": ev.severity.upper(),
                "Domain": dom,
                "Category": cat,
                "Customer Message": u_in[:60] + "..." if len(u_in) > 60 else u_in,
            })

        df_table = pd.DataFrame(df_rows)
        st.dataframe(df_table, width="stretch", hide_index=True)

        st.markdown("---")
        st.markdown("##### 2. 'Why Did This Response Fail?' Root Cause Diagnostic")
        st.caption("Select a specific failure event to inspect the operational evidence, root cause diagnosis, and prompt remediation.")

        if filtered:
            selected_f_id = st.selectbox(
                "Select Failure ID to Diagnose",
                [f[0].failure_id for f in filtered],
                format_func=lambda fid: f"{fid} — {next(f[0].scenario_id for f in filtered if f[0].failure_id == fid)} ({next(f[0].failure_type for f in filtered if f[0].failure_id == fid)})"
            )

            # Find matching item
            match = next(f for f in filtered if f[0].failure_id == selected_f_id)
            ev, dom, cat, u_in, raw_resp = match
            meta = FAILURE_TAXONOMY.get(ev.failure_type)

            diag_c1, diag_c2 = st.columns([1, 1])

            with diag_c1:
                st.markdown(f"**Customer Query ({dom} • {cat}):**")
                st.info(u_in)

                st.markdown("**Model Assistant Response:**")
                st.code(raw_resp, language="text")

            with diag_c2:
                # Root cause diagnosis card matching Section 68
                st.markdown(f"""
                <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-left: 4px solid #ef4444; border-radius: 4px; padding: 14px;">
                    <div style="font-weight: 700; color: #991b1b; font-size: 0.95rem; margin-bottom: 6px;">
                        FAILURE: {ev.failure_type} — {meta.name if meta else 'Failure'} [{ev.severity.upper()}]
                    </div>
                    <div style="font-size: 0.85rem; color: #1e293b; margin-bottom: 8px;">
                        <strong>Evidence:</strong><br>
                        {ev.evidence}
                    </div>
                    <div style="font-size: 0.85rem; color: #1e293b; margin-bottom: 8px;">
                        <strong>Root Cause Diagnosis:</strong><br>
                        {ev.diagnosis}
                    </div>
                    <div style="font-size: 0.85rem; color: #1e293b; margin-bottom: 8px;">
                        <strong>Recommended Prompt Fix:</strong><br>
                        {ev.recommended_fix}
                    </div>
                    <div style="font-size: 0.82rem; color: #64748b;">
                        <strong>Regression Check Guidance:</strong><br>
                        Rerun this scenario and related {cat} scenarios with prompt version V3 or V4 to verify remediation.
                    </div>
                </div>
                """, unsafe_allow_html=True)
