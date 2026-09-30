-- 02_failure_breakdown.sql
-- Failure frequency, severity distribution, and proportion per prompt version.
-- Answers: Which failure types (F1..F8) dominate in each prompt version?

WITH failure_counts AS (
    SELECT
        fe.prompt_version,
        fe.failure_type,
        fe.severity,
        COUNT(fe.failure_id) AS event_count
    FROM failure_events fe
    GROUP BY fe.prompt_version, fe.failure_type, fe.severity
),
version_totals AS (
    SELECT
        prompt_version,
        COUNT(failure_id) AS total_failures
    FROM failure_events
    GROUP BY prompt_version
)
SELECT
    fc.prompt_version,
    fc.failure_type,
    fc.severity,
    fc.event_count,
    vt.total_failures AS total_version_failures,
    ROUND((CAST(fc.event_count AS FLOAT) / vt.total_failures) * 100.0, 1) AS pct_of_version_failures,
    DENSE_RANK() OVER (PARTITION BY fc.prompt_version ORDER BY fc.event_count DESC) AS failure_rank
FROM failure_counts fc
JOIN version_totals vt ON fc.prompt_version = vt.prompt_version
ORDER BY fc.prompt_version ASC, fc.event_count DESC;
