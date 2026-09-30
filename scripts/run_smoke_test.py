"""Deterministic Smoke Benchmark Runner for FinEval.

Runs 6 distinct scenarios covering:
- Normal pass
- Hallucination trap
- Ambiguous inquiry
- Multi-turn interaction
- Contradictory customer input
- Emergency / fraud escalation

Succeeds quickly and verifies the end-to-end evaluation pipeline.
"""

import sys

from src.database.connection import get_db_session, init_db
from src.database.models import Scenario
from src.domain.scenario import ScenarioSchema
from src.services.benchmark_runner import BenchmarkRunner, select_benchmark_scenarios
from src.utils.logger import get_logger

logger = get_logger("smoke_test")


def run_smoke_test() -> bool:
    init_db()

    with get_db_session() as session:
        db_scenarios = session.query(Scenario).all()
        if not db_scenarios:
            logger.error("No scenarios in database. Run seed_database.py first.")
            return False

        scenarios = [
            ScenarioSchema(
                scenario_id=s.scenario_id,
                domain=s.domain,
                category=s.category,
                subcategory=s.subcategory,
                difficulty=s.difficulty,
                language_style=s.language_style,
                conversation_type=s.conversation_type,
                turns=s.turns,
                user_input=s.user_input,
                context=s.context,
                expected_action=s.expected_action,
                expected_facts=s.expected_facts,
                allowed_claims=s.allowed_claims,
                prohibited_claims=s.prohibited_claims,
                must_include=s.must_include,
                must_not_include=s.must_not_include,
                severity_if_failed=s.severity_if_failed,
                tags=s.tags,
                gold_rationale=s.gold_rationale,
            ) for s in db_scenarios
        ]

    smoke_cases = select_benchmark_scenarios(scenarios, mode="smoke")
    logger.info(f"Running deterministic smoke benchmark with {len(smoke_cases)} scenarios on V4 prompt...")

    runner = BenchmarkRunner(
        prompt_version="V4",
        model_name="mock-gpt-4o-mini",
        provider_type="mock",
        evaluation_mode="smoke",
        judge_provider_type="mock",
    )

    run_id = runner.run(smoke_cases)
    logger.info(f"Smoke benchmark completed successfully. Run ID: {run_id}")
    return True


if __name__ == "__main__":
    success = run_smoke_test()
    if not success:
        sys.exit(1)
    print("Smoke test passed successfully!")
