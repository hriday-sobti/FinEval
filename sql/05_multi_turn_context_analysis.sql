-- 05_multi_turn_context_analysis.sql
-- In-depth inspection of multi-turn interactions and context retention performance.
-- Answers: How frequently does context loss (F4) occur across multi-turn interactions in each prompt version?

WITH multi_turn_evals AS (
    SELECT
        s.scenario_id,
        s.subcategory,
        e.prompt_version,
        e.benchmark_run_id,
        e.consistency_score,
        e.overall_score,
        e.passed
    FROM scenarios s
    JOIN evaluations e ON s.scenario_id = e.scenario_id
    WHERE s.conversation_type = 'multi_turn'
),
context_failures AS (
    SELECT
        mte.prompt_version,
        COUNT(DISTINCT mte.scenario_id) AS multi_turn_scenarios_tested,
        COUNT(DISTINCT CASE WHEN fe.failure_type = 'F4' THEN fe.scenario_id END) AS context_loss_cases,
        ROUND(AVG(mte.consistency_score), 2) AS avg_consistency_score,
        ROUND(AVG(mte.overall_score), 2) AS avg_overall_score,
        ROUND((CAST(SUM(CASE WHEN mte.passed = 1 OR mte.passed = true THEN 1 ELSE 0 END) AS FLOAT) / COUNT(mte.scenario_id)) * 100.0, 1) AS multi_turn_pass_rate_pct
    FROM multi_turn_evals mte
    LEFT JOIN failure_events fe ON mte.scenario_id = fe.scenario_id
                                AND mte.prompt_version = fe.prompt_version
                                AND fe.failure_type = 'F4'
    GROUP BY mte.prompt_version
)
SELECT
    prompt_version,
    multi_turn_scenarios_tested,
    context_loss_cases,
    ROUND((CAST(context_loss_cases AS FLOAT) / multi_turn_scenarios_tested) * 100.0, 1) AS context_failure_rate_pct,
    avg_consistency_score,
    avg_overall_score,
    multi_turn_pass_rate_pct
FROM context_failures
ORDER BY prompt_version ASC;
