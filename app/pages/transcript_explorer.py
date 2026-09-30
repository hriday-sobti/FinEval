"""View 5: Chronological Transcript Explorer and Multi-Turn Conversation Analyzer.

Features:
1. Multi-Dimensional Filters:
   - Prompt Version, Domain, Scenario Category, Failure Type, Pass/Fail status
2. Interactive Transcript Viewer:
   - Full conversation turns in chronological sequence (Turn 0, 1, 2...)
   - Visual highlighting of the specific turn where failure occurred
   - Side-by-side failure metadata and operational evidence
"""

import streamlit as st

from app.components.cards import render_badge, render_header
from src.database.connection import get_db_session
from src.database.models import Evaluation, ModelResponse, Scenario, TranscriptTurn


def render_transcript_explorer():
    render_header(title="Transcript Explorer & Multi-Turn Forensics", benchmark_label="Transcript Forensics")

    with get_db_session() as session:
        # Fetch evaluated scenarios
        records = (
            session.query(
                ModelResponse.response_id,
                ModelResponse.benchmark_run_id,
                ModelResponse.scenario_id,
                ModelResponse.prompt_version,
                ModelResponse.latency_ms,
                Scenario.domain,
                Scenario.category,
                Scenario.conversation_type,
                Evaluation.overall_score,
                Evaluation.passed,
                Evaluation.is_critical_fail,
            )
            .join(Scenario, ModelResponse.scenario_id == Scenario.scenario_id)
            .join(Evaluation, ModelResponse.response_id == Evaluation.response_id)
            .order_by(ModelResponse.created_at.desc())
            .all()
        )

        if not records:
            st.info("No transcripts found in the database. Run a benchmark first.")
            return

        # Filters
        st.markdown("##### Transcript Filters")
        st.caption(
            "Select a conversation to view it turn-by-turn in chronological order. "
            "Multi-turn scenarios are where F4 (Context Loss) failures occur — "
            "look for turns where the model asks for information it was already given."
        )
        c1, c2, c3, c4 = st.columns(4)

        all_vers = sorted(list(set(r.prompt_version for r in records)))
        all_doms = sorted(list(set(r.domain for r in records)))
        all_cats = sorted(list(set(r.category for r in records)))

        with c1:
            sel_ver = st.selectbox("Prompt Version", ["All"] + all_vers, index=0)
        with c2:
            sel_dom = st.selectbox("Domain", ["All"] + all_doms, index=0)
        with c3:
            sel_cat = st.selectbox("Category", ["All"] + all_cats, index=0)
        with c4:
            sel_status = st.selectbox("Evaluation Status", ["All", "Pass Only", "Fail Only"], index=0)

        # Apply filtering
        filtered_records = []
        for r in records:
            if sel_ver != "All" and r.prompt_version != sel_ver:
                continue
            if sel_dom != "All" and r.domain != sel_dom:
                continue
            if sel_cat != "All" and r.category != sel_cat:
                continue
            if sel_status == "Pass Only" and not r.passed:
                continue
            if sel_status == "Fail Only" and r.passed:
                continue
            filtered_records.append(r)

        st.caption(f"Showing {len(filtered_records)} of {len(records)} transcripts.")

        # Selector
        if not filtered_records:
            st.warning("No transcripts match the selected filters.")
            return

        selected_resp_id = st.selectbox(
            "Select Conversation Record",
            [r.response_id for r in filtered_records],
            format_func=lambda rid: f"{next(r.scenario_id for r in filtered_records if r.response_id == rid)} — Prompt {next(r.prompt_version for r in filtered_records if r.response_id == rid)} ({'PASS' if next(r.passed for r in filtered_records if r.response_id == rid) else 'FAIL'} | {next(r.overall_score for r in filtered_records if r.response_id == rid):.1f}%)"
        )

        active_rec = next(r for r in filtered_records if r.response_id == selected_resp_id)

        st.markdown("---")
        st.markdown("##### 2. Chronological Conversation Transcript")

        # Fetch turns for this response
        turns = (
            session.query(TranscriptTurn)
            .filter_by(response_id=selected_resp_id)
            .order_by(TranscriptTurn.turn_index.asc())
            .all()
        )

        t_col1, t_col2 = st.columns([2, 1])

        with t_col1:
            for t in turns:
                role_label = "CUSTOMER" if t.role == "user" else "ASSISTANT"
                border_color = "#ef4444" if t.has_failure else ("#3b82f6" if t.role == "assistant" else "#cbd5e1")
                bg_color = "#fef2f2" if t.has_failure else ("#f8fafc" if t.role == "assistant" else "#ffffff")

                st.markdown(f"""
                <div style="background: {bg_color}; border: 1px solid {border_color}; border-left: 4px solid {border_color}; border-radius: 4px; padding: 10px 14px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="font-size: 0.75rem; font-weight: 700; color: #475569;">TURN {t.turn_index} • {role_label}</span>
                        {f'<span class="badge-fail">FAILURE: {t.failure_type}</span>' if t.has_failure else ''}
                    </div>
                    <div style="font-size: 0.88rem; color: #0f172a; white-space: pre-wrap;">{t.content}</div>
                </div>
                """, unsafe_allow_html=True)

        with t_col2:
            st.markdown("###### Session Audit Metadata")
            st.markdown(f"**Scenario ID:** `{active_rec.scenario_id}`")
            st.markdown(f"**Domain:** {active_rec.domain}")
            st.markdown(f"**Category:** {active_rec.category}")
            st.markdown(f"**Conversation Type:** `{active_rec.conversation_type}`")
            st.markdown(f"**Prompt Version:** `{active_rec.prompt_version}`")
            st.markdown(f"**Latency:** {active_rec.latency_ms:.1f}ms")
            st.markdown(f"**Quality Score:** {active_rec.overall_score:.1f}%")

            status_badge = render_badge("PASS", "pass") if active_rec.passed else render_badge("FAIL", "fail")
            crit_badge = render_badge("CRITICAL FAIL", "fail") if active_rec.is_critical_fail else ""
            st.markdown(f"**Evaluation Status:** {status_badge} {crit_badge}", unsafe_allow_html=True)
