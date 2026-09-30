"""Power BI & SQL Data Model Generator for FinEval.

Generates star-schema dimensional tables ready for Power BI consumption:
- Dim_Prompt (Version, Name, Purpose, Change Type, Hypothesis)
- Dim_Scenario (Scenario ID, Domain, Category, Subcategory, Difficulty, Severity)
- Dim_FailureTaxonomy (Code, Name, Description, Default Severity, Remediation)
- Fact_Evaluation (Evaluation ID, Run ID, Scenario ID, Version, Scores, Passed, Latency)
- Fact_FailureEvent (Failure ID, Evaluation ID, Scenario ID, Version, Failure Type, Severity)

Saves clean CSVs to data/powerbi/ for instant Power BI import.
"""

from pathlib import Path

import pandas as pd

from src.database.connection import get_db_session
from src.database.models import (
    Evaluation,
    FailureEvent,
    ModelResponse,
    PromptVersion,
    Scenario,
)
from src.domain.failure_taxonomy import FAILURE_TAXONOMY


def export_power_bi_star_schema():
    pbi_dir = Path("data/powerbi")
    pbi_dir.mkdir(parents=True, exist_ok=True)

    with get_db_session() as session:
        # 1. Dim_Prompt
        prompts = session.query(PromptVersion).all()
        df_dim_prompt = pd.DataFrame([{
            "PromptVersionKey": p.version,
            "PromptName": p.name,
            "Purpose": p.purpose,
            "ChangeType": p.change_type,
            "Hypothesis": p.hypothesis,
        } for p in prompts])
        df_dim_prompt.to_csv(pbi_dir / "Dim_Prompt.csv", index=False)

        # 2. Dim_Scenario
        scenarios = session.query(Scenario).all()
        df_dim_scenario = pd.DataFrame([{
            "ScenarioKey": s.scenario_id,
            "Domain": s.domain,
            "Category": s.category,
            "Subcategory": s.subcategory,
            "Difficulty": s.difficulty,
            "LanguageStyle": s.language_style,
            "ConversationType": s.conversation_type,
            "SeverityIfFailed": s.severity_if_failed,
            "ExpectedAction": s.expected_action,
        } for s in scenarios])
        df_dim_scenario.to_csv(pbi_dir / "Dim_Scenario.csv", index=False)

        # 3. Dim_FailureTaxonomy
        df_dim_taxonomy = pd.DataFrame([{
            "FailureTypeCode": meta.code,
            "FailureTypeName": meta.name,
            "Description": meta.description,
            "DefaultSeverity": meta.default_severity,
            "RemediationGuidance": meta.remediation_guidance,
        } for meta in FAILURE_TAXONOMY.values()])
        df_dim_taxonomy.to_csv(pbi_dir / "Dim_FailureTaxonomy.csv", index=False)

        # 4. Fact_Evaluation
        evals = (
            session.query(Evaluation, ModelResponse.latency_ms)
            .join(ModelResponse, Evaluation.response_id == ModelResponse.response_id)
            .all()
        )
        df_fact_eval = pd.DataFrame([{
            "EvaluationKey": e[0].evaluation_id,
            "BenchmarkRunKey": e[0].benchmark_run_id,
            "ScenarioKey": e[0].scenario_id,
            "PromptVersionKey": e[0].prompt_version,
            "AccuracyScore": e[0].accuracy_score,
            "GroundednessScore": e[0].groundedness_score,
            "InstructionFollowingScore": e[0].instruction_following_score,
            "RelevanceScore": e[0].relevance_score,
            "ConsistencyScore": e[0].consistency_score,
            "SafetyScore": e[0].safety_score,
            "ClarityScore": e[0].clarity_score,
            "OverallScore": e[0].overall_score,
            "PassedFlag": 1 if e[0].passed else 0,
            "CriticalFailFlag": 1 if e[0].is_critical_fail else 0,
            "LatencyMs": e[1],
        } for e in evals])
        df_fact_eval.to_csv(pbi_dir / "Fact_Evaluation.csv", index=False)

        # 5. Fact_FailureEvent
        failures = session.query(FailureEvent).all()
        df_fact_failures = pd.DataFrame([{
            "FailureEventKey": f.failure_id,
            "EvaluationKey": f.evaluation_id,
            "BenchmarkRunKey": f.benchmark_run_id,
            "ScenarioKey": f.scenario_id,
            "PromptVersionKey": f.prompt_version,
            "FailureTypeCode": f.failure_type,
            "Severity": f.severity,
            "Evidence": f.evidence,
            "Diagnosis": f.diagnosis,
        } for f in failures])
        df_fact_failures.to_csv(pbi_dir / "Fact_FailureEvent.csv", index=False)

    print(f"Generated 5 Star-Schema dimensional tables in {pbi_dir}")


if __name__ == "__main__":
    export_power_bi_star_schema()
