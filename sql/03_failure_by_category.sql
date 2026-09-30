-- 03_failure_by_category.sql
-- Matrix of scenario categories against pass rates and critical failure occurrences.
-- Answers: Which customer inquiry categories (e.g. Hallucination Trap, Adversarial) are most vulnerable?

WITH scenario_eval_stats AS (
    SELECT
        s.category AS scenario_category,
        e.prompt_version,
        COUNT(e.evaluation_id) AS total_evaluated,
        SUM(CASE WHEN e.passed = 1 OR e.passed = true THEN 1 ELSE 0 END) AS passed_count,
        SUM(CASE WHEN e.is_critical_fail = 1 OR e.is_critical_fail = true THEN 1 ELSE 0 END) AS critical_fail_count,
        ROUND(AVG(e.overall_score), 2) AS category_avg_score
    FROM scenarios s
    JOIN evaluations e ON s.scenario_id = e.scenario_id
    GROUP BY s.category, e.prompt_version
)
SELECT
    scenario_category,
    prompt_version,
    total_evaluated,
    passed_count,
    ROUND((CAST(passed_count AS FLOAT) / total_evaluated) * 100.0, 1) AS category_pass_rate_pct,
    critical_fail_count,
    category_avg_score,
    CASE
        WHEN (CAST(passed_count AS FLOAT) / total_evaluated) >= 0.85 THEN 'HIGH_RELIABILITY'
        WHEN (CAST(passed_count AS FLOAT) / total_evaluated) >= 0.60 THEN 'MODERATE_RISK'
        ELSE 'CRITICAL_VULNERABILITY'
    END AS operational_risk_status
FROM scenario_eval_stats
ORDER BY scenario_category ASC, prompt_version ASC;
