-- Safety Reporting Exception Quality Lab
-- SQL check patterns for a warehouse with equivalent source tables.
-- Table names are illustrative and match the CSV files in data/.

-- 1. Recurring report SLA adherence by report and source system.
SELECT
  report_name,
  cadence,
  source_system,
  COUNT(*) AS report_runs,
  AVG(CASE WHEN sla_met THEN 1.0 ELSE 0.0 END) AS sla_adherence,
  AVG(refresh_delay_hours) AS avg_refresh_delay_hours,
  AVG(completeness_rate) AS avg_completeness,
  SUM(duplicate_keys) AS duplicate_keys,
  SUM(unmapped_records) AS unmapped_records
FROM safety_report_runs
GROUP BY report_name, cadence, source_system
ORDER BY sla_adherence ASC, report_runs DESC;

-- 2. Data quality rule failure rate by source system.
SELECT
  source_system,
  check_name,
  SUM(records_tested) AS records_tested,
  SUM(failed_records) AS failed_records,
  SUM(failed_records) * 1.0 / NULLIF(SUM(records_tested), 0) AS failure_rate
FROM data_quality_checks
GROUP BY source_system, check_name
HAVING SUM(records_tested) > 0
ORDER BY failure_rate DESC;

-- 3. Open high and critical exceptions requiring field support.
SELECT
  region,
  division,
  source_system,
  exception_type,
  severity,
  owner_group,
  COUNT(*) AS open_exceptions,
  MAX(age_days) AS max_age_days,
  SUM(CASE WHEN requires_field_followup THEN 1 ELSE 0 END) AS field_followups
FROM safety_report_exceptions
WHERE status = 'open'
  AND severity IN ('critical', 'high')
GROUP BY region, division, source_system, exception_type, severity, owner_group
ORDER BY open_exceptions DESC, max_age_days DESC;

-- 4. Rollout training segments below an 85 percent completion guardrail.
SELECT
  region,
  division,
  go_live_wave,
  SUM(assigned_employee_partners) AS assigned,
  SUM(completed_employee_partners) AS completed,
  SUM(overdue_employee_partners) AS overdue,
  SUM(completed_employee_partners) * 1.0 / NULLIF(SUM(assigned_employee_partners), 0) AS completion_rate
FROM report_rollout_training
GROUP BY region, division, go_live_wave
HAVING SUM(completed_employee_partners) * 1.0 / NULLIF(SUM(assigned_employee_partners), 0) < 0.85
ORDER BY completion_rate ASC;

-- 5. Field support request turnaround by request type and priority.
SELECT
  request_type,
  priority,
  COUNT(*) AS requests,
  AVG(CASE WHEN met_target THEN 1.0 ELSE 0.0 END) AS target_met_rate,
  AVG(turnaround_hours) AS avg_turnaround_hours
FROM field_support_requests
GROUP BY request_type, priority
ORDER BY target_met_rate ASC, requests DESC;

-- 6. Monthly reporting reliability trend.
SELECT
  SUBSTR(run_date, 1, 7) AS month,
  COUNT(*) AS report_runs,
  AVG(CASE WHEN sla_met THEN 1.0 ELSE 0.0 END) AS sla_adherence,
  AVG(completeness_rate) AS avg_completeness,
  SUM(duplicate_keys) AS duplicate_keys,
  SUM(unmapped_records) AS unmapped_records
FROM safety_report_runs
GROUP BY SUBSTR(run_date, 1, 7)
ORDER BY month;
