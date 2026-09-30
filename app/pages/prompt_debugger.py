"""View 6: Interactive Prompt Debugger & Live Retest Sandbox.

Features:
1. Scenario & Prompt Version Inspector matching Section 39 specification:
   - PROMPT (full prompt text)
   - SCENARIO (customer message, operational context, expected behavior)
   - RESPONSE (actual model response)
   - EVALUATION (dimension scores: accuracy, groundedness, instruction, relevance, consistency, safety, clarity)
   - FAILURES (F1..F8 codes and severity)
   - DIAGNOSIS (concise root-cause explanation)
   - RECOMMENDED FIX (specific prompt modification)
   - REVISED PROMPT (editable text area for iterative prompt debugging)
   - RETEST (instant re-evaluation of revised prompt against the scenario)
2. Failure Fingerprint Tool matching Section 43:
   - Lineage of single scenario across V1 -> V2 -> V3 -> V4
"""

import pandas as pd
import streamlit as st

from app.components.cards import render_header
from src.analysis.regression import get_scenario_fingerprint
from src.database.connection import get_db_session
from src.database.models import Evaluation, FailureEvent, ModelResponse, PromptVersion, Scenario
from src.domain.scenario import ScenarioSchema
from src.evaluation.engine import evaluate_response
from src.llm.base_provider import ChatMessage
from src.llm.provider_factory import get_llm_provider


