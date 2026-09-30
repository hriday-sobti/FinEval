-- 06_severity_summary.sql
-- High-level executive risk distribution by severity level (Critical, High, Medium, Low).
-- Answers: How did prompt engineering affect high-risk and critical operational exposures?

WITH severity_counts AS (
    SELECT
        prompt_version,
        severity,
        COUNT(failure_id) AS incident_count
    FROM failure_events
    GROUP BY prompt_version, severity
),
pivoted AS (
    SELECT
        prompt_version,
        SUM(CASE WHEN severity = 'critical' THEN incident_count ELSE 0 END) AS critical_incidents,
        SUM(CASE WHEN severity = 'high' THEN incident_count ELSE 0 END) AS high_incidents,
        SUM(CASE WHEN severity = 'medium' THEN incident_count ELSE 0 END) AS medium_incidents,
        SUM(CASE WHEN severity = 'low' THEN incident_count ELSE 0 END) AS low_incidents,
        SUM(incident_count) AS total_incidents
    FROM severity_counts
    GROUP BY prompt_version
)
SELECT
    prompt_version,
    critical_incidents,
    high_incidents,
    medium_incidents,
    low_incidents,
    total_incidents,
    ROUND((CAST(critical_incidents AS FLOAT) / total_incidents) * 100.0, 1) AS critical_share_pct,
    ROUND((CAST(high_incidents + critical_incidents AS FLOAT) / total_incidents) * 100.0, 1) AS severe_share_pct
FROM pivoted
ORDER BY prompt_version ASC;
