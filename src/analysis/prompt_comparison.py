"""Prompt Comparison and Python-Native Unified Diff Engine."""

import difflib
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database.connection import get_db_session
from src.database.models import BenchmarkRun, Evaluation, FailureEvent, ModelResponse, PromptVersion


class PromptVersionMetrics(BaseModel):
    version: str
    name: str
    run_id: str
    test_count: int
    average_score: float
    pass_rate: float
    hallucination_rate: float  # F1
    instruction_failure_rate: float  # F2
    context_failure_rate: float  # F4 in multi-turn
    critical_failures: int
    average_latency_ms: float
    score_uplift_vs_v1: float = 0.0


class DiffLine(BaseModel):
    line_type: str  # "equal", "insert", "delete"
    text: str
    line_num_old: Optional[int] = None
    line_num_new: Optional[int] = None


class PromptDiffResult(BaseModel):
    old_version: str
    new_version: str
    old_text: str
    new_text: str
    added_lines_count: int
    deleted_lines_count: int
    unified_diff: List[str]
    diff_lines: List[DiffLine]


def compute_prompt_diff(old_text: str, new_text: str, old_version: str, new_version: str) -> PromptDiffResult:
    """Computes python-native line diff between two prompt versions."""
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    diff_lines: List[DiffLine] = []
    added = 0
    deleted = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for idx, line in enumerate(old_lines[i1:i2]):
                diff_lines.append(DiffLine(
                    line_type="equal",
                    text=line,
                    line_num_old=i1 + idx + 1,
                    line_num_new=j1 + idx + 1
                ))
        elif tag == "delete":
            for idx, line in enumerate(old_lines[i1:i2]):
                deleted += 1
                diff_lines.append(DiffLine(
                    line_type="delete",
                    text=line,
                    line_num_old=i1 + idx + 1,
                    line_num_new=None
                ))
        elif tag == "insert":
            for idx, line in enumerate(new_lines[j1:j2]):
                added += 1
                diff_lines.append(DiffLine(
                    line_type="insert",
                    text=line,
                    line_num_old=None,
                    line_num_new=j1 + idx + 1
                ))
        elif tag == "replace":
            for idx, line in enumerate(old_lines[i1:i2]):
                deleted += 1
                diff_lines.append(DiffLine(
                    line_type="delete",
                    text=line,
                    line_num_old=i1 + idx + 1,
                    line_num_new=None
                ))
            for idx, line in enumerate(new_lines[j1:j2]):
                added += 1
                diff_lines.append(DiffLine(
                    line_type="insert",
                    text=line,
                    line_num_old=None,
                    line_num_new=j1 + idx + 1
                ))

    raw_unified = list(difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"Prompt {old_version}",
        tofile=f"Prompt {new_version}",
        lineterm=""
    ))

    return PromptDiffResult(
        old_version=old_version,
        new_version=new_version,
        old_text=old_text,
        new_text=new_text,
        added_lines_count=added,
        deleted_lines_count=deleted,
        unified_diff=raw_unified,
        diff_lines=diff_lines,
    )


def compare_prompt_benchmarks(
    run_ids: Optional[List[str]] = None,
    session: Optional[Session] = None,
) -> List[PromptVersionMetrics]:
    """Generates comparative operational metrics across benchmark runs."""

    def _query(s: Session) -> List[PromptVersionMetrics]:
        # If run_ids provided, filter by them, else pick the latest run per prompt version
        if run_ids:
            runs = s.query(BenchmarkRun).filter(BenchmarkRun.benchmark_run_id.in_(run_ids)).all()
        else:
            # Pick latest run for V1, V2, V3, V4
            runs = []
            for ver in ["V1", "V2", "V3", "V4"]:
                latest = (
                    s.query(BenchmarkRun)
                    .filter_by(prompt_version=ver)
                    .order_by(BenchmarkRun.timestamp.desc())
                    .first()
                )
                if latest:
                    runs.append(latest)

        results: List[PromptVersionMetrics] = []
        v1_score = None

        for r in sorted(runs, key=lambda x: x.prompt_version):
            evals = s.query(Evaluation).filter_by(benchmark_run_id=r.benchmark_run_id).all()
            if not evals:
                continue

            test_count = len(evals)
            passed = sum(1 for e in evals if e.passed)
            pass_rate = round((passed / test_count) * 100.0, 2)
            avg_score = round(sum(e.overall_score for e in evals) / test_count, 2)

            # Failures breakdown
            failures = s.query(FailureEvent).filter_by(benchmark_run_id=r.benchmark_run_id).all()
            f1_cases = len(set(f.scenario_id for f in failures if f.failure_type == "F1"))
            f2_cases = len(set(f.scenario_id for f in failures if f.failure_type == "F2"))
            f4_cases = len(set(f.scenario_id for f in failures if f.failure_type == "F4"))
            crit_fails = sum(1 for f in failures if f.severity == "critical")

            h_rate = round((f1_cases / test_count) * 100.0, 2)
            i_rate = round((f2_cases / test_count) * 100.0, 2)
            c_rate = round((f4_cases / test_count) * 100.0, 2)

            # Latency
            responses = s.query(ModelResponse).filter_by(benchmark_run_id=r.benchmark_run_id).all()
            avg_lat = round(sum(resp.latency_ms for resp in responses) / len(responses), 1) if responses else 0.0

            pv = s.query(PromptVersion).filter_by(version=r.prompt_version).first()
            p_name = pv.name if pv else r.prompt_version

            if r.prompt_version == "V1":
                v1_score = avg_score

            uplift = round(avg_score - v1_score, 2) if v1_score is not None else 0.0

            results.append(PromptVersionMetrics(
                version=r.prompt_version,
                name=p_name,
                run_id=r.benchmark_run_id,
                test_count=test_count,
                average_score=avg_score,
                pass_rate=pass_rate,
                hallucination_rate=h_rate,
                instruction_failure_rate=i_rate,
                context_failure_rate=c_rate,
                critical_failures=crit_fails,
                average_latency_ms=avg_lat,
                score_uplift_vs_v1=uplift,
            ))

        return results

    if session:
        return _query(session)
    with get_db_session() as s:
        return _query(s)