def render_prompt_debugger():
    render_header(title="Prompt Debugger & Scenario Retest Sandbox", benchmark_label="Prompt Debugger")

    tab1, tab2 = st.tabs(["Iterative Prompt Debugger", "Scenario Failure Fingerprint"])

    with get_db_session() as session:
        scenarios = session.query(Scenario).order_by(Scenario.scenario_id.asc()).all()
        prompts = session.query(PromptVersion).order_by(PromptVersion.version.asc()).all()

        if not scenarios or not prompts:
            st.warning("Database contains no scenarios or prompt versions. Run database seed first.")
            return

        with tab1:
            st.markdown("##### 1. Select Inspection Target")
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                sel_sc_id = st.selectbox(
                    "Select Scenario",
                    [s.scenario_id for s in scenarios],
                    format_func=lambda sid: f"{sid} — {next(s.category for s in scenarios if s.scenario_id == sid)} ({next(s.subcategory for s in scenarios if s.scenario_id == sid)})"
                )
            with s_col2:
                sel_pv = st.selectbox("Select Prompt Version", [p.version for p in prompts], index=0)

            active_sc = next(s for s in scenarios if s.scenario_id == sel_sc_id)
            active_pv = next(p for p in prompts if p.version == sel_pv)

            # Fetch existing evaluation and model response if present
            eval_record = (
                session.query(Evaluation)
                .filter_by(scenario_id=sel_sc_id, prompt_version=sel_pv)
                .order_by(Evaluation.created_at.desc())
                .first()
            )
            resp_record = (
                session.query(ModelResponse)
                .filter_by(scenario_id=sel_sc_id, prompt_version=sel_pv)
                .order_by(ModelResponse.created_at.desc())
                .first()
            )

            # Debugger Layout (Section 39)
            col_left, col_right = st.columns([1, 1])

            with col_left:
                st.markdown("###### SCENARIO CONTEXT & INPUT")
                st.markdown(f"**Customer Message:** `{active_sc.user_input}`")
                st.markdown(f"**Operational Context:**\n> {active_sc.context}")
                st.markdown(f"**Expected Action:** `{active_sc.expected_action}`")

                st.markdown("###### ACTIVE SYSTEM PROMPT")
                st.code(active_pv.prompt_text, language="text")

                st.markdown("###### MODEL RESPONSE")
                if resp_record:
                    st.code(resp_record.raw_response, language="text")
                else:
                    st.caption("No historical response found for this combination.")

            with col_right:
                st.markdown("###### EVALUATION & SCORES")
                if eval_record:
                    score_cols = st.columns(4)
                    with score_cols[0]:
                        st.metric("Overall", f"{eval_record.overall_score:.1f}%")
                    with score_cols[1]:
                        st.metric("Grounded", f"{eval_record.groundedness_score:.1f}/5")
                    with score_cols[2]:
                        st.metric("Safety", f"{eval_record.safety_score:.1f}/5")
                    with score_cols[3]:
                        st.metric("Status", "PASS" if eval_record.passed else "FAIL")

                    # Failures
                    failures = session.query(FailureEvent).filter_by(evaluation_id=eval_record.evaluation_id).all()
                    if failures:
                        st.markdown("###### DETECTED FAILURES & DIAGNOSIS")
                        for f in failures:
                            st.error(f"**{f.failure_type} ({f.severity.upper()})**: {f.evidence}")
                            st.markdown(f"**Diagnosis:** {f.diagnosis}")
                            st.markdown(f"**Recommended Prompt Fix:** {f.recommended_fix}")
                    else:
                        st.success("All evaluation dimensions passed successfully with no detected failures.")
                else:
                    st.caption("No evaluation records available. Use Retest below to generate evaluation.")

            st.markdown("---")
            st.markdown("##### 2. Prompt Revision & Retest Sandbox")
            st.caption("Modify or add instructions to the prompt text below and retest instantly against this scenario.")

            default_revised = active_pv.prompt_text + "\n- Explicitly ensure grounded facts and safety boundaries."
            revised_prompt_text = st.text_area("Revised Prompt Text", value=default_revised, height=140)

            if st.button("Retest Scenario with Revised Prompt", type="primary"):
                # Execute generation and evaluation
                provider = get_llm_provider("mock", model="mock-gpt-4o-mini")

                messages = [
                    ChatMessage(role="system", content=f"{revised_prompt_text}\n\nOPERATIONAL CONTEXT:\n{active_sc.context}"),
                    ChatMessage(role="user", content=active_sc.user_input)
                ]

                # Run provider
                retest_resp = provider.generate(messages, prompt_version="Revised", scenario_id=active_sc.scenario_id, scenario_context=active_sc.context)

                # Schema format
                sc_schema = ScenarioSchema(
                    scenario_id=active_sc.scenario_id,
                    domain=active_sc.domain,
                    category=active_sc.category,
                    subcategory=active_sc.subcategory,
                    difficulty=active_sc.difficulty,
                    language_style=active_sc.language_style,
                    conversation_type=active_sc.conversation_type,
                    turns=active_sc.turns,
                    user_input=active_sc.user_input,
                    context=active_sc.context,
                    expected_action=active_sc.expected_action,
                    expected_facts=active_sc.expected_facts,
                    allowed_claims=active_sc.allowed_claims,
                    prohibited_claims=active_sc.prohibited_claims,
                    must_include=active_sc.must_include,
                    must_not_include=active_sc.must_not_include,
                    severity_if_failed=active_sc.severity_if_failed,
                    tags=active_sc.tags,
                    gold_rationale=active_sc.gold_rationale,
                )

                retest_eval = evaluate_response(retest_resp.content, sc_schema, prompt_version="V4")

                st.markdown("###### RETEST OUTCOME")
                rc1, rc2 = st.columns(2)
                with rc1:
                    st.markdown("**New Model Response:**")
                    st.code(retest_resp.content, language="text")
                with rc2:
                    st.markdown(f"**New Quality Score:** {retest_eval.overall_score:.1f}% ({'PASS' if retest_eval.passed else 'FAIL'})")
                    if retest_eval.failures:
                        for rf in retest_eval.failures:
                            st.warning(f"{rf.failure_type}: {rf.evidence}")
                    else:
                        st.success("Clean pass: No failures detected with the revised prompt instructions!")

        with tab2:
            st.markdown("##### Failure Fingerprint Lineage (Section 43)")
            st.caption("Inspect how a single operational scenario behaves across all four prompt versions (V1 → V2 → V3 → V4).")

            fp_sc_id = st.selectbox("Select Scenario for Fingerprint", [s.scenario_id for s in scenarios], key="fp_select")
            try:
                fingerprint = get_scenario_fingerprint(fp_sc_id, session=session)

                st.markdown(f"**Scenario:** `{fingerprint.scenario_id}` • **Category:** {fingerprint.category} • **Topic:** {fingerprint.subcategory}")
                st.markdown(f"**Customer Query:** {fingerprint.user_input}")

                # Display table of states across versions
                fp_data = []
                for st_item in fingerprint.history:
                    fail_str = ", ".join(st_item.failures) if st_item.failures else "None (Clean Pass)"
                    fp_data.append({
                        "Prompt Version": st_item.prompt_version,
                        "Run ID": st_item.run_id,
                        "Status": "PASS" if st_item.passed else "FAIL",
                        "Quality Score": f"{st_item.overall_score}%",
                        "Active Failures": fail_str,
                        "Max Severity": st_item.severity.upper() if st_item.failures else "N/A"
                    })

                if fp_data:
                    st.dataframe(pd.DataFrame(fp_data), use_container_width=True, hide_index=True)
                    if fingerprint.resolved_at_version:
                        st.success(f"Issue verified resolved starting at prompt version: **{fingerprint.resolved_at_version}**")
                    if fingerprint.has_regressed:
                        st.error("Regression Warning: This scenario passed in an earlier prompt version but subsequently failed.")
                else:
                    st.info("No comparative historical evaluations recorded yet for this scenario.")
            except Exception as e:
                st.error(f"Could not load fingerprint: {e}")
