-- 01_prompt_comparison.sql
-- Comparative performance across prompt versions using CTEs and window functions.
-- Answers: What is the observed quality score, pass rate, and incremental uplift for each prompt?

WITH run_aggregates AS (
    SELECT
        br.prompt_version,
        pv.name AS prompt_name,
        br.benchmark_run_id,
        br.timestamp,
        COUNT(e.evaluation_id) AS total_cases,
        SUM(CASE WHEN e.passed = 1 OR e.passed = true THEN 1 ELSE 0 END) AS passed_cases,
        ROUND(AVG(e.overall_score), 2) AS avg_score,
        ROUND(AVG(e.groundedness_score), 2) AS avg_groundedness,
        ROUND(AVG(e.safety_score), 2) AS avg_safety,
        ROUND(AVG(mr.latency_ms), 1) AS avg_latency_ms,
        ROW_NUMBER() OVER (PARTITION BY br.prompt_version ORDER BY br.timestamp DESC) AS rn
    FROM benchmark_runs br
    JOIN prompt_versions pv ON br.prompt_version = pv.version
    JOIN evaluations e ON br.benchmark_run_id = e.benchmark_run_id
    JOIN model_responses mr ON e.response_id = mr.response_id
    GROUP BY br.prompt_version, pv.name, br.benchmark_run_id, br.timestamp
),
latest_runs AS (
    SELECT *
    FROM run_aggregates
    WHERE rn = 1
),
baseline AS (
    SELECT avg_score AS v1_baseline_score
    FROM latest_runs
    WHERE prompt_version = 'V1'
)
SELECT
    lr.prompt_version,
    lr.prompt_name,
    lr.benchmark_run_id,
    lr.total_cases,
    lr.passed_cases,
    ROUND((CAST(lr.passed_cases AS FLOAT) / lr.total_cases) * 100.0, 1) AS pass_rate_pct,
    lr.avg_score,
    ROUND(lr.avg_score - b.v1_baseline_score, 2) AS observed_uplift_vs_v1,
    ROUND(((lr.avg_score - b.v1_baseline_score) / b.v1_baseline_score) * 100.0, 1) AS relative_uplift_pct,
    lr.avg_groundedness,
    lr.avg_safety,
    lr.avg_latency_ms
FROM latest_runs lr
CROSS JOIN baseline b
ORDER BY lr.prompt_version ASC;
