-- 04_regression_analysis.sql
-- Direct pair-wise comparison between sequential prompt iterations.
-- Answers: For each scenario, did the prompt change fix a bug, maintain state, or cause a regression?

WITH prompt_pairs AS (
    SELECT
        e_old.scenario_id,
        s.category,
        e_old.prompt_version AS old_version,
        e_new.prompt_version AS new_version,
        e_old.passed AS old_passed,
        e_new.passed AS new_passed,
        e_old.overall_score AS old_score,
        e_new.overall_score AS new_score,
        ROUND(e_new.overall_score - e_old.overall_score, 2) AS score_delta
    FROM evaluations e_old
    JOIN evaluations e_new ON e_old.scenario_id = e_new.scenario_id
    JOIN scenarios s ON e_old.scenario_id = s.scenario_id
    WHERE (e_old.prompt_version = 'V2' AND e_new.prompt_version = 'V3')
       OR (e_old.prompt_version = 'V3' AND e_new.prompt_version = 'V4')
)
SELECT
    old_version || ' -> ' || new_version AS transition,
    category,
    COUNT(scenario_id) AS total_cases,
    SUM(CASE WHEN (old_passed = 0 OR old_passed = false) AND (new_passed = 1 OR new_passed = true) THEN 1 ELSE 0 END) AS resolved_count,
    SUM(CASE WHEN (old_passed = 1 OR old_passed = true) AND (new_passed = 0 OR new_passed = false) THEN 1 ELSE 0 END) AS regressed_count,
    SUM(CASE WHEN (old_passed = 0 OR old_passed = false) AND (new_passed = 0 OR new_passed = false) THEN 1 ELSE 0 END) AS persistent_failures,
    SUM(CASE WHEN (old_passed = 1 OR old_passed = true) AND (new_passed = 1 OR new_passed = true) THEN 1 ELSE 0 END) AS sustained_passes,
    ROUND(AVG(score_delta), 2) AS avg_score_change
FROM prompt_pairs
GROUP BY old_version, new_version, category
ORDER BY transition ASC, regressed_count DESC;
