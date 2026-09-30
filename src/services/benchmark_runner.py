"""Benchmark Execution Engine and Result Persistence.

Executes scenarios in bulk across:
- smoke (6 scenarios: 1 normal pass, 1 trap, 1 ambiguous, 1 multi-turn, 1 contradiction, 1 escalation)
- core (60 scenarios: balanced across categories)
- full (200 scenarios: complete dataset)

Persists:
- benchmark_runs
- model_responses
- evaluations
- failure_events
- transcripts
"""

import time
import uuid
from datetime import datetime
from typing import Callable, Dict, List, Optional

from src.database.connection import get_db_session
from src.database.models import (
    BenchmarkRun,
    Evaluation,
    FailureEvent,
    ModelResponse,
    PromptVersion,
    TranscriptTurn,
)
from src.domain.scenario import ScenarioSchema
from src.evaluation.engine import evaluate_response
from src.llm.base_provider import ChatMessage
from src.llm.provider_factory import get_llm_provider
from src.utils.logger import get_logger, log_benchmark_event

logger = get_logger("benchmark_runner")


def select_benchmark_scenarios(
    all_scenarios: List[ScenarioSchema],
    mode: str = "core",
    limit: Optional[int] = None,
) -> List[ScenarioSchema]:
    """Filters scenarios based on benchmark level."""
    mode = mode.lower()
    if mode == "smoke":
        # At least: 1 normal pass, 1 hallucination trap, 1 ambiguous, 1 multi-turn, 1 contradiction, 1 escalation
        smoke_ids = ["SC-001", "SC-051", "SC-101", "SC-126", "SC-146", "SC-186"]
        filtered = [s for s in all_scenarios if s.scenario_id in smoke_ids]
        if len(filtered) < 6:
            # Fallback to first 6 if exact IDs not matched
            filtered = all_scenarios[:6]
        return filtered

    elif mode == "core":
        # 60 balanced scenarios across categories
        # Standard: 15, Ambiguous: 8, Edge: 8, Multi-turn: 8, Contradictory: 6, Trap: 6, Adversarial: 5, Policy: 4
        targets = {
            "Standard": 15,
            "Ambiguous": 8,
            "Edge Case": 8,
            "Multi-turn": 8,
            "Contradictory": 6,
            "Hallucination Trap": 6,
            "Adversarial": 5,
            "Policy / Escalation Sensitive": 4,
        }
        selected = []
        counts: Dict[str, int] = {k: 0 for k in targets}
        for s in all_scenarios:
            cat = s.category
            if cat in targets and counts[cat] < targets[cat]:
                selected.append(s)
                counts[cat] += 1
        return selected[:60]

    else:
        # Full benchmark (200 scenarios)
        return all_scenarios[:limit] if limit else all_scenarios


