"""Regression Detection Engine and Failure Fingerprint Service.

Features:
1. Regression Detection: Compares run A (prior) vs run B (new).
   - Resolved failures (improved cases)
   - Newly introduced failures (regressions)
   - Unchanged failures (persistent issues)
   - Net change calculation and regression status
2. Failure Fingerprint: Multi-prompt lineage of a specific scenario (V1 -> V2 -> V3 -> V4)
"""

from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.connection import get_db_session
from src.database.models import Evaluation, Scenario


class RegressionReport(BaseModel):
    prior_run_id: str
    new_run_id: str
    prior_prompt_version: str
    new_prompt_version: str
    total_evaluated_cases: int
    prior_pass_rate: float
    new_pass_rate: float
    pass_rate_uplift: float
    resolved_failure_count: int
    resolved_scenario_ids: List[str] = Field(default_factory=list)
    new_regression_count: int
    regressed_scenario_ids: List[str] = Field(default_factory=list)
    persistent_failure_count: int
    persistent_scenario_ids: List[str] = Field(default_factory=list)
    is_mixed_impact: bool
    summary_verdict: str


class PromptScenarioState(BaseModel):
    prompt_version: str
    run_id: str
    passed: bool
    overall_score: float
    failures: List[str] = Field(default_factory=list)
    severity: str


class FailureFingerprint(BaseModel):
    scenario_id: str
    category: str
    subcategory: str
    user_input: str
    history: List[PromptScenarioState] = Field(default_factory=list)
    resolved_at_version: Optional[str] = None
    has_regressed: bool = False


def detect_regressions(
    prior_run_id: str,
    new_run_id: str,
    session: Optional[Session] = None,
) -> RegressionReport:
    """Analyzes benchmark diff between two runs to identify resolved issues vs new regressions."""

    def _query(s: Session) -> RegressionReport:
        prior_evals = {e.scenario_id: e for e in s.query(Evaluation).filter_by(benchmark_run_id=prior_run_id).all()}
        new_evals = {e.scenario_id: e for e in s.query(Evaluation).filter_by(benchmark_run_id=new_run_id).all()}

        common_ids = set(prior_evals.keys()).intersection(set(new_evals.keys()))
        prior_p_ver = prior_evals[next(iter(common_ids))].prompt_version if common_ids else "Unknown"
        new_p_ver = new_evals[next(iter(common_ids))].prompt_version if common_ids else "Unknown"

        resolved = []
        regressed = []
        persistent = []

        prior_passes = sum(1 for e in prior_evals.values() if e.passed)
        new_passes = sum(1 for e in new_evals.values() if e.passed)

        for s_id in common_ids:
            p_pass = prior_evals[s_id].passed
            n_pass = new_evals[s_id].passed

            if not p_pass and n_pass:
                resolved.append(s_id)
            elif p_pass and not n_pass:
                regressed.append(s_id)
            elif not p_pass and not n_pass:
                persistent.append(s_id)

        prior_rate = (prior_passes / len(prior_evals) * 100.0) if prior_evals else 0.0
        new_rate = (new_passes / len(new_evals) * 100.0) if new_evals else 0.0
        uplift = round(new_rate - prior_rate, 2)

        is_mixed = len(resolved) > 0 and len(regressed) > 0

        if len(regressed) == 0 and len(resolved) > 0:
            verdict = f"Pure Quality Improvement: Fixed {len(resolved)} failures with 0 regressions."
        elif is_mixed:
            verdict = f"Mixed Impact: Fixed {len(resolved)} failures, but introduced {len(regressed)} new regressions."
        elif len(resolved) == 0 and len(regressed) > 0:
            verdict = f"Net Negative Regression: Introduced {len(regressed)} new failures without resolving issues."
        else:
            verdict = "Neutral Impact: Quality metrics remained unchanged."

        return RegressionReport(
            prior_run_id=prior_run_id,
            new_run_id=new_run_id,
            prior_prompt_version=prior_p_ver,
            new_prompt_version=new_p_ver,
            total_evaluated_cases=len(common_ids),
            prior_pass_rate=round(prior_rate, 2),
            new_pass_rate=round(new_rate, 2),
            pass_rate_uplift=uplift,
            resolved_failure_count=len(resolved),
            resolved_scenario_ids=sorted(resolved),
            new_regression_count=len(regressed),
            regressed_scenario_ids=sorted(regressed),
            persistent_failure_count=len(persistent),
            persistent_scenario_ids=sorted(persistent),
            is_mixed_impact=is_mixed,
            summary_verdict=verdict,
        )

    if session:
        return _query(session)
    with get_db_session() as s:
        return _query(s)


def get_scenario_fingerprint(
    scenario_id: str,
    session: Optional[Session] = None,
) -> FailureFingerprint:
    """Extracts scenario lifecycle across all prompt versions."""

    def _query(s: Session) -> FailureFingerprint:
        sc = s.query(Scenario).filter_by(scenario_id=scenario_id).first()
        if not sc:
            raise ValueError(f"Scenario {scenario_id} not found.")

        # Find evaluations across all runs ordered by timestamp
        evals = (
            s.query(Evaluation)
            .filter_by(scenario_id=scenario_id)
            .order_by(Evaluation.created_at.asc())
            .all()
        )

        history: List[PromptScenarioState] = []
        resolved_at = None
        has_regressed = False
        last_pass = None

        for ev in evals:
            # Get failure types for this evaluation
            fails = [f.failure_type for f in ev.failures]
            sev = ev.failures[0].severity if fails else "low"

            state = PromptScenarioState(
                prompt_version=ev.prompt_version,
                run_id=ev.benchmark_run_id,
                passed=ev.passed,
                overall_score=round(ev.overall_score, 1),
                failures=fails,
                severity=sev,
            )
            history.append(state)

            if ev.passed and resolved_at is None:
                resolved_at = ev.prompt_version

            if last_pass is True and not ev.passed:
                has_regressed = True
            last_pass = ev.passed

        return FailureFingerprint(
            scenario_id=scenario_id,
            category=sc.category,
            subcategory=sc.subcategory,
            user_input=sc.user_input,
            history=history,
            resolved_at_version=resolved_at,
            has_regressed=has_regressed,
        )

    if session:
        return _query(session)
    with get_db_session() as s:
        return _query(s)
