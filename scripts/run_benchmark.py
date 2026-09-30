"""Bulk Benchmark CLI Runner for FinEval.

Allows executing Core or Full benchmark runs from terminal without opening Streamlit:
Usage: python -m scripts.run_benchmark --level core --prompt V4 --model gpt-4o-mini
"""

import argparse
import sys

from src.database.connection import get_db_session, init_db
from src.database.models import Scenario
from src.domain.scenario import ScenarioSchema
from src.services.benchmark_runner import BenchmarkRunner, select_benchmark_scenarios
from src.utils.logger import get_logger

logger = get_logger("run_benchmark_cli")


def main():
    parser = argparse.ArgumentParser(description="FinEval Bulk Benchmark Runner CLI")
    parser.add_argument("--level", choices=["smoke", "core", "full"], default="core", help="Benchmark level")
    parser.add_argument("--prompt", choices=["V1", "V2", "V3", "V4"], default="V4", help="Prompt version")
    parser.add_argument("--provider", choices=["mock", "live"], default="mock", help="Provider mode")
    parser.add_argument("--model", default="gpt-4o-mini", help="Model name")
    args = parser.parse_args()

    init_db()

    with get_db_session() as session:
        db_scenarios = session.query(Scenario).all()
        if not db_scenarios:
            logger.error("No scenarios found in database. Run seed_database.py first.")
            sys.exit(1)

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

    selected = select_benchmark_scenarios(scenarios, mode=args.level)
    logger.info(f"Selected {len(selected)} scenarios for level={args.level}, prompt={args.prompt}, provider={args.provider}...")

    runner = BenchmarkRunner(
        prompt_version=args.prompt,
        model_name=args.model,
        provider_type=args.provider,
        evaluation_mode=args.level,
        judge_provider_type="mock" if args.provider == "mock" else "live",
    )

    run_id = runner.run(selected)
    print(f"Benchmark run complete. Run ID: {run_id}")


if __name__ == "__main__":
    main()