class BenchmarkRunner:
    def __init__(
        self,
        prompt_version: str,
        model_name: str = "gpt-4o-mini",
        provider_type: str = "mock",
        evaluation_mode: str = "core",
        dataset_version: str = "v1.0",
        judge_provider_type: str = "mock",
    ):
        self.prompt_version = prompt_version
        self.model_name = model_name
        self.provider_type = provider_type
        self.evaluation_mode = evaluation_mode
        self.dataset_version = dataset_version
        self.judge_provider_type = judge_provider_type
        self.provider = get_llm_provider(provider_type=provider_type, model=model_name)

    def run(
        self,
        scenarios: List[ScenarioSchema],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> str:
        """Executes the benchmark run, persists all results in relational DB, and returns benchmark_run_id."""
        run_id = f"RUN-{uuid.uuid4().hex[:10].upper()}"
        start_time = time.time()
        logger.info(f"Starting benchmark run {run_id} (mode={self.evaluation_mode}, prompt={self.prompt_version}, cases={len(scenarios)})")

        with get_db_session() as session:
            # 1. Fetch Prompt Text
            pv = session.query(PromptVersion).filter_by(version=self.prompt_version).first()
            prompt_text = pv.prompt_text if pv else "You are a customer support assistant."

            # 2. Initialize BenchmarkRun record
            bench_run = BenchmarkRun(
                benchmark_run_id=run_id,
                timestamp=datetime.utcnow(),
                prompt_version=self.prompt_version,
                model_name=self.model_name,
                evaluation_mode=self.evaluation_mode,
                dataset_version=self.dataset_version,
                total_scenarios=len(scenarios),
                passed_scenarios=0,
                failed_scenarios=0,
                average_score=0.0,
                duration_seconds=0.0,
            )
            session.add(bench_run)
            session.flush()

            passed_count = 0
            total_score_sum = 0.0

            # 3. Iterate through scenarios
            for idx, sc in enumerate(scenarios, 1):
                if progress_callback:
                    progress_callback(idx, len(scenarios), f"Running {sc.scenario_id} ({sc.category})")

                # Build messages
                messages = [
                    ChatMessage(role="system", content=f"{prompt_text}\n\nOPERATIONAL CONTEXT:\n{sc.context}"),
                ]
                for turn in sc.turns[:-1]:
                    messages.append(ChatMessage(role=turn.role, content=turn.content))
                # Add final turn
                messages.append(ChatMessage(role="user", content=sc.user_input))

                # Generate model response
                llm_resp = self.provider.generate(
                    messages=messages,
                    prompt_version=self.prompt_version,
                    scenario_id=sc.scenario_id,
                    scenario_context=sc.context,
                )

                # Persist ModelResponse
                resp_id = f"RESP-{uuid.uuid4().hex[:10].upper()}"
                m_resp = ModelResponse(
                    response_id=resp_id,
                    benchmark_run_id=run_id,
                    scenario_id=sc.scenario_id,
                    prompt_version=self.prompt_version,
                    model_name=self.model_name,
                    full_prompt=prompt_text,
                    raw_response=llm_resp.content,
                    latency_ms=llm_resp.latency_ms,
                    token_usage=llm_resp.token_usage,
                    status=llm_resp.status,
                    error_message=llm_resp.error_message,
                    created_at=datetime.utcnow(),
                )
                session.add(m_resp)
                session.flush()

                # Evaluate Response
                eval_res = evaluate_response(
                    response_text=llm_resp.content,
                    scenario=sc,
                    prompt_version=self.prompt_version,
                    judge_provider_override=self.judge_provider_type,
                )

                if eval_res.passed:
                    passed_count += 1
                total_score_sum += eval_res.overall_score

                # Persist Evaluation
                eval_id = f"EVAL-{uuid.uuid4().hex[:10].upper()}"
                db_eval = Evaluation(
                    evaluation_id=eval_id,
                    benchmark_run_id=run_id,
                    scenario_id=sc.scenario_id,
                    response_id=resp_id,
                    prompt_version=self.prompt_version,
                    accuracy_score=eval_res.dimensions.accuracy,
                    groundedness_score=eval_res.dimensions.groundedness,
                    instruction_following_score=eval_res.dimensions.instruction_following,
                    relevance_score=eval_res.dimensions.relevance,
                    consistency_score=eval_res.dimensions.consistency,
                    safety_score=eval_res.dimensions.safety,
                    clarity_score=eval_res.dimensions.clarity,
                    overall_score=eval_res.overall_score,
                    passed=eval_res.passed,
                    is_critical_fail=eval_res.is_critical_fail,
                    layer_results={
                        "layer1": eval_res.layer1.model_dump(),
                        "layer2": eval_res.layer2.model_dump(),
                        "layer3": eval_res.layer3.model_dump(),
                        "layer4": eval_res.layer4.model_dump(),
                    },
                    evaluator_mode=f"{self.provider_type}_and_{self.judge_provider_type}",
                    created_at=datetime.utcnow(),
                )
                session.add(db_eval)
                session.flush()

                # Persist Failures
                for f in eval_res.failures:
                    fail_id = f"FAIL-{uuid.uuid4().hex[:10].upper()}"
                    db_fail = FailureEvent(
                        failure_id=fail_id,
                        scenario_id=sc.scenario_id,
                        benchmark_run_id=run_id,
                        evaluation_id=eval_id,
                        prompt_version=self.prompt_version,
                        failure_type=f.failure_type,
                        severity=f.severity,
                        evidence=f.evidence,
                        diagnosis=f.diagnosis,
                        recommended_fix=f.recommended_fix,
                        created_at=datetime.utcnow(),
                    )
                    session.add(db_fail)

                # Persist Transcript Turns
                # User turns from scenario
                for t in sc.turns:
                    session.add(TranscriptTurn(
                        transcript_id=f"TR-{uuid.uuid4().hex[:10].upper()}",
                        benchmark_run_id=run_id,
                        response_id=resp_id,
                        scenario_id=sc.scenario_id,
                        turn_index=t.turn_index,
                        role=t.role,
                        content=t.content,
                        has_failure=False,
                    ))
                # Final assistant response turn
                final_has_fail = len(eval_res.failures) > 0
                first_f = eval_res.failures[0].failure_type if final_has_fail else None
                session.add(TranscriptTurn(
                    transcript_id=f"TR-{uuid.uuid4().hex[:10].upper()}",
                    benchmark_run_id=run_id,
                    response_id=resp_id,
                    scenario_id=sc.scenario_id,
                    turn_index=len(sc.turns),
                    role="assistant",
                    content=llm_resp.content,
                    has_failure=final_has_fail,
                    failure_type=first_f,
                ))

                log_benchmark_event(
                    logger=logger,
                    run_id=run_id,
                    scenario_id=sc.scenario_id,
                    prompt_version=self.prompt_version,
                    model=self.model_name,
                    status=llm_resp.status,
                    latency_ms=llm_resp.latency_ms,
                    evaluation_status="PASS" if eval_res.passed else "FAIL",
                    extra={"score": f"{eval_res.overall_score:.1f}"}
                )

            # 4. Finalize Benchmark Run Stats
            total_cases = len(scenarios)
            final_avg_score = round(total_score_sum / total_cases, 2) if total_cases > 0 else 0.0
            bench_run.passed_scenarios = passed_count
            bench_run.failed_scenarios = total_cases - passed_count
            bench_run.average_score = final_avg_score
            bench_run.duration_seconds = round(time.time() - start_time, 2)

        logger.info(f"Completed run {run_id}: {passed_count}/{len(scenarios)} passed ({final_avg_score:.1f}% avg)")
        return run_id
