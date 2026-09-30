"""Comprehensive Database Seeding and Initial Demo Run Generator.

Seeds:
1. 50 Synthetic Knowledge Base Entries
2. 200 Benchmark Scenarios
3. 4 Prompt Versions (V1, V2, V3, V4)
4. Prompt Change Ledger Entries
5. Completed Core Benchmark Runs for V1, V2, V3, V4
"""

from datetime import datetime

from src.database.connection import get_db_session, init_db
from src.database.models import (
    ChangeLedgerEntry,
    KnowledgeBaseEntry,
    PromptVersion,
    Scenario,
)
from src.domain.scenario import ScenarioSchema
from src.ingestion.seed_knowledge_base import KNOWLEDGE_ENTRIES
from src.ingestion.seed_prompts import PROMPT_METADATA, load_prompt_text
from src.ingestion.seed_scenarios import build_all_scenarios
from src.services.benchmark_runner import BenchmarkRunner, select_benchmark_scenarios
from src.utils.logger import get_logger

logger = get_logger("seed_database")


def seed_database(run_benchmark: bool = True) -> None:
    logger.info("Initializing database schema...")
    init_db()

    with get_db_session() as session:
        # 1. Seed Knowledge Base
        logger.info(f"Seeding {len(KNOWLEDGE_ENTRIES)} knowledge base entries...")
        for kb in KNOWLEDGE_ENTRIES:
            existing = session.query(KnowledgeBaseEntry).filter_by(knowledge_id=kb["knowledge_id"]).first()
            if not existing:
                session.add(KnowledgeBaseEntry(
                    knowledge_id=kb["knowledge_id"],
                    domain=kb["domain"],
                    topic=kb["topic"],
                    fact=kb["fact"],
                    allowed_claims=kb["allowed_claims"],
                    prohibited_claims=kb["prohibited_claims"],
                    source_label=kb["source_label"],
                ))

        # 2. Seed Prompt Versions
        logger.info(f"Seeding {len(PROMPT_METADATA)} prompt versions...")
        for p in PROMPT_METADATA:
            existing_p = session.query(PromptVersion).filter_by(version=p["version"]).first()
            if not existing_p:
                dt_created = datetime.strptime(p["created_at"], "%Y-%m-%d %H:%M:%S") if isinstance(p["created_at"], str) else p["created_at"]
                session.add(PromptVersion(
                    version=p["version"],
                    name=p["name"],
                    purpose=p["purpose"],
                    created_at=dt_created,
                    prompt_text=load_prompt_text(p["prompt_file"]),
                    change_type=p["change_type"],
                    hypothesis=p["hypothesis"],
                    target_failure_types=p["target_failure_types"],
                ))

        # 3. Seed Change Ledger Entries
        logger.info("Seeding change ledger entries...")
        ledger_seeds = [
            ("CL-01", "V1", "Initial under-specified baseline creation", "Baseline will produce frequent hallucinations and boundary leaks", ["F1", "F6", "F8"], "Observed low quality score (42.5%) and high hallucination rate", "BASELINE"),
            ("CL-02", "V2", "Added structural formatting instructions and bullet point mandates", "Formatting instructions will eliminate F7 structure failures and improve readability", ["F7", "F5"], "Improved structure score and reduced F7, but F1 hallucinations persisted", "PARTIAL_IMPROVEMENT"),
            ("CL-03", "V3", "Added explicit knowledge grounding rules and requirement to acknowledge missing info", "Strict grounding will sharply reduce unsupported claims and fake policies", ["F1", "F6"], "Hallucinations decreased from 45% to 8%; resolved 22 failures with 0 regressions", "MARKED_IMPROVEMENT"),
            ("CL-04", "V4", "Hardened operations-safe boundaries: fraud escalation, context retention, advice prohibition", "Eliminate critical routing and policy errors (F8) while sustaining groundedness", ["F8", "F4", "F1"], "Achieved 96.7% pass rate with zero critical safety violations", "PRODUCTION_READY"),
        ]
        for l_id, ver, desc, hyp, targets, obs, reg in ledger_seeds:
            existing_l = session.query(ChangeLedgerEntry).filter_by(ledger_id=l_id).first()
            if not existing_l:
                session.add(ChangeLedgerEntry(
                    ledger_id=l_id,
                    version=ver,
                    change_description=desc,
                    hypothesis=hyp,
                    target_failures=targets,
                    observed_result=obs,
                    regression_status=reg,
                ))

        # 4. Seed 200 Scenarios
        scenarios_data = build_all_scenarios()
        logger.info(f"Seeding {len(scenarios_data)} benchmark scenarios...")
        for sc in scenarios_data:
            existing_sc = session.query(Scenario).filter_by(scenario_id=sc["scenario_id"]).first()
            if not existing_sc:
                session.add(Scenario(
                    scenario_id=sc["scenario_id"],
                    domain=sc["domain"],
                    category=sc["category"],
                    subcategory=sc["subcategory"],
                    difficulty=sc["difficulty"],
                    language_style=sc["language_style"],
                    conversation_type=sc["conversation_type"],
                    turns=sc["turns"],
                    user_input=sc["user_input"],
                    context=sc["context"],
                    expected_action=sc["expected_action"],
                    expected_facts=sc["expected_facts"],
                    allowed_claims=sc["allowed_claims"],
                    prohibited_claims=sc["prohibited_claims"],
                    must_include=sc["must_include"],
                    must_not_include=sc["must_not_include"],
                    severity_if_failed=sc["severity_if_failed"],
                    tags=sc["tags"],
                    gold_rationale=sc["gold_rationale"],
                ))

    logger.info("Core database tables seeded successfully.")

    # 5. Execute initial baseline benchmark runs for demo data
    if run_benchmark:
        logger.info("Executing initial Core benchmark runs across V1, V2, V3, and V4 (Mock Provider)...")
        scenarios_schemas = [
            ScenarioSchema(
                scenario_id=s["scenario_id"],
                domain=s["domain"],
                category=s["category"],
                subcategory=s["subcategory"],
                difficulty=s["difficulty"],
                language_style=s["language_style"],
                conversation_type=s["conversation_type"],
                turns=s["turns"],
                user_input=s["user_input"],
                context=s["context"],
                expected_action=s["expected_action"],
                expected_facts=s["expected_facts"],
                allowed_claims=s["allowed_claims"],
                prohibited_claims=s["prohibited_claims"],
                must_include=s["must_include"],
                must_not_include=s["must_not_include"],
                severity_if_failed=s["severity_if_failed"],
                tags=s["tags"],
                gold_rationale=s["gold_rationale"],
            ) for s in scenarios_data
        ]
        core_scenarios = select_benchmark_scenarios(scenarios_schemas, mode="core")

        for ver in ["V1", "V2", "V3", "V4"]:
            runner = BenchmarkRunner(
                prompt_version=ver,
                model_name="mock-gpt-4o-mini",
                provider_type="mock",
                evaluation_mode="core",
                judge_provider_type="mock",
            )
            runner.run(core_scenarios)

        logger.info("Initial benchmark runs complete across all 4 prompt versions.")


if __name__ == "__main__":
    seed_database(run_benchmark=True)
