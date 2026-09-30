"""View 3: Prompt Lab, Visual Unified Diff, and Change Ledger.

Features:
1. Prompt Library & Metadata Inspector
   - Prompt Version (V1, V2, V3, V4)
   - Change Type & Hypothesis
   - Target Failure Types (F1..F8)
2. Prompt Diff Tool
   - Visual side-by-side / unified diff (V2->V3, V3->V4)
   - Highlight additions, deletions, modifications
3. Prompt Change Ledger
   - Traceable record of version experiments, observed result, and regression status
"""

import json

import pandas as pd
import streamlit as st

from app.components.cards import render_header
from src.analysis.prompt_comparison import compute_prompt_diff
from src.database.connection import get_db_session
from src.database.models import ChangeLedgerEntry, PromptVersion


def render_prompt_lab():
    render_header(title="Prompt Engineering Lab & Experiment Ledger", benchmark_label="Prompt Operations")

    tab1, tab2, tab3 = st.tabs(["Prompt Version Inspector", "Visual Prompt Diff", "Prompt Change Ledger"])

    with get_db_session() as session:
        prompts = session.query(PromptVersion).order_by(PromptVersion.version.asc()).all()
        prompt_map = {p.version: p for p in prompts}

        with tab1:
            st.markdown("##### Prompt Version Specifications")
            selected_v = st.selectbox("Select Version to Inspect", [p.version for p in prompts], index=3)
            p = prompt_map[selected_v]

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**Name:** {p.name}")
                st.markdown(f"**Created At:** {p.created_at.strftime('%Y-%m-%d %H:%M') if p.created_at else '2026-09-01'}")
            with c2:
                st.markdown(f"**Change Type:** `{p.change_type}`")
                targets = p.target_failure_types if isinstance(p.target_failure_types, list) else json.loads(p.target_failure_types or "[]")
                st.markdown(f"**Target Failures:** {', '.join(f'`{t}`' for t in targets)}")
            with c3:
                st.markdown(f"**Purpose:** {p.purpose}")

            st.markdown("###### Change Hypothesis")
            st.info(p.hypothesis)

            st.markdown("###### Full System Prompt Text")
            st.code(p.prompt_text, language="text")

        with tab2:
            st.markdown("##### Visual Prompt Diff Inspector")
            st.caption("Compare iterative changes between baseline and hardened operational prompts (e.g. V2 → V3 or V3 → V4).")

            cd1, cd2 = st.columns(2)
            with cd1:
                old_ver = st.selectbox("Base Version", [p.version for p in prompts], index=1)
            with cd2:
                new_ver = st.selectbox("Target Version", [p.version for p in prompts], index=2)

            if old_ver == new_ver:
                st.warning("Please select two distinct prompt versions to view diff.")
            else:
                p_old = prompt_map[old_ver]
                p_new = prompt_map[new_ver]
                diff_res = compute_prompt_diff(p_old.prompt_text, p_new.prompt_text, old_ver, new_ver)

                cm1, cm2, cm3 = st.columns(3)
                with cm1:
                    st.metric("Lines Added", f"+{diff_res.added_lines_count}")
                with cm2:
                    st.metric("Lines Removed", f"-{diff_res.deleted_lines_count}")
                with cm3:
                    st.metric("Net Change", f"{diff_res.added_lines_count - diff_res.deleted_lines_count:+d}")

                st.markdown("###### Unified Line Diff")
                # Render clean HTML diff block
                diff_html = '<div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 4px; padding: 10px;">'
                for d in diff_res.diff_lines:
                    if d.line_type == "insert":
                        diff_html += f'<div class="diff-insert">+ {d.text}</div>'
                    elif d.line_type == "delete":
                        diff_html += f'<div class="diff-delete">- {d.text}</div>'
                    else:
                        diff_html += f'<div class="diff-equal">&nbsp;&nbsp;{d.text}</div>'
                diff_html += "</div>"
                st.markdown(diff_html, unsafe_allow_html=True)

        with tab3:
            st.markdown("##### Traceable Prompt Change Ledger")
            st.caption("Experiments and observed benchmark impacts tracked systematically matching Section 41 specification.")

            ledgers = session.query(ChangeLedgerEntry).order_by(ChangeLedgerEntry.created_at.asc()).all()
            if ledgers:
                ledger_data = []
                for entry in ledgers:
                    targets = entry.target_failures if isinstance(entry.target_failures, list) else json.loads(entry.target_failures or "[]")
                    ledger_data.append({
                        "Version": entry.version,
                        "Change Description": entry.change_description,
                        "Hypothesis": entry.hypothesis,
                        "Target Failures": ", ".join(targets),
                        "Observed Result": entry.observed_result,
                        "Regression Status": entry.regression_status,
                    })
                st.dataframe(pd.DataFrame(ledger_data), use_container_width=True, hide_index=True)
            else:
                # Fallback display of specification ledger
                st.info("No recorded ledger entries in DB yet. Populating during database seed.")
